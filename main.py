import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import minimize
import threading
from datetime import datetime
import random
import os

from strategies import equal_weight, minimum_variance, max_sharpe, efficient_frontier
from configuration import TOTAL_BALANCE, bound, MARKETCAP_LIMIT, RETURN_PERIOD,  DATA_DIR, get_write_path
from history_prices import get_prices
from portfolio import portfolio_return, portfolio_std, portfolio_sharpe

hist_prices = get_prices(download=True)
hist_return = hist_prices/hist_prices.shift(RETURN_PERIOD)
hist_log_return = np.log(hist_return)

# Calculating mean (expected returns), covariance (expected volatility), and correlation
hist_mean_return = hist_log_return.mean(axis=0).to_frame()
hist_mean_return.columns = ['mu']
hist_cov = hist_log_return.cov()
hist_corr = hist_log_return.corr()

TICKERS=hist_prices.keys()


#----------- Equally Weighted Portfolio -------------#
equally_weighted_weights = np.array(equal_weight(TICKERS))
equally_weighted_return = portfolio_return(equally_weighted_weights, hist_mean_return)
equally_weighted_std = portfolio_std(equally_weighted_weights, hist_cov)
equally_weighted_sharpe_ratio = portfolio_sharpe(equally_weighted_return, equally_weighted_std)

with open(get_write_path('portfolio_equally_weighted', ext='json'), 'w+') as f_eq:
    var_dict = {}
    tw_l = [ (t,w) for t, w in zip(TICKERS, equally_weighted_weights) ]
    tw_l.sort(key=lambda pair: pair[1], reverse=True)
    var_dict['portfolio'] = tw_l
    var_dict['return'] = equally_weighted_return
    var_dict['std'] = equally_weighted_std
    var_dict['sharpe'] = equally_weighted_sharpe_ratio
    f_eq.write(str(var_dict))

#----------- Global Minimum Variance Portfolio ------#
gmv_weights = np.array(minimum_variance(hist_log_return, bound))
gmv_return = portfolio_return(gmv_weights, hist_mean_return)
gmv_std = portfolio_std(gmv_weights, hist_cov)
gmv_sharpe_ratio = portfolio_sharpe(gmv_return, gmv_std)

with open(get_write_path('portfolio_var', ext='json'), 'w+') as f_var:
    var_dict = {}
    tw_l = [ (t,w) for t, w in zip(TICKERS, gmv_weights) ]
    tw_l.sort(key=lambda pair: pair[1], reverse=True)
    var_dict['portfolio'] = tw_l
    var_dict['return'] = gmv_return
    var_dict['std'] = gmv_std
    var_dict['sharpe'] = gmv_sharpe_ratio
    f_var.write(str(var_dict))

#----------- Max Sharpe Portfolio ------#
max_sharpe_weights = np.array(max_sharpe(hist_log_return, bound))
max_sharpe_return = portfolio_return(max_sharpe_weights, hist_mean_return)
max_sharpe_std = portfolio_std(max_sharpe_weights, hist_cov)
max_sharpe_sharpe_ratio = portfolio_sharpe(max_sharpe_return, max_sharpe_std)

with open(get_write_path('portfolio_sharpe', ext='json'), 'w+') as f_sharpe:
    var_dict = {}
    tw_l = [ (t,w) for t, w in zip(TICKERS, max_sharpe_weights) ]
    tw_l.sort(key=lambda pair: pair[1], reverse=True)
    var_dict['portfolio'] = tw_l
    var_dict['return'] = max_sharpe_return
    var_dict['std'] = max_sharpe_std
    var_dict['sharpe'] = max_sharpe_sharpe_ratio
    f_sharpe.write(str(var_dict))


# simulate randomized portfolios
n_portfolios = len(hist_prices.columns)
portfolio_returns = []
portfolio_stds = []
for i in range(n_portfolios):
    weights = np.random.rand(len(TICKERS))
    weights = weights / sum(weights)
    port_return = portfolio_return(weights, hist_mean_return)
    port_std = portfolio_std(weights, hist_cov)
    sharpe_ratio = portfolio_sharpe(port_return, port_std)
    portfolio_returns.append(port_return)
    portfolio_stds.append(port_std)


# figure out the range for target return. 10% lower than min value, 10% higher than max value.
min_return = min(portfolio_returns+[gmv_return])
min_return = min_return*1.1 if min_return<0 else min_return*0.9
max_return = max(portfolio_returns+[max_sharpe_return])
max_return = max_return*1.1 if max_return>0 else max_return*0.9
target_returns = np.linspace(min_return, max_return, 100)
efficient_frontier_risk = efficient_frontier(target_returns, hist_cov, hist_mean_return, equally_weighted_weights, len(TICKERS))

# portfolio value over time
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

# plot return vs volatility
plt.plot(date_range, equally_weighted_portfolio, label='equally weighted portfolio')
plt.plot(date_range, gmv_portfolio, label='global min variance portfolio')
plt.plot(date_range, max_sharpe_portfolio, label='max sharpe portfolio')

plt.title('Portfolio Value')
plt.xlabel('Date')
plt.ylabel('Value in dollars')

plt.legend()
plt.savefig(get_write_path('portfolio', ext='png'))
plt.clf()

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
plt.savefig(get_write_path('volatility', ext='png'))
