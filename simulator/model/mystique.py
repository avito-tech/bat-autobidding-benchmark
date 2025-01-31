# https://www.yahooinc.com/research/publications/mystique-a-budget-pacing-system-for-performance-optimization-in-online-advertising

import numpy as np
from simulator.model.bidder import _Bidder
from simulator.simulation.modules import History
from simulator.model.traffic import Traffic
from typing import Dict


class Mystique(_Bidder):
    default_params = {
        'traffic_path': '../data/traffic_share.csv',
        'pf0': 300,
        'C_max': 50,
        'C_min': 5,
        'E_max': 10,
        'E_gmc': 10
    }

    def __init__(self, params: dict = None):
        super().__init__()

        self.day_initial_balance = 0
        self.count = 0

        params = params or {}

        self.traffic = Traffic(path=params.get("traffic_path", self.default_params['traffic_path']))
        self.C_max = params.get('C_max', self.default_params['C_max'])
        self.C_min = params.get('C_min', self.default_params['C_min'])
        self.E_max = params.get('E_max', self.default_params['E_max'])
        self.E_gmc = params.get('E_gmc', self.default_params['E_gmc'])

        self.balance_previous = np.array([])
        self.bid_previous = np.array([])
        self.timestamp_previous = np.array([])

    def place_bid(self, bidding_input_params: Dict[str, any], history: History) -> float:
        self.count += 1
        start = bidding_input_params['campaign_start_time']
        end = bidding_input_params['campaign_end_time']
        initial_balance = bidding_input_params['initial_balance']
        balance = bidding_input_params['balance']
        curr_time = bidding_input_params['curr_time']

        if len(self.bid_previous) == 0:
            self.balance_previous = np.pad(
                self.balance_previous,
                pad_width=[0, 1],
                constant_values=balance,
            )
            self.timestamp_previous = np.pad(
                self.timestamp_previous,
                pad_width=[0, 1],
                constant_values=curr_time,
                )
            self.bid_previous = np.pad(
                self.bid_previous,
                pad_width=[0, 1],
                constant_values=300.0,
                )
            return 300.0
        else:
            day = (curr_time-start) // 3600 // 24
            hour = (curr_time-start) // 3600 % 24
            desired_days = (end-start) // 3600 // 24
            day_quote = initial_balance / desired_days

            region_id = bidding_input_params['region_id']
            traffic_campaign = self.traffic.get_traffic_share(region_id, start, end)
            hours = np.arange(start, curr_time, 3600)
            traffic_list = np.array([self.traffic.get_traffic_share(region_id, hour0, hour0 + 3600) for hour0 in hours])
            traffic_list = traffic_list / traffic_campaign if traffic_campaign != 0 else np.zeros_like(traffic_list)
            target_spend = initial_balance * np.cumsum(traffic_list)
            initial_day_balance = None
            # Find initial_day_balance
            hour_previous = [(t - start) // 3600 % 24 for t in self.timestamp_previous]

            if day == 0:
                initial_day_balance = initial_balance
            else:
                if hour_previous[-1] > hour:
                    initial_day_balance = self.balance_previous[-1]
                else:
                    for i in range(len(hour_previous) - 1, max(-1, len(hour_previous)-12), -1):
                        if hour_previous[i] < hour_previous[i-1]:
                            initial_day_balance = self.balance_previous[i]
                            break

            if initial_day_balance is None:
                initial_day_balance = self.balance_previous[-1]

            if initial_day_balance - balance >= day_quote:
                if self.count % 3 != 1:
                    bid = self.bid_previous[-1]
                else:
                    bid = 0.95 * self.bid_previous[-1]

                self.balance_previous = np.pad(
                    self.balance_previous,
                    pad_width=[0, 1],
                    constant_values=balance,
                )

                self.timestamp_previous = np.pad(
                    self.timestamp_previous,
                    pad_width=[0, 1],
                    constant_values=curr_time,
                )

                self.bid_previous = np.pad(
                    self.bid_previous,
                    pad_width=[0, 1],
                    constant_values=bid,
                )
                return bid

            else:
                spend_error = (initial_balance - balance - target_spend[int(hour)])

                # Calculate gradient error
                if int(hour) > 0:
                    desired_gradient = (target_spend[int(hour)] - target_spend[int(hour)-1]) / 3600
                    real_gradient = (self.balance_previous[-1] - balance) / (curr_time - self.timestamp_previous[-1])
                    gradient_spend_error = real_gradient - desired_gradient
                else:
                    gradient_spend_error = 0

                # Calculate tau and weights
                if gradient_spend_error == 0:
                    tau = 1000000
                else:
                    tau = -spend_error / gradient_spend_error

                if tau < 0:
                    ws = 0.5
                    wg = 0.5
                else:
                    ws = min(0.9, 0.2 * tau)
                    wg = 1 - ws

                # Final bid calculation
                spend_error_c = min(self.C_max, self.C_max * abs(spend_error) / self.E_max)

                gradient_spend_error_i = min(1, abs(gradient_spend_error))
                gradient_spend_error_c = max(self.C_min, self.C_max * gradient_spend_error_i / self.E_gmc)

                if self.count % 3 != 1:
                    bid = self.bid_previous[-1]
                else:
                    bid = self.bid_previous[-1] - ws * spend_error_c * np.sign(spend_error) - \
                      wg * gradient_spend_error_c * np.sign(gradient_spend_error)

                self.balance_previous = np.pad(
                    self.balance_previous,
                    pad_width=[0, 1],
                    constant_values=balance,
                )
                self.timestamp_previous = np.pad(
                    self.timestamp_previous,
                    pad_width=[0, 1],
                    constant_values=curr_time,
                )
                self.bid_previous = np.pad(
                    self.bid_previous,
                    pad_width=[0, 1],
                    constant_values=bid,
                )

                return bid
