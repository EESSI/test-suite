import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

df = pd.read_csv("benchmarks.csv")
df = df.sort_values(by=["mode", "cores", "mpi.x", "mpi.y", "mpi.z"])

group = df.query(f"mode == 'strong scaling'")

fig = plt.figure(figsize=(12, 6))
ax = fig.subplots().axes
xdata = group["cores"].to_numpy()
ydata = group["mean"].to_numpy()
ax.axline((xdata[0], xdata[0]), slope=1, linestyle="--", color="grey", label="Theoretical maximum")
ax.plot(xdata, ydata[0] / ydata, "o-", label="Measurements")
ax.set_title("Strong scaling")
ax.set_xlabel("Number of cores")
ax.set_ylabel("Speed-up")
ax.set_xscale("log", base=2)
ax.set_yscale("log", base=10)
ax.legend()
plt.show()

group = df.query(f"mode == 'weak scaling'")

fig = plt.figure(figsize=(12, 6))
ax = fig.subplots().axes
xdata = group["cores"].to_numpy()
ydata = group["mean"].to_numpy()
ax.axline((-np.inf, 1), slope=0, linestyle="--", color="grey", label="Theoretical maximum")
ax.plot(xdata, ydata[0] / ydata, "o-", label="Measurements")
ax.set_title("Weak scaling")
ax.set_xlabel("Number of cores")
ax.set_ylabel("Efficiency")
ax.set_xscale("log", base=2)
ax.yaxis.set_major_formatter(mtick.PercentFormatter(1))
ax.legend()
plt.show()
