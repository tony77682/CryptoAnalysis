import streamlit as st
import asyncio
from datetime import datetime
import json
from requests import Session
from tradingview_ta import *
from multiprocessing import Process, Queue, current_process, freeze_support, set_start_method




class Crypto_analysis:
    
    
    all=[]
    interval=""
    mma_coins={}
    buy=[]
    sell=[]
    strong_buy=[]
    strong_sell=[]
    recommanded_list=[]
    

    #this method collect the 200 latest cryptocurrency 
    #filtering them by taking only the positive changes in 1h, 24h, 7d, +Vol_24h
    def get_marketCap():
        url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
        parameters = {
        'start':'1',
        'limit':'100', 
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
        
    
    ## Example{'RECOMMENDATION': 'BUY', 'BUY': 9, 'SELL': 5, 'NEUTRAL': 1, 'COMPUTE': {'EMA10': 'SELL', 'SMA10': 'SELL', 'EMA20': 'SELL', 'SMA20': 'SELL', 'EMA30': 'BUY', 'SMA30': 'BUY', 'EMA50': 'BUY', 'SMA50': 'BUY', 'EMA100': 'BUY', 'SMA100': 'BUY', 'EMA200': 'BUY', 'SMA200': 'BUY', 'Ichimoku': 'NEUTRAL', 'VWMA': 'SELL', 'HullMA': 'BUY'}}

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
       
    def draw_sidebar():

        # setup the screen for streamlit to be wide
        st.set_page_config(layout="wide")
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

    def draw_body():
        
        st.header("BUY/SELL")
        col1, col2,col3,col4= st.columns(4)

        if Crypto_analysis.strong_buy or Crypto_analysis.strong_sell is not None:
           
            #col1.success("Recommanded")
            col1.success("Strong buy")
            col2.success("Buy")
            col3.error("Sell")
            col4.error("Strong sell")
            #col1.table(list(Crypto_analysis.recommanded_list))
            col1.table(list(Crypto_analysis.strong_buy))
            col2.table(list(Crypto_analysis.buy))
            col3.table(list(Crypto_analysis.sell))
            col4.table(list(Crypto_analysis.strong_sell))
        else:
            col2.success("Buy")
            col3.error("Sell")
            col2.table(Crypto_analysis.buy)
            col3.table(Crypto_analysis.sell)

    #
    # Function run by worker processes
    #

    def worker(input, output):
        for func, args in iter(input.get, 'STOP'):
            result =Crypto_analysis.calculate(func, args)
            output.put(result)

    #
    # Function used to calculate result
    #

    def calculate(func, args):
        result = func(*args)
        return '%s says that %s%s = %s' % \
            (current_process().name, func.__name__, args, result)

    def loop_tasks(task):
        NUMBER_OF_PROCESSES = 4
        processes: list[Process] = []

        # Create queues
        task_queue = Queue()
        done_queue = Queue()
    
        # Submit tasks
        for task in task:
            task_queue.put(task)
        
        #start the processes
        for i in range(NUMBER_OF_PROCESSES):
            p=Process(target=Crypto_analysis.worker, args=(task_queue, done_queue))
            p.start()
            processes.append(p)
        
        # Join the processes
        for p in processes:
            p.join()
        
        # Tell child processes to stop
        for p in range(NUMBER_OF_PROCESSES):
            task_queue.put('STOP')



def main():
    
       
    Crypto_analysis.draw_sidebar()
    Crypto_analysis.get_marketCap()

    loop_workersOSC = [(Crypto_analysis.get_analysis_osc(ticker)) for ticker in Crypto_analysis.all]
    loop_workersMMA = [(Crypto_analysis.get_analysis_mma(ticker)) for ticker in Crypto_analysis.mma_coins.keys()]

    Crypto_analysis.loop_tasks(loop_workersOSC)
    Crypto_analysis.loop_tasks(loop_workersMMA)

    Crypto_analysis.draw_body()
   
    
if __name__ == '__main__':
    
    start=datetime.now()
    #freeze_support()
    main()
    
    st.write("Execution time",datetime.now()-start)
    
    
    
