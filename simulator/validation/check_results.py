import pandas as pd
from time import time
from typing import Type, Dict, Any, List
from simulator.simulation.simulate import simulate_campaign
from simulator.simulation.modules import Campaign
from simulator.validation.metrics import compile_metrics


def autobidder_check(
    bidder: Type,
    params: Dict[str, Any],
    auction_mode: str = 'VCG',
    mean_click_price: float = 5.0
) -> Dict[str, Any]:
    """
    Perform an automated check of a bidding strategy across multiple campaigns.

    This function simulates campaigns using the provided bidder and compiles performance metrics.

    Args:
        bidder: The bidder class to be used in simulations.
        params: Dictionary containing simulation parameters.
        auction_mode: The auction mode to use. Defaults to 'VCG'.
        category: The category of campaigns to simulate. Defaults to 'Transport'.

    Returns: A dictionary containing simulation results and performance metrics.
    """
    status = "OK!"
    status_msg = ""
    time_all_start = time()

    data_campaigns = pd.read_csv(params["input_campaigns"]).reset_index()
    data_stats = pd.read_csv(params["input_stats"])

    time_inf_start = time()
    hist_data_list: List[pd.DataFrame] = []

    for _, campaign in data_campaigns.iterrows():
        campaign_instance = create_campaign_instance(campaign, mean_click_price)
        bidder_instance = bidder(params)

        sim_hist = simulate_campaign(
            campaign=campaign_instance,
            bidder=bidder_instance,
            stats_file=data_stats[data_stats.campaign_id == int(campaign['campaign_id'])].copy(),
            auction_mode=auction_mode
        )
        hist_data_list.append(sim_hist.to_data_frame())
        break

    time_inf_end = time()

    metrics = compile_metrics(pd.concat(hist_data_list, axis=0, ignore_index=True))

    time_all_end = time()
    return {
        "status": status,
        "status_msg": status_msg,
        "time_overall_sec": time_all_end - time_all_start,
        "time_inference_sec": time_inf_end - time_inf_start,
        "score": metrics
    }


def create_campaign_instance(campaign: pd.Series, mean_click_price: float) -> Campaign:
    """
    Create a Campaign instance from a pandas Series.
    """
    return Campaign(
        item_id=campaign['item_id'],
        campaign_id=int(campaign['campaign_id']),
        loc_id=int(campaign["loc_id"]),
        region_id=int(campaign["region_id"]),
        logical_category=campaign["logical_category"],
        microcat_ext=int(campaign["microcat_ext"]),
        campaign_start=int(campaign["campaign_start"]),
        campaign_end=int(campaign["campaign_end"]),
        initial_balance=campaign['auction_budget'],
        balance=campaign['auction_budget'],
        curr_time=int(campaign["campaign_start"]),
        prev_time=int(campaign["campaign_start"]),
        prev_balance=campaign['auction_budget'],
        prev_bid=0,
        prev_clicks=0,
        desired_clicks=max(1, campaign['auction_budget'] // mean_click_price),
        desired_time=(int(campaign["campaign_end"]) - int(campaign["campaign_start"])) // 3600,
    )
