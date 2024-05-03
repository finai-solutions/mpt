from history_prices import get_token_date
from portfolio import get_equally_weighted_portfolio, get_global_minimum_variance_portfolio, get_max_sharpe_portfolio
from vis import plot
from configuration import TOTAL_BALANCE

start_dates = ['2018-01-01-00-00', '2019-01-01-00-00', '2020-01-01-00-00', '2021-01-01-00-00', '2022-01-01-00-00', '2023-01-01-00-00', '2024-01-01-00-00']
start_dates.sort(reverse=True)
granularities = [86400, 21600, 3600, 900, 300, 60]
mcs = [10**9, 10**10]
bounds = [(0,0.4), (0,1), (-1,1)]
return_periods = [30, 45, 60, 90, 180, 365]

for return_period in return_periods:
    for mc in mcs:
        for bound in bounds:
            for date_date in start_dates:
                for granularity in granularities:
                    get_portfolio(start_date, None, granularity, mc, bound, return_period, TOTAL_BALANCE, True)
