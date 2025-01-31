import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from .modules import History
from datetime import datetime, timedelta
import matplotlib.ticker as mticker


def price2bin(price: float) -> int:
    """
    Conversion from BID value to BIN value
    price = 1.2 ** bin
    """
    if price <= 0:
        return 0
    return np.round(np.log(price) / np.log(1.2))


def bin2price(bin_: int) -> float:
    """
    Reverse conversion from BIN value to BID value
    price = 1.2 ** bin
    """
    return np.power(1.2, bin_)


def plot_campaign_results(sim_hist: History):
    """
    Some utils to plot campaign simulation history
    """
    data = sim_hist.to_data_frame()
    _, ax = plt.subplots(figsize=(6, 3))

    ax_secondary = ax.twinx()

    ax.plot(
        data["curr_time"],
        data["balance"],
        "-ob"
    )
    ax_secondary.plot(
        data["curr_time"],
        data["clicks"],
        "-or"
    )

    ax.set_ylabel("balance", color="b")
    ax_secondary.set_ylabel("клики", color="r")
    ax.set_xlabel("time")
    ax.tick_params(axis='x', labelrotation=45)
    plt.tight_layout()
    plt.show()


def plot_history(df: pd.DataFrame):
    campaign_id = df.iloc[0]["campaign_id"]
    start = datetime.fromtimestamp(df.iloc[0]["campaign_start_time"]).strftime('%Y-%m-%d %H:%M:%S')
    end = datetime.fromtimestamp(df.iloc[0]["campaign_end_time"]).strftime('%Y-%m-%d %H:%M:%S')

    fig, axs = plt.subplots(3, 1, figsize=(12, 15), dpi=100)

    colors = ['#FF1493', '#1E90FF', '#00FF00']
    twaxs = [x.twinx() for x in axs]

    axs[0].plot(df["curr_time"], df["tr_share"], color=colors[0], linewidth=4, marker='o',
                markersize=4, label='Traffic share')
    twaxs[0].plot(df["curr_time"], df["clicks"], color=colors[1], linewidth=4, marker='s',
                  markersize=4, label='Clicks')

    axs[1].plot(df["tr_share_cs"], df["bid"], color=colors[0], linewidth=4, marker='o', markersize=4, label='Bid')
    twaxs[1].plot(df["tr_share_cs"], df["balance"], color=colors[1], linewidth=4, marker='s',
                  markersize=4, label='Balance')

    axs[2].plot(df["tr_share_cs"], df["price_bin"], color=colors[0], linewidth=4, marker='o',
                markersize=4, label='Price bin')
    twaxs[2].plot(df["tr_share_cs"], df["balance"], color=colors[1], linewidth=4, marker='s',
                  markersize=4, label='Balance')

    for i, (ylabel_left, ylabel_right) in enumerate([
                                                    ("Traffic share delta", "Clicks"),
                                                    ("Bid", "Balance"),
                                                    ("Bin", "Balance")]):
        axs[i].set_ylabel(ylabel_left, fontsize=12, fontweight='bold', color=colors[0])
        twaxs[i].set_ylabel(ylabel_right, fontsize=12, fontweight='bold', color=colors[1])
        axs[i].tick_params(axis='y', colors=colors[0])
        twaxs[i].tick_params(axis='y', colors=colors[1])

    axs[0].set_xlabel("Time", fontsize=12, fontweight='bold')
    axs[1].set_xlabel("Traffic share portion", fontsize=12, fontweight='bold')
    axs[2].set_xlabel("Traffic share portion", fontsize=12, fontweight='bold')

    axs[1].set_yscale("log")

    myLocator = mticker.MultipleLocator(18)
    axs[0].xaxis.set_major_locator(myLocator)
    plt.setp(axs[0].xaxis.get_majorticklabels(), rotation=35, ha='right')

    # Title and layout
    fig.suptitle(f"Campaign ID: {campaign_id}\nFrom {start} to {end}", fontsize=16, fontweight='bold')
    plt.tight_layout()

    # Add legend
    for i, ax in enumerate(axs):
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = twaxs[i].get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left', bbox_to_anchor=(0.05, 1), fontsize=10)

    plt.show()
    return fig


