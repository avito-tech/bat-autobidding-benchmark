import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from datetime import timedelta
from simulator.model.traffic import Traffic


LINEWIDTH = 5
FONTSIZE = 16


def plot_history_article(dfs: list, model_names: list = ['ALM', 'TA-PID', 'M-PID'], single_plot=True):
    fig, axs = plt.subplots(5, 1, figsize=(12, 12), dpi=150)
    colors = ['#AEF071', '#F08F71', '#7189F0', '#FFA500', '#800080']
    twaxs_0 = axs[0].twinx()
    if single_plot:
        dfs = [dfs]
        model_names = ['Single Model']
    elif model_names is None:
        model_names = [f'Model {i+1}' for i in range(len(dfs))]

    legend_lines = []
    legend_labels = []

    for idx, (name, df) in enumerate(zip(model_names, dfs)):
        line, = axs[0].plot(df["curr_time"], df["spend_history"], color=colors[idx], linewidth=LINEWIDTH, markersize=4)
        legend_lines.append(line)
        legend_labels.append(f'{name}')

        axs[1].plot(df["curr_time"], df["cpc"], color=colors[idx], linewidth=LINEWIDTH, markersize=4)
        axs[2].plot(df["curr_time"], df["bid"], color=colors[idx], linewidth=LINEWIDTH, markersize=4)

        df['curr_time'] = pd.to_datetime(df['curr_time'])
        start_p = df['curr_time'][0] - timedelta(hours=1)
        time_with_0 = pd.to_datetime(np.hstack((start_p, df['curr_time'])))
        balance_with_0 = np.hstack((df['initial_balance'][0], df['balance']))
        clicks_with_0 = np.hstack((0, df['clicks']))

        axs[3].plot(time_with_0, balance_with_0, color=colors[idx], linewidth=LINEWIDTH,  markersize=4)
        axs[4].plot(time_with_0, clicks_with_0, color=colors[idx], linewidth=LINEWIDTH)

    longest_run = max(dfs, key=len)

    line, = twaxs_0.plot(longest_run["curr_time"],
                         longest_run["tr_share"],
                         color='grey',
                         linewidth=2,
                         marker='o',
                         markersize=4,
                         linestyle='--')
    legend_lines.append(line)
    legend_labels.append('Traffic share')

    axs[2].set_ylim(bottom=0)

    for i, ylabel in enumerate(["Spend per hour", "CPC", "Bid", "Balance", "Clicks"]):
        axs[i].set_ylabel(ylabel, fontsize=FONTSIZE, fontweight='bold', color='black')
        axs[i].tick_params(axis='y', colors='black')
        axs[i].grid(True, alpha=0.7)

    twaxs_0.set_ylabel('Traffic Share', fontsize=FONTSIZE, fontweight='bold', color='black')

    letters = ['(a)', '(b)', '(c)', '(d)', '(e)']
    for idx in range(len(axs)):
        ax = axs[idx]
        ax.set_xlabel('Time', fontsize=FONTSIZE, fontweight='bold', x=0.05)
        ax.xaxis.set_label_coords(0.05, -0.12)

        ax.text(0.5, -0.2, letters[idx], transform=ax.transAxes,
                fontsize=FONTSIZE, fontweight='bold', ha='center', va='center')

    plt.setp(axs[0].xaxis.get_majorticklabels(), ha='center')

    fig.legend(legend_lines, legend_labels, loc='upper center', bbox_to_anchor=(0.5, 0.9),
               ncol=5, fontsize=FONTSIZE-2, framealpha=0.7)

    plt.tight_layout()
    fig.subplots_adjust(top=0.85)

    fig.suptitle("Campaign Performance Comparison", fontsize=FONTSIZE+2, fontweight='bold')

    plt.show()
    return fig


def data_prep_vis(viz_data: pd.DataFrame) -> pd.DataFrame:
    viz_data["tr_share"] = viz_data.apply(
            lambda x: 0 if x["prev_timestamp"] == 0 else Traffic(path="../data/traffic_share.csv").get_traffic_share(
                x["region_id"],
                x["prev_timestamp"],
                x["curr_timestamp"],
            ), axis=1
        )

    viz_data["tr_share_cs"] = viz_data["tr_share"].cumsum()
    viz_data["price_bin"] = np.log(viz_data["bid"]) / np.log(1.2)

    clicks = np.hstack((0, viz_data.clicks))
    clicks_per_hour = [clicks[i] - clicks[i-1] for i in range(1, len(clicks))]
    viz_data['cpc'] = viz_data.spend_history / clicks_per_hour
    viz_data['cpc'] = viz_data['cpc'].fillna(0)

    return viz_data
