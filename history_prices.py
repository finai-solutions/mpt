import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from Historic_Crypto import HistoricalData, Cryptocurrencies
import threading
import time

from strategies import equal_weight
from strategies import minimum_variance
from strategies import max_sharpe
from configuration import PORTFOLIO_TOKEN_LENGTH, START_DATE, END_DATE, TOTAL_BALANCE, bound, GRANULARITY
from portfolio import portfolio_return, portfolio_std, portfolio_sharpe
from configuration import PORTFOLIO_SIZE
tickers_hist = {}
def get_pairs():
    usd_pairs = []
    usdc_pairs = []
    usdt_pairs = []
    attempts_max = 3
    counter = 0
    #TODO use more reliable lib.
    # loop to avoid missing pairs
    while counter < attempts_max:
        pairs = Cryptocurrencies().find_crypto_pairs()
        for pair in list(pairs['id']):
            # filter token-usd, token-usdc, token-usdt
            tokens = pair.split('-')
            lhs_pair = tokens[0]
            rhs_pair = tokens[1]
            if lhs_pair=='USD' or lhs_pair=='USDT' or lhs_pair=='USDC':
                continue
            if rhs_pair =='USD' and pair not in usd_pairs:
                usd_pairs+=[pair]
            elif rhs_pair=='USDT' and pair not in usdt_pairs:
                usdt_pairs+=[pair]
            elif rhs_pair=='USDC' and pair not in usdc_pairs:
                usdc_pairs+=[pair]
        counter+=1
    all_pairs = usd_pairs + usdc_pairs + usdt_pairs
    return all_pairs

def get_data(usd_pair):
    global tickers_hist
    try:
        usd_pair_hist = HistoricalData(usd_pair, GRANULARITY, start_date=START_DATE, end_date=END_DATE).retrieve_data()
        tickers_hist[usd_pair] = usd_pair_hist
    except Exception as e:
        print("error: {}".format(e))
        exit()

def get_tickers_hist(usd_tickers):
    threads = []
    for usd_pair in usd_tickers:
        thread = threading.Thread(target=get_data, args=(usd_pair,))
        threads+=[thread]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return tickers_hist

def get_hist_prices(all_pairs):
    tickers_hist_dict = get_tickers_hist(all_pairs)
    hist_prices_list = [(pair, ticker_hist['close']) for pair, ticker_hist in tickers_hist_dict.items()]
    # TODO add market cap filter constraints
    # Retrieve historical prices and calculate returns
    hist_prices = pd.DataFrame()

    for pair, hist_price in hist_prices_list:
        hist_prices_isna_sum = hist_price.isna().sum()
        usd_pair  = '-'.join([pair.split('-')[0], 'USD'])
        usdc_pair = '-'.join([pair.split('-')[0], 'USDC'])
        usdt_pair = '-'.join([pair.split('-')[0], 'USDT'])
        hist_prices_columns = hist_prices.columns
        if usd_pair in hist_prices_columns:
            if hist_prices[usd_pair].isna().sum() > hist_prices_isna_sum:
                continue
            else:
                hist_prices = hist_prices.drop(usd_pair, axis='columns')
                hist_prices[pair] = hist_price
        elif usdc_pair in hist_prices_columns:
            if hist_prices[usdc_pair].isna().sum() > hist_prices_isna_sum:
                continue
            else:
                hist_prices = hist_prices.drop(usdc_pair, axis='columns')
                hist_prices[pair] = hist_price
        elif usdt_pair in hist_prices_columns:
            if hist_prices[usdt_pair].isna().sum() > hist_prices_isna_sum:
                continue
            else:
                hist_prices = hist_prices.drop(usdt_pair, axis='columns')
                hist_prices[pair] = hist_price
        else:
            hist_prices[pair] = hist_price

    return hist_prices

def high_sharpe_portfolio(hist_prices):
    if 'time' in hist_prices.columns:
        hist_prices = hist_prices.drop('time', axis='columns')
    all_pairs = hist_prices.keys()
    hist_return = np.log(hist_prices/hist_prices.shift())
    # Calculating mean (expected returns), covariance (expected volatility), and correlation
    hist_mean = hist_return.mean(axis=0).to_frame()
    hist_mean.columns = ['mu']
    hist_cov = hist_return.cov()

    #n_portfolios = len(hist_prices.columns)
    #portfolio_returns = []
    #portfolio_stds = []

    #for i in range(n_portfolios):
    weights = np.array([1/len(hist_prices.keys())]*len(hist_prices.keys()))
        #port_return = np.log(hist_prices/hist_prices.shift())
    print("weights: {}".format(weights))
    print("mean: {}".format(hist_mean))
    port_return = portfolio_return(weights, hist_mean)
    port_std = portfolio_std(weights, hist_cov)
    sharpe = portfolio_sharpe(port_return, port_std)
    #portfolio_returns.append(port_return)
    #portfolio_stds.append(port_std)
    #sharpe = portfolio_sharpe(portfolio_returns, portfolio_stds)

    print("std: {}".format(port_std))
    print("return: {}".format(port_return))
    print("sharpe: {}".format(sharpe))
    print("hist_prices keys: {}".format(hist_prices.keys()))
    sharpe_index = [(idx,sharpe) for idx, sharpe in enumerate(sharpe)]
    print("sharpe_index: {}".format(sharpe_index))
    sharpe_index.sort(key=lambda si: si[1], reverse=True)
    portfolio_index = sharpe_index if len(sharpe_index)<=PORTFOLIO_SIZE else  sharpe_index[0:PORTFOLIO_SIZE]
    print('portfolio_index: {}'.format(portfolio_index))
    portfolio = hist_prices[[all_pairs[idx] for idx, _ in portfolio_index]]
    print("portfolio: {}".format(portfolio))
    return portfolio
