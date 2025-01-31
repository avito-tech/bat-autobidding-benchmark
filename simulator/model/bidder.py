from typing import Dict
from ..simulation.modules import History
from abc import ABC, abstractmethod


class _Bidder(ABC):
    """
    Abstract base class for bidding strategies.

    This class defines the template for all bidder implementations.
    Subclasses must implement the `place_bid` method.

    Attributes:
        Any custom attributes can be added in subclasses.

    Methods:
        __init__: Initialize the bidder (can be overridden in subclasses).
        place_bid: Abstract method to calculate and return a bid.
    """

    def __init__(self):
        """
        Initialize the bidder.

        This method can be overridden in subclasses to set up any necessary attributes or state.
        """
        pass

    @abstractmethod
    def place_bid(self, bidding_input_params: Dict[str, any], history: History) -> float:
        """
        Calculate and return a bid based on input parameters and auction history.

        This method must be implemented by all subclasses.

        Args:
            bidding_input_params (Dict[str, any]): A dictionary containing bidding input parameters.
                Keys include:
                - 'item_id': ID of the item
                - 'campaign_id': ID of the paid campaign
                - 'loc_id': Location ID
                - 'region_id': Region ID
                - 'logical_category': Item category
                - 'microcat_ext': Extended item category
                - 'initial_balance': Starting balance of the campaign
                - 'campaign_start_time': Timestamp of campaign start
                - 'campaign_end_time': Timestamp of campaign end
                - 'curr_time': Current timestamp
                - 'prev_time': Timestamp of last calculation
                - 'prev_bid': Bid from the last calculation
                - 'clicks': Total clicks collected by the campaign
                - 'prev_clicks': Clicks at the last calculation
                - 'balance': Current campaign balance
                - 'prev_balance': Balance at the last calculation
                Additional parameters can be included as needed.

            history: Auction history for the specific campaign.
                Note: History does not carry over between campaigns.
                The bidder class is reinitialized when simulating a new campaign.

        Returns:
            float: The calculated bid amount.
        """
        raise NotImplementedError("Subclasses must implement place_bid method")
