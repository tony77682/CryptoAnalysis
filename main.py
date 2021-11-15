import streamlit as st
import asyncio
import os 
from datetime import datetime
import json
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
from requests import Request, Session
from tradingview_ta import TA_Handler, Interval, Exchange



# setup the screen for streamlit to be wide
st.set_page_config(layout="wide")


async def get_marketCap():
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
    parameters = {
    'start':'1',
    'limit':'100', # 100 i think is the best depending on the time analysis
    'convert':'USDT'#bridge coin (btcusdt) u can change it to BUSD or any bridge
    }
    headers = {
    'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': '23958fbd-8c7e-4ecf-86db-caca0a910906',
    }

    session = Session()
    session.headers.update(headers)

    try:
        crypto_data=[] 
        changes={}
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
        
        for d in data.keys():
            if d=="data":
                for i in data[d]:
                    ticker=i["symbol"]
                    proc_1h = i["quote"]["USDT"]["percent_change_1h"]
                    proc_24h= i["quote"]["USDT"]["percent_change_24h"]
                    proc_7d = i["quote"]["USDT"]["percent_change_7d"]
                    crypto_data.append(ticker)
                    changes[ticker] = [proc_1h, proc_24h, proc_7d]
        
        return crypto_data,changes 
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        return e
    #await asyncio.sleep(1)


async def get_analysis_mma(ticker,interval):
    try:
        ticker_summery = TA_Handler(
            symbol=ticker,
            screener="crypto",  # "america"
            exchange="binance",  # "NASDAQ"
            interval=interval  # Interval.INTERVAL_1_DAY
        )
        analyse = ticker_summery.get_analysis().moving_averages
        if analyse is not None:
            return analyse 
    except:
        pass
    #await asyncio.sleep(1)


async def get_analysis_osc(ticker,interval):
    try:
        ticker_summery = TA_Handler(
            symbol=ticker,
            screener="crypto",  # "america"
            exchange="binance",  # "NASDAQ"
            interval=interval  # Interval.INTERVAL_1_DAY
        )
        analyse = ticker_summery.get_analysis().oscillators
        if analyse is not None and analyse["RECOMMENDATION"]=="BUY": 
            return analyse 
    except:
        pass
    #await asyncio.sleep(1)

async def crypto_analysis(info):
    sell, buy, strong_buy, strong_sell=[]

    for i in info:
        if info[i]["RECOMMENDATION"] == "BUY":
            buy.append(i.replace("USDT",""))
        if info[i]["RECOMMENDATION"] == "SELL":
            sell.append(i.replace("USDT", ""))
        if info[i]["RECOMMENDATION"] == "STRONG_BUY":
            strong_buy.append(i.replace("USDT",""))
        if info[i]["RECOMMENDATION"] == "STRONG_SELL":
            strong_sell.append(i.replace("USDT", ""))
    
    if strong_buy and strong_sell is not None:
        return buy, sell, strong_buy, strong_sell#await asyncio.sleep(1)


def save_file(final_list):
    with open("supported_coin_list.txt", "w") as file:
        for coin in final_list:
            file.writelines(coin+'\n')
        file.close()
    #await asyncio.sleep(1)

def coinsFiltring(crypto_changes):
    filtered_coins = [coin for coin in crypto_changes.keys() if crypto_changes[coin][0] and crypto_changes[coin][1] and crypto_changes[coin][2] > 0]
    
    return filtered_coins
    #await asyncio.sleep(1)

def infoFiltering(info_mma):
    #st.write(self.info_mma)
    if(len(info_mma)==0): 
        st.write("List is empty")
    else: 
        info_filtered = {x: y for x, y in info_mma.items() if (y is not None and y != 0)}
    
    return info_filtered     
    #await asyncio.sleep(1)

def btn_mma(btn,ticker):
    
    info_mma={}
    if btn=="1 minute":
        info_mma[ticker] = get_analysis_mma( Interval.INTERVAL_1_MINUTE)
    
    if btn=="5 minutes":
        info_mma[ticker] = get_analysis_mma( Interval.INTERVAL_5_MINUTES)
    
    if btn=="15 minutes":
        info_mma[ticker] = get_analysis_mma( Interval.INTERVAL_15_MINUTES)
    
    if btn=="1 hour":
       info_mma[ticker] = get_analysis_mma( Interval.INTERVAL_1_HOUR)
    
    if btn=="4 hours":
        info_mma[ticker] = get_analysis_mma( Interval.INTERVAL_4_HOURS)
    
    if btn=="1 day":
        info_mma[ticker] = get_analysis_mma( Interval.INTERVAL_1_DAY)
    
    if btn=="1 week":
        info_mma[ticker] = get_analysis_mma( Interval.INTERVAL_1_WEEK)
    
    if btn=="1 month":
        info_mma[ticker] = get_analysis_mma( Interval.INTERVAL_1_MONTH)

    return info_mma


def btn_osc(btn,ticker):
    info_osc={}
    if btn=="1 minute":
        info_osc[ticker] = get_analysis_osc( Interval.INTERVAL_1_MINUTE)  
    if btn=="5 minutes":
        info_osc[ticker] = get_analysis_osc( Interval.INTERVAL_5_MINUTES)
    if btn=="15 minutes":
       info_osc[ticker] = get_analysis_osc( Interval.INTERVAL_15_MINUTES)
    if btn=="1 hour":
        info_osc[ticker] = get_analysis_osc( Interval.INTERVAL_1_HOUR)
    if btn=="4 hours":
        info_osc[ticker] = get_analysis_osc( Interval.INTERVAL_4_HOURS)
    if btn=="1 day":
        info_osc[ticker] = get_analysis_osc( Interval.INTERVAL_1_DAY)
    if btn=="1 week":
        info_osc[ticker] = get_analysis_osc( Interval.INTERVAL_1_WEEK)
    if btn=="1 month":
        info_osc[ticker] = get_analysis_osc( Interval.INTERVAL_1_MONTH)
    
    return info_osc

def draw_sidebar():
    st.sidebar.header("Crypto-Analysis")
    btn = st.sidebar.radio("Choose interval",(
        "1 minute", 
        "5 minutes",
        "15 minutes",
        "1 hour",
        "4 hours",
        "1 day",
        "1 week",
        "1 month"))
    if btn is not None: return btn
     

def draw_body(strong_buy,strong_sell,buy,sell,recommanded_crypto):
    
    st.header("BUY/SELL")
    col1, col2,col3,col4,col5 = st.columns(5)
    if strong_buy or strong_sell is not None:
        col1.success("recommanded")
        col2.success("Strong buy")
        col3.success("Buy")
        col4.error("Sell")
        col5.error("Strong sell")
        col1.table(recommanded_crypto)
        col2.table(strong_buy)
        col3.table(buy)
        col4.table(sell)
        col5.table(strong_sell)
    else:
        col2.success("Buy")
        col3.error("Sell")
        col2.table(buy)
        col3.table(sell)

def do_job():
    
    #fix before sending
    cryptoChanges = {}


    filteredData={}
    recommanded_crypto={}

    #make sure it return the btn correctly
    btn = draw_sidebar()
    

    filtered_coins = coinsFiltring(cryptoChanges)
    
    # make sure filtered_coins is not empty
    for ticker in filtered_coins:
        btnMMA= btn_mma(btn,ticker)



    info_filtered_mma = infoFiltering(btnMMA)
    
    buy, sell, strong_buy, strong_sell = crypto_analysis(info_filtered_mma)
    
    for ticker in info_filtered_mma:
        ticker = ticker+"USDT"
    info_osc = btn_osc(btn,ticker)

    for ticker in info_osc.keys():
        recommanded_crypto.append(ticker)  
        st.write(ticker)

    #self.recommanded_crypto=list(info2_filtered.copy())  
    
    draw_body(strong_buy,strong_sell,buy,sell,recommanded_crypto)
    

"""
    # add this to draw sidebar
    st.sidebar.subheader("Overwrite [supported_coin_list.txt] coin list")
    option = st.sidebar.radio("", (
        "Strong buy list",
        "Buy list","Recommanded list"))
    bt = st.sidebar.button("save")



    if bt:
        if option=="Strong buy list":
            self.save_file(self.strong_buy)
        if option=="Buy list":
            self.save_file(self.buy)
        if option == "Recommanded list":
            self.save_file(self.recommanded_crypto)
        directory_path = os.getcwd()
        st.sidebar.success(
            f"file [supported_coin_list.txt]\nfile_path: {directory_path}")
"""

async def main():
    divs1 = loop.create_task(get_marketCap())
    divs2 = loop.create_task(get_analysis_mma())
    divs3 = loop.create_task(get_analysis_osc())
    divs4 = loop.create_task(crypto_analysis())
    divs5 = loop.create_task(save_file())
    divs6 = loop.create_task(coinsFiltring())
    divs7 = loop.create_task(infoFiltering())

    await asyncio.wait([divs1,divs2,divs3,divs4,divs5,divs6,divs7])
    return divs1, divs2, divs3, divs4, divs5, divs6, divs7

if __name__ == '__main__':
    try:
        loop = asyncio.get_event_loop()
        loop.set_debug(1)
        div1, div2, div3, div4, div5, div6, div7 = loop.run_until_complete(main())
        print("result div1= "+ div1.result()+"\n")
        print("result div2= "+ div2.result()+"\n")
        print("result div3= "+ div3.result()+"\n")
        print("result div4= "+ div4.result()+"\n")
        print("result div5= "+ div5.result()+"\n")
        print("result div6= "+ div6.result()+"\n")
        print("result div7= "+ div7.result()+"\n")
    
    except Exception as e:
        pass
    
    finally:
        loop.close()