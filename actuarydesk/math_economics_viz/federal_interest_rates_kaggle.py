"""
Author: Arief Anbiya
Email: anbarief@live.com
Date: 2 Sept 2020

The dataset used is the Federal Interest Rates, collected from:

https://www.kaggle.com/federalreserve/interest-rates

The function plot_rates can plot the effective fund rates, unemployment rates, and inflation rates.
To plot their correlations, use the function correlation_plot.

DATASET FILE: "federal_interest_rates_kaggle.csv"
Download the dataset from Google Drive link
(see https://anbarief.github.io/actuarydesk/)
"""

import math

import pandas
import matplotlib.pyplot as plt

FILE_PATH = "PATH OF THE DATASET"

df = pandas.read_csv(FILE_PATH)
n = len(df)
time_points = []
for i in range(n):
    year = df['Year'][i]
    month = df['Month'][i]/12
    day = (df['Day'][i]/(31))/12
    time_point = year + month + day
    time_points.append(time_point)
df['Time Points'] = time_points

labels = ['Effective Federal Funds Rate', \
              'Unemployment Rate', \
              'Inflation Rate']
rates = [df[i] for i in labels]
index = [0,1,2]
color = ['red', 'green', 'blue']

def plot_rates(min_year, max_year, effective_rate = True, \
               unemployment_rate = False, inflation_rate = False):

    bools = [effective_rate, unemployment_rate, inflation_rate]
    if not any(bools):
        return None
    n_true = len([b for b in bools if b])
    
    if n_true==3:
        pass
    elif n_true==2:
        if not effective_rate:
            index.pop(0)
        if not unemployment_rate:
            index.pop(1)
        if not inflation_rate:
            index.pop(2)
    else:
        if effective_rate:
            index = [0]
        if unemployment_rate:
            index = [1]
        if inflation_rate:
            index = [2]
        
    rates_index = []
    for i in range(n):    
        rate = [rates[idx][i] for idx in index]
        if all([not math.isnan(r) for r in rate]):
            rates_index.append(i)
            
    fig, ax = plt.subplots()
    filtered_index = [i for i in rates_index if min_year <= time_points[i] <= max_year]
    for idx in index:
        line = ax.plot([time_points[i] for i in filtered_index], [rates[idx][i] for i in filtered_index], '-', color=color[idx])
        line[0].set_label(labels[idx])   
    ax.legend()
    ax.set_xticks(range(min_year, max_year+1))
    ax.set_xticklabels(range(min_year, max_year+1), rotation = -90, fontsize=7)
    ax.set_ylabel("Rate")
    fig.show()
    return None

def correlation_plot(min_year, max_year, var_1, var_2, var_3 = False):

    rates_index = []
    x = df[var_1]; y = df[var_2]
    fig, ax = plt.subplots()

    if not var_3:
        for i in range(n):
            rate_1 = x[i]; rate_2 = y[i]
            if (not math.isnan(rate_1)) \
               and (not math.isnan(rate_2)):
                rates_index.append(i)
        filtered_index = [i for i in rates_index if min_year <= time_points[i] <= max_year]
        ax.plot([x[i] for i in filtered_index], [y[i] for i in filtered_index], 'o')
    else:
        color_var = [i for i in labels if ((i != var_1) and (i != var_2))][0]
        z = df[color_var]
        for i in range(n):
            rate_1 = x[i]; rate_2 = y[i]; rate_3 = z[i]
            if (not math.isnan(rate_1)) \
               and (not math.isnan(rate_2)) \
               and (not math.isnan(rate_3)):
                rates_index.append(i)
        filtered_index = [i for i in rates_index if min_year <= time_points[i] <= max_year]
        z_values = [z[i] for i in filtered_index]; max_z = max(z_values)
        colors = [(1,0,0, max(i/max_z, 0.2)) for i in z_values]
        x_values = [x[i] for i in filtered_index]; y_values = [y[i] for i in filtered_index]
        for i in range(len(colors)):
            ax.plot(x_values[i], y_values[i], 'o', color = colors[i])
        ax.set_title("Solid color represents high {}.".format(color_var))  

    ax.set_xlabel(var_1); ax.set_ylabel(var_2)
    fig.show()
