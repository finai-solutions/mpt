import os
import requests

from bs4 import BeautifulSoup

DATA_DIR="data"

def get_market_cap(token_name):
    base_url = "https://coinmarketcap.com/currencies/"
    url = base_url+token_name
    r = requests.get(url)
    data = r.text
    soup = BeautifulSoup(data, "html5lib")
    try:
        return float(''.join(soup.find("div", attrs={'coin-metrics'}).find("dd").text.split('$')[1].split(',')))
    except Exception as e:
        print(e)
    return 0

def get_symbol_name(symbol):
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
        print(e)
    return token_name

def get_write_path(start_date, end_date, granularity, market_cap, bound, return_period, file_name, ext='txt'):
    return DATA_DIR+os.sep+file_name+'_'+'_'.join([str(i) for i in [start_date, end_date, str(granularity), market_cap,  bound, return_period]])+'.'+ext
