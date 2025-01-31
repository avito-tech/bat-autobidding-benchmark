from datetime import datetime
import pandas as pd


class Traffic:
    def __init__(self, path: str) -> None:
        """
        This class is part of the baseline. You can reuse it in your solutions.
        It calculates the share of weekly traffic between two timestamps.
        """
        self.traffic_share_pdf = pd.read_csv(path)

    def get_traffic_share(self, region_id: int, start: int, end: int) -> float:
        """
        This function calculates the share of weekly traffic with hourly precision.
        If you input a 2-week period, the answer will be 2.0.
        If you input a full Monday, the answer will be the share of weekly traffic that occurs on Monday.
        The model assumes a static traffic distribution across weekdays; holidays and special days are not considered.

        Args:
            region_id: loc_id of the region
            start: timestamp of the period start
            end: timestamp of the period end
        """

        ts_pdf = self.traffic_share_pdf[self.traffic_share_pdf['region_id'] == region_id]
        # fallback if the region is not found - use the most popular one
        if ts_pdf.empty:
            ts_pdf = self.traffic_share_pdf[self.traffic_share_pdf['region_id'] == 637640]

        traffic_share = 0.0

        while end - start > 3600 * 24 * 7:
            traffic_share += 1.0
            end -= 3600 * 24 * 7

        if end - start == 3600 * 24 * 7:
            return traffic_share + 1.0

        dtm_start = datetime.fromtimestamp(start)
        dtm_end = datetime.fromtimestamp(end)

        if dtm_end.weekday() >= dtm_start.weekday():
            traffic_share += (
                ts_pdf[
                    (
                        (ts_pdf['dow'] > dtm_start.weekday() + 1) |
                        ((ts_pdf['dow'] == dtm_start.weekday() + 1) & (ts_pdf['hour'] >= dtm_start.hour))
                    ) &
                    (
                        (ts_pdf['dow'] < dtm_end.weekday() + 1) |
                        ((ts_pdf['dow'] == dtm_end.weekday() + 1) & (ts_pdf['hour'] < dtm_end.hour))
                    )
                ]['traffic_share'].sum()
            )
        else:
            traffic_share += (
                ts_pdf[
                    (
                        (ts_pdf['dow'] > dtm_start.weekday() + 1) |
                        ((ts_pdf['dow'] == dtm_start.weekday() + 1) & (ts_pdf['hour'] >= dtm_start.hour))
                    )
                ]['traffic_share'].sum()
            )
            traffic_share += (
                ts_pdf[
                    (
                        (ts_pdf['dow'] < dtm_end.weekday() + 1) |
                        ((ts_pdf['dow'] == dtm_end.weekday() + 1) & (ts_pdf['hour'] < dtm_end.hour))
                    )
                ]['traffic_share'].sum()
            )
        return traffic_share
