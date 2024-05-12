import numpy as np
import pandas as pd
from scipy.optimize import minimize

# calculate portfolio returns, standard deviation (volatility), and sharpe ratio
def portfolio_return(weights, mean, return_period):
    portfolio_return = np.dot(weights.T, mean.values) * return_period
    return portfolio_return[0]

# std is the same as volatility, and target is minimizing volatility.
def portfolio_std(weights, covariance):
    portfolio_std = np.sqrt(np.dot(weights.T, np.dot(covariance, weights)) * 250)
    return portfolio_std

# target is to maximize returns, and minimize std
def portfolio_sharpe(returns, std):
    return np.array(returns) / np.array(std)

def equal_weight(assets):
    optimal = [1/len(assets) for i in range(len(assets))]
    return optimal

def minimum_variance(ret, bound, return_period):
    def find_port_variance(weights):
        # this is actually std
        cov = ret.cov()
        port_var = np.sqrt(np.dot(weights.T, np.dot(cov, weights)) * return_period)
        return port_var

    def weight_cons(weights):
        return np.sum(weights) - 1


    bounds_lim = [bound for x in range(len(ret.columns))] # change to (-1, 1) if you want to short
    init = [1/len(ret.columns) for i in range(len(ret.columns))]
    constraint = {'type': 'eq', 'fun': weight_cons}

    optimal = minimize(fun=find_port_variance,
                       x0=init,
                       bounds=bounds_lim,
                       constraints=constraint,
                       method='SLSQP'
                       )

    return list(optimal['x'])

def max_sharpe(ret, bound, return_period):
    #TODO rank target returns, ore return second to optimal, and third, and so on.
    def sharpe_func(weights):
        hist_mean = ret.mean(axis=0).to_frame()
        hist_cov = ret.cov()

        port_ret = np.dot(weights.T, hist_mean.values) * return_period
        port_std = np.sqrt(np.dot(weights.T, np.dot(hist_cov, weights)) * return_period)
        return -1 * port_ret / port_std

    def weight_cons(weights):
        return np.sum(weights) - 1


    bounds_lim = [bound for x in range(len(ret.columns))]
    init = [1/len(ret.columns) for i in range(len(ret.columns))]
    constraint = {'type': 'eq', 'fun': weight_cons}

    optimal = minimize(fun=sharpe_func,
                       x0=init,
                       bounds=bounds_lim,
                       constraints=constraint,
                       method='SLSQP'
                       )

    return list(optimal['x'])

def efficient_frontier(target_returns, hist_cov, hist_mean_return, equally_weighted_weights, tickers_len, return_period, bound):
    efficient_frontier_risk = []
    for ret in target_returns:
        optimal = minimize(
            fun=portfolio_std,
            args=hist_cov,
            x0=equally_weighted_weights,
            bounds=[bound for x in range(tickers_len)],
            constraints=(
                {'type': 'eq', 'fun': lambda x: portfolio_return(x, hist_mean_return, return_period) - ret},
                {'type': 'eq', 'fun': lambda weights: np.sum(weights) - 1}
            ),
            method='SLSQP'
        )
        efficient_frontier_risk.append(optimal['fun'])
    return efficient_frontier_risk
