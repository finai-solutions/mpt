import os
import time
import threading

from glob import glob
import tqdm
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import ast
import json
from Historic_Crypto import HistoricalData, Cryptocurrencies

from portfolio.utils import get_market_cap, get_symbol_name, get_write_path
from configuration import DATA_DIR


def get_ondisk_load_pairs():
    all_pairs_files_glob = DATA_DIR+os.sep+'all_pairs*'
    return glob(all_pairs_files_glob)

def load_pairs(all_pairs_files):
    all_pairs = []
    for glob_file in all_pairs_files:
        with open(glob_file) as f:
            buf = f.read()
            all_pairs += ast.literal_eval(buf)
    return list(set(all_pairs))

def get_pairs(loadpairs=True, attempts_max = 1, verbose=False):
    all_pairs_files = get_ondisk_load_pairs()
    if len(all_pairs_files)>0 and loadpairs:
        if verbose:
            print("loading pairs from disk")
        return load_pairs(all_pairs_files)
    usd_pairs = []
    usdc_pairs = []
    usdt_pairs = []
    counter = 0
    # loop to avoid missing pairs
    while counter < attempts_max:
        pairs = Cryptocurrencies(verbose=False).find_crypto_pairs()
        for pair in tqdm.tqdm(list(pairs['id']), desc='getting pairs', position=5):
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
def download_data(start_date, end_date, granularity, usd_pair, verbose=False, clip_date=False, attempts_max=1):
    global tickers_hist
    if verbose:
        print('downloading: {} history at range {}-{}'.format(usd_pair, start_date, end_date))
    usd_pair_hist = None
    is_sparse = True
    counter = 0
    # free api's aren't reliable, keep trying to max_attempts
    while counter<attempts_max and is_sparse:
            try:
                usd_pair_hist = HistoricalData(usd_pair, granularity, start_date=start_date, end_date=end_date, verbose=verbose).retrieve_data()
            except Exception as e:
                if verbose:
                    print(e)
                is_sparse=True
                counter+=1
                continue
            is_sparse = usd_pair_hist['close'].isna().sum() > 1/3*usd_pair_hist['close'].size or usd_pair_hist.empty
            counter+=1
    # only if price history isn't sparse add it.
    if clip_date and usd_pair_hist.index[0] > datetime.strptime(start_date, '%Y-%m-%d-%H-%M') + timedelta(1):
        if verbose:
            print("{} is skipped, token launch is after start date".format(usd_pair))
        return
    else:
        tickers_hist[usd_pair] = usd_pair_hist
    return tickers_hist

'''
def load_hist_prices(granularity):
    pass
'''

def get_hist_prices(start_date, end_date, granularity, market_cap, bound, return_period, all_pairs, clip_date=False, verbose=False, singlecore=True, attempts_max = 1):
    #coinbase free pro api doesn't doesn't return full price history for frequent queries during concurrency.
    threads = []
    #load_hist_prices
    hist_prices_glob = DATA_DIR+os.sep+"hist_prices*"
    hist_prices_glob_files = glob(hist_prices_glob)
    for usd_pair in all_pairs:

        #adjust start_date, and end_date to download only the remaining
        adjusted_start_date = start_date
        adjusted_end_date = end_date
        if singlecore:
            if verbose:
                print("get {} history prices in single core mode".format(usd_pair))
            hist = download_data(adjusted_start_date, adjusted_end_date, granularity, usd_pair, verbose, clip_date, attempts_max)
        else:
            if verbose:
                print("get {} history prices in threading mode".format(usd_pair))
            thread = threading.Thread(target=download_data, args=(adjusted_start_date, adjusted_end_date, granularity, usd_pair, verbose, clip_date, attempts_max))
            threads+=[thread]
    if not singlecore:
        for thread in threads:
            if verbose:
                print("start {} history prices thread".format(thread))
            thread.start()
        for thread in threads:
            if verbose:
                print("join {} history prices thread".format(thread))
            thread.join()

    # Retrieve historical prices and calculate returns
    hist_prices = pd.DataFrame()
    for pair, hist_price in tickers_hist.items():
        if hist_price is None:
            if verbose:
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

def get_ondisk_pairs_names():
    glob_pairs_names_glob = DATA_DIR + os.sep + 'all_names_mc_filtered*'
    return glob(glob_pairs_names_glob)

def load_pairs_names(glob_pairs_names_files):
    pairs_names = {}
    for file_glob in glob_pairs_names_files:
        with open(file_glob) as f:
            buf = f.read()
            pairs_names |= ast.literal_eval(buf)
    return pairs_names

