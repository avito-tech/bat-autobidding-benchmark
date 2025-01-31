# Section Traffic-aware PID (TA-PID)

import numpy as np
from typing import Dict, Any
from datetime import datetime
from ..simulation.modules import History
from ..simulation.utils import bin2price
from .traffic import Traffic
from .bidder import _Bidder
from random import random


k_dict = {
    "k_p": 1e-3,
    "k_i": 1e-4,
    "k_d": 6e-5,
}


def PIDcontrol(
        avg_spend: float,
        initial_balance: float,
        balance: list,
        tr_share: list,
        k_dict: dict
):
    """
    Method for managing bid correction using PID control.
    """
    if tr_share.shape[0] < 3:
        return 0
    tr_cumsum = tr_share
    # Error function: difference between ideal average spend and current
    err_func = (
        avg_spend -
        (initial_balance - balance) /
        np.where(tr_cumsum > 0, tr_cumsum, 0.005)
    )

    K_p = k_dict["k_p"]
    T_i = k_dict["k_p"] / k_dict["k_i"]
    T_d = k_dict["k_d"] / k_dict["k_p"]
    res = None

    if tr_cumsum[-1] == tr_cumsum[-2]:
        res = 0.0
    else:
        dt = tr_cumsum[-1] - tr_cumsum[-2]
        # Proportional component
        p_part = K_p*err_func[-1]
        # Integral component
        i_part = K_p/T_i*np.dot(
            err_func[1:],
            tr_cumsum[1:] - tr_cumsum[:-1]
        )
        # Differential component
        d_part = K_p * T_d / dt * (
            err_func[-1] - err_func[-2]
        )
        res = p_part + i_part + d_part

    return res


class TAPIDBidder(_Bidder):
    default_params = {
        'traffic_path': '../data/traffic_share.csv',
        'k_dict': k_dict,
        'cold_start_coef': 0.37,
        'sampling': 1,
    }

    def __init__(self, params: dict = None):
        super().__init__()

        params = params or {}
        self.campaign_traffic = None
        self.traffic_share_history = np.array([])
        self.balance_history = np.array([])
        self.spend_history = np.array([])
        self.times = np.array([])
        self.traffic = Traffic(path=params.get("traffic_path", self.default_params['traffic_path']))
        self.hist_len = params.get("hist_len", 10_000)
        self.sampling = params.get("sampling", self.default_params['sampling'])
        self.k_dict = params.get("k_dict", self.default_params['k_dict'])
        self.coef = params.get("coef", self.default_params['cold_start_coef'])

    def place_bid(self, bidding_input_params: Dict[str, Any], history: History) -> float:
        """
        Place a bid based on the current state and history of the campaign.
        """
        history = history.rows
        # Cold start bid
        cold_start_bid = bidding_input_params['initial_balance'] * self.coef
        if len(history) == 0:
            return cold_start_bid

        region_id = bidding_input_params['region_id']
        start = bidding_input_params['campaign_start_time']
        end = bidding_input_params['campaign_end_time']
        curr_time = bidding_input_params['curr_time']
        balance = bidding_input_params['balance']
        initial_balance = bidding_input_params['initial_balance']
        prev_balance = bidding_input_params['prev_balance']
        prev_bid = bidding_input_params['prev_bid']
        assert start < end
        assert (curr_time < end) & (curr_time > start)

        # Simulate calculator computation skips
        if random() > self.sampling:
            return prev_bid

        self.balance_history = np.pad(
            self.balance_history,
            pad_width=[0, 1],
            constant_values=balance,
        )

        self.times = np.pad(
            self.times,
            pad_width=[0, 1],
            constant_values=curr_time,
        )

        self.spend_history = np.pad(
            self.spend_history,
            pad_width=[0, 1],
            constant_values=-balance + (prev_balance or 0),
        )

        if self.times.shape[0] > 1:
            self.traffic_share_history = np.pad(
                self.traffic_share_history,
                pad_width=[0, 1],
                constant_values=self.traffic.get_traffic_share(
                    region_id,
                    start,
                    self.times[-1],
                ),
            )
        else:
            self.traffic_share_history = np.pad(
                self.traffic_share_history,
                pad_width=[0, 1],
                constant_values=0,
            )

        if not self.campaign_traffic:
            self.campaign_traffic = self.traffic.get_traffic_share(
                region_id,
                start,
                end
            )
            if self.campaign_traffic == 0:
                return cold_start_bid
            self.avg_spend = initial_balance / self.campaign_traffic

        action = PIDcontrol(
            self.avg_spend,
            initial_balance,
            # Simulate history length limitation
            self.balance_history[-self.hist_len:] if self.hist_len else self.balance_history,
            self.traffic_share_history[-self.hist_len:] if self.hist_len else self.traffic_share_history,
            k_dict=self.k_dict
        )

        hour = datetime.fromtimestamp(curr_time).hour
        #  Limit bid change amplitude during night hours
        if 1 <= hour <= 6:
            action = action / 5

        # We don't use price2bin util function, since
        # it's important not to round the bid bin for accumulating changes
        prev_bin = np.log(prev_bid) / np.log(1.2)
        bin_ = prev_bin + action

        # Limit bid change from the previous bid
        bin_ = np.clip(bin_, prev_bin - 7, prev_bin + 4)
        bid = bin2price(bin_)

        return bid
