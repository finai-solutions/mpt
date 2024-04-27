import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from Historic_Crypto import HistoricalData, Cryptocurrencies
import threading

from strategies import equal_weight
from strategies import minimum_variance
from strategies import max_sharpe
from configuration import PORTFOLIO_TOKEN_LENGTH, START_DATE, END_DATE, TOTAL_BALANCE, bound, GRANULARITY, PORTFOLIO_SIZE
from history_prices import get_hist_prices, get_pairs, high_sharpe_portfolio
from portfolio import portfolio_return, portfolio_std, portfolio_sharpe


all_pairs = get_pairs()
hist_prices = get_hist_prices(all_pairs)

# filter tokens by high sharpe index
hist_prices = high_sharpe_portfolio(hist_prices, all_pairs)
#TODO save hist prices permanently in ticks with all details such as granularity
#TODO read all hist prices from disk
hist_return = np.log(hist_prices/hist_prices.shift())
#hist_return.dropna(axis=0)
# Calculating mean (expected returns), covariance (expected volatility), and correlation
hist_mean = hist_return.mean(axis=0).to_frame()
hist_mean.columns = ['mu']
hist_cov = hist_return.cov()
hist_corr = hist_return.corr()

print("all_pairs: {}".format(all_pairs))
print("hist_prices: {}".format(hist_prices))
print("hist_return: {}".format(hist_return))
print("hist_mean: {}".format(hist_mean))
print("hist_cov: {}".format(hist_cov))
print("hist_corr: {}".format(hist_corr))

# simulate randomized portfolios
n_portfolios = len(hist_prices.columns)
portfolio_returns = []
portfolio_stds = []
TICKERS=hist_prices.keys()
print('n: {}'.format(n_portfolios))
for i in range(n_portfolios):

    weights = np.random.rand(len(TICKERS))
    weights = weights / sum(weights)
    port_return = portfolio_return(weights, hist_mean)
    port_std = portfolio_std(weights, hist_cov)
    sharpe_ratio = portfolio_sharpe(port_return, port_std)
    portfolio_returns.append(port_return)
    portfolio_stds.append(port_std)

#------------ Optimized portfolios ------------------#

#----------- Equally Weighted Portfolio -------------#
equally_weighted_weights = np.array(equal_weight(TICKERS))
equally_weighted_return = portfolio_return(equally_weighted_weights, hist_mean)
equally_weighted_std = portfolio_std(equally_weighted_weights, hist_cov)
equally_weighted_sharpe_ratio = portfolio_sharpe(equally_weighted_return, equally_weighted_std)

print('---------- Equally Weighted Portfolio ----------')
print('Weights:', equally_weighted_weights)
print('Return:', equally_weighted_return)
print('Volatility:', equally_weighted_std)
print('Sharpe Ratio:', equally_weighted_sharpe_ratio)

print()

#----------- Global Minimum Variance Portfolio ------#
gmv_weights = np.array(minimum_variance(hist_return, bound))
gmv_return = portfolio_return(gmv_weights, hist_mean)
gmv_std = portfolio_std(gmv_weights, hist_cov)
gmv_sharpe_ratio = portfolio_sharpe(gmv_return, gmv_std)

print('---------- Global Minimum Variance ----------')
print('Weights:', gmv_weights)
print('Return:', gmv_return)
print('Volatility:', gmv_std)
print('Sharpe Ratio:', gmv_sharpe_ratio)

print()
#----------- Max Sharpe Portfolio ------#
max_sharpe_weights = np.array(max_sharpe(hist_return, bound))
max_sharpe_return = portfolio_return(max_sharpe_weights, hist_mean)
max_sharpe_std = portfolio_std(max_sharpe_weights, hist_cov)
max_sharpe_sharpe_ratio = portfolio_sharpe(max_sharpe_return, max_sharpe_std)

print('---------- Max Sharpe Ratio ----------')
print('Weights:', max_sharpe_weights)
print('Return:', max_sharpe_return)
print('Volatility:', max_sharpe_std)
print('Sharpe Ratio:', max_sharpe_sharpe_ratio)


def plot():
    #----------- Efficient Frontier ------#
    target_returns = np.linspace(0.06, 0.17, 100)
    efficient_frontier_risk = []
    for ret in target_returns:
        optimal = minimize(
            fun=portfolio_std,
            args=hist_cov,
            x0=equally_weighted_weights,
            bounds=[bound for x in range(len(TICKERS))],
            constraints=(
                {'type': 'eq', 'fun': lambda x: portfolio_return(x, hist_mean) - ret},
                {'type': 'eq', 'fun': lambda weights: np.sum(weights) - 1}
            ),
            method='SLSQP'
        )
        efficient_frontier_risk.append(optimal['fun'])

    # Print out portfolio value over time
    date_range = []
    equally_weighted_portfolio = []
    gmv_portfolio = []
    max_sharpe_portfolio = []
    FINAL_BALANCE = 0

    for index, day in hist_prices.iterrows():
        equal_weighted_port_val = 0
        gmv_port_val = 0
        max_sharpe_port_val = 0
        for i, asset in enumerate(TICKERS):
            equal_weighted_port_val += equally_weighted_weights[i] * TOTAL_BALANCE / hist_prices[asset].iloc[1] * day[asset]
            gmv_port_val += gmv_weights[i] * TOTAL_BALANCE / hist_prices[asset].iloc[1] * day[asset]
            max_sharpe_port_val += max_sharpe_weights[i] * TOTAL_BALANCE / hist_prices[asset].iloc[1] * day[asset]

        date_range.append(index)
        equally_weighted_portfolio.append(equal_weighted_port_val)
        gmv_portfolio.append(gmv_port_val)
        max_sharpe_portfolio.append(max_sharpe_port_val)

    plt.plot(date_range, equally_weighted_portfolio, label='equally weighted portfolio')
    plt.plot(date_range, gmv_portfolio, label='global min variance portfolio')
    plt.plot(date_range, max_sharpe_portfolio, label='max sharpe portfolio')

    plt.title('Portfolio Value')
    plt.xlabel('Date')
    plt.ylabel('Value in dollars')

    plt.legend()
    plt.savefig('portfolio.png')

    # Display portfolios
    plt.scatter(portfolio_stds, portfolio_returns, marker='o', s=3, label='Random')
    plt.plot(efficient_frontier_risk, target_returns, 'og', markersize=3, label='Efficient Frontier')
    plt.plot(equally_weighted_std, equally_weighted_return, 'or', label='Equally Weighted')
    plt.plot(gmv_std, gmv_return, 'oc', label='Global Minimum Variance')
    plt.plot(max_sharpe_std, max_sharpe_return, 'om', label='Max Sharpe')
    plt.title('Volatility vs Returns for Different Portfolios')
    plt.xlabel('Expected Volatility')
    plt.ylabel('Expected Returns')
    plt.legend()
    plt.savefig('volatility.png')

plot()
