# https://arxiv.org/pdf/2301.13306

import numpy as np
from typing import Dict
from simulator.model.bidder import _Bidder
from simulator.simulation.modules import History


class BROI(_Bidder):
    default_params = {
        'theta': 0.,
        'ro': 4,
        'v_bar': 100
    }

    def __init__(self, params: dict = None):
        super().__init__()

        params = params or {}

        self.theta = params.get("theta", self.default_params['theta'])
        self.w = 0.1
        self.ro = params.get("ro", self.default_params['ro'])
        self.v_bar = params.get("v_bar", self.default_params['v_bar'])
        self.gamma = self.theta

        self.mu_roi = self.gamma - 1
        self.mu_budget = 1 / (2 * self.ro)
        self.eta_roi = 1 / self.v_bar
        self.eta_budget = min(1 / self.ro, 1 / self.v_bar)
        self.history_value = np.array([])

    def place_bid(self, bidding_input_params: Dict[str, any], history: History) -> float:
        initial_balance = bidding_input_params['initial_balance']
        self.theta = initial_balance
        self.w = 0.1
        self.gamma = self.theta * bidding_input_params['prev_ctr'] / self.w
        self.mu_roi = self.gamma - 1
        delta_mu_roi, delta_mu_budget = 0, 0

        # if we don't have any clicks on previous step
        # we never update mu_roi, update only mu_budget
        if len(history.rows):
            price = np.sum(history.rows[-1]["spend_history"])
            x = 1 if price else 0  # history.rows[-1]["clicks"] # in [0,1]
            value = bidding_input_params['prev_ctr'] * self.theta
            self.history_value = np.append(self.history_value, value)

            delta_mu_roi = self.eta_roi * x * (self.gamma * price - value)
            delta_mu_budget = self.eta_budget * (x * price - self.ro)

        if len(history.rows) > 1:
            # optimistic realization
            x_prev = history.rows[-2]["clicks"]
            price_prev = np.sum(history.rows[-2]["spend_history"])

            value_prev = self.history_value[-2]

            delta_mu_roi = delta_mu_roi * 2 - self.eta_roi * x_prev * (self.gamma * price_prev - value_prev)
            delta_mu_budget = delta_mu_budget * 2 - self.eta_budget * (x_prev * price_prev - self.ro)

        self.mu_budget += delta_mu_budget
        self.mu_roi += delta_mu_roi

        self.mu_budget = max(min(self.mu_budget, 1 / (2 * self.ro)), 0)
        self.mu_roi = max(min(self.mu_roi, self.gamma - 1), 0)

        if len(history.rows) == 0:
            value = bidding_input_params['prev_ctr'] * self.theta

        mu = np.max([self.mu_roi, self.mu_budget, 0])
        min_bid = 1.2**10
        bid = max(min_bid, value / (mu + 1))

        return bid
