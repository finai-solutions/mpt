from datetime import datetime

PORTFOLIO_TOKEN_LENGTH = 5
START_DATE = '2022-07-25-00-00'
END_DATE = datetime.now().strftime("%Y-%m-%d-%H-%M")
TOTAL_BALANCE = 10000
GRANULARITY = 86400  #86400, 21600, 3600, 900, 300, 60
bound = (0,0.4) # change to (-1, 1) if you want to short
PORTFOLIO_SIZE = 3
MARKETCAP_LIMIT = 10**10 #unicorn
RETURN_PERIOD = 45 # 45 days
INCREMENTAL_ID = datetime.now()
DATA_DIR="data"
