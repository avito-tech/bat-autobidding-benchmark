import pandas as pd
import numpy as np
from typing import List, Tuple
from simulator.model.traffic import Traffic
# Section Metrics


def clicks_sum_metric(clicks: pd.Series, desired_clicks: pd.Series) -> float:
    """
    Calculate the mean ratio between actual clicks and desired clicks.

    Args:
        clicks: Series of actual click counts.
        desired_clicks: Series of desired click counts.

    Returns: Mean percentage of achieved clicks relative to desired clicks.
    """
    clicks_sum = clicks.sum()  # Formula from section Metrics, CR
    return clicks_sum  # clicks_percent.mean()


def cpc_rel(budget: pd.Series,
            desired_clicks: pd.Series,
            real_clicks: pd.Series, 
            spend_history: pd.Series) -> float:
    # cpc = Budget / desired_clicks
    # abs(1 - rel) -> min
    cpc = 1.0  # budget #/ desired_clicks
    thr = 1e-3
    penalty = 1e4
    spend_padded = []
    max_len = max(len(s) for s in spend_history)
    # mask = []
    for s in spend_history:
        spend_padded.append(pad_spend_with_zeros(s, max_len))
    clicks_padded = []
    for c in real_clicks:
        clicks_padded.append(pad_spend_with_zeros(c, max_len))

    clicks_padded = np.array(clicks_padded)
    spend_padded = np.array(spend_padded)

    mask_to_penalty = (clicks_padded.sum(axis=1) < thr).astype(int) * penalty
    real_cpc = np.divide(spend_padded, clicks_padded, out=np.zeros_like(spend_padded), where=clicks_padded != 0)
    real_cpc = real_cpc.mean(axis=1) + mask_to_penalty
    real_cpc_mean = real_cpc.mean() / cpc
    return real_cpc_mean


def pad_spend_with_zeros(spend_history: List[float], target_length: int) -> np.ndarray:
    """
    Pad the spend array with zeros to reach the target length.

    Args:
        spend_history: Original spend array.
        target_length: Desired length of the padded array.

    Returns: Padded spend array.
    """
    spend_array = np.array(spend_history)
    padding = np.zeros(target_length - len(spend_array))
    return np.concatenate([spend_array, padding])


def rmse_with_traffic(campaign_start: pd.Series,
                      campaign_end: pd.Series,
                      traffic: Traffic,
                      region_id: pd.Series,
                      spend_history: pd.Series,
                      budget: pd.Series) -> float:
    """
    Calculate the Root Mean Square Error (RMSE) of spend distribution 
    normalized by traffic share.

    This function compares the actual spend distribution against an ideal
    spend distribution based on traffic share.

    Args:
        campaign_start: Series of campaign start timestamps.
        campaign_end: Series of campaign end timestamps.
        traffic: Traffic object for retrieving traffic share data.
        region_id: Series of region IDs.
        spend: Series of actual spend data.
        budget: Series of campaign budgets.

    Returns: Mean RMSE across all campaigns.
    """
    results = []
    for start, end, reg_id, s, b in zip(campaign_start, campaign_end, region_id, spend_history, budget):
        start, end = int(start), int(end)
        reg_id = int(reg_id)
        b = float(b)

        campaign_duration = (end - start) // 3600 + 1
        s_padded = pad_spend_with_zeros(s, campaign_duration)

        traffic_campaign = traffic.get_traffic_share(reg_id, start, end)
        hours = np.arange(start, end + 3600, 3600) 
        traffic_list = np.array([traffic.get_traffic_share(reg_id, hour, hour + 3600) for hour in hours])
        traffic_list = traffic_list / traffic_campaign if traffic_campaign != 0 else np.zeros_like(traffic_list)

        ideal_spend = b * traffic_list
        rmse_value = np.sqrt(
            np.mean((ideal_spend - s_padded) ** 2
                    / (b / campaign_duration) ** 2)
            )  # Formula from section Metrics, RMSE_T but normalized!
        results.append(rmse_value)
    return np.mean(results)


def quickspend_metric(spend_history: pd.Series, budget: pd.Series):
    '''
    Returns the proportion of campaigns that spent the majority of their
    budget (90%) within the first half of the campaign duration.
    '''
    half_time_spend = spend_history.apply(lambda x: sum(x[:len(x) // 2]))
    if_quickspend = (half_time_spend > budget * 0.9).astype(int)
    return sum(if_quickspend) / len(if_quickspend)


def compile_metrics(hist_data: pd.DataFrame) -> Tuple[float, float]:
    """
    Compile performance metrics based on historical campaign data.

    This method calculates two key metrics:
    1. Mean Click Ratio (MCR): Average of the mean click ratios across all campaigns.
    2. RMSE with Traffic: Root Mean Square Error of spend distribution normalized by traffic share.

    Args:
        hist_data: Historical data of campaigns.

    Returns: A tuple containing (MCR, RMSE).
    """
    data = (
        hist_data
        .groupby("campaign_id")
        .agg(
            start_time=("campaign_start_time", "first"),
            end_time=("campaign_end_time", "first"),
            region_id=("region_id", "first"),
            clicks=('clicks', 'max'),
            initial_balance=('initial_balance', 'first'),
            desired_clicks=('desired_clicks', 'first'),
            spend_history=('spend_history', lambda x: list(x)),
            clicks_history=('clicks_history', lambda x: list(x))
        )
    )
    traffic = Traffic(path='../data/traffic_share.csv')
    clicks_sum = clicks_sum_metric(data["clicks"], data['desired_clicks'])
    rmse = rmse_with_traffic(
        campaign_start=data['start_time'],
        campaign_end=data['end_time'],
        traffic=traffic,
        region_id=data['region_id'],
        spend_history=data['spend_history'],
        budget=data['initial_balance']
    )

    quickspend = quickspend_metric(data['spend_history'],
                                   data['initial_balance'])
    cpc_relative = cpc_rel(
        budget=data['initial_balance'],
        desired_clicks=data['desired_clicks'],
        real_clicks=data["clicks_history"],
        spend_history=data['spend_history']
    )
    return (cpc_relative, rmse, clicks_sum, quickspend)
