import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from Historic_Crypto import HistoricalData, Cryptocurrencies
import threading

from strategies import equal_weight
from strategies import minimum_variance
from strategies import max_sharpe
from configuration import PORTFOLIO_TOKEN_LENGTH, START_DATE, END_DATE, TOTAL_BALANCE, bound, GRANULARITY
from portfolio import portfolio_return, portfolio_std, portfolio_sharpe
from configuration import PORTFOLIO_SIZE
tickers_hist = {}
def get_pairs():
    pairs = Cryptocurrencies().find_crypto_pairs()
    # filter token-usd, token-usdc, token-usdt
    usd_pairs = []
    usdc_pairs = []
    usdt_pairs = []
    for pair in list(pairs['id']):
        tokens = pair.split('-')
        lhs_pair = tokens[0]
        rhs_pair = tokens[1]
        if rhs_pair =='USD':
            usd_pairs+=[pair]
        elif rhs_pair=='USDT':
            usdt_pairs+=[pair]
        elif rhs_pair=='USDC':
            usdc_pairs+=[pair]

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
    all_pairs = hist_prices.keys()
    hist_return = np.log(hist_prices/hist_prices.shift())
    #hist_return.dropna(axis=0)
    # Calculating mean (expected returns), covariance (expected volatility), and correlation
    hist_mean = hist_return.mean(axis=0).to_frame()
    hist_mean.columns = ['mu']
    hist_cov = hist_return.cov()
    n_portfolios = len(hist_prices.columns)
    portfolio_returns = []
    portfolio_stds = []
    for i in range(n_portfolios):

        weights = np.random.rand(len(hist_prices.keys()))
        weights = weights / sum(weights)
        port_return = portfolio_return(weights, hist_mean)
        port_std = portfolio_std(weights, hist_cov)
        sharpe_ratio = portfolio_sharpe(port_return, port_std)
        portfolio_returns.append(port_return)
        portfolio_stds.append(port_std)

    #print('returns: {}'.format(portfolio_returns))
    #print("stds: {}".format(portfolio_stds))
    sharpe = portfolio_sharpe(portfolio_returns, portfolio_stds)
    sharpe_index = [(idx,sharpe) for idx, sharpe in enumerate(sharpe)]
    sharpe_index.sort(key=lambda si: si[1], reverse=True)
    #print("sorted sharpe_index: {}".format(sharpe_index))
    portfolio_index = sharpe_index if len(sharpe_index)<=PORTFOLIO_SIZE else  sharpe_index[0:PORTFOLIO_SIZE]
    portfolio = hist_prices[[all_pairs[idx] for idx, _ in portfolio_index]]
    #print('portfolio: {}'.format(portfolio))
    hist_prices=portfolio
    return hist_prices
