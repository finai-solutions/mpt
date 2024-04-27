import numpy as np

# calculate portfolio returns, standard deviation (volatility), and sharpe ratio
def portfolio_return(weights, mean):
    portfolio_return = np.dot(weights.T, mean.values) * 250 # annualize data; ~250 trading days in a year
    return portfolio_return[0]

# std is the same as volatility, and target is minimizing volatility.
def portfolio_std(weights, covariance):
    portfolio_std = np.sqrt(np.dot(weights.T, np.dot(covariance, weights)) * 250)
    return portfolio_std

# target is to maximize returns, and minimize std
def portfolio_sharpe(returns, std):
    return np.array(returns) / np.array(std)
