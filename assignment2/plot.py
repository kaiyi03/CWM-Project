# !/usr/bin/python3
import numpy as np
import matplotlib.pyplot as plt


# parameters to modify 
filename = "rtt_0001.txt"
label = "interval 0.0001s"
xlabel = "RTT (ms)"
ylabel = "Cumulative probability"
title = "CDF of localhost ping - interval 0.0001s"
fig_name = "cdf_ping_0001.png"
bins=100 #adjust the number of bins to your plot

## load data from input file
t = np.loadtxt(filename, delimiter=" ", dtype="float")

## if your data is "X Y" (2 cols), use the following line
#plt.plot(t[:,0], t[:,1], label=label)  # Plot some data on the (implicit) axes.

## if your data is "X" (1 col), use the following line
#plt.plot(t, label=label)  # Plot some data on the (implicit) axes.

## comment the lines above and uncomment the line below to plot a simple CDF
#plt.hist(t[:], bins, density=True, histtype='step', cumulative=True, label=label)

## comment the lines above and uncomment the 4 lines below for a nicer CDF
n = np.arange(1,len(t)+1) / float(len(t))
ts = np.sort(t)
fig, ax = plt.subplots()
ax.step(ts,n)
ax.set_xlim(0, 0.1)

plt.xlabel(xlabel)
plt.ylabel(ylabel)
plt.title(title)
plt.legend()
plt.savefig(fig_name)
plt.show()
