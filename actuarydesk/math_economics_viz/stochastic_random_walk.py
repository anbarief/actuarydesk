"""
Author: Arief Anbiya
Email: anbarief@live.com
Date: 3 Sept 2020

Simple Random Walk animation.
"""

import random
import statistics

import matplotlib.pyplot as plt
import matplotlib.animation as animation

def animate_randomwalk(initial_value = 0, dt = 1, h = 1, p = 0.5, n = 1000, n_update = 5, interval_between_frame = 50):

    X = [initial_value]; t = [0]    

    fig, ax = plt.subplots()
    plot1 = ax.plot(t[0], X[0], '-', color='gray'); plot1[0].set_label('X(t)')
    plot2 = ax.plot(t[0], X[0], '-', color='blue'); plot2[0].set_label('Moving mean at t')
    ax.legend()
    ax.set_xlabel("t"); ax.set_ylabel("X(t)")

    moving_mean = [X[0]]
    def animate(frame):
        plot = []
        for i in range(n_update):
            if random.uniform(0, 1) <= p:
                X.append(X[-1] + h)
            else:
                X.append(X[-1] - h)
            t.append(t[-1]+dt)
            moving_mean.append(statistics.mean(X))
            plot.append(ax.plot([t[-2], t[-1]], [X[-2], X[-1]], '-', color = 'gray', lw = 1)[0])
            plot.append(ax.plot([t[-2], t[-1]], [moving_mean[-2], moving_mean[-1]], color = 'blue', lw = 1)[0])
        return plot

    ani = animation.FuncAnimation(fig, animate, range(n), repeat=False, interval=interval_between_frame)
    plt.show()
