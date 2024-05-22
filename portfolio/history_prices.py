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

from portfolio.utils import get_market_cap, get_symbol_name, get_write_path, get_initial_date, get_file_params, get_timestamp_from_mergedate, get_stable_pairs, is_wrapper
from portfolio.merger import load_merge_dfs
from configuration import DATA_DIR


def get_ondisk_load_pairs(market_cap, granularity):
    all_pairs_files_glob = DATA_DIR+os.sep+'all_pairs*'
    all_pairs_files = glob(all_pairs_files_glob)
    filtered_files = []
    for file_glob in all_pairs_files:
        file_params = get_file_params(file_glob)
        if file_params['market_cap']>=market_cap and file_params['granularity']==granularity:
            filtered_files+=[file_glob]
    return filtered_files

def load_pairs(all_pairs_files):
    all_pairs = []
    for glob_file in all_pairs_files:
        with open(glob_file) as f:
            buf = f.read()
            all_pairs += ast.literal_eval(buf)
    return list(set(all_pairs))

def get_pairs(market_cap, granularity, loadpairs=True, attempts_max = 1, verbose=False):
    all_pairs_files = get_ondisk_load_pairs(market_cap, granularity)
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

def download_data(tickers_hist, start_date, end_date, granularity, usd_pair, verbose=False, attempts_max=1):
    initial_date = get_initial_date(usd_pair, [start_date, end_date])
    if start_date <= initial_date:
        start_date = initial_date
    if verbose:
        print('downloading: {} history at range {}-{}'.format(usd_pair, start_date, end_date))
    usd_pair_hist = None
    is_sparse = True
    counter = 0
    # free api's aren't reliable, keep trying to max_attempts
    while counter<attempts_max and is_sparse:
            try:
                print("start_date: {}".format(start_date))
                print('end_date: {}'.format(end_date))
                usd_pair_hist = HistoricalData(usd_pair, granularity, start_date=start_date, end_date=end_date, verbose=verbose).retrieve_data()
            except Exception as e:
                if verbose:
                    print(e)
                is_sparse=True
                counter+=1
                continue
            if 'close' in usd_pair_hist:
                is_sparse = usd_pair_hist['close'].isna().sum() > 1/3*usd_pair_hist['close'].size or usd_pair_hist.empty
            counter+=1
    if usd_pair_hist is None:
        return tickers_hist[usd_pair] if usd_pair in tickers_hist else pd.Series()
    # only if price history isn't sparse add it.
    start_date = datetime.strptime(start_date, '%Y-%m-%d-%H-%M') + timedelta(1)
    download_start_date = usd_pair_hist.index[0]
    if verbose:
        print("start_date: {}, download_start_date: {}".format(start_date, download_start_date))
    if  download_start_date > start_date:
        if verbose:
            print("{} is skipped, token launch is after start date".format(usd_pair))
    # if token is already there, then concatenate series with new downloaded history,
    concat_with_aggregate_hist = usd_pair_hist['close'] if usd_pair not in tickers_hist else pd.concat([usd_pair_hist['close'], tickers_hist[usd_pair]]).sort_index()
    tickers_hist[usd_pair] = concat_with_aggregate_hist
    if verbose:
        print("concat_with_aggragate_hist: {}".format(concat_with_aggregate_hist))
    #TODO note that if tickers_hist length is less than assigned series,
    # then the newly appended series will be cropped to dataframe length
    # by index range, that is why concat_with_aggregate_hist is returned,
    # and not tickers_hist so that you can unwrap the tickers_hist, fill missing
    # intervals, then concatenate the dataframe.
    return concat_with_aggregate_hist

