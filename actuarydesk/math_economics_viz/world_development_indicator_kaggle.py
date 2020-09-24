"""
Author: Arief Anbiya
Email: anbarief@live.com
Date: 9 Sept 2020

The dataset used in this module is the World Development Indicators by the World Bank, available on Kaggle.
Source: https://www.kaggle.com/worldbank/world-development-indicators.
Terms of Use of the dataset is written here: https://www.worldbank.org/en/about/legal/terms-of-use-for-datasets

The plot_values function results line plot(s) of an indicator form time to time of one or more countries (comparing them).
If the colors argument is set to 'default' then the color of the lines will follow the default from Matplotlib.

If plot_values shows dynamics, the plot_bars function results bar plot of an indicator of one or more countries in a specific year.
The user can interact with the plot (by hovering on the axes).

DATASET FILE:
-"wdi_indicators_kaggle.csv" (FILE_PATH_1)
-"wdi_countries_kaggle.csv" (FILE_PATH_2)
Download the dataset from Google Drive link
(see https://anbarief.github.io/actuarydesk/)
"""

import math

import pandas
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

FILE_PATH_1 = "PATH OF THE DATASET"
FILE_PATH_2 = "PATH OF THE DATASET"

df = pandas.read_csv(FILE_PATH_1)
df_countries  = pandas.read_csv(FILE_PATH_2)
years = sorted(list(set(df['Year'])))
indicator_names= sorted(list(set(df['IndicatorName'])))
color_code = {'no data': (0, 0, 0, 0.5), \
              'Europe & Central Asia': (0, 0, 1, 0.5), \
              'Middle East & North Africa': (186/255, 138/255, 6/255, 0.5), \
              'North America': (1, 0, 0, 0.5), \
              'Latin America & Caribbean': (0, 1, 0, 0.5), \
              'Sub-Saharan Africa': (1, 0, 1, 0.5), \
              'South Asia': (0, 0.5, 0.5, 0.5), \
              'East Asia & Pacific': (1, 1, 50/255, 0.5)}

def filter_by_country(country_name):
    return df[df['CountryName']==country_name]

def filter_by_indicator_country(country_name, indicator_name):
    result = filter_by_country(country_name)
    return result[result['IndicatorName']==indicator_name]

def find_countries_with_indicator(indicator):
    countries = list(set(df['CountryName']))
    result = []
    for country in countries:
        if len(filter_by_indicator_country(country, indicator))>0:
            result.append(country)
    return result

def country_exist_by_indicator(country, indicator):
    if len(filter_by_indicator_country(country, indicator))>0:
        return True
    return False

def plot_values(countries, colors, indicator):    

    dfs=[filter_by_indicator_country(country, indicator) for country in countries]
    bools = [len(dfs[i])>0 for i in range(len(countries))]
    if not any(bools):
        print("No data")
        return None
    
    all_years = []
    for df in dfs:
        all_years += list(df['Year'])
        
    min_year = min(all_years); max_year = max(all_years)

    fig, ax = plt.subplots()
    for i in range(len(countries)):
        
        if bools[i]:
            if colors == "default":
                p=ax.plot(dfs[i]['Year'], dfs[i]['Value']);
            else:
                p=ax.plot(dfs[i]['Year'], dfs[i]['Value'], color=colors[i]);
            p[0].set_label(countries[i])
    
    ax.set_title(indicator, fontsize=10)
    ax.set_xticks(range(min_year, max_year+1)); ax.set_xticklabels([str(i) for i in range(min_year, max_year+1)], rotation = -90, fontsize=6);
    ax.legend()
    plt.tight_layout()
    fig.show()

def plot_bars(indicator, year, lowest_rank = 10):

    if lowest_rank < 1:
        print("Rank must be at least 1")
        return None

    df1=df[df['IndicatorName']==indicator]
    if len(df1)==0:
        print("No data available")
        return None
    
    df2=df1[df1['Year']==year]
    if len(df2)==0:
        print("No data available")
        return None
    
    n = len(df2['CountryCode'])
    top_m = min(lowest_rank, n)

    values = [i for i in df2['Value']]
    country_code = [i for i in df2['CountryCode']]
    country_name = [i for i in df2['CountryName']]
    region = [list(df_countries[df_countries['CountryCode']==i]['Region'])[0] for i in country_code]
    for i in range(len(region)):    
        if (type(region[i]) != str) and math.isnan(region[i]):
            region[i]='no data'
        
    paired = sorted([(i, j, k, l) for i, j, k, l in zip(country_code, country_name, region, values)], key = lambda x: x[3])
    top_m_paired = paired[-top_m:]

    fig, ax = plt.subplots()
    ax.set_ylim([min(values), 1.3*max(values)])
    for i in color_code.keys():
        p=ax.plot(0,min(values)-1000,'o', color = color_code[i])
        p[0].set_label(i)
    ax.legend()
    
    for i in range(top_m):
        ax.bar(top_m-i,  paired[-(i+1)][3],color = color_code[paired[-(i+1)][2]], ec = 'black')

    dashed_line = ax.plot(0,min(values)-1000,'--', color = 'gray', lw = 1)[0]
    def on_motion(event):
        x_pos, y_pos = event.xdata, event.ydata
        if x_pos != None:
            for i in range(1, top_m+1):
                if abs(x_pos-i) < 0.5: 
                    text = top_m_paired[i-1][1] + " ({})".format(top_m_paired[i-1][3])
                    ax.set_xlabel(text, fontsize=10)
                    if y_pos > top_m_paired[i-1][3]:
                        dashed_line.set_xdata([i, i]); dashed_line.set_ydata([top_m_paired[i-1][3], y_pos])
                    else:
                        dashed_line.set_ydata([min(values)-1000, min(values)-1000])
                    fig.show()
                    break
        
    cid = fig.canvas.mpl_connect('motion_notify_event', on_motion)
    ax.set_xticks(range(1, top_m+1)); ax.set_xticklabels(["" for i in range(top_m)], fontsize=4);
    ax.set_title(indicator, fontsize=12)
    ax.set_ylabel("Value")
    plt.tight_layout()
    fig.show()