def download_hist_prices(start_date, end_date, granularity, market_cap, bound, return_period, verbose=False, singlecore=True, loadpairs=True, loadpairsnames=True):
    all_pairs_path = get_write_path(start_date, end_date, granularity, market_cap, bound, return_period, "all_pairs")
    all_pairs = []
    if os.path.exists(all_pairs_path):
        with open(all_pairs_path, 'r') as f:
            buf = f.read()
            all_pairs = ast.literal_eval(buf)
    else:
        all_pairs = get_pairs(loadpairs)
        with open(all_pairs_path, 'w+') as f:
            f.write(str(all_pairs))
    if verbose:
        print("pairs: {}".format(all_pairs))
    # use csv values, it take too long to retrive them.
    pairs_names = {}
    def filter_pair(sym):
        name = None
        try:
            name = get_symbol_name(sym, verbose)
        except Exception as e:
            if verbose:
                print(e)
        if name!=None:
            mc = get_market_cap(name, verbose)
            if mc >= market_cap:
                pairs_names[sym] = name
        else:
            # if you can't get mc, add pair
            #pairs_names[sym] = sym
            if verbose:
                print("skipping {} below target mc".format(sym))
    names_path = get_write_path(start_date, end_date, granularity, market_cap, bound, return_period, "all_names_mc_filtered", ext="json")
    if os.path.exists(names_path):
        with open(names_path, 'r') as f:
            buf = f.read().replace("\'", '\"')
            names_path = json.loads(buf)
    else:
        pairs_names_files = get_ondisk_pairs_names()
        if len(pairs_names_files) > 0 and loadpairsnames:
            pairs_names |= load_pairs_names(pairs_names_files)
        elif singlecore:
            print('singlecore')
            for sym in all_pairs:
                filter_pair(sym)
        else:
            print("threading")
            threads = []
            for sym in all_pairs:
                print("create")
                thread = threading.Thread(target=filter_pair, args=(sym,))
                threads+=[thread]
            for th in threads:
                print("start")
                th.start()
                time.sleep(1)
            for th in threads:
                print("join")
                th.join()
            with open(get_write_path(start_date, end_date, granularity, market_cap, bound, return_period, "all_names_mc_filtered", ext="json"), 'w+') as f:
                f.write(str(pairs_names))
    assert len(pairs_names)>0
    if verbose:
        print("pairs names: {}".format(pairs_names))
    all_pairs = pairs_names.keys()
    hist_prices = get_hist_prices(start_date, end_date, granularity, market_cap, bound, return_period, all_pairs, verbose=verbose, singlecore=singlecore, attempts_max=3)
    hist_prices.to_csv(get_write_path(start_date, end_date, granularity, market_cap, bound, return_period, "hist_prices", ext='csv'))
    hist_prices = hist_prices.interpolate(method ='linear', limit_direction ='forward')
    hist_prices = hist_prices.interpolate(method ='linear', limit_direction ='backward')
    if verbose:
        print("hist_prices: {}".format(hist_prices))
    return hist_prices

def load_hist_prices(hist_prices_file):
    if hist_prices_file is None:
        return None
    hist_prices = pd.read_csv(hist_prices_file)
    print(hist_prices.columns)
    hist_prices = hist_prices.set_index('time')
    hist_prices = hist_prices.interpolate(method ='linear', limit_direction ='forward')
    hist_prices = hist_prices.interpolate(method ='linear', limit_direction ='backward')
    print("hist_prices: {}".format(hist_prices))
    return hist_prices

def get_prices(start_date, end_date, granularity, market_cap, bound, return_period,  verbose=False, singlecore=True):
    #TODO save hist prices permanently in ticks with all details such as granularity
    #TODO read all hist prices from disk
    hist_prices_path = get_write_path(start_date, end_date, granularity, market_cap, bound, return_period, 'hist_prices', ext='csv')
    hist_prices = None
    if os.path.exists(hist_prices_path):
        hist_prices = load_hist_prices(hist_prices_path)
    else:
        hist_prices = download_hist_prices(start_date, end_date, granularity, market_cap, bound, return_period, verbose, singlecore)
    return hist_prices

def get_token_data(start_date, end_date, granularity, market_cap, bound, return_period, verbose=False, singlecore=True):
    hist_prices = get_prices(start_date, end_date, granularity, market_cap, bound, return_period, verbose, singlecore)
    hist_return = hist_prices/hist_prices.shift(return_period)
    hist_log_return = np.log(hist_return)

    # Calculating mean (expected returns), covariance (expected volatility), and correlation
    hist_mean_return = hist_log_return.mean(axis=0).to_frame()
    hist_mean_return.columns = ['mu']
    hist_cov = hist_log_return.cov()
    hist_corr = hist_log_return.corr()

    return hist_prices, hist_log_return, hist_mean_return, hist_cov, hist_corr
