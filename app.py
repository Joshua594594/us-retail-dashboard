import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import yfinance as yf # 👈 금융 데이터 호출용

# 1. 페이지 설정 및 제목
st.set_page_config(page_title="US Market & Trade Dashboard", layout="wide")
st.title("📊 US Market & Trade & Company Dashboard")

# 2. 탭 생성 (이제 탭이 4개입니다!)
# 💡 기존의 3개짜리 st.tabs를 지우고, 반드시 아래와 같이 4개로 정의해야 합니다!
tab1, tab2, tab3, tab4 = st.tabs(["📈 FRED 소매 판매", "🚢 OTEXA 수입 데이터", "🏢 기업 모니터링", "🌐 거시경제 및 원가"])

# ==========================================
# [Tab 1] 미국 소매 판매 현황 (FRED)
# ==========================================
with tab1:
    try:
        df = pd.read_csv('retail_output.csv')
        df['Date'] = pd.to_datetime(df['Date'])
        
        latest_date = df['Date'].max()
        current_year = latest_date.year
        prev_year = current_year - 1
        max_month = latest_date.month

        st.subheader(f"📈 미국 소매 카테고리 별 성장률 (1-{max_month}월) {prev_year} vs {current_year} (%)")
        
        df_curr = df[(df['Date'].dt.year == current_year) & (df['Date'].dt.month <= max_month)]
        sum_curr = df_curr.groupby('Category')['Sales'].sum()
        
        df_prev = df[(df['Date'].dt.year == prev_year) & (df['Date'].dt.month <= max_month)]
        sum_prev = df_prev.groupby('Category')['Sales'].sum()
        
        ytd_growth = ((sum_curr / sum_prev) - 1) * 100
        ytd_growth = ytd_growth.dropna().reset_index()
        ytd_growth.columns = ['Category', 'Growth']
        
        custom_order_keywords = [
            "Retail Trade Total", "Nonstore Retailers", "Sporting Goods", 
            "General Merchandise", "Furniture", "Electronics", "Clothing", 
            "Motor Vehicle", "Building", "Food and Beverage", "Health", 
            "Gasoline", "Miscellaneous", "Offline"
        ]
        
        ordered_categories = []
        for keyword in custom_order_keywords:
            for cat in ytd_growth['Category'].unique():
                if keyword.lower() in cat.lower() and cat not in ordered_categories:
                    ordered_categories.append(cat)
        
        for cat in ytd_growth['Category'].unique():
            if cat not in ordered_categories:
                ordered_categories.append(cat)

        ytd_growth['Category'] = pd.Categorical(ytd_growth['Category'], categories=ordered_categories, ordered=True)
        ytd_growth = ytd_growth.sort_values('Category', ascending=False)
        
        colors = ['#CC0000' if val < 0 else '#0070C0' for val in ytd_growth['Growth']]
        
        fig = go.Figure(go.Bar(
            x=ytd_growth['Growth'],
            y=ytd_growth['Category'],
            orientation='h',
            text=ytd_growth['Growth'].apply(lambda x: f"{x:.1f}%"),
            textposition='outside',
            marker_color=colors,
            marker_line_width=0 
        ))

        # 긴 레드 박스 (라벨 끝까지 확장 버전)
        target_cat = "Clothing and Clothing Access. Stores"
        cat_list = ytd_growth['Category'].tolist()
        
        if any(target_cat in c for c in cat_list):
            target_idx = [i for i, c in enumerate(cat_list) if target_cat in c][0]
            
            fig.add_shape(
                type="rect", xref="paper", x0=-0.25, x1=1.05, yref="y",
                y0=target_idx - 0.4, y1=target_idx + 0.4,
                line=dict(color="Red", width=2),
                fillcolor="rgba(255, 0, 0, 0.05)", layer="below"
            )

        fig.update_layout(
            plot_bgcolor='white', height=600, 
            margin=dict(l=350, r=50, t=30, b=0), # l(왼쪽 여백)을 350으로 넉넉히 설정
            xaxis=dict(showgrid=True, gridcolor='lightgray'),
            yaxis=dict(
                categoryorder='array', categoryarray=ordered_categories[::-1],
                automargin=True 
            )
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("📋 미국 소매 카테고리 별 전년 동월대비 증감률(%)")
        
        df_pivot = df.pivot(index='Date', columns='Category', values='Sales')
        yoy_df = df_pivot.pct_change(periods=12) * 100
        table_df = yoy_df.tail(12).T
        
        valid_table_order = [c for c in ordered_categories if c in table_df.index]
        table_df = table_df.reindex(valid_table_order)
        
        formatted_cols = [f"'{str(d.year)[-2:]} / {d.month}" for d in table_df.columns]
        table_df.columns = formatted_cols
        
        def highlight_clothing(row):
            if 'Clothing' in row.name:
                return ['background-color: #ffe6e6; border-top: 2px solid red; border-bottom: 2px solid red'] * len(row)
            return [''] * len(row)

        styled_table = table_df.style.apply(highlight_clothing, axis=1).format("{:.1f}%", na_rep="-")
        st.dataframe(styled_table, use_container_width=True, height=550)

    except Exception as e:
        st.error(f"소매 판매 데이터를 불러오는 중 오류가 발생했습니다: {e}")

# ==========================================
# [Tab 2] 미국 의류 수입 현황 (OTEXA)
# ==========================================
with tab2:
    try:
        df_share = pd.read_csv('otexa_share.csv')
        st.markdown("### * 미국 의류 수입 국가별 비중 (%)")
        
        fig_share = go.Figure()
        colors_years = ['#1f497d', '#2e75b6', '#5b9bd5', '#9dc3e6', '#c6d9f1']
        years = df_share.columns[1:] 
        
        for idx, year in enumerate(years):
            fig_share.add_trace(go.Bar(
                x=df_share['Country'],
                y=df_share[year],
                name=str(year),
                marker_color=colors_years[idx % len(colors_years)],
                text=df_share[year].apply(lambda x: f"{x:.1f}%" if pd.notnull(x) and (idx == 0 or idx == len(years)-1) else ""),
                textposition='outside'
            ))
            
        fig_share.update_layout(
            barmode='group', plot_bgcolor='white', height=400, margin=dict(t=20),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_share, use_container_width=True)
        
        st.markdown("---")
        st.markdown("### * 미국 의류 수입 국가별 전년 동월대비 증감률(%)")
        
        df_yoy = pd.read_csv('otexa_yoy.csv')
        df_yoy = df_yoy.set_index('Country')
        
        def style_country_bg(row):
            color_map = {
                'World': 'background-color: #808080; color: white; font-weight: bold;',
                'China': 'background-color: #ed7d31; color: white; font-weight: bold;',
                'Vietnam': 'background-color: #a9d18e; color: black; font-weight: bold;',
                'Indonesia': 'background-color: #5b9bd5; color: white; font-weight: bold;',
                'Cambodia': 'background-color: #1f497d; color: white; font-weight: bold;',
                'Nicaragua': 'background-color: #ff0000; color: white; font-weight: bold;',
                'Guatemala': 'background-color: #00b050; color: white; font-weight: bold;'
            }
            bg = color_map.get(row.name, '')
            return [bg] * len(row)

        styled_yoy = df_yoy.style.format("{:.1f}%", na_rep="-").apply(style_country_bg, axis=1)
        st.dataframe(styled_yoy, use_container_width=True)
        
    except Exception as e:
        st.error(f"OTEXA 데이터를 불러올 수 없습니다. 오류 내용: {e}")

# ==========================================
# [Tab 3] 글로벌 패션·유통 기업 모니터링 (QoQ 실적 고정 + 국적별 뉴스 타겟 수집)
# ==========================================
with tab3:
    st.subheader("🏢 요청 기업 실시간 주가 및 정보 모니터링")
    
    # 💡 10분 캐싱 함수 (QoQ 고정 및 국내/해외 뉴스 타겟 수집 시스템)
    @st.cache_data(ttl=600)
    def get_complete_company_data(ticker_symbol, selected_company, search_keyword):
        ticker = yf.Ticker(ticker_symbol)
        
        # 1. 1년치 주가 데이터 가져오기
        try:
            hist = ticker.history(period="1y")
        except Exception:
            hist = pd.DataFrame()
            
        # 2. 분기 실적 데이터 (💡 요청사항: 전분기 대비 QoQ로 100% 고정)
        financials_df = pd.DataFrame()
        try:
            q_fin = ticker.quarterly_financials
            if q_fin is not None and not q_fin.empty:
                revenue_idx = [idx for idx in q_fin.index if 'Total Revenue' in idx or 'Revenue' in idx]
                op_inc_idx = [idx for idx in q_fin.index if 'Operating Income' in idx]
                
                rows_to_extract = []
                row_labels = []
                if revenue_idx:
                    rows_to_extract.append(revenue_idx[0])
                    row_labels.append('매출액')
                if op_inc_idx:
                    rows_to_extract.append(op_inc_idx[0])
                    row_labels.append('영업이익')
                    
                if rows_to_extract:
                    raw_fin = q_fin.loc[rows_to_extract].copy()
                    raw_fin.index = row_labels
                    raw_fin = raw_fin.reindex(columns=sorted(raw_fin.columns))
                    
                    # 💡 periods=1 로 설정하여 무조건 직전 분기 대비(QoQ) 증감률을 계산해 4개 분기를 다 채웁니다.
                    growth_df = raw_fin.pct_change(periods=1, axis=1) * 100
                    financials_df = growth_df.iloc[:, -4:]
        except Exception:
            pass
            
        # 3. 기업 기본 정보 및 국적 파악
        info_dict = {}
        try:
            info_dict = ticker.info
        except Exception:
            pass
            
        is_korean = ".KS" in ticker_symbol or ".KQ" in ticker_symbol
        if is_korean:
            info_dict['currency'] = "KRW"
        elif ".T" in ticker_symbol:
            info_dict['currency'] = "JPY"
        else:
            info_dict['currency'] = "USD"
                
        # 4. 뉴스 데이터 가져오기 및 [초정밀 필터링 / 번역]
        from deep_translator import GoogleTranslator
        raw_news = []
        try:
            raw_news = ticker.news
        except Exception:
            pass
            
        translated_news = []
        valid_news_count = 0
        
        keyword_lower = search_keyword.lower()
        ticker_core = ticker_symbol.split('.')[0].lower()
        
        # 야후 뉴스 매칭 시도
        if raw_news:
            for item in raw_news:
                title = item.get('title', '')
                link = item.get('link', '')
                publisher = item.get('publisher', 'Unknown Source')
                
                if title and link:
                    t_lower = title.lower()
                    if keyword_lower in t_lower or ticker_core in t_lower:
                        try:
                            # 💡 한국 회사 기사면 번역하지 않고 그대로 노출, 외국 기사면 한글 번역
                            if is_korean:
                                display_title = f"[{publisher}] {title}"
                            else:
                                ko_title = GoogleTranslator(source='auto', target='ko').translate(title)
                                display_title = f"[{publisher}] {ko_title}"
                        except Exception:
                            display_title = f"[{publisher}] {title}"
                        translated_news.append({"title": display_title, "orig_title": title, "link": link})
                        valid_news_count += 1
                        
                if valid_news_count >= 5:
                    break

        # 통과된 뉴스가 부족하면 구글 뉴스 RSS 백업 시스템 가동 (★한국 포털 뉴스 크롤링 효과)
        if valid_news_count < 5:
            try:
                import xml.etree.ElementTree as ET
                import urllib.request
                import urllib.parse
                
                # 💡 [핵심 해결책] 한국 회사는 국내 미디어 전용 망(hl=ko&gl=KR)을 설정해 네이버 등에 연동된 국내 뉴스를 전부 긁어옵니다.
                if is_korean:
                    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(search_keyword)}&hl=ko&gl=KR&ceid=KR:ko"
                else:
                    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(search_keyword)}&hl=en-US&gl=US&ceid=US:en"
                    
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                xml_data = urllib.request.urlopen(req).read()
                
                root = ET.fromstring(xml_data)
                for item in root.findall('.//item'):
                    g_title = item.find('title').text if item.find('title') is not None else ''
                    g_link = item.find('link').text if item.find('link') is not None else ''
                    g_pub = item.find('source').text if item.find('source') is not None else 'Google News'
                    
                    if g_title and g_link:
                        t_lower = g_title.lower()
                        if keyword_lower in t_lower or ticker_core in t_lower:
                            try:
                                if is_korean:
                                    display_title = f"[{g_pub}] {g_title}"
                                else:
                                    ko_g_title = GoogleTranslator(source='auto', target='ko').translate(g_title)
                                    display_title = f"[{g_pub}] {ko_g_title}"
                            except Exception:
                                display_title = f"[{g_pub}] {g_title}"
                            
                            # 중복 링크 방지 체크 후 삽입
                            if not any(n['link'] == g_link for n in translated_news):
                                translated_news.append({"title": display_title, "orig_title": g_title, "link": g_link})
                                valid_news_count += 1
                            
                    if valid_news_count >= 5:
                        break
            except Exception:
                pass
                
        return info_dict, hist, financials_df, translated_news

    # 대상 기업 리스트
    companies = {
        "Walmart (월마트)": ("WMT", "Walmart"), 
        "Target (타겟)": ("TGT", "Target"), 
        "Kohl's (콜스)": ("KSS", "Kohl's"),
        "Victoria's Secret (빅토리아 시크릿)": ("VSCO", "Victoria's Secret"), 
        "Abercrombie & Fitch (아베크롬비)": ("ANF", "Abercrombie"),
        "Carter's (카터스)": ("CRI", "Carter's"), 
        "Fast Retailing (유니클로 모기업)": ("9983.T", "Fast Retailing"),
        "Under Armour (언더아머)": ("UA", "Under Armour"), 
        "Amazon (아마존)": ("AMZN", "Amazon"), 
        "Alibaba (알리바바)": ("BABA", "Alibaba"),
        "한세실업": ("105630.KS", "한세실업"), 
        "영원무역": ("111770.KS", "영원무역"), 
        "노브랜드": ("145170.KQ", "노브랜드"), 
        "TP inc. (태평양물산)": ("007980.KS", "태평양물산"), 
        "Shinwon (신원)": ("009270.KS", "신원"), 
        "제이에스코퍼레이션": ("194370.KS", "제이에스코퍼레이션")
    }
    
    selected_company = st.selectbox("분석할 기업을 선택하세요", list(companies.keys()))
    ticker_symbol, search_keyword = companies[selected_company]
    
    try:
        # 정보 호출
        info, hist, financials_df, final_news = get_complete_company_data(ticker_symbol, selected_company, search_keyword)
        
        # 1. 현재 주가 및 화폐 단위 셋팅
        current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
        if current_price == 0 and not hist.empty:
            current_price = hist['Close'].iloc[-1]
            
        currency = info.get('currency', 'USD')
        
        if currency == "KRW":
            currency_symbol = "₩"
            price_formatted = f"{currency_symbol} {int(current_price):,}"
        elif currency == "JPY":
            currency_symbol = "¥"
            price_formatted = f"{currency_symbol} {int(current_price):,}"
        else:
            currency_symbol = "$"
            price_formatted = f"{currency_symbol} {current_price:,.2f}"
            
        # 최근 한 달의 월별 평균 주가 전월 대비 증감률(MoM)
        mom_growth = 0.0
        if not hist.empty:
            hist_df = hist.reset_index()
            hist_df['YearMonth'] = hist_df['Date'].dt.to_period('M')
            monthly_avg = hist_df.groupby('YearMonth')['Close'].mean().reset_index()
            if len(monthly_avg) >= 2:
                latest_avg = monthly_avg['Close'].iloc[-1]
                prev_avg = monthly_avg['Close'].iloc[-2]
                mom_growth = ((latest_avg / prev_avg) - 1) * 100

        delta_formatted = f"{mom_growth:+.2f}% (최근 월간 평균 주가 전월대비 MoM)"
        st.metric(label="현재 주가", value=price_formatted, delta=delta_formatted)
        
        # 2. 1년치 주가추세 차트
        st.markdown("### 📈 최근 1년 주가 추세")
        if not hist.empty:
            fig_trend = go.Figure(go.Scatter(
                x=hist.index, y=hist['Close'],
                mode='lines', line=dict(color='#0070C0', width=2),
                name='종가'
            ))
            fig_trend.update_layout(
                plot_bgcolor='white',
                width=850, height=350,
                margin=dict(l=50, r=40, t=20, b=30),
                xaxis=dict(showgrid=True, gridcolor='lightgray'),
                yaxis=dict(showgrid=True, gridcolor='lightgray', tickformat="," if currency != "USD" else ",.2f")
            )
            st.plotly_chart(fig_trend, use_container_width=False)
        else:
            st.info("주가 차트 데이터를 불러올 수 없습니다.")
            
        # 3. 최근 4개분기 매출액 & 영업이익 증감률 차트 (QoQ 완벽 고정)
        if not financials_df.empty:
            st.markdown("### 📊 최근 4개 분기 실적 증감률")
            st.caption("※ 전분기 대비 (QoQ, %)")
                
            quarters = [str(col).split(' ')[0] for col in financials_df.columns]
            
            fig_fin = go.Figure()
            
            if '매출액' in financials_df.index:
                fig_fin.add_trace(go.Bar(
                    x=quarters, y=financials_df.loc['매출액'],
                    name='매출 증감률', marker_color='#1f497d',
                    text=financials_df.loc['매출액'].apply(lambda x: f"{x:+.1f}%" if pd.notnull(x) else "-"),
                    textposition='outside'
                ))
            if '영업이익' in financials_df.index:
                fig_fin.add_trace(go.Bar(
                    x=quarters, y=financials_df.loc['영업이익'],
                    name='영업이익 증감률', marker_color='#ed7d31',
                    text=financials_df.loc['영업이익'].apply(lambda x: f"{x:+.1f}%" if pd.notnull(x) else "-"),
                    textposition='outside'
                ))
                
            fig_fin.update_layout(
                barmode='group', plot_bgcolor='white',
                width=850, height=350,
                margin=dict(l=50, r=40, t=30, b=30),
                xaxis=dict(type='category'),
                yaxis=dict(showgrid=True, gridcolor='lightgray', title="증감률 (%)"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_fin, use_container_width=False)
        else:
            st.info("최근 분기 실적 데이터를 공급하지 않거나 야후 금융 API 과부하로 차트가 일시 제한되었습니다.")
            
        # 4. 최신 뉴스 리스트 (국내/해외 맞춤형)
        st.markdown("---")
        st.markdown(f"### 📰 {selected_company} 관련 최신 뉴스")
        
        if final_news:
            for item in final_news:
                with st.expander(item['title']):
                    st.write(f"**원본 제목:** {item['orig_title']}")
                    st.write(f"[기사 원문 링크]({item['link']})")
        else:
            st.info("현재 해당 기업의 이름이 직접 언급된 최신 뉴스 기사를 찾을 수 없습니다.")
            
    except Exception as e:
        st.error(f"데이터를 처리하는 중 일시적인 오류가 발생했습니다: {e}")

# ==========================================
# [Tab 4] 🌐 거시경제 및 원가 지표 (공식 FRED API 적용 - 절대 안 막힘!)
# ==========================================
with tab4:
    st.subheader("🌐 글로벌 거시경제 및 패션 원가 지표 모니터링")
    st.caption("환율, 원자재, 미국 거시경제(GDP, CPI 등) 지표를 실시간으로 가져옵니다.")
    
    # 💡 1시간 단위 캐싱
    @st.cache_data(ttl=3600)
    def get_macro_data():
        import pandas as pd
        import datetime
        import requests
        
        # 1. 야후 파이낸스 데이터
        yf_tickers = {
            "원/달러 환율": "KRW=X",
            "글로벌 면화(Cotton)": "CT=F",
            "WTI 국제 유가": "CL=F"
        }
        yf_data = {}
        for name, ticker in yf_tickers.items():
            try:
                hist = yf.Ticker(ticker).history(period="1y")
                yf_data[name] = hist['Close']
            except Exception:
                yf_data[name] = pd.Series()
                
        # 2. 미국 FRED 데이터 (💡 정식 API Key를 사용하여 100% 안정적으로 가져옵니다!)
        FRED_API_KEY = "7cbd5f701c3b7e514e3dfcb6810d2fb7"
        
        fred_tickers = {
            "미국 실질 GDP": "GDPC1",                 
            "미국 의류 소비자물가지수(CPI)": "CPIAPPSL",  
            "미국 소매업 재고율 (Inventory-to-Sales)": "RETAILIRSA" 
        }
        fred_data = {}
        start_date = pd.Timestamp.today() - pd.DateOffset(years=5)
        
        for name, ticker in fred_tickers.items():
            try:
                # FRED의 공식 API 정문을 통해 데이터를 JSON 형태로 요청합니다.
                url = f"https://api.stlouisfed.org/fred/series/observations?series_id={ticker}&api_key={FRED_API_KEY}&file_type=json"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                # JSON 데이터 파싱
                data = response.json()['observations']
                df = pd.DataFrame(data)
                
                # 날짜와 수치 데이터로 변환 (결측치 '.' 는 안전하게 무시)
                df['date'] = pd.to_datetime(df['date'])
                df['value'] = pd.to_numeric(df['value'], errors='coerce')
                
                # 인덱스 설정 및 최근 5년치 필터링
                df = df.set_index('date')
                df = df[df.index >= start_date]
                fred_data[name] = df['value'].dropna()
                
            except Exception as e:
                fred_data[name] = pd.Series()
                
        return yf_data, fred_data

    try:
        yf_data, fred_data = get_macro_data()
        
        # --- 1층: 환율 ---
        st.markdown("### 💱 원/달러 환율 동향 (최근 1년)")
        if not yf_data["원/달러 환율"].empty:
            current_krw = yf_data["원/달러 환율"].iloc[-1]
            fig_krw = go.Figure(go.Scatter(
                x=yf_data["원/달러 환율"].index, y=yf_data["원/달러 환율"], 
                mode='lines', line=dict(color='#2E86C1', width=2)
            ))
            fig_krw.update_layout(
                title=f"원/달러 환율 (현재: {current_krw:,.2f}원)", 
                width=850, height=300,
                margin=dict(l=30, r=30, t=40, b=30), 
                plot_bgcolor='white', 
                xaxis=dict(showgrid=True, gridcolor='lightgray'), 
                yaxis=dict(showgrid=True, gridcolor='lightgray')
            )
            st.plotly_chart(fig_krw, use_container_width=False)
        else:
            st.info("현재 환율 데이터를 불러올 수 없습니다.")

        st.markdown("---")
        
        # --- 2층: 원자재 ---
        st.markdown("### 🛢️ 핵심 원자재 가격 동향 (최근 1년)")
        col3, col4 = st.columns(2)
        
        with col3:
            if not yf_data["글로벌 면화(Cotton)"].empty:
                current_cotton = yf_data["글로벌 면화(Cotton)"].iloc[-1]
                fig_ct = go.Figure(go.Scatter(x=yf_data["글로벌 면화(Cotton)"].index, y=yf_data["글로벌 면화(Cotton)"], mode='lines', line=dict(color='#F1C40F', width=2)))
                fig_ct.update_layout(title=f"국제 면화 선물 (현재: ${current_cotton:,.2f})", width=400, height=300, margin=dict(l=30, r=30, t=40, b=30), plot_bgcolor='white', xaxis=dict(showgrid=True, gridcolor='lightgray'), yaxis=dict(showgrid=True, gridcolor='lightgray'))
                st.plotly_chart(fig_ct, use_container_width=True)
            else:
                st.info("면화 데이터를 불러올 수 없습니다.")
                
        with col4:
            if not yf_data["WTI 국제 유가"].empty:
                current_wti = yf_data["WTI 국제 유가"].iloc[-1]
                fig_wti = go.Figure(go.Scatter(x=yf_data["WTI 국제 유가"].index, y=yf_data["WTI 국제 유가"], mode='lines', line=dict(color='#34495E', width=2)))
                fig_wti.update_layout(title=f"WTI 국제 유가 (현재: ${current_wti:,.2f})", width=400, height=300, margin=dict(l=30, r=30, t=40, b=30), plot_bgcolor='white', xaxis=dict(showgrid=True, gridcolor='lightgray'), yaxis=dict(showgrid=True, gridcolor='lightgray'))
                st.plotly_chart(fig_wti, use_container_width=True)
            else:
                st.info("유가 데이터를 불러올 수 없습니다.")

        st.markdown("---")
        
        # --- 3층: 거시경제 ---
        st.markdown("### 🦅 미국 거시경제 및 소비 지표 (최근 5년 트렌드)")
        st.caption("※ 데이터 출처: 미국 연방준비은행 (FRED) 공식 API 연동 완료")
        
        col5, col6 = st.columns(2)
        
        with col5:
            if not fred_data["미국 실질 GDP"].empty:
                fig_gdp = go.Figure(go.Scatter(x=fred_data["미국 실질 GDP"].index, y=fred_data["미국 실질 GDP"], mode='lines+markers', line=dict(color='#8E44AD', width=2)))
                fig_gdp.update_layout(title="미국 실질 GDP (분기별)", width=400, height=300, margin=dict(l=30, r=30, t=40, b=30), plot_bgcolor='white', xaxis=dict(showgrid=True, gridcolor='lightgray'), yaxis=dict(showgrid=True, gridcolor='lightgray'))
                st.plotly_chart(fig_gdp, use_container_width=True)
            else:
                st.info("GDP 데이터를 불러오지 못했습니다. API 키를 다시 확인해 주세요.")
                
        with col6:
            if not fred_data["미국 의류 소비자물가지수(CPI)"].empty:
                fig_cpi = go.Figure(go.Scatter(x=fred_data["미국 의류 소비자물가지수(CPI)"].index, y=fred_data["미국 의류 소비자물가지수(CPI)"], mode='lines', line=dict(color='#D35400', width=2)))
                fig_cpi.update_layout(title="미국 의류 CPI (인플레이션)", width=400, height=300, margin=dict(l=30, r=30, t=40, b=30), plot_bgcolor='white', xaxis=dict(showgrid=True, gridcolor='lightgray'), yaxis=dict(showgrid=True, gridcolor='lightgray'))
                st.plotly_chart(fig_cpi, use_container_width=True)
            else:
                st.info("CPI 데이터를 불러오지 못했습니다. API 키를 다시 확인해 주세요.")

        if not fred_data["미국 소매업 재고율 (Inventory-to-Sales)"].empty:
            fig_inv = go.Figure(go.Scatter(x=fred_data["미국 소매업 재고율 (Inventory-to-Sales)"].index, y=fred_data["미국 소매업 재고율 (Inventory-to-Sales)"], mode='lines', fill='tozeroy', line=dict(color='#16A085', width=2)))
            fig_inv.update_layout(title="미국 소매업 재고율 (높을수록 창고에 재고가 많음을 의미)", width=850, height=300, margin=dict(l=30, r=30, t=40, b=30), plot_bgcolor='white', xaxis=dict(showgrid=True, gridcolor='lightgray'), yaxis=dict(showgrid=True, gridcolor='lightgray', tickformat=".2f"))
            st.plotly_chart(fig_inv, use_container_width=False)
        else:
            st.info("소매업 재고율 데이터를 불러오지 못했습니다. API 키를 다시 확인해 주세요.")

    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")