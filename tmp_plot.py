import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
from tools_class import CNAV
from skyrim.whiterun import CCalendar

plt.rcParams["font.sans-serif"] = ["SimSun"]  # 用来正常显示中文标签

fd = {
    "family": "serif",
    "style": "normal",
    "weight": "bold",
    "size": 10
}


ROOT_DIR = os.path.join("/Works", "Trade", "Reports")
INTERMEDIARY_DIR = os.path.join(ROOT_DIR, "intermediary")
CALENDAR_DIR = os.path.join("/Database", "Calendar")
nav_file = "组合净值.xlsx"

calendar = CCalendar(os.path.join(CALENDAR_DIR, "cne_calendar.csv"))

# load nav
nav_path = os.path.join(INTERMEDIARY_DIR, nav_file)
nav_df = pd.read_excel(nav_path)
nav_df["trade_date"] = nav_df["日期"].map(lambda z: z.strftime("%Y-%m-%d"))
nav_df["nav"] = nav_df["单位净值"]
nav_df = nav_df[["trade_date", "nav"]].set_index("trade_date")
nav_df = nav_df.loc[nav_df.index <= "20211231"]

# return-risk index
nav = CNAV(t_nav_srs=nav_df["nav"], t_annual_rf_rate=2.5, t_freq="D")
nav.cal_annual_return()
nav.cal_max_drawdown()
nav.cal_mdd_duration(t_calendar=calendar)
nav.cal_sharpe_ratio0()
nav.cal_sharpe_ratio1()
nav.cal_hold_period_return()
return_risk_index = nav.to_dict()
description = "年化收益={:.2f}%\n夏普比率={:.2f}\n最大回撤={:.2f}%".format(
    return_risk_index["annual_return"],
    return_risk_index["sharpe_ratio"],
    return_risk_index["max_drawdown"],
)

# --- plot
last_date = nav_df.index[-1]
for i in range(1, 3):
    next_date = calendar.get_next_date(t_this_date=last_date.replace("-", ""), t_shift=i)
    append_date = next_date[0:4] + "-" + next_date[4:6] + "-" + next_date[6:8]
    nav_df = nav_df.append(pd.Series(name=append_date, dtype=float))
y_max = nav_df["nav"].max()
y_min = nav_df["nav"].min()

n_ticks = len(nav_df)
fig0, ax0 = plt.subplots(figsize=(16, 9))
nav_df.plot(ax=ax0, lw=3.0)
xticks = np.arange(0, n_ticks, int(n_ticks / 7))
xticklabels = nav_df.index[xticks]
ax0.set_xticks(xticks)
ax0.set_xticklabels(xticklabels, fontdict=fd)
ax0.set_xlabel("")

yticks = np.arange(y_min * 0.95, y_max * 1.05, 0.02)
yticklabels = ["{:.2f}".format(_) for _ in yticks]
ax0.set_yticks(yticks)
ax0.set_yticklabels(yticklabels, fontdict=fd)
ax0.yaxis.tick_right()

ax0.set_ylim((y_min * 0.96, y_max * 1.04))
ax0.text(
    x=3, y=y_max * 1.04 * 0.950, s=description, fontdict={"size": 16, "weight": "heavy"},
    bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5)
)
ax0.get_legend().remove()
ax0.set_title("单位净值")
fig0_name = "组合净值.new.png"
fig0_path = os.path.join(INTERMEDIARY_DIR, fig0_name)
fig0.savefig(fig0_path, bbox_inches="tight")
plt.close(fig0)