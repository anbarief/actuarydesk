"""
Author: Arief Anbiya
Email: anbarief@live.com
Date: 9 Sept 2020

The dataset used is the US Stocks Financial Indicators, collected from:

https://www.kaggle.com/cnic92/200-financial-indicators-of-us-stocks-20142018

show_bias_variance(feature_variables, n_test, n_train) usage example: show_bias_variance(['Revenue', 'R&D Expenses'], 500, 2000) plots the Bias-Variance of the Prediction Error by Regression Tree models with max_depth from 1 to 30, using 'Revenue' and 'R&D Expenses' as the feature variables.

n_test is the number of points used for the test set (only 1 test set chosen at the beginning).
n_train is the number of points for the training sets (total of 50 sets for each degrees of freedom (max_depth value)).
When choosing n_test and n_train, look at the total number of points in the data after filtering the NaNs by filter_data.
If n is the total number of points after filter_data, then n_train <= n-n_test is required.

The variable we are predicting is "Class", which has value either 1 or 0, 1 meaning that the stock is recommended to be bought and keep for 1 year, 0 meaning the opposite.

DATASET FILE: "financial_indicators_US_stocks_kaggle.csv"
Download the dataset from Google Drive link
(see https://anbarief.github.io/actuarydesk/)
"""

import random
import math
import statistics

import pandas
import matplotlib.pyplot as plt
from sklearn.tree import DecisionTreeRegressor as DTR

FILE_PATH = "PATH OF THE DATASET"

df = pandas.read_csv(FILE_PATH)
n = len(df)

sectors = list(set(df['Sector']))
sector_idx = {sectors[i-1]: i  for i in range(1,len(sectors)+1)}
sector = [sector_idx[i] for i in df['Sector']]
df['Sector Index'] = sector

def filter_data(feature_variables):

    target_variable = "Class"
    X = []; Y = []
    variables = [list(df[i]) for i in feature_variables]
    for i in range(n):
        bools = [not math.isnan(var[i]) for var in variables] + [not math.isnan(df[target_variable][i])]
        if all(bools):
            X.append([var[i] for var in variables])
            Y.append(df[target_variable][i])
            
    return X,Y

def show_bias_variance(feature_variables, n_test, n_train):

    target_variable = 'Class'
    X, Y = filter_data(feature_variables)

    n_x = len(X)
    random_test_index = random.sample(range(n_x), n_test)

    X_test = [X[i] for i in random_test_index]
    Y_test = [[Y[i]] for i in random_test_index]

    max_df = 30
    dfs = range(1, max_df+1) #max_depth
    result  = {i: [] for i in dfs}
    train_pool_index = [i for i in range(n_x) if i not in random_test_index]

    train_indexes = []
    for i in range(50):
        train_indexes_sample = random.sample(train_pool_index, n_train)
        as_list = sorted(train_indexes_sample)
        train_indexes.append(as_list)

    for df in dfs:
        model = DTR(max_depth = df, max_features=len(feature_variables))
        prediction_errors = []
        training_errors = []
        for i in range(50):
            X_train = [X[j] for j in train_indexes[i]]
            Y_train = [[Y[j]] for j in train_indexes[i]]
            model.fit(X_train, Y_train)
            y_predict = model.predict(X_test)
            y_predict_train = model.predict(X_train) 
            mse = statistics.mean([(y_predict[j]-Y_test[j][0])**2   for j in range(n_test)])
            mse_train = statistics.mean([(y_predict_train[j]-Y_train[j][0])**2   for j in range(n_train)])
            prediction_errors.append(mse)
            training_errors.append(mse_train)

        result[df].append(prediction_errors)
        result[df].append(statistics.mean(prediction_errors))
        result[df].append(training_errors)
        result[df].append(statistics.mean(training_errors))

    fig, ax = plt.subplots()
    sort_dfs = sorted(dfs)

    for i in range(max_df):
        ax.plot(sort_dfs, [result[df][0][i] for df in sort_dfs], '-', color = (1,0.2,0,0.25), lw = 2)
        p=ax.plot(sort_dfs, [result[df][1] for df in sort_dfs], '-', color = (1,0,0,1), lw = 1.5)
    p[0].set_label("Expected Test Error Estimate")
    
    for i in range(max_df):
        ax.plot(sort_dfs, [result[df][2][i] for df in sort_dfs], '-', color = (0,0.2,1,0.25), lw = 2)
        p=ax.plot(sort_dfs, [result[df][3] for df in sort_dfs], '-', color = (0,0,1,1), lw = 1.5)
    p[0].set_label("Expected Training Error Estimate")

    ax.legend()
    ax.set_xlabel('Max Depth')
    ax.set_ylabel('Prediction Error')
    fig.show()