LINEWIDTH = 5
FONTSIZE = 16


def plot_history_article_(dfs: list, model_names: list = ['ALM', 'TA-PID', 'M-PID']):
    fig, axs = plt.subplots(5, 1, figsize=(12, 12), dpi=100)
    colors = ['#AEF071', '#F08F71', '#7189F0', '#FFA500', '#800080']
    twaxs_0 = axs[0].twinx()

    for idx, (name, df) in enumerate(zip(model_names, dfs)):
        axs[0].plot(df["curr_time"], df["spend"], color=colors[idx], linewidth=LINEWIDTH, marker='s',
                    markersize=4, label=f'Spend per hour ({name})')
        axs[1].plot(df["curr_time"], df["cpc"], color=colors[idx], linewidth=LINEWIDTH, marker='s',
                    markersize=4, label=f'CPC ({name})')
        axs[2].plot(df["curr_time"], df["bid"], color=colors[idx], linewidth=LINEWIDTH, marker='o',
                    markersize=4, label=f'Bid ({name})')
        # add starting point to the plot
        df['curr_time'] = pd.to_datetime(df['curr_time'])
        start_p = df['curr_time'][0] - timedelta(hours=1)
        time_with_0 = pd.to_datetime(np.hstack((start_p, df['curr_time'])))
        balance_with_0 = np.hstack((df['initial_balance'][0], df['balance']))
        axs[3].plot(time_with_0, balance_with_0, color=colors[idx], linewidth=LINEWIDTH, marker='s',
                    markersize=4, label=f'Balance ({name})')
        axs[4].plot(df["curr_time"], df["clicks"], color=colors[idx], linewidth=LINEWIDTH, marker='s',
                    markersize=4, label=f'Clicks ({name})')

    CPC_CONST = 100
    longest_run = max(dfs, key=len)
    max_t = len(longest_run)
    cpc_ref_list = [CPC_CONST for i in range(max_t)]
    twaxs_0.plot(longest_run["curr_time"], longest_run["tr_share"], color='grey', linewidth=2, marker='o',
                 markersize=4, linestyle='--', label='Traffic share')
    axs[1].plot(longest_run['curr_time'], cpc_ref_list, color='brown', linewidth=LINEWIDTH,
                markersize=4, linestyle='--', label='CPC Reference')
    axs[2].set_ylim(bottom=0)

    for i, ylabel in enumerate(["Spend per hour", "CPC", "Bid", "Balance", "Clicks"]):
        axs[i].set_ylabel(ylabel, fontsize=FONTSIZE, fontweight='bold', color='black')
        axs[i].tick_params(axis='y', colors='black')
        axs[i].grid(True, alpha=0.7)

    twaxs_0.set_ylabel('Traffic Share', fontsize=FONTSIZE, fontweight='bold', color='black')
    letters = ['(a)', '(b)', '(c)', '(d)', '(e)']
    for idx in range(len(axs)):
        axs[idx].set_xlabel(f"{letters[idx]} Time", fontsize=FONTSIZE, fontweight='bold')

    myLocator = mticker.MultipleLocator(18)
    axs[0].xaxis.set_major_locator(myLocator)
    plt.setp(axs[0].xaxis.get_majorticklabels(), rotation=35, ha='right')

    plt.tight_layout()

    for i, ax in enumerate(axs):
        ax.legend(loc='upper right', bbox_to_anchor=(0.55, 1), fontsize=FONTSIZE-2, framealpha=0.7)

    fig.suptitle("Campaign Performance Comparison", fontsize=FONTSIZE+2, fontweight='bold')
    fig.subplots_adjust(top=0.93)

    plt.show()
    return fig


