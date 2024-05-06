import json
import numpy as np
import pandas as pd
from scipy.optimize import minimize

from portfolio.utils import get_write_path
from portfolio.history_prices import get_token_data
from portfolio.vis import plot
from portfolio.strategies import equal_weight, minimum_variance, max_sharpe,  portfolio_return, portfolio_std, portfolio_sharpe

def get_equally_weighted_portfolio(start_date, end_date, granularity, market_cap, bound, return_period, tickers, mean_return, cov):
    equally_weighted_weights = np.array(equal_weight(tickers))
    equally_weighted_return = portfolio_return(equally_weighted_weights, mean_return, return_period) #TODO verify it's log return
    equally_weighted_std = portfolio_std(equally_weighted_weights, cov)
    equally_weighted_sharpe_ratio = portfolio_sharpe(equally_weighted_return, equally_weighted_std)

    with open(get_write_path(start_date, end_date, granularity, market_cap, bound, return_period, 'portfolio_equally_weighted', ext='json'), 'w+') as f_eq:
        var_dict = {}
        tw_l = [ (t,w) for t, w in zip(tickers, equally_weighted_weights) ]
        tw_l.sort(key=lambda pair: pair[1], reverse=True)
        var_dict['portfolio'] = tw_l
        var_dict['return'] = equally_weighted_return
        var_dict['std'] = equally_weighted_std
        var_dict['sharpe'] = equally_weighted_sharpe_ratio
        f_eq.write(json.dumps(var_dict))
    return equally_weighted_weights, equally_weighted_std, equally_weighted_return

def get_global_minimum_variance_portfolio(start_date, end_date, granularity, market_cap, bound, return_period, tickers, log_return, mean_return, cov):

    gmv_weights = np.array(minimum_variance(log_return, bound, return_period))
    gmv_return = portfolio_return(gmv_weights, mean_return, return_period)
    gmv_std = portfolio_std(gmv_weights, cov)
    gmv_sharpe_ratio = portfolio_sharpe(gmv_return, gmv_std)

    with open(get_write_path(start_date, end_date, granularity, market_cap, bound, return_period, 'portfolio_var', ext='json'), 'w+') as f_var:
        var_dict = {}
        tw_l = [ (t,w) for t, w in zip(tickers, gmv_weights) ]
        tw_l.sort(key=lambda pair: pair[1], reverse=True)
        var_dict['portfolio'] = tw_l
        var_dict['return'] = gmv_return
        var_dict['std'] = gmv_std
        var_dict['sharpe'] = gmv_sharpe_ratio
        f_var.write(json.dumps(var_dict))
    return gmv_weights, gmv_std, gmv_return

def get_max_sharpe_portfolio(start_date, end_date, granularity, market_cap, bound, return_period, tickers, log_return, mean_return, cov):
    max_sharpe_weights = np.array(max_sharpe(log_return, bound, return_period))
    max_sharpe_return = portfolio_return(max_sharpe_weights, mean_return, return_period)
    max_sharpe_std = portfolio_std(max_sharpe_weights, cov)
    max_sharpe_sharpe_ratio = portfolio_sharpe(max_sharpe_return, max_sharpe_std)

    with open(get_write_path(start_date, end_date, granularity, market_cap, bound, return_period, 'portfolio_sharpe', ext='json'), 'w+') as f_sharpe:
        var_dict = {}
        tw_l = [ (t,w) for t, w in zip(tickers, max_sharpe_weights) ]
        tw_l.sort(key=lambda pair: pair[1], reverse=True)
        var_dict['portfolio'] = tw_l
        var_dict['return'] = max_sharpe_return
        var_dict['std'] = max_sharpe_std
        var_dict['sharpe'] = max_sharpe_sharpe_ratio
        f_sharpe.write(json.dumps(var_dict))
    return max_sharpe_weights, max_sharpe_std, max_sharpe_return

def get_portfolio(start_date, end_date, granularity, market_cap, bound, return_period, balance, verbose=True, singlecore=True):
    try:
        prices, log_return, mean_return, cov, _ = get_token_data(start_date, end_date, granularity, market_cap, bound, return_period, verbose=verbose, singlecore=singlecore)
        tickers = prices.keys()
        eq_w, eq_std, eq_return = get_equally_weighted_portfolio(start_date, end_date, granularity, market_cap, bound, return_period, tickers, mean_return, cov)
        gmv_w, gmv_std, gmv_return = get_global_minimum_variance_portfolio(start_date, end_date, granularity, market_cap, bound, return_period, tickers, log_return, mean_return, cov)
        max_sharpe_w, max_sharpe_std, max_sharpe_return = get_max_sharpe_portfolio(start_date, end_date, granularity, market_cap, bound, return_period, tickers, log_return, mean_return, cov)
        with open(get_write_path(start_date, end_date, granularity, market_cap, bound, return_period, 'returns', ext='json'), 'w+') as f_returns:
            returns_dict = {}
            returns_dict['equally_weighted_return'] = eq_return
            returns_dict['gmv_return'] = gmv_return
            returns_dict['max_sharpe_return'] = max_sharpe_return
            f_returns.write(json.dumps(returns_dict))
        plot(start_date, end_date, granularity, market_cap, bound, prices, tickers, balance, return_period, mean_return, cov, eq_return, eq_std, eq_w, gmv_return, gmv_std, gmv_w, max_sharpe_return, max_sharpe_std, max_sharpe_w)
        return True
    except Exception as e:
        if verbose:
            print(e)
        return None
