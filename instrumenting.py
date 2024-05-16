import time
import os
from datetime import datetime

import tqdm

from portfolio.portfolio import get_portfolio
from portfolio.utils import fmt
from configuration import TOTAL_BALANCE
from portfolio.utils import get_write_path

start_dates = ['2018-01-01-00-00', '2019-01-01-00-00', '2020-01-01-00-00', '2021-01-01-00-00', '2022-01-01-00-00', '2023-01-01-00-00', '2024-01-01-00-00']
start_dates.sort(reverse=True)
granularities = [3600]
mcs = [10**10, 10**9]
bounds = [(0,0.4)]
return_periods = [30]

# data analysis instrumentation
for return_period in tqdm.tqdm(return_periods, desc='return period', position=0):
    for mc in tqdm.tqdm(mcs, desc='market cap', position=1, leave=False):
        for bound in tqdm.tqdm(bounds, desc='bound', position=2, leave=False):
            for start_date in tqdm.tqdm(start_dates, desc='start_date', position=3, leave=False):
                for granularity in tqdm.tqdm(granularities, desc='granularity', position=4, leave=False):
                    get_portfolio(start_date, datetime.now().strftime(fmt), granularity, mc, bound, return_period, TOTAL_BALANCE, verbose=True, singlecore=False)
