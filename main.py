from configuration import TOTAL_BALANCE
from portfolio import get_portfolio

START_DATE = '2024-01-01-00-00'
END_DATE = None
GRANULARITY = 86400  #86400(1d), 21600(6h), 3600(1h), 900(15min), 300(5min), 60(min)
BOUND = (0,0.4) # change to (-1, 1) if you want to short
MARKETCAP_LIMIT = 10**10 #unicorn
RETURN_PERIOD = 45 # 45 days


res = get_portfolio(START_DATE, END_DATE, GRANULARITY, MARKETCAP_LIMIT, BOUND, RETURN_PERIOD, TOTAL_BALANCE, True, False)
if res:
    print("success, check data/ for portfolio details")
else:
    print("failed")
