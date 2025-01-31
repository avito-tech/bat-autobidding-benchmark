# [1] https://arxiv.org/pdf/1905.10928

import numpy as np
from typing import Tuple, Dict, Any
from scipy.optimize import linprog

from simulator.model.bidder import _Bidder
from simulator.model.traffic import Traffic
from simulator.simulation.modules import History


class MPIDBidder(_Bidder):
    default_k_dict = {
        'k_p': (4.377576468445429e-06, 0.0333706926755201),
        'k_i': (0.5624063314848002, 0.6955061331189949),
        'k_d': (0.008335020922363772, 0.003801165974001581)
    }

    default_params = {
        'B': 1000.0,
        'n': 1,
        'k_dict': None,
        'correction': [0.22, 0.37],
        'auction_mode': 'FPA',
        'log': False,
        'cold_start_coef': 0.37,
        'lower_clip': 0.5,
        'upper_clip': 2,
        'bid_factor': 1,
        'traffic_path': '../data/traffic_share.csv',
    }

    def __init__(self, params: dict = None):
        super().__init__()

        params = params or {}
        self.B = params.get('B', self.default_params['B'])
        self.n = params.get('n', self.default_params['n'])
        self.k_dict = params.get('k_dict', self.default_params['k_dict']) or self.default_k_dict
        self.correction = params.get('correction', self.default_params['correction'])
        self.auction_mode = params.get('auction_mode', self.default_params['auction_mode'])
        self.log = params.get('log', self.default_params['log'])
        self.cold_start_coef = params.get('cold_start_coef', self.default_params['cold_start_coef'])
        self.lower_clip = params.get('lower_clip', self.default_params['lower_clip'])
        self.upper_clip = params.get('upper_clip', self.default_params['upper_clip'])
        self.bid_factor = params.get('bid_factor', self.default_params['bid_factor'])
        self.temp_constr = 25
        self.temp_coef = 5

        if self.B <= 0 or self.n <= 0:
            raise ValueError("B and n must be positive")

        alpha, beta = self.correction
        self.correction = np.array([[alpha, 1 - alpha], [1 - beta, beta]])

        if self.auction_mode not in {'FPA', 'VCG'}:
            raise ValueError(f"Wrong auction mode: {self.auction_mode}. Only 'VCG' and 'FPA' are accepted.")

        self.n = int(2 * self.B)
        self.traffic_path = params.get('traffic_path') or self.default_params["traffic_path"]
        self._load_data()
        self._init_params(self.B)

    def _load_data(self) -> None:
        '''
        Loads data files with respect to the auction mode
        '''
        self.traffic = Traffic(path=self.traffic_path)

    def _init_params(self, B):
        constraint = B / self.temp_constr
        # Desired clicks, same as for the autobidder_check function
        # n = max(1, B // 100.0)  # Formula from section Model predictive PID (M-PID), for CPC
        # Initial state vector [p, q]
        self.x_0: np.ndarray = np.array([0, 0])
        # Error history for PID controller
        self.error: np.ndarray = np.empty((0, 2))
        # Click counters
        self.click: float = 0.0
        self.last_click: float = 0.0
        # Bid adjustment factor
        self.bid_factor: float = 2.5
        cpc = constraint  # Cost per click is adjusted as a campaign's budget
        # Reference vector for PID controller [budget_pace, desired_cpc]
        self.reference: np.ndarray = np.array([0, cpc])
        self.C: float = constraint
        # Minimum allowed bid
        self.min_bid = constraint // self.temp_coef
        # Initial bid for cold start
        self.init_bid: float = self.C * self.cold_start_coef
        # List to store previous bids
        self.prev_bids: list = [self.init_bid]

    def place_bid(self, bidding_input_params, history: History) -> float:
        # Calculate budget pace from step 0 to current
        budget_pace = self.budget_pace_count(bidding_input_params)
        self.reference[0] = budget_pace
        self.last_click = bidding_input_params['clicks'] - bidding_input_params['prev_clicks']
        self.u = self.reference
        if len(history.rows) == 0:
            # Cold start: return a simple initial bid
            return self.init_bid
        elif len(history.rows) == 1:
            # Chilly start: use LP solver
            p, q = self.calculate_pq(bidding_input_params)
            self.x_0 = np.array([p, q])
        else:
            # Regular bidding process
            spent = bidding_input_params['prev_balance'] - bidding_input_params['balance']
            cur_cpc = (
                    (bidding_input_params['initial_balance'] - bidding_input_params['balance']) /
                    bidding_input_params['clicks']
                ) if bidding_input_params['clicks'] > 0 else 0
            y = np.array([spent, cur_cpc])
            self.click = bidding_input_params['clicks']
            p, q = self.pid_compute(self.reference, y)

        CTR, CVR = bidding_input_params['prev_ctr'], bidding_input_params['prev_cr']
        bid = max(self.bid_compute(p, q, self.C, CTR, CVR), self.min_bid)
        mean_bid = sum(self.prev_bids) / len(self.prev_bids)
        bid = np.clip(bid, self.lower_clip * mean_bid, self.upper_clip * mean_bid)
        self.prev_bids.append(bid)
        return bid

    def pid_compute(self, reference, y) -> Tuple[float, float]:
        cur_error = reference - y  # 2d array

        if self.last_click:
            cur_error[1] *= self.last_click
        self.error = np.append(self.error, [cur_error], axis=0)

        k_i = self.k_dict['k_i']
        k_p = self.k_dict['k_p']
        k_d = self.k_dict['k_d']

        u = k_p * self.error[-1] + k_i * sum(self.error) +\
            (k_d * (self.error[-1] - self.error[-2]) if len(self.error) > 1 else 0)
        if self.click:
            u[1] /= self.click
        u = self.apply_alpha(u)
        x = self.x_0 * np.exp(-np.clip(u, -700, 700))
        self.u = u
        return x

    def apply_alpha(self, u):
        # Apply correction to u_p(t) and u_q(t)
        u_new_p = self.correction[0][0] * u[0] + self.correction[0][1] * u[1]
        u_new_q = self.correction[1][0] * u[0] + self.correction[1][1] * u[1]
        return np.array([u_new_p, u_new_q])

    def bid_compute(self, p: float, q: float, C: float, CTR: float, CVR: float) -> float:
        p_q = max(p + q, 1e-4)
        bid = (CVR + CTR * C * q) / p_q  # Section "Model predictive PID (M-PID)" from [1], formula of bid
        return self.cold_start_coef * bid

    def budget_pace_count(self, bidding_input_params: Dict[str, Any]) -> float:
        region_id = bidding_input_params['region_id']
        end = bidding_input_params['campaign_end_time']
        curr_time = bidding_input_params['curr_time']

        left_traffic = self.traffic.get_traffic_share(region_id, curr_time, end)
        if left_traffic:
            balance = bidding_input_params['balance']
            cur_traffic = self.traffic.get_traffic_share(region_id, curr_time, curr_time + 3600)
            # Section "Model predictive PID (M-PID)" from [1], ideal spending formula
            return balance * (cur_traffic / left_traffic)
        else:
            return 0

    def calculate_pq(self, bidding_input_params: Dict[str, Any]) -> Tuple[float, float]:
        # Section Problem formulation from [1], linear programming problem
        wp = bidding_input_params['wp_for_lp']
        ctr = bidding_input_params['ctr_for_lp']
        cvr = bidding_input_params['cr_for_lp']
        B, C, N = self.B, self.C, cvr.shape[0]
        c = np.ones(N + 2)
        c[-2], c[-1] = B, 0
        A_up = -1 * np.vstack((np.vstack((np.eye(N), wp)), wp - ctr * C)).T
        res = linprog(c=c, A_ub=A_up, b_ub=-np.array(cvr), bounds=(0, None))
        p, q = res.x[-2], res.x[-1]
        return max(p, 0.1), max(q, 0.1)
