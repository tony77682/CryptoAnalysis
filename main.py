import streamlit as st
import asyncio
from datetime import date, datetime
import json
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
from requests import Session
from tradingview_ta import *

# setup the screen for streamlit to be wide
st.set_page_config(layout="wide")

class Crypto_analysis:
    interval=""
    info_mma={}
    analyse_mma={}
    analyse_osc={}
    recommanded_crypto=[]
    filtered_coins=[]
    info_filtered_mma={}
    buy=[]
    sell=[]
    strong_buy=[]
    strong_sell=[]
    all_tasks=[]
    

    async def get_marketCap():
        start=datetime.now()
        url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
        parameters = {
        'start':'1',
        'limit':'100', # 100 i think is the best depending on the time analysis (execution time is aroud: 53 seconds) each 50 takes around 17 second
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
            
            with st.spinner("Collecting 100 latest Cyrpto and save the crypto with positive changes"):
                for d in data.keys():
                    if d=="data":
                        for i in data[d]:
                            ticker=i["symbol"]
                            proc_1h = i["quote"]["USDT"]["percent_change_1h"]
                            proc_24h= i["quote"]["USDT"]["percent_change_24h"]
                            proc_7d = i["quote"]["USDT"]["percent_change_7d"]
                            vol_ch24h=i["quote"]["USDT"]["volume_change_24h"]
                            crypto_data.append(ticker)
                            changes[ticker] = [proc_1h, proc_24h, proc_7d, vol_ch24h]
            st.write("Execution time: ",datetime.now()-start)
            st.success("Done Collecting and sorting Crypto!")    
            #filter the coins with the changes in 1 hour, one day, one week 
            
            Crypto_analysis.filtered_coins = [coin for coin in changes.keys() if changes[coin][0] and changes[coin][1] and changes[coin][2] and changes[coin][3]> 0] 
            return Crypto_analysis.filtered_coins 
        
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            return e
        

    # add progress bar to th analysis
    async def get_analysis_mma():
        start=datetime.now()
        with st.spinner("Make MMA analysis"):
            for ticker in Crypto_analysis.filtered_coins:
                try:
                    ticker_summery = TA_Handler(
                        symbol=ticker+"USDT",
                        screener="crypto",  # "america"
                        exchange="binance",  # "NASDAQ"
                        interval=Crypto_analysis.interval  # Interval.INTERVAL_1_DAY
                    )
                    
                    Crypto_analysis.analyse_mma[ticker] =  ticker_summery.get_analysis().moving_averages
                    #return Crypto_analysis.analyse_mma
                except:
                    pass
        
        st.write("Execution time",datetime.now()-start)
        st.success('Done making the MMA. analysis!')
        #Crypto_analysis.info_filtered_mma = {x: y for x, y in Crypto_analysis.analyse_mma.items() if (y is not None and y != 0)}
    
    # add a progress bar for the analysis
    async def get_analysis_osc():
        start=datetime.now()
        with st.spinner('Making OSC. analysis...'):
            for ticker in Crypto_analysis.analyse_mma.keys():
                try:
                    ticker_summery = TA_Handler(
                        symbol=ticker+"USDT",
                        screener="crypto",  # "america"
                        exchange="binance",  # "NASDAQ"
                        interval=Crypto_analysis.interval  # Interval.INTERVAL_1_DAY
                    )
                    
                    rec = Crypto_analysis.analyse_mma[ticker]["RECOMMENDATION"]
                    if rec == "BUY": Crypto_analysis.buy.append(ticker)
                    if rec == "SELL": Crypto_analysis.sell.append(ticker)
                    if rec == "STRONG_BUY": Crypto_analysis.strong_buy.append(ticker)
                    if rec == "STRONG_SELL": Crypto_analysis.strong_sell.append(ticker)
                    
                    osc = ticker_summery.get_analysis().oscillators
                    
                    if osc is not None and osc["RECOMMENDATION"]=="BUY": 
                        Crypto_analysis.analyse_osc[ticker]=osc
                        Crypto_analysis.recommanded_crypto.append(ticker)
                    
                    #return Crypto_analysis.recommanded_crypto
                except: #(ConnectionError, Timeout, TooManyRedirects) as e:
                    pass
        st.write("Execution time",datetime.now()-start)
        st.success('Done making the OSC. analysis!')

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
        if Crypto_analysis.interval is not None: return Crypto_analysis.interval


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
    start = datetime.now()
    
    
    task0 =  asyncio.create_task(Crypto_analysis.draw_sidebar())
    task1  = asyncio.create_task(Crypto_analysis.get_marketCap())
    
    group1 =  asyncio.create_task(Crypto_analysis.get_analysis_mma())
    group2 =  asyncio.create_task(Crypto_analysis.get_analysis_osc())
    #task2 = asyncio.create_task(Crypto_analysis.get_analysis_mma())
    #task3 = asyncio.create_task(Crypto_analysis.get_analysis_osc())
    task4 = asyncio.create_task(Crypto_analysis.draw_body())
    
    
if __name__ == '__main__':
    asyncio.run(main())
    
    
    
    