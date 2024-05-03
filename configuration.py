from datetime import datetime

PORTFOLIO_TOKEN_LENGTH = 5
START_DATE = '2024-01-01-00-00'
END_DATE = datetime.now().strftime("%Y-%m-%d-%H-%M")
TOTAL_BALANCE = 10000
GRANULARITY = 300  #86400(1d), 21600(6h), 3600(1h), 900(15min), 300(5min), 60(min)
bound = (0,0.4) # change to (-1, 1) if you want to short
PORTFOLIO_SIZE = 3
MARKETCAP_LIMIT = 10**9 #unicorn
RETURN_PERIOD = 45 # 45 days
INCREMENTAL_ID = datetime.now()
DATA_DIR="data"
