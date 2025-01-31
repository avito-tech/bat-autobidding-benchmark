#  Section Adaptive Linear Model (ALM)

import numpy as np
from simulator.model.bidder import _Bidder
from simulator.model.traffic import Traffic
from simulator.simulation.modules import History
from simulator.simulation.utils import bin2price, price2bin


class LinearBidder(_Bidder):
    default_params = {
        'traffic_path': '../data/traffic_share.csv',
        'cold_start_coef': 0.3,
        'factor': 2.5,
        'lower_clip': 5,
        'upper_clip': 5
    }

    def __init__(self, params: dict = None):
        """
        Baseline solution implementing a simple controller.
        Uses linear prediction of spending rate and traffic share table.

        The algorithm's goal is to ensure the budget is exhausted
        at the moment the promotion campaign ends.

        General idea:
        - Take current and previous auto-bidding runs, plot a line on the spend(traffic) graph
        - Check the function value at the point spend(traffic = traffic at campaign end)
        - Take the delta with zero, multiply by a coefficient, add to the bid bin
        """
        super().__init__()

        params = params or {}
        self.traffic = Traffic(path=params.get("traffic_path", self.default_params['traffic_path']))
        self.cold_start_coef = params.get("cold_start_coef", self.default_params['cold_start_coef'])
        self.lower_clip = params.get("lower_clip", self.default_params['lower_clip'])
        self.upper_clip = params.get("upper_clip", self.default_params['upper_clip'])
        self.factor = params.get("factor", self.default_params['factor'])

    def place_bid(self, bidding_input_params, history: History) -> float:
        """
        Place a bid based on the current state and history of the campaign.
        """
        initial_balance = bidding_input_params['initial_balance']
        start = bidding_input_params['campaign_start_time']
        end = bidding_input_params['campaign_end_time']

        # Cold start bid
        if len(history.rows) == 0:
            return initial_balance * self.cold_start_coef

        region_id = bidding_input_params['region_id']
        logical_category = bidding_input_params['logical_category']
        curr_time = bidding_input_params['curr_time']
        prev_time = bidding_input_params['prev_time']
        balance = bidding_input_params['balance']
        prev_balance = bidding_input_params['prev_balance']
        prev_bid = bidding_input_params['prev_bid']

        cur_traffic = self.traffic.get_traffic_share(region_id, start, curr_time)
        prev_traffic = self.traffic.get_traffic_share(region_id, start, prev_time)
        left_traffic = self.traffic.get_traffic_share(region_id, curr_time, end)

        # Don't adjust bid during night hours
        lower_clip = self.lower_clip
        upper_clip = self.upper_clip
        if logical_category in ('Transport.UsedCars',):
            upper_clip = 1
            if cur_traffic - prev_traffic == 0:
                return prev_bid
        else:
            if cur_traffic - prev_traffic < 1 / 24 / 7 / 2:
                return prev_bid

        # Convert balance to relative values
        balance = balance / initial_balance
        prev_balance = prev_balance / initial_balance
        # Formula from section Adaptive Linear Model (ALM), k=\frac{\hat{B}_{n}-\hat{B}_{n-1}}{T_n-T_{n-1}}:
        slope = (balance - prev_balance) / (cur_traffic - prev_traffic)
        # Formula from section Adaptive Linear Model (ALM), \hat{B}_{left}=\hat{B}_n+k\cdot T_{left}
        balance_at_end = balance + slope * left_traffic

        # Apply linear correction to the bid bin
        # price = 1.2**bin
        # Bins are used in production for bid discretization, and there's a ready-made conversion function
        # For auto-bidding purposes, any other function could be used
        prev_bin = price2bin(prev_bid)
        bin_ = prev_bin + balance_at_end * self.factor

        # Bid changes by no more than a factor of 2
        bin_ = np.clip(bin_, prev_bin - lower_clip, prev_bin + upper_clip)
        bid = bin2price(bin_)

        return bid
