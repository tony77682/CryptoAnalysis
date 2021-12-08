import streamlit as st
from datetime import datetime
import json
from requests import Session
from tradingview_ta import *
import concurrent.futures

class Crypto_analysis:
    
    all=[]
    interval=""
    mma_coins={}
    buy=[]
    sell=[]
    strong_buy=[]
    strong_sell=[]
    recommanded_list=[]
    

    #this method collect the 100 latest cryptocurrency 
    #filtering them by taking only the positive changes in 1h, 24h, 7d, +Vol_24h
    def get_marketCap():
        url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
        parameters = {
        'start':'1',
        'limit':'200', # you can change this value to get bigger list, but it will effect raise the processing time around 2 min with each 100
        'convert':'USDT'#bridge coin (btcusdt) u can change it to BUSD or any bridge
        }
        headers = {
        'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': 'API-KEY',
        }

        session = Session()
        session.headers.update(headers)

        try:
            changes={}
            response = session.get(url, params=parameters)
            data = json.loads(response.text)
            
            with st.spinner("Collecting latest Cyrpto and save the crypto with positive changes"):
                
                for d in data.keys():
                    if d=="data":
                        for i in data[d]:
                            ticker=i["symbol"]
                            Crypto_analysis.all.append(ticker)
                            proc_1h = i["quote"]["USDT"]["percent_change_1h"]
                            proc_24h= i["quote"]["USDT"]["percent_change_24h"]
                            proc_7d = i["quote"]["USDT"]["percent_change_7d"]
                            vol_ch24h=i["quote"]["USDT"]["volume_change_24h"]
                            changes[ticker] = [proc_1h,proc_24h ,proc_7d, vol_ch24h]
            
            Crypto_analysis.recommanded_list = [coin for coin in changes.keys() if changes[coin][0] and changes[coin][1]and changes[coin][2]and changes[coin][3]> 0] 
            
        except: 
            pass 
        st.success("Done collecting Cryptos")
    
    def get_analysis_mma(ticker):
        try:
            ticker_summery = TA_Handler(
                symbol=ticker+"USDT",
                screener="crypto",
                exchange="binance",
                interval=Crypto_analysis.interval
            )
            
            rec = ticker_summery.get_analysis().moving_averages["RECOMMENDATION"]

            if rec == "SELL": Crypto_analysis.sell.append(ticker)
            if rec == "STRONG_SELL": Crypto_analysis.strong_sell.append(ticker)
            if rec == "BUY": Crypto_analysis.buy.append(ticker)
            if rec == "STRONG_BUY": Crypto_analysis.strong_buy.append(ticker)

        except:
            pass
        
    def get_analysis_osc(ticker):
        try:
            ticker_summery = TA_Handler(
                symbol=ticker+"USDT",
                screener="crypto",  
                exchange="binance", 
                interval=Crypto_analysis.interval 
            )
            Crypto_analysis.mma_coins[ticker] = ticker_summery.get_analysis().oscillators["RECOMMENDATION"]          
            
        except: 
            pass
       
    def do_draw_sidebar():

        # setup the screen for streamlit to be wide
        
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

    def do_draw_body():
        
        st.header("BUY/SELL")
        col1, col2,col3,col4= st.columns(4)
   
        col1.success("Strong buy")
        col2.success("Buy")
        col3.error("Sell")
        col4.error("Strong sell")
        
        col1.table(list(Crypto_analysis.strong_buy))
        col2.table(list(Crypto_analysis.buy))
        col3.table(list(Crypto_analysis.sell))
        col4.table(list(Crypto_analysis.strong_sell))
    
    def do_analysis():
        with concurrent.futures.ProcessPoolExecutor() as executor:
            futures = [executor.submit(Crypto_analysis.get_analysis_osc(ticker),) for ticker in Crypto_analysis.all]
            futures = [executor.submit(Crypto_analysis.get_analysis_mma(ticker),) for ticker in Crypto_analysis.mma_coins.keys()]

def main():
    Crypto_analysis.do_draw_sidebar()
    Crypto_analysis.get_marketCap()
    Crypto_analysis.do_analysis()    
    Crypto_analysis.do_draw_body()
        
if __name__ == '__main__':
    start=datetime.now()
    main()
    st.write("Execution time",datetime.now()-start)
