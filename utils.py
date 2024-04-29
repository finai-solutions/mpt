from bs4 import BeautifulSoup
import requests
'''
def get_symbol_name(token_symbol=None):
    base_url = "https://coinmarketcap.com/all/views/all/"
    r = requests.get(base_url)
    data = r.text
    soup = BeautifulSoup(data, "html5lib")
    token_name=None
    rows = soup.find_all("tr", attrs="cmc-table-row")
    print(len(rows))
    print(rows[20])
    for tr_i in rows:
        tr_i_div = tr_i.find("div", attrs="sc-22e34915-0")
        #TODO FAILS TO WORK DUE TO HIDDEN HTML CONTENT,
        # VIA AJAX CALLS.
        tr_i_text = tr_i_div.text
        if tr_i_text[:len(token_symbol)]==token_symbol:
            token_name = tr_i_text[len(token_symbol):]
            break
    if len(token_name.split(' '))>1:
        token_name='-'.join(token_name.split(' '))
    return token_name

'''
def get_market_cap(token_name):
    base_url = "https://coinmarketcap.com/currencies/"
    url = base_url+token_name
    r = requests.get(url)
    data = r.text
    soup = BeautifulSoup(data, "html5lib")
    print('token_name: {}'.format(token_name))
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
