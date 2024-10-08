import os

import numpy as np
import pandas as pd
from glob import glob
from configuration import DATA_DIR
from datetime import datetime

from portfolio import utils

def adjust_dates(gran_mc_filtered_files, timefmt='%Y-%m-%d %H:%M:%S'):
    adjusted_dates_files = []
    for file in gran_mc_filtered_files:
        df = pd.read_csv(file['file'])
        adjusted_start_date = datetime.strptime(df.iloc[0]['time'], timefmt)
        adjusted_end_date = datetime.strptime(df.iloc[-1]['time'], timefmt)
        adjusted_dates_files += [{'file':file['file'], 'start_date':adjusted_start_date, 'end_date': adjusted_end_date}]
    return adjusted_dates_files

def load_history_dfs(granularity, market_cap, verbose=True):
    all_pairs_files_glob = DATA_DIR+os.sep+"hist_prices*"
    all_hist_files = glob(all_pairs_files_glob)
    dfs = []
    for file in all_hist_files:
        dfs+=[pd.read_csv(file)]
    if len(all_hist_files)==0:
        return dfs

    granularities = {}
    for file in all_hist_files:
        file_params = utils.get_file_params(file)
        #file_params = file.split('/')[1].split('.[a-z]*')[0].split('_')[2:]
        if file_params['granularity'] not in granularities:
            granularities[file_params['granularity']] = []
        granularities[file_params['granularity']] += [file_params]
    if granularity not in granularities:
        if verbose:
            print("can't find {} in ondisk files".format(granularity))
        return dfs

    gran_filtered = granularities[granularity]
    gran_mc_filtered_files = [i for i in gran_filtered if i['market_cap'] >= market_cap]
    # get actual initial, last date of each DataFrame
    #TODO adjusted_dates isn't utilized.
    #date_adjusted_files = adjust_dates(gran_mc_filtered_files)
    data_frames = []
    for file in gran_mc_filtered_files:
        data_frames += [pd.read_csv(file['file'])]
    return dfs

def get_nan_intervals(token_series, start_date, end_date):
    mask = token_series == 0
    start_date_idx = len(mask)-1
    end_date_idx = len(mask)-1
    intervals = []
    print('for {} get null interval start: {}-{}'.format(token_series.name, start_date, end_date))
    if start_date < token_series.index[0]:
        try:
            intervals +=[(start_date, datetime.strptime(token_series.index[0], utils.fmtin).strftime(utils.fmt))]
        except Exception as e:
            intervals +=[(start_date, datetime.strptime(token_series.index[0], utils.fmtin2).strftime(utils.fmt))]

    for i in range(len(mask)):
        # if nan is encountered
        if mask.iloc[i]:
            # if it's begining of nan interval
            if i==0 or mask.iloc[i-1]==False:
                start_date_idx=i
            # if it's end of interval at end of series
            if i==len(mask)-1 and mask.iloc[i-1]:
                end_date_idx=i
                # if first interval at beginning of series, then set start_date to query start_date.
                interval_start_date = token_series.index[start_date_idx]
                interval_end_date = token_series.index[end_date_idx]
                intervals+=[(interval_start_date, interval_end_date)]
        # if not NaN is encountered
        else:
            # if NaN range just ended, add interval, and set end_date_idx
            if i>0 and mask.iloc[i-1]:
                end_date_idx=i-1
                intervals+=[(token_series.index[start_date_idx], token_series.index[end_date_idx])]
    if end_date > token_series.index[-1]:
        intervals += [(datetime.strptime(token_series.index[-1], utils.fmtin).strftime(utils.fmt), end_date)]
    print("nan intervals: {}".format(intervals))
    return intervals

def merge_dfs_intervals(start_date, end_date, dfs):
    adf = pd.DataFrame()
    col_intervals = {}
    if len(dfs)==0:
        return adf, col_intervals
    df = pd.DataFrame()
    df = pd.concat(dfs)
    df=df.set_index('time')
    gdf = df.groupby('time')


    for col in df.columns:
        adf[col] = gdf[col].agg('mean')
    # clip aggregated data frame to [start_date, end_date] range
    print('start: {}'.format(start_date))
    print('end: {}'.format(end_date))
    print("index 0 date: {}".format(adf.index[0]))

    print(".")
    try:
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        adf = adf[start:end]
    except Exception as e:
        start = datetime.strptime(start_date, utils.fmt).strftime(utils.fmtin)
        end = datetime.strptime(end_date, utils.fmt).strftime(utils.fmtin)
        adf = adf[start:end]

    for col in adf.columns:
        interval = get_nan_intervals(adf[col], start_date, end_date)
        col_intervals[col] = interval

    return adf, col_intervals

def load_merge_dfs(start_date, end_date, granularity, market_cap):
    print('loading merge DataFrames from disk at interval: {}-{} for gran: {}, mc: {}'.format(start_date, end_date, granularity, market_cap))
    date_adjusted_df = load_history_dfs(granularity, market_cap)
    aggregated_df, missing_intervals = merge_dfs_intervals(start_date, end_date, date_adjusted_df)
    print('3')

    return aggregated_df, missing_intervals
