#!/usr/bin/env python3
"""Plota a cwnd gravada pelo cwnd_monitor.py (bônus B1).

    python3 plot_cwnd_simples.py dados/b1/bb-q100/cwnd.csv graficos/b1-reno-cwnd-q100.png
"""
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

df = pd.read_csv(sys.argv[1])
# sem --sport o monitor grava todas as conexões para h2; a do iperf é a de maior cwnd
fluxo = df.groupby("flow_id")["cwnd_pkts"].max().idxmax()
d = df[df["flow_id"] == fluxo]
fig, ax = plt.subplots(figsize=(9, 3.5))
ax.plot(d["t_s"] - d["t_s"].iloc[0], d["cwnd_pkts"], lw=0.9)
ax.set_xlabel("tempo (s)")
ax.set_ylabel("cwnd (pacotes)")
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(sys.argv[2], dpi=150)
print("gravado", sys.argv[2])
