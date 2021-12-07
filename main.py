import streamlit as st
import asyncio
from datetime import datetime
import json
from requests import Session
from tradingview_ta import *

# setup the screen for streamlit to be wide
st.set_page_config(layout="wide")

class Crypto_analysis:
    
    
    
    interval=""
    filtered_coins=[]
    buy=[]
    sell=[]
    strong_buy=[]
    strong_sell=[]
    recommanded_crypto=[]

    #this method collect the 200 latest cryptocurrency 
    #filtering them by taking only the positive changes in 1h, 24h, 7d, +Vol_24h
    async def get_marketCap():
        url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
        parameters = {
        'start':'1',
        'limit':'200', 
        'convert':'USDT'#bridge coin (btcusdt) u can change it to BUSD or any bridge
        }
        headers = {
        'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': 'API-key',
        }

        session = Session()
        session.headers.update(headers)

        try:
            changes={}
            response = session.get(url, params=parameters)
            data = json.loads(response.text)
            
            with st.spinner("Collecting 100 latest Cyrpto and save the crypto with positive changes"):
                
                for d in data.keys():
                    if d=="data":
                        for i in data[d]:
                            ticker=i["symbol"]
                            proc_1h = i["quote"]["USDT"]["percent_change_1h"]
                            proc_24h= i["quote"]["USDT"]["percent_change_24h"]
                            proc_7d = i["quote"]["USDT"]["percent_change_7d"]
                            vol_ch24h=i["quote"]["USDT"]["volume_change_24h"]
                            changes[ticker] = [proc_1h, proc_24h, proc_7d, vol_ch24h]
            
            Crypto_analysis.filtered_coins = [coin for coin in changes.keys() if changes[coin][0] and changes[coin][1] and changes[coin][2] and changes[coin][3]> 0] 
            
        except: 
            pass 
        st.success("Done collecting Cryptos")
        
    
    # add progress bar to th analysis
    async def get_analysis_mma():
        
        with st.spinner("Making MMA analysis..."):
            for ticker in Crypto_analysis.filtered_coins:
                try:
                    ticker_summery = TA_Handler(
                        symbol=ticker+"USDT",
                        screener="crypto",  # "america"
                        exchange="binance",  # "NASDAQ"
                        interval=Crypto_analysis.interval  # Interval.INTERVAL_1_DAY
                    )
                    
                    rec=ticker_summery.get_analysis().moving_averages["RECOMMENDATION"]
                    if rec == "BUY": Crypto_analysis.buy.append(ticker)
                    if rec == "SELL": Crypto_analysis.sell.append(ticker)
                    if rec == "STRONG_BUY": Crypto_analysis.strong_buy.append(ticker)
                    if rec == "STRONG_SELL": Crypto_analysis.strong_sell.append(ticker)
                except:
                    pass
        st.success("Done Money moves analysis") 
    
    async def get_analysis_osc():
        recommanded_list=Crypto_analysis.strong_buy + Crypto_analysis.buy 

        with st.spinner('Making OSC. analysis...'):
            
            for ticker in recommanded_list:
                try:
                    ticker_summery = TA_Handler(
                        symbol=ticker+"USDT",
                        screener="crypto",  # "america"
                        exchange="binance",  # "NASDAQ"
                        interval=Crypto_analysis.interval  # Interval.INTERVAL_1_DAY
                    )
                    osc = ticker_summery.get_analysis().oscillators
                    
                    if osc is not None and osc["RECOMMENDATION"]=="BUY": 
                        Crypto_analysis.recommanded_crypto.append(ticker)
                    
                except: 
                    pass
        st.success("Done OSC analysis")
       
    async def draw_sidebar():

        st.sidebar.header("Crypto-Analysis")
        Crypto_analysis.interval = st.sidebar.radio("Choose interval",(
            "1 minute", 
            "5 minutes",
            "15 minutes",
            "1 hour",
            "4 hours",
            "1 day",
            "1 week",
            "1 month"))

    async def draw_body():
        
        st.header("BUY/SELL")
        col1, col2,col3,col4,col5 = st.columns(5)
        if Crypto_analysis.strong_buy or Crypto_analysis.strong_sell is not None:
            col1.success("recommanded (MMA/OSC)")
            col2.success("Strong buy (MMA)")
            col3.success("Buy (MMA)")
            col4.error("Sell (MMA)")
            col5.error("Strong sell (MMA)")
            col1.table(Crypto_analysis.recommanded_crypto)
            col2.table(Crypto_analysis.strong_buy)
            col3.table(Crypto_analysis.buy)
            col4.table(Crypto_analysis.sell)
            col5.table(Crypto_analysis.strong_sell)
        else:
            col2.success("Buy")
            col3.error("Sell")
            col2.table(Crypto_analysis.buy)
            col3.table(Crypto_analysis.sell)

async def main():
    
    asyncio.create_task(Crypto_analysis.draw_sidebar())
    asyncio.create_task(Crypto_analysis.get_marketCap())
    asyncio.create_task(Crypto_analysis.get_analysis_mma())
    asyncio.create_task(Crypto_analysis.get_analysis_osc())
    asyncio.create_task(Crypto_analysis.draw_body())
    
    
if __name__ == '__main__':
    start=datetime.now()
    asyncio.run(main())
    st.write("Execution time",datetime.now()-start)
    
    
    
    
