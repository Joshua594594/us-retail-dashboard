from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import yfinance as yf
import requests
import os
import math
from deep_translator import GoogleTranslator
import urllib.parse
import xml.etree.ElementTree as ET

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRED_API_KEY = "7cbd5f701c3b7e514e3dfcb6810d2fb7"
HEADERS = {'User-Agent': 'Mozilla/5.0'}

# [Tab 1] FRED 소매 판매
@app.get("/api/fred")
def get_fred_data():
    series_map = {
        "Total Retail Trade": "RSAFS", "Nonstore Retailers": "RSNSR",
        "Motor Vehicle and Parts Dealers": "RSMVPD", "Furniture and Home Furnishings Stores": "RSFHFS",
        "Electronics and Appliance Stores": "RSEAS", "Building Material and Garden Equipment and Supplies Dealers": "RSBMGESD",
        "Food and Beverage Stores": "RSDBS", "Health and Personal Care Stores": "RSHPCS",
        "Gasoline Stations": "RSGASS", "Clothing and Clothing Accessories Stores": "RSCCAS",
        "Sporting Goods, Hobby, Musical Instrument, and Book Stores": "RSSGHBMS",
        "General Merchandise Stores": "RSGMS", "Miscellaneous Store Retailers": "RSMSR"
    }
    all_data = []
    for cat, ticker in series_map.items():
        try:
            url = f"https://api.stlouisfed.org/fred/series/observations?series_id={ticker}&api_key={FRED_API_KEY}&file_type=json"
            res = requests.get(url, headers=HEADERS, timeout=5).json()
            df = pd.DataFrame(res['observations'])
            df['Date'] = pd.to_datetime(df['date'])
            df['Sales'] = pd.to_numeric(df['value'], errors='coerce')
            df['Category'] = cat
            all_data.append(df[['Date', 'Category', 'Sales']].dropna())
        except:
            continue
            
    if not all_data: return {"error": "FRED 데이터를 불러올 수 없습니다."}
    
    df = pd.concat(all_data, ignore_index=True)
    df_pivot = df.pivot(index='Date', columns='Category', values='Sales')
    if 'Total Retail Trade' in df_pivot and 'Nonstore Retailers' in df_pivot:
        df_pivot['Offline'] = df_pivot['Total Retail Trade'] - df_pivot['Nonstore Retailers']
    
    latest_date = df_pivot.index.max()
    curr_df = df_pivot[df_pivot.index.year == latest_date.year]
    prev_df = df_pivot[(df_pivot.index.year == latest_date.year - 1) & (df_pivot.index.month <= latest_date.month)]
    
    ytd_growth = ((curr_df.sum() / prev_df.sum()) - 1) * 100
    ytd_growth = ytd_growth.fillna(0).to_dict()
    
    yoy_df = df_pivot.pct_change(periods=12) * 100
    table_df = yoy_df.tail(12).fillna(0)
    table_data = [{"Date": d.strftime("'%y / %m"), **row} for d, row in table_df.iterrows()]
    
    return {"ytd": ytd_growth, "table": table_data, "latest_month": latest_date.month, "year": latest_date.year}

# [Tab 2] OTEXA (CSV 필요)
@app.get("/api/otexa")
def get_otexa_data():
    if not os.path.exists('otexa_share.csv') or not os.path.exists('otexa_yoy.csv'):
        return {"error": "OTEXA CSV 파일이 서버에 없습니다."}
    
    share_df = pd.read_csv('otexa_share.csv').fillna(0)
    yoy_df = pd.read_csv('otexa_yoy.csv').fillna(0)
    
    return {
        "share": share_df.to_dict(orient='records'),
        "yoy": yoy_df.to_dict(orient='records'),
        "years": [c for c in share_df.columns if c != 'Country']
    }

