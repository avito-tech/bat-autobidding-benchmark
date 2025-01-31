from .utils import price2bin, bin2price
from .modules import SimulationResult, Campaign, History
from ..model.bidder import _Bidder
import pandas as pd
from typing import Tuple


def simulate_step(
    stats_pdf: pd.DataFrame,
    campaign: Campaign,
    bid: float,
    auction_mode: str = 'VCG'
) -> SimulationResult:
    """
    Simulate one step of the auction for a 1-hour period.
    Args:
        stats_pdf: Statistics dataframe
        campaign: Current campaign object
        bid: Bid value
        auction_mode: Auction type, either 'VCG' or 'FPA'. Default is 'VCG'

    Returns:
        SimulationResult: Results of the auction step
    """

    # Convert bid to bin or set to minimum if bid is zero or negative
    bid_price_bin = price2bin(bid) if bid > 0 else -1000

    # Filter stats for the current time window and campaign
    stats_window = stats_pdf[
        (stats_pdf['period'] >= campaign.curr_time) &
        (stats_pdf['period'] < campaign.curr_time + 3600) &
        (stats_pdf['campaign_id'] == campaign.campaign_id)
    ].copy()

    # Aggregate data for bids less than or equal to the current bid
    agg_data = stats_window[
        stats_window['contact_price_bin'] <= bid_price_bin
    ][
        [
            'AuctionWinBidSurplus',
            'AuctionVisibilitySurplus',
            'AuctionClicksSurplus',
            'AuctionContactsSurplus'
        ]
    ].sum()

    # Create SimulationResult based on auction mode
    if auction_mode == 'VCG':
        return SimulationResult(
            spent=agg_data['AuctionWinBidSurplus'],
            visibility=agg_data['AuctionVisibilitySurplus'],
            clicks=agg_data['AuctionClicksSurplus'],
            contacts=agg_data['AuctionContactsSurplus'],
            bid=bid,
        )
    elif auction_mode == 'FPA':
        return SimulationResult(
            spent=agg_data['AuctionContactsSurplus'] * bid,
            visibility=agg_data['AuctionVisibilitySurplus'],
            clicks=agg_data['AuctionClicksSurplus'],
            contacts=agg_data['AuctionContactsSurplus'],
            bid=bid,
        )
    else:
        raise ValueError("auction_mode must be either 'VCG' or 'FPA'")