def get_hist_prices(start_date, end_date, granularity, market_cap, bound, return_period, all_pairs, verbose=False, singlecore=True, attempts_max = 1):
    #coinbase free pro api doesn't doesn't return full price history for frequent queries during concurrency.
    hist_prices, missing_intervals = load_merge_dfs(start_date, end_date, granularity, market_cap)
    if verbose:
        print("aggregated dataframe info: {}".format(hist_prices.info()))
        print("aggregated dataframe: {}".format(hist_prices))
    # if aggregated data frame has any relevant price history within date-range,
    # then only query the missing intervals.
    tickers_hist = {}
    if len(hist_prices)>0:
        # drop columns that aren't in all_pairs
        disjoint_tokens = list(set(hist_prices.columns)^set(all_pairs))
        if verbose:
            print("aggregating data frames with price history")
            print('disjoint tokens: {}'.format(disjoint_tokens))
        hist_prices = hist_prices.drop(columns=disjoint_tokens, errors='ignore')
        hist_prices_series={}
        for token, intervals in missing_intervals.items():
            if token in disjoint_tokens:
                continue
            if token in hist_prices_series:
                hist_prices_series[token] = hist_prices[token]
            for interval in intervals:
                if verbose:
                    print("downloading {} prices at interval {} - {}".format(token, interval[0], interval[1]))
                start = interval[0]
                end = interval[1]
                interval_hist = download_data(tickers_hist, start, end, granularity, token, verbose, attempts_max)
                if verbose:
                    print('downloaded price history from {} to {}'.format(interval[0], interval[1]))
                if verbose:
                    print('assign {} hist interval: {}-{}'.format(token, start, end))
                    print("interval_hist: {}".format(interval_hist))
                #hist_prices_series[token]=pd.concat([interval_hist, hist_prices_series[token]]) if token in hist_prices_series else interval_hist
                hist_prices_series[token] = interval_hist
        if verbose:
            print("aggregated price history info: {}".format(hist_prices.info()))
        print("1-hist_prices: {}".format(hist_prices))
        # concatenate hist prices for each token after appending missing intervals.
        hist_prices = pd.concat(hist_prices_series.values(), axis=1, keys=hist_prices_series.keys())
        print("2-hist_prices: {}".format(hist_prices))
        # sort hist prices by index
        hist_prices.index = pd.to_datetime(hist_prices.index)
        print("3-hist_prices: {}".format(hist_prices))
        hist_prices.sort_index(inplace=True)
    # retrieve tokens history for tokens not in aggregated data frame/hist_prices
    remaining_pairs = list(set(all_pairs)-set(hist_prices.columns))
    if verbose:
        print('requested pairs: {}'.format(all_pairs))
        print("aggregated_pairs: {}".format(hist_prices.columns))
        print("remaining pairs to be downloaded: {}".format(remaining_pairs))
    # append aggregated pairs to tickers_hist
    if verbose:
        print('hist_prices: {}'.format(hist_prices))
    # merge aggregated df `hist_prices`, and downloaded missing intervals `hist_prices`
    for usd_pair in hist_prices.columns:
        if usd_pair in tickers_hist:
            tickers_hist[usd_pair] = pd.concat([hist_prices[usd_pair], tickers_hist[usd_pair]], axis=1, keys=[usd_pair]).sort_index()
        else:
            tickers_hist[usd_pair] = hist_prices[usd_pair]
    if verbose:
        print('tickers hist: {}'.format(tickers_hist))
    ###########################
    # download remaining pairs
    ###########################
    threads = []
    for usd_pair in remaining_pairs:
        if verbose:
            print("downloading {} price history".format(usd_pair))
        #TODO adjust start_date, and end_date to download only the remaining
        adjusted_start_date = start_date
        adjusted_end_date = end_date
        if singlecore:
            if verbose:
                print("get {} history prices in single core mode".format(usd_pair))
            hist = download_data(tickers_hist, adjusted_start_date, adjusted_end_date, granularity, usd_pair, verbose, attempts_max)
        else:
            if verbose:
                print("get {} history prices in threading mode".format(usd_pair))
            thread = threading.Thread(target=download_data, args=(tickers_hist, adjusted_start_date, adjusted_end_date, granularity, usd_pair, verbose, attempts_max))
            threads+=[thread]
    if singlecore==False:
        for thread in threads:
            if verbose:
                print("start {} history prices thread".format(thread))
            thread.start()
        for thread in threads:
            if verbose:
                print("join {} history prices thread".format(thread))
            thread.join()
    #######
    # end #
    #######
    for pair, token in tickers_hist.items():
        token_isna_sum = token.isna().sum()
        iswrapper = is_wrapper(pair, all_pairs)
        if verbose:
            print("{} is a wrapper: {}".format(pair, iswrapper))
        stables, wrappers = get_stable_pairs(pair, iswrapper)
        stable_pairs = stables + wrappers
        if verbose:
            print('stable pairs: {}'.format(stable_pairs))
        nan_counts = []
        for nonsparse_stable_pair in stable_pairs:
            # if pair has less nan than rest of pairs, keep it and remove the rest.
            nan_counts += [(nonsparse_stable_pair, hist_prices[nonsparse_stable_pair].isna().sum() if nonsparse_stable_pair in hist_prices else hist_prices.shape[0])]
        nan_counts.sort(key=lambda i:i[1])

        # if they are all equal keep usdt_pair, or not available usdc_pair, if not avilable then usd pair, if not avilable then do nothing.
        removing_pairs = []
        if sum([i[1]-nan_counts[0][1] for i in nan_counts])==0:
            if verbose:
                print("all pairs have equal nan values: {}".format(nan_counts[0][1]))
            for stable_pair in stables:
                if stable_pair in hist_prices:
                    removing_pairs = list(set(stable_spairs)-set([stable_pair]))
        else:
            removing_pairs = [i[0] for i in nan_counts[1:]]
        if verbose:
            print('keeping {}, removing: {}'.format(nan_counts[0], removing_pairs))
        for remove_pair in removing_pairs:
            if remove_pair in hist_prices:
                hist_prices = hist_prices.drop(remove_pair, axis='columns')
    if verbose:
        print("downloaded/loaded price history with info: {}".format(hist_prices.info()))
    return hist_prices

