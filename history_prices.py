import numpy as np
import pandas as pd
import threading
import time
from datetime import datetime, timedelta
import ast
import os

from Historic_Crypto import HistoricalData, Cryptocurrencies
from configuration import PORTFOLIO_TOKEN_LENGTH, START_DATE, END_DATE,  GRANULARITY, MARKETCAP_LIMIT, DATA_DIR
from portfolio import portfolio_return, portfolio_std, portfolio_sharpe
from configuration import PORTFOLIO_SIZE, INCREMENTAL_ID
from utils import get_market_cap, get_symbol_name

def get_pairs():
    usd_pairs = []
    usdc_pairs = []
    usdt_pairs = []
    attempts_max = 3
    counter = 0
    # loop to avoid missing pairs
    while counter < attempts_max:
        pairs = Cryptocurrencies(verbose=False).find_crypto_pairs()
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

tickers_hist = {}
def get_hist_prices(all_pairs, clip_date=False):

    def download_data(usd_pair):
        global tickers_hist
        usd_pair_hist = None
        is_sparse = True
        counter = 0
        while counter<3 and is_sparse:
            try:
                usd_pair_hist = HistoricalData(usd_pair, GRANULARITY, start_date=START_DATE, end_date=END_DATE, verbose=False).retrieve_data()
            except Exception as e:
                print(e)
                is_sparse=True
                counter+=1
                continue

            is_sparse = usd_pair_hist['close'].isna().sum() > 1/3*usd_pair_hist['close'].size or usd_pair_hist.empty
            counter+=1
        # only if price history isn't sparse add it.
        if clip_date and usd_pair_hist.index[0] > datetime.strptime(START_DATE, '%Y-%m-%d-%H-%M') + timedelta(1):
            print("{} is skipped, token launch is after start date".format(usd_pair))
            return
        else:
            tickers_hist[usd_pair] = usd_pair_hist

    threads = []
    for usd_pair in all_pairs:
        thread = threading.Thread(target=download_data, args=(usd_pair,))
        threads+=[thread]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # Retrieve historical prices and calculate returns
    hist_prices = pd.DataFrame()
    for pair, hist_price in tickers_hist.items():

        if hist_price is None:
            print("skipping {} is None".format(pair))
            continue
        hist_price = hist_price['close']
        hist_prices_isna_sum = hist_price.isna().sum()
        usd_pair  = '-'.join([pair.split('-')[0], 'USD'])
        usdc_pair = '-'.join([pair.split('-')[0], 'USDC'])
        usdt_pair = '-'.join([pair.split('-')[0], 'USDT'])
        hist_prices_columns = hist_prices.columns
        if usd_pair in hist_prices_columns:
            if hist_prices[usd_pair].isna().sum() < hist_prices_isna_sum:
                continue
            else:
                hist_prices = hist_prices.drop(usd_pair, axis='columns')
                hist_prices[pair] = hist_price
        elif usdc_pair in hist_prices_columns:
            if hist_prices[usdc_pair].isna().sum() < hist_prices_isna_sum:
                continue
            else:
                hist_prices = hist_prices.drop(usdc_pair, axis='columns')
                hist_prices[pair] = hist_price
        elif usdt_pair in hist_prices_columns:
            if hist_prices[usdt_pair].isna().sum() < hist_prices_isna_sum:
                continue
            else:
                hist_prices = hist_prices.drop(usdt_pair, axis='columns')
                hist_prices[pair] = hist_price
        else:
            hist_prices[pair] = hist_price

    return hist_prices

def download_hist_prices():
    all_pairs = get_pairs()
    #random.shuffle(all_pairs)
    # use csv values, it take too long to retrive them.
    pairs_names = {}
    def filter_pair(sym):
        name = None
        try:
            name = get_symbol_name(sym)
        except Exception as e:
            print(e)
        if name!=None:
            mc = get_market_cap(name)
            if mc >= MARKETCAP_LIMIT:
                pairs_names[sym] = name
        else:
            # if you can't get mc, add pair
            #pairs_names[sym] = sym
            print("skipping {} below target mc".format(sym))
    threads = []
    for sym in all_pairs:
        thread = threading.Thread(target=filter_pair, args=(sym,))
        threads+=[thread]
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    with open(DATA_DIR+os.sep+"all_pairs_names_filtered_by_mc"+str(INCREMENTAL_ID)+".txt", 'w+') as f:
        f.write(str(pairs_names))

    all_pairs = pairs_names.keys()
    hist_prices = get_hist_prices(all_pairs)
    hist_prices.to_csv("hist_prices"+str(INCREMENTAL_ID)+'.csv')
    hist_prices = hist_prices.interpolate(method ='linear', limit_direction ='forward')
    hist_prices = hist_prices.interpolate(method ='linear', limit_direction ='backward')
    return hist_prices

def load_hist_prices(hist_prices_file):
    if hist_prices_file is None:
        return None
    hist_prices = pd.read_csv(hist_prices_file)
    hist_prices = hist_prices.interpolate(method ='linear', limit_direction ='forward')
    hist_prices = hist_prices.interpolate(method ='linear', limit_direction ='backward')
    hist_prices.set_index('time')
    return hist_prices

def get_prices(download=False, hist_path=None):
    #TODO save hist prices permanently in ticks with all details such as granularity
    #TODO read all hist prices from disk
    hist_prices =  download_hist_prices() if download else load_hist_prices(hist_path)
    return hist_prices