def simulate_campaign(
    campaign: Campaign,
    bidder: _Bidder,
    stats_file: pd.DataFrame,
    start_time: int = None,
    auction_mode: str = 'VCG'
) -> History:
    """
    Simulate a campaign using historical data.

    Args:
        campaign: Campaign object
        bidder: Bidder object
        stats_file: Historical statistics
        start_time: Start time for simulation. Defaults to None.
        auction_mode: Auction mode ('VCG' or 'FPA'). Defaults to 'VCG'.

    Returns:
        History: Simulation history of spending and clicks
    """
    if start_time:
        campaign.curr_time = start_time // 3600 * 3600
    else:
        campaign.curr_time = campaign.campaign_start // 3600 * 3600

    simulation_history = History()

    bidder_spend = 0
    bidder_clicks = 0
    # For M-PID only, not used for cold start, so could be set any
    campaign_ctr, campaign_cr = 0.0, 0.0
    wp_for_lp = None
    ctr_for_lp = None
    cr_for_lp = None

    while campaign.curr_time < campaign.campaign_end:
        # Request bid from bidder
        bid = bidder.place_bid(
            history=simulation_history,
            bidding_input_params={
                    'item_id': campaign.item_id,
                    'loc_id': campaign.loc_id,
                    'region_id': campaign.region_id,
                    'logical_category': campaign.logical_category,
                    'microcat_ext': campaign.microcat_ext,
                    'balance': campaign.balance,
                    'initial_balance': campaign.initial_balance,
                    'clicks': campaign.clicks,
                    'campaign_id': campaign.campaign_id,
                    'campaign_start_time': campaign.campaign_start,
                    'campaign_end_time': campaign.campaign_end,
                    'curr_time': campaign.curr_time,
                    'prev_balance': campaign.prev_balance,
                    'prev_bid': campaign.prev_bid,
                    'prev_clicks': campaign.prev_clicks,
                    'prev_contacts': campaign.prev_contacts,
                    'prev_time': campaign.prev_time,
                    'desired_clicks': campaign.desired_clicks,
                    'desired_time': campaign.desired_time,
                    'prev_ctr': campaign_ctr,
                    'prev_cr': campaign_cr,
                    'ctr_for_lp': ctr_for_lp,
                    'cr_for_lp': cr_for_lp,
                    'wp_for_lp': wp_for_lp
                }
        )

        # Simulate auction results for a 1-hour window
        simulation_result = simulate_step(
            stats_pdf=stats_file,
            campaign=campaign,
            bid=bid,
            auction_mode=auction_mode,
        )
        bidder_spend = simulation_result.spent
        bidder_clicks = simulation_result.clicks

        # Adjust results if spend exceeds budget
        coef = 1.0
        if simulation_result.spent > campaign.balance:
            coef = campaign.balance / simulation_result.spent

        # Update campaign status
        campaign.prev_balance = campaign.balance
        campaign.prev_clicks = campaign.clicks
        campaign.prev_time = campaign.curr_time
        campaign.prev_bid = bid
        campaign.balance -= simulation_result.spent * coef
        campaign.clicks += simulation_result.clicks * coef
        campaign.contacts += simulation_result.contacts * coef
        campaign.curr_time += 3600

        # Get stats for the current time window
        stats_window = (
            stats_file
            [
                (stats_file['period'] >= campaign.curr_time - 3600) &
                (stats_file['period'] < campaign.curr_time) &
                (stats_file['campaign_id'] == campaign.campaign_id)
            ]
            .copy()
        )

        # Find the nearest stats window with logs
        i = 1
        while stats_window.empty:
            stats_window = (
                stats_file[
                    (stats_file['period'] >= campaign.curr_time - 3600 * i) &
                    (stats_file['period'] < campaign.curr_time - 3600 * (i - 1)) &
                    (stats_file['campaign_id'] == campaign.campaign_id)
                ]
                .copy()
            )
            i += 1

        # Collect CTR, CVR for M-PID with campaign's history
        if any(c.__name__ in ['MPIDBidder', 'SlivkinsBidder'] for c in type(bidder).__mro__):
            # Calculate this only one time through simulation
            if ctr_for_lp is None:
                ctr_for_lp, cr_for_lp, wp_for_lp = ctr_cvr_count_for_lp(stats_window)

            campaign_ctr, campaign_cr = ctr_cvr_count(stats_window, bid)
            # print(campaign_ctr)

        # Add record to simulation history
        simulation_history.add(
            campaign=campaign,
            bid=bid,
            spend=bidder_spend,
            clicks=bidder_clicks
        )
        if campaign.balance < 0.00001:
            break

    return simulation_history


def ctr_cvr_count(stats_window: pd.DataFrame, bid: float) -> Tuple[float, float]:
    """
    Calculate CTR and CVR based on the closest bin to the given bid.
    """
    filtered_bins = stats_window[stats_window.contact_price_bin > price2bin(bid)]['contact_price_bin']
    if not filtered_bins.empty:
        closest_bin = filtered_bins.min()
    else:
        closest_bin = stats_window['contact_price_bin'].max()
    campaign_ctr = stats_window[stats_window.contact_price_bin == closest_bin]['CTRPredicts'].max()
    campaign_cr = stats_window[stats_window.contact_price_bin == closest_bin]['CRPredicts'].max()
    return campaign_ctr, campaign_cr


def ctr_cvr_count_for_lp(stats_window: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Extract CTR, CVR, and winning prices for LP problem in M-PID.
    """
    campaign_ctr = stats_window['CTRPredicts']
    campaign_cr = stats_window['CRPredicts']
    wp_for_lp = bin2price(stats_window['contact_price_bin'])
    return campaign_ctr, campaign_cr, wp_for_lp
