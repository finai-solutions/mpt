from configuration import TOTAL_BALANCE, BOUND, MARKETCAP_LIMIT, RETURN_PERIOD
from portfolio import get_portfolio
from configuration import START_DATE, END_DATE, GRANULARITY, MARKETCAP_LIMIT, BOUND, RETURN_PERIOD, TOTAL_BALANCE

res = get_portfolio(START_DATE, END_DATE, GRANULARITY, MARKETCAP_LIMIT, BOUND, RETURN_PERIOD, TOTAL_BALANCE, True, True)
if res:
    print("success, check data/ for portfolio details")