# [Tab 3] 기업 모니터링
@app.get("/api/company")
def get_company_data(ticker: str, keyword: str):
    tkr = yf.Ticker(ticker)
    try: hist = tkr.history(period="1y")
    except: hist = pd.DataFrame()
    
    info = {}
    try: info = tkr.info
    except: pass
    
    # 현재가 (NaN 버그 픽스 적용)
    current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
    if (current_price == 0 or pd.isna(current_price)) and not hist.empty:
        valid_closes = hist['Close'].dropna()
        current_price = valid_closes.iloc[-1] if not valid_closes.empty else 0
        
    mom_growth = 0
    hist_json = []
    if not hist.empty:
        hist_df = hist.reset_index()
        hist_df['YM'] = hist_df['Date'].dt.to_period('M')
        monthly_avg = hist_df.groupby('YM')['Close'].mean()
        if len(monthly_avg) >= 2:
            mom_growth = ((monthly_avg.iloc[-1] / monthly_avg.iloc[-2]) - 1) * 100
        hist_json = [{"date": str(d)[:10], "close": c if not pd.isna(c) else 0} for d, c in zip(hist.index, hist['Close'])]
        
    # 재무 (QoQ)
    fin_data = []
    try:
        q_fin = tkr.quarterly_financials
        if q_fin is not None and not q_fin.empty:
            rev_idx = [i for i in q_fin.index if 'Total Revenue' in i or 'Revenue' in i]
            op_idx = [i for i in q_fin.index if 'Operating Income' in i]
            rows = []
            if rev_idx: rows.append(rev_idx[0])
            if op_idx: rows.append(op_idx[0])
            if rows:
                raw_fin = q_fin.loc[rows].copy().iloc[:, :4]
                raw_fin.columns = [str(c).split(' ')[0] for c in raw_fin.columns]
                raw_fin = raw_fin[raw_fin.columns[::-1]]
                growth = raw_fin.pct_change(periods=1, axis=1) * 100
                fin_data = growth.fillna(0).reset_index().to_dict(orient='records')
    except: pass
    
    # 뉴스
    translated_news = []
    try:
        url = f"https://news.google.com/rss/search?q={urllib.parse.quote(keyword)}&hl=ko&gl=KR&ceid=KR:ko" if ".KS" in ticker or ".KQ" in ticker else f"https://news.google.com/rss/search?q={urllib.parse.quote(keyword)}&hl=en-US&gl=US&ceid=US:en"
        req = urllib.request.Request(url, headers=HEADERS)
        xml_data = urllib.request.urlopen(req).read()
        root = ET.fromstring(xml_data)
        for item in root.findall('.//item')[:5]:
            title = item.find('title').text
            link = item.find('link').text
            pub = item.find('source').text
            if not (".KS" in ticker or ".KQ" in ticker):
                title = GoogleTranslator(source='auto', target='ko').translate(title)
            translated_news.append({"title": f"[{pub}] {title}", "link": link})
    except: pass

    return {
        "price": current_price,
        "mom": mom_growth,
        "history": hist_json,
        "financials": fin_data,
        "news": translated_news
    }

# [Tab 4] 거시경제
@app.get("/api/macro")
def get_macro():
    macro_res = {}
    
    # YF Data
    yfs = {"krw": "KRW=X", "cotton": "CT=F", "wti": "CL=F"}
    for k, tkr in yfs.items():
        try:
            h = yf.Ticker(tkr).history(period="1y")['Close'].dropna()
            macro_res[k] = {"start": h.iloc[0], "end": h.iloc[-1], "chg": ((h.iloc[-1]/h.iloc[0])-1)*100, "history": [{"d": str(d)[:10], "v": v} for d, v in zip(h.index, h)]}
        except: macro_res[k] = None

    # FRED Data
    freds = {"gdp": "GDPC1", "cpi": "CPIAPPSL", "inv": "MRTSIR448USS", "sales": "RSCCASN", "us_rate": "FEDFUNDS"}
    for k, tkr in freds.items():
        try:
            url = f"https://api.stlouisfed.org/fred/series/observations?series_id={ticker}&api_key={FRED_API_KEY}&file_type=json"
            res = requests.get(url, headers=HEADERS, timeout=5).json()['observations']
            df = pd.DataFrame(res)
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            df = df.dropna().tail(60) # 5년
            macro_res[k] = {"start": df['value'].iloc[0], "end": df['value'].iloc[-1], "chg": ((df['value'].iloc[-1]/df['value'].iloc[0])-1)*100, "history": [{"d": d, "v": v} for d, v in zip(df['date'], df['value'])]}
        except: macro_res[k] = None

    return macro_res