from datetime import datetime
import os

START_DATE = '2024-01-01-00-00'
END_DATE = None
TOTAL_BALANCE = 10000
GRANULARITY = 300  #86400(1d), 21600(6h), 3600(1h), 900(15min), 300(5min), 60(min)
bound = (0,0.4) # change to (-1, 1) if you want to short
MARKETCAP_LIMIT = 10**9 #unicorn
RETURN_PERIOD = 45 # 45 days
DATA_DIR="data"

def get_write_path(file_name, ext='txt'):
    return DATA_DIR+os.sep+file_name+'_'+'_'.join([str(i) for i in [START_DATE, END_DATE, str(GRANULARITY), MARKETCAP_LIMIT,  bound, RETURN_PERIOD]])+'.'+ext
