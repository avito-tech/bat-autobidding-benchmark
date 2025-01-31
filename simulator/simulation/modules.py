from dataclasses import dataclass
from datetime import datetime
import pandas as pd


@dataclass
class SimulationResult:
    """
    Represents the results of auction simulations for a one-hour period.

    Attributes:
        bid: The bid amount used in the auctions.
        spent: Total amount spent during the simulations.
        visibility: Measure of ad visibility or impressions.
        clicks: Number of clicks received.
        contacts: Number of user contacts or interactions.
    """
    bid: float = 0
    spent: int = 0
    visibility: int = 0
    clicks: int = 0
    contacts: int = 0

    def to_dict(self) -> dict:
        return {
            'bid': self.bid,
            'spent': self.spent,
            'visibility': self.visibility,
            'clicks': self.clicks,
            'contacts': self.contacts,
        }


@dataclass
class Campaign:
    """
    Represents a campaign model for simulation purposes.

    This class encapsulates all relevant attributes and metadata
    for simulating an advertising campaign's performance in auctions.
    """
    item_id: int = 0
    campaign_id: int = 0
    campaign_start: int = 0
    campaign_end: int = 0
    initial_balance: float = 0.0
    balance: float = 0.0
    clicks: float = 0
    contacts: float = 0
    curr_time: int = 0
    loc_id: int = 0
    region_id: int = 0
    logical_category: str = ""
    microcat_ext: int = 0
    prev_time: int = 0
    prev_bid: float = 0
    prev_clicks: float = 0
    prev_balance: float = 0
    prev_contacts: float = 0
    desired_clicks: int = 0  # clicks desired
    desired_time: int = 0  # lifetime desired, in hours

    def to_dict(self):
        return {
            'curr_time': self.curr_time,
            'curr_time_str': datetime.strftime(
                datetime.fromtimestamp(self.curr_time),
                '%Y-%m-%d %H-%M'
            ),
            'campaign_id': self.campaign_id,
            'balance': self.balance,
            'clicks': self.clicks,
            'contacts': self.contacts,
            'item_id': self.item_id,
            'loc_id': self.loc_id,
            'region_id': self.region_id,
            'logical_category': self.logical_category,
            'microcat_ext': self.microcat_ext,
            'initialBalance': self.initial_balance,
            'campaignStartTime': self.campaign_start,
            'campaignEndTime': self.campaign_end,
            'prev_time': self.prev_time,
            'prev_bid':  self.prev_bid,
            'prev_clicks': self.prev_clicks,
            'prev_balance': self.prev_balance,
            'prev_contacts': self.prev_contacts,
        }


class History:
    """
    Aggregates and manages simulation results for auction outcomes of a single campaign.

    This class provides methods to add simulation results and convert them
    to a pandas DataFrame for further analysis.
    """
    def __init__(self):
        self.rows = []

    def add(self, campaign: Campaign, bid: float, spend: list, clicks: list) -> None:
        curr_time_str = datetime.fromtimestamp(campaign.curr_time)

        d = {
            'curr_time': curr_time_str,
            'curr_timestamp': campaign.curr_time,
            'campaign_start_time': campaign.campaign_start,
            'campaign_end_time': campaign.campaign_end,
            'campaign_id': campaign.campaign_id,
            'balance': campaign.balance,
            'initial_balance': campaign.initial_balance,
            'clicks': campaign.clicks,
            'contacts': campaign.contacts,
            'bid': bid,
            'loc_id': campaign.loc_id,
            'region_id': campaign.region_id,
            'logical_category': campaign.logical_category,
            'microcat_ext': campaign.microcat_ext,
            'prev_timestamp': campaign.prev_time,
            'desired_clicks': campaign.desired_clicks,
            'desired_time': campaign.desired_time,
            'spend_history': spend,
            'clicks_history': clicks
        }
        self.rows.append(d)

    def to_data_frame(self) -> pd.DataFrame:
        return pd.DataFrame(self.rows)