def plot_history_article(dfs: list, model_names: list = ['ALM', 'TA-PID', 'M-PID']):
    fig, axs = plt.subplots(5, 1, figsize=(12, 12), dpi=150)
    colors = ['#AEF071', '#F08F71', '#7189F0', '#FFA500', '#800080']
    twaxs_0 = axs[0].twinx()

    legend_lines = []
    legend_labels = []

    for idx, (name, df) in enumerate(zip(model_names, dfs)):
        line, = axs[0].plot(df["curr_time"], df["spend"], color=colors[idx], linewidth=LINEWIDTH, markersize=4)
        legend_lines.append(line)
        legend_labels.append(f'{name}')

        axs[1].plot(df["curr_time"], df["cpc"], color=colors[idx], linewidth=LINEWIDTH, markersize=4)
        axs[2].plot(df["curr_time"], df["bid"], color=colors[idx], linewidth=LINEWIDTH, markersize=4)

        df['curr_time'] = pd.to_datetime(df['curr_time'])
        start_p = df['curr_time'][0] - timedelta(hours=1)
        time_with_0 = pd.to_datetime(np.hstack((start_p, df['curr_time'])))
        balance_with_0 = np.hstack((df['initial_balance'][0], df['balance']))

        axs[3].plot(time_with_0, balance_with_0, color=colors[idx], linewidth=LINEWIDTH,  markersize=4)
        axs[4].plot(df["curr_time"], (-1) ** idx * 0.25 ** idx + df["clicks"], color=colors[idx], linewidth=LINEWIDTH)

    CPC_CONST = 100
    longest_run = max(dfs, key=len)
    max_t = len(longest_run)
    cpc_ref_list = [CPC_CONST for i in range(max_t)]

    line, = twaxs_0.plot(longest_run["curr_time"], longest_run["tr_share"], color='grey', linewidth=2, marker='o',
                         markersize=4, linestyle='--')
    legend_lines.append(line)
    legend_labels.append('Traffic share')

    line, = axs[1].plot(longest_run['curr_time'], cpc_ref_list, color='brown', linewidth=2,
                        markersize=LINEWIDTH, linestyle='--')
    legend_lines.append(line)
    legend_labels.append('CPC Reference')

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


def plot_bidder_with_logs(bidder_logs, sim_hist):
    fig, axs = plt.subplots(2, 2, figsize=(15, 10))

    x = np.arange(1, len(bidder_logs.p) + 1)
    axs[0, 0].plot(x, bidder_logs.p, '--', label='p')
    axs[0, 0].plot(x, bidder_logs.q, '-.', label='q')
    axs[0, 0].legend()
    axs[0, 0].set_title('p and q')

    x = np.arange(1, len(bidder_logs.p))
    axs[0, 1].plot(x, bidder_logs.u[:, 0], label='u_0')
    axs[0, 1].plot(x, bidder_logs.u[:, 1], label='u_1')
    axs[0, 1].legend()
    axs[0, 1].set_title('u_0 and u_1')

    x = np.arange(1, len(bidder_logs.y[:, 1]) + 1)
    axs[1, 0].plot(x, bidder_logs.reference[:, 1], '-.', label='ref_cpc')
    axs[1, 0].plot(x, bidder_logs.reference[:, 0], label='ref_budget_pace')
    axs[1, 0].plot(x, bidder_logs.y[:, 1], '-.', label='y_cpc')
    axs[1, 0].plot(x, bidder_logs.y[:, 0], label='y_budget_pace')
    axs[1, 0].legend()
    axs[1, 0].set_title('Reference and y')

    data = sim_hist.to_data_frame()

    ax_secondary = axs[1, 1].twinx()

    axs[1, 1].plot(
        data["curr_time"],
        data["balance"],
        "-ob"
    )
    ax_secondary.plot(
        data["curr_time"],
        data["clicks"],
        "-or"
    )

    axs[1, 1].set_ylabel("balance", color="b")
    ax_secondary.set_ylabel("clicks", color="r")
    axs[1, 1].set_xlabel("time")
    axs[1, 1].tick_params(axis='x', labelrotation=45)
    plt.tight_layout()
    plt.show()