def get_ondisk_pairs_names(market_cap, granularity):
    glob_pairs_names_glob = DATA_DIR + os.sep + 'all_names_mc_filtered*'
    all_pairs_files = glob(glob_pairs_names_glob)
    filtered_files = []
    for file_glob in all_pairs_files:
        file_params = get_file_params(file_glob)
        if file_params['market_cap']>=market_cap and file_params['granularity']==granularity:
            filtered_files+=[file_glob]
    return filtered_files

def load_pairs_names(glob_pairs_names_files, granularity, market_cap):
    pairs_names = {}
    for file_glob in glob_pairs_names_files:
        file_params = get_file_params(file_glob)
        if file_params['market_cap']>=market_cap and file_params['granularity']==granularity:
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
        all_pairs = get_pairs(market_cap, granularity, loadpairs)
        with open(all_pairs_path, 'w+') as f:
            f.write(str(all_pairs))
    print("all_pairs: {}".format(all_pairs))
    # use csv values, it take too long to retrive them.
    pairs_names = {}
    def filter_pair(sym):
        if verbose:
            print('filtering sym: {} by market-cap: {}'.format(sym, market_cap))
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
            pairs_names = json.loads(buf)
    else:
        pairs_names_files = get_ondisk_pairs_names(market_cap, granularity)
        if len(pairs_names_files) > 0 and loadpairsnames:
            if verbose:
                print('load pairs names')
            pairs_names |= load_pairs_names(pairs_names_files, granularity, market_cap)

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
            for th in threads:
                print("join")
                th.join()
            with open(get_write_path(start_date, end_date, granularity, market_cap, bound, return_period, "all_names_mc_filtered", ext="json"), 'w+') as f:
                f.write(str(pairs_names))
    assert len(pairs_names.items())>0
    if verbose:
        print("pairs names: {}".format(pairs_names))
    all_pairs = pairs_names.keys()
    hist_prices = get_hist_prices(start_date, end_date, granularity, market_cap, bound, return_period, all_pairs, verbose=verbose, singlecore=singlecore, attempts_max=3)
    hist_prices_path = get_write_path(start_date, end_date, granularity, market_cap, bound, return_period, "hist_prices", ext='csv')
    if verbose:
        print("writing {} to {}".format(hist_prices, hist_prices_path))
    hist_prices.to_csv(hist_prices_path)
    hist_prices = hist_prices.interpolate(method ='linear', limit_direction ='forward')
    hist_prices = hist_prices.interpolate(method ='linear', limit_direction ='backward')
    return hist_prices

def load_hist_prices(hist_prices_file):
    if hist_prices_file is None:
        return None
    hist_prices = pd.read_csv(hist_prices_file)
    print(hist_prices.columns)
    hist_prices = hist_prices.set_index('time')
    hist_prices = hist_prices.interpolate(method ='linear', limit_direction ='forward')
    hist_prices = hist_prices.interpolate(method ='linear', limit_direction ='backward')
    return hist_prices

def get_prices(start_date, end_date, granularity, market_cap, bound, return_period,  verbose=False, singlecore=True):
    #TODO save hist prices permanently in ticks with all details such as granularity
    #TODO read all hist prices from disk
    hist_prices_path = get_write_path(start_date, end_date, granularity, market_cap, bound, return_period, 'hist_prices', ext='csv')
    hist_prices = None
    if os.path.exists(hist_prices_path):
        if verbose:
            print('loading history prices file: {}'.format(hist_prices_path))
        hist_prices = load_hist_prices(hist_prices_path)
    else:
        if verbose:
            print('downloading history prices to file: {}'.format(hist_prices_path))
        hist_prices = download_hist_prices(start_date, end_date, granularity, market_cap, bound, return_period, verbose=verbose, singlecore=singlecore)
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
