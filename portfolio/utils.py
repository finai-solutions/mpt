import os
import requests
from datetime import datetime, timedelta
import re

from bs4 import BeautifulSoup

from Historic_Crypto import HistoricalData
from configuration import DATA_DIR

fmt='%Y-%m-%d-%H-%M'
fmtin='%Y-%m-%d %H:%M:%S'
fmtin2 = '%Y-%m-%d'

def get_timestamp_from_mergedate(str_date):
    print("mergedate: {}".format(str_date))
    timestamp = datetime.strptime(str_date, fmt)
    print('timestamp: {}'.format(timestamp))
    return timestamp


def get_market_cap(token_name, verbose=False):
    base_url = "https://coinmarketcap.com/currencies/"
    url = base_url+token_name
    r = requests.get(url)
    data = r.text
    soup = BeautifulSoup(data, "html5lib")
    try:
        return float(''.join(soup.find("div", attrs={'coin-metrics'}).find("dd").text.split('$')[1].split(',')))
    except Exception as e:
        if verbose:
            print(e)
    return 0

def get_symbol_name(symbol, verbose=False):
    symbol = symbol.split('-')[0]
    url = "https://www.coindesk.com/calculator/"+symbol+"/usd/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html5lib")
    convert_msg = soup.find('h1', class_="typography__StyledTypography-sc-owin6q-0").text
    token_name = None
    try:
        res_symbol = convert_msg.split(':')[0].split(' ')[1]
        if res_symbol==symbol:
            token_name = convert_msg.split(':')[1].split(' to ')[0].strip()
        if len(token_name.split(' '))>1:
            token_name='-'.join(token_name.split(' '))
    except Exception as e:
        if verbose:
            print(e)
    return token_name


def get_write_path(start_date, end_date, granularity, market_cap, bound, return_period, file_name, ext='txt'):
    return DATA_DIR+os.sep+file_name+'_'+'_'.join([str(i) for i in [start_date, end_date, str(granularity), market_cap,  bound, return_period]])+'.'+ext


def valid_date(token, date, fmt, max_granularity=86400, verbose=False):
    try:
        res = HistoricalData(token, max_granularity, date, (datetime.strptime(date, fmt)+timedelta(days=1)).strftime(fmt), verbose=False).retrieve_data()
        print('valid_date: {}'.format(date))
        return True
    except Exception as e:
        if verbose:
            print('valida_date error: {}'.format(e))
        return False
    return True

def get_midway(s, e, fmt):
    delta = (datetime.strptime(e, fmt)-datetime.strptime(s, fmt))
    delta = timedelta(days=delta.days)
    return (datetime.strptime(s,fmt)+delta/2).strftime(fmt)

def get_initial_date(token, interval, max_granularity=86400, fmt='%Y-%m-%d-%H-%M'):
    s = interval[0]
    e = interval[1]
    if valid_date(token, s, fmt, max_granularity):
        return s
    else:
        # if no initial date within given interval, throw an error
        if s==e:
            raise Error("no initial date within given interval")
        # check midway throrough m between s, e
        m = get_midway(s, e, fmt)
        if s==m:
            return s
        print('m: {}, s: {}, e: {}'.format(m, s, e))
        # if it's valid, then get_intial_date with new interval <s,m>
        if valid_date(token, m, fmt, max_granularity):
            res = get_initial_date(token, [s,m])
            print('<s,m>: {}'.format(res))
            return res
        # else get_intial_date with new pair <m,e>
        else:
            res = get_initial_date(token, [m,e])
            print('<m,e>: {}:'.format(res))
            return res

    return e #TODO (res)

def get_file_params(file, verbose=True):
    file_params = re.split(DATA_DIR+'/'+'[a-z_]+', file)[1]
    file_params = file_params.split('_')
    return {'file': file, 'start_date': file_params[0], 'end_date': file_params[1], 'granularity': int(file_params[2]), 'market_cap': int(file_params[3]), 'bound': file_params[4], 'return_period': int(file_params[5].split('.')[0])}
