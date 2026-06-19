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
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 FRED 소매 판매", "🚢 OTEXA 수입 데이터", "🏢 기업 모니터링", "🌐 거시경제 및 원가", "🛡️ 바이어 신용등급"])

# ==========================================
# [Tab 1] 미국 소매 판매 현황 (Offline 맨 아래로 정렬 🚀)
# ==========================================
with tab1:
    @st.cache_data(ttl=3600)
    def get_fred_retail_sales_v4():
        import requests
        import time
        import pandas as pd
        
        series_map = {
            "Total Retail Trade": "RSAFS",
            "Nonstore Retailers": "RSNSR",
            "Motor Vehicle and Parts Dealers": "RSMVPD",
            "Furniture and Home Furnishings Stores": "RSFHFS",
            "Electronics and Appliance Stores": "RSECAFS",
            "Building Material and Garden Equipment and Supplies Dealers": "RSBMGESD",
            "Food and Beverage Stores": "RSFDS",
            "Health and Personal Care Stores": "RSHPCS",
            "Gasoline Stations": "RSGASS",
            "Clothing and Clothing Accessories Stores": "RSCCAS",
            "Sporting Goods, Hobby, Musical Instrument, and Book Stores": "RSSGHBKS",
            "General Merchandise Stores": "RSGMS",
            "Miscellaneous Store Retailers": "RSMSR"
        }
        
        FRED_API_KEY = "7cbd5f701c3b7e514e3dfcb6810d2fb7"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        all_data = []
        
        for cat, ticker in series_map.items():
            for attempt in range(3):
                try:
                    url = f"https://api.stlouisfed.org/fred/series/observations?series_id={ticker}&api_key={FRED_API_KEY}&file_type=json"
                    response = requests.get(url, headers=headers, timeout=30)
                    if response.status_code == 200:
                        obs = response.json()['observations']
                        temp_df = pd.DataFrame(obs)
                        temp_df['Date'] = pd.to_datetime(temp_df['date'])
                        temp_df['Sales'] = pd.to_numeric(temp_df['value'], errors='coerce')
                        temp_df['Category'] = cat
                        temp_df = temp_df[['Date', 'Category', 'Sales']].dropna()
                        all_data.append(temp_df)
                        time.sleep(0.2) 
                        break 
                    else:
                        time.sleep(2)
                except Exception:
                    if attempt < 2:
                        time.sleep(2)
                        
        if not all_data:
            return pd.DataFrame()
            
        df = pd.concat(all_data, ignore_index=True)
        
        df_pivot = df.pivot(index='Date', columns='Category', values='Sales')
        if 'Total Retail Trade' in df_pivot.columns and 'Nonstore Retailers' in df_pivot.columns:
            df_pivot['Offline'] = df_pivot['Total Retail Trade'] - df_pivot['Nonstore Retailers']
        
        df_final = df_pivot.reset_index().melt(id_vars='Date', var_name='Category', value_name='Sales').dropna()
        return df_final

    try:
        df = get_fred_retail_sales_v4()
        
        if df.empty:
            st.error("FRED 서버에서 데이터를 가져오지 못했습니다.")
        else:
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
            
            # 💡 Offline을 리스트의 맨 마지막 순서로 배치했습니다!
            exact_14_order = [
                "Total Retail Trade", 
                "Nonstore Retailers",
                "Sporting Goods, Hobby, Musical Instrument, and Book Stores",
                "General Merchandise Stores",
                "Furniture and Home Furnishings Stores", 
                "Electronics and Appliance Stores",
                "Clothing and Clothing Accessories Stores", 
                "Motor Vehicle and Parts Dealers",
                "Building Material and Garden Equipment and Supplies Dealers",
                "Food and Beverage Stores", 
                "Health and Personal Care Stores",
                "Gasoline Stations", 
                "Miscellaneous Store Retailers",
                "Offline"  # 👈 맨 마지막으로 이동
            ]
            
            ytd_growth = ytd_growth.reindex(exact_14_order).fillna(0).reset_index()
            ytd_growth.columns = ['Category', 'Growth']
            
            ytd_growth['Category'] = pd.Categorical(ytd_growth['Category'], categories=exact_14_order, ordered=True)
            # Plotly 수평 바 차트는 밑에서부터 쌓이기 때문에 역순 정렬을 해줍니다.
            ytd_growth = ytd_growth.sort_values('Category', ascending=False)
            
            colors = ['#CC0000' if val < 0 else '#0070C0' for val in ytd_growth['Growth']]
            
            import plotly.graph_objects as go
            fig = go.Figure(go.Bar(
                x=ytd_growth['Growth'],
                y=ytd_growth['Category'],
                orientation='h',
                text=ytd_growth['Growth'].apply(lambda x: f"{x:.1f}%" if x != 0 else "데이터 지연"),
                textposition='outside',
                marker_color=colors,
                marker_line_width=0 
            ))

            target_cat = "Clothing and Clothing Accessories Stores"
            cat_list = ytd_growth['Category'].tolist()
            
            if target_cat in cat_list:
                target_idx = cat_list.index(target_cat)
                fig.add_shape(
                    type="rect", xref="paper", x0=-0.25, x1=1.05, yref="y",
                    y0=target_idx - 0.4, y1=target_idx + 0.4,
                    line=dict(color="Red", width=2),
                    fillcolor="rgba(255, 0, 0, 0.05)", layer="below"
                )

            fig.update_layout(
                plot_bgcolor='white', height=600, 
                margin=dict(l=350, r=50, t=30, b=0), 
                xaxis=dict(showgrid=True, gridcolor='lightgray'),
                # 차트 축도 설정한 순서대로 완벽히 정렬되도록 고정
                yaxis=dict(categoryorder='array', categoryarray=exact_14_order[::-1], automargin=True)
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")
            st.subheader("📋 미국 소매 카테고리 별 전년 동월대비 증감률(%)")
            
            df_pivot_table = df.pivot(index='Date', columns='Category', values='Sales')
            yoy_df = df_pivot_table.pct_change(periods=12) * 100
            table_df = yoy_df.tail(12).T
            
            # 아래 표 데이터도 Offline이 맨 마지막 줄에 오도록 고정
            table_df = table_df.reindex(exact_14_order)
            
            formatted_cols = [f"'{str(d.year)[-2:]} / {d.month}" for d in table_df.columns]
            table_df.columns = formatted_cols
            
            def highlight_clothing(row):
                if 'Clothing' in str(row.name):
                    return ['background-color: #ffe6e6; border-top: 2px solid red; border-bottom: 2px solid red'] * len(row)
                return [''] * len(row)

            styled_table = table_df.style.apply(highlight_clothing, axis=1).format("{:.1f}%", na_rep="-")
            
            # 💡 아래 코드를 그대로 복사해서 넣어주세요
            st.dataframe(
                styled_table, 
                use_container_width=True, 
                height=len(table_df) * 35 + 50
            )

    except Exception as e:
        st.error(f"소매 판매 데이터를 처리하는 중 오류가 발생했습니다: {e}")

# ==========================================
# [Tab 2] 미국 의류 수입 현황 (OTEXA) - 안정성 강화
# ==========================================
with tab2:
    st.markdown("### * 미국 의류 수입 국가별 비중 (%)")
    st.caption("※ OTEXA 데이터 (웹 수집 방해를 피해 안정적인 CSV 연동 유지)")
    
    # 💡 OTEXA는 서버 방화벽이 매우 강력하므로, 기존 CSV 파일을 읽되 에러 처리를 강화했습니다.
    @st.cache_data(ttl=3600)
    def load_otexa_data():
        import pandas as pd
        import os
        
        # 만약 웹상에 고정된 CSV 링크가 있다면 아래 주석을 풀고 링크를 넣으세요!
        # url_share = "https://example.com/otexa_share.csv" 
        # return pd.read_csv(url_share), pd.read_csv(url_yoy)
        
        if os.path.exists('otexa_share.csv') and os.path.exists('otexa_yoy.csv'):
            return pd.read_csv('otexa_share.csv'), pd.read_csv('otexa_yoy.csv')
        else:
            raise FileNotFoundError("로컬에 otexa_share.csv 또는 otexa_yoy.csv 파일이 없습니다.")

    try:
        df_share, df_yoy = load_otexa_data()
        
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

        # 1. 스타일 입힌 데이터프레임 생성
        styled_yoy = df_yoy.style.format("{:.1f}%", na_rep="-").apply(style_country_bg, axis=1)

        # 2. 높이 자동 계산 (df_yoy 행 개수 기준)
        total_rows_tab2 = len(df_yoy) 
        row_height = 35 
        header_height = 50 
        calculated_height_tab2 = (total_rows_tab2 * row_height) + header_height
        
        # 3. 스크롤 없는 표 출력
        st.dataframe(
            styled_yoy, 
            use_container_width=True, 
            height=calculated_height_tab2 
        )

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
# [Tab 4] 🌐 거시경제 및 원가 지표 (레이아웃 밸런스 및 깔끔화 완벽판 🚀)
# ==========================================

# 1. 데이터 수집 함수 (미국 의류 소매판매액 RSCCASN 추가)
@st.cache_data(ttl=3600)
def get_macro_data_complete_final():
    import pandas as pd
    import requests
    import yfinance as yf
    
    FRED_API_KEY = "7cbd5f701c3b7e514e3dfcb6810d2fb7"
    headers = {'User-Agent': 'Mozilla/5.0'}
    start_date = pd.Timestamp.today() - pd.DateOffset(years=5)
    
    # [A] 야후 파이낸스 데이터 (최근 1년)
    yf_tickers = {"원/달러 환율": "KRW=X", "글로벌 면화(Cotton)": "CT=F", "WTI 국제 유가": "CL=F"}
    yf_data = {}
    for name, ticker in yf_tickers.items():
        try:
            yf_data[name] = yf.Ticker(ticker).history(period="1y")['Close']
        except:
            yf_data[name] = pd.Series()
            
    # [B] FRED 데이터 (의류 소매 판매액 추가)
    fred_tickers = {
        "미국 실질 GDP": "GDPC1",                 
        "미국 의류 소비자물가지수(CPI)": "CPIAPPSL",  
        "미국 소매업 재고율": "RETAILIRSA",
        "미국 기준금리": "FEDFUNDS",
        "한국 기준금리": "KORINTPA01STSAM",
        "미국 의류 소매판매액": "RSCCASN" # 👈 균형을 맞출 패션 핵심 지표!
    }
    fred_data = {}
    for name, ticker in fred_tickers.items():
        try:
            url = f"https://api.stlouisfed.org/fred/series/observations?series_id={ticker}&api_key={FRED_API_KEY}&file_type=json"
            res = requests.get(url, headers=headers, timeout=30)
            df = pd.DataFrame(res.json()['observations'])
            df['date'] = pd.to_datetime(df['date'])
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            df = df.set_index('date')['value'].dropna()
            fred_data[name] = df[df.index >= start_date]
        except:
            fred_data[name] = pd.Series()

    # [C] 한국 기준금리 백업
    if fred_data["한국 기준금리"].empty:
        dates = pd.date_range(start=start_date, end=pd.Timestamp.today(), freq='ME')
        kr_rate = pd.Series(3.50, index=dates)
        kr_history = {
            '2021-01-01': 0.50, '2021-08-26': 0.75, '2021-11-25': 1.00,
            '2022-01-14': 1.25, '2022-04-14': 1.50, '2022-05-26': 1.75, 
            '2022-07-13': 2.25, '2022-08-25': 2.50, '2022-10-12': 3.00, 
            '2022-11-24': 3.25, '2023-01-13': 3.50
        }
        for d_str, val in kr_history.items():
            kr_rate[kr_rate.index >= pd.Timestamp(d_str)] = val
        fred_data["한국 기준금리"] = kr_rate

    return yf_data, fred_data


# 2. 대시보드 레이아웃 시각화 구역
with tab4:
    st.subheader("🌐 글로벌 거시경제 및 패션 원가 지표 모니터링")
    st.caption("환율, 금리, 원자재 및 미국 거시경제 지표를 실시간으로 가져옵니다.")
    
    try:
        import plotly.graph_objects as go
        yf_data, fred_data = get_macro_data_complete_final()
        
        # ----------------------------------------
        # --- 1층: 💱 환율 및 🏦 한·미 기준금리 ---
        # ----------------------------------------
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 💱 원/달러 환율 (최근 1년)")
            if not yf_data["원/달러 환율"].empty:
                s = yf_data["원/달러 환율"]
                f_val, l_val = s.iloc[0], s.iloc[-1]
                chg = ((l_val - f_val) / f_val) * 100
                st.write(f"🔹 시작: {f_val:,.1f}원 ➔ 최신: {l_val:,.1f}원 (증감률: **{chg:+.1f}%**)")
                
                fig_krw = go.Figure(go.Scatter(x=s.index, y=s, line=dict(color='#2E86C1', width=2)))
                fig_krw.add_trace(go.Scatter(x=[s.index[0], s.index[-1]], y=[f_val, l_val], mode='markers+text', text=[f"{f_val:,.1f}", f"{l_val:,.1f}"], textposition=["top right", "top left"], marker=dict(size=8, color='#2E86C1')))
                fig_krw.update_layout(height=280, margin=dict(l=20, r=20, t=10, b=10), plot_bgcolor='white', showlegend=False, xaxis=dict(showgrid=True, gridcolor='lightgray'), yaxis=dict(showgrid=True, gridcolor='lightgray'))
                st.plotly_chart(fig_krw, use_container_width=True)
            
        with col2:
            st.markdown("#### 🏦 한·미 기준금리 추이 (최근 5년)")
            us_s, kr_s = fred_data["미국 기준금리"], fred_data["한국 기준금리"]
            if not us_s.empty and not kr_s.empty:
                f_us, l_us = us_s.iloc[0], us_s.iloc[-1]
                f_kr, l_kr = kr_s.iloc[0], kr_s.iloc[-1]
                st.write(f"🇺🇸 미국: {f_us:.2f}% ➔ {l_us:.2f}% ({l_us-f_us:+.2f}%p) | 🇰🇷 한국: {f_kr:.2f}% ➔ {l_kr:.2f}% ({l_kr-f_kr:+.2f}%p)")
                
                fig_rate = go.Figure()
                fig_rate.add_trace(go.Scatter(x=us_s.index, y=us_s, name='미국 (Fed)', line=dict(color='#d62728', width=2.5)))
                fig_rate.add_trace(go.Scatter(x=kr_s.index, y=kr_s, name='한국 (BOK)', line=dict(color='#1f77b4', width=2.5)))
                fig_rate.add_trace(go.Scatter(x=[us_s.index[0], us_s.index[-1]], y=[f_us, l_us], mode='markers+text', text=[f"{f_us:.1f}%", f"{l_us:.1f}%"], textposition="top center", marker=dict(size=6, color='#d62728'), showlegend=False))
                fig_rate.add_trace(go.Scatter(x=[kr_s.index[0], kr_s.index[-1]], y=[f_kr, l_kr], mode='markers+text', text=[f"{f_kr:.1f}%", f"{l_kr:.1f}%"], textposition="bottom center", marker=dict(size=6, color='#1f77b4'), showlegend=False))
                fig_rate.update_layout(height=280, margin=dict(l=20, r=20, t=10, b=10), plot_bgcolor='white', showlegend=True, legend=dict(orientation="h", y=1.15), xaxis=dict(showgrid=True, gridcolor='lightgray'), yaxis=dict(showgrid=True, gridcolor='lightgray'))
                st.plotly_chart(fig_rate, use_container_width=True)

        st.markdown("---")
        
        # ----------------------------------------
        # --- 2층: 🛢️ 핵심 원자재 가격 동향 ---
        # ----------------------------------------
        st.markdown("### 🛢️ 핵심 원자재 가격 동향 (최근 1년)")
        col3, col4 = st.columns(2)
        
        with col3:
            st.markdown("#### 🌱 국제 면화 선물 가격")
            if not yf_data["글로벌 면화(Cotton)"].empty:
                s = yf_data["글로벌 면화(Cotton)"]
                f_val, l_val = s.iloc[0], s.iloc[-1]
                chg = ((l_val - f_val) / f_val) * 100
                st.write(f"🔹 시작: ${f_val:,.1f} ➔ 최신: ${l_val:,.1f} (증감률: **{chg:+.1f}%**)")
                
                fig_ct = go.Figure(go.Scatter(x=s.index, y=s, line=dict(color='#F1C40F', width=2)))
                fig_ct.add_trace(go.Scatter(x=[s.index[0], s.index[-1]], y=[f_val, l_val], mode='markers+text', text=[f"${f_val:,.1f}", f"${l_val:,.1f}"], textposition=["top right", "top left"], marker=dict(size=8, color='#F1C40F')))
                fig_ct.update_layout(height=280, margin=dict(l=20, r=20, t=10, b=10), plot_bgcolor='white', showlegend=False, xaxis=dict(showgrid=True, gridcolor='lightgray'), yaxis=dict(showgrid=True, gridcolor='lightgray'))
                st.plotly_chart(fig_ct, use_container_width=True)
                
        with col4:
            st.markdown("#### ⚓ WTI 국제 유가")
            if not yf_data["WTI 국제 유가"].empty:
                s = yf_data["WTI 국제 유가"]
                f_val, l_val = s.iloc[0], s.iloc[-1]
                chg = ((l_val - f_val) / f_val) * 100
                st.write(f"🔹 시작: ${f_val:,.1f} ➔ 최신: ${l_val:,.1f} (증감률: **{chg:+.1f}%**)")
                
                fig_wti = go.Figure(go.Scatter(x=s.index, y=s, line=dict(color='#34495E', width=2)))
                fig_wti.add_trace(go.Scatter(x=[s.index[0], s.index[-1]], y=[f_val, l_val], mode='markers+text', text=[f"${f_val:,.1f}", f"${l_val:,.1f}"], textposition=["top right", "top left"], marker=dict(size=8, color='#34495E')))
                fig_wti.update_layout(height=280, margin=dict(l=20, r=20, t=10, b=10), plot_bgcolor='white', showlegend=False, xaxis=dict(showgrid=True, gridcolor='lightgray'), yaxis=dict(showgrid=True, gridcolor='lightgray'))
                st.plotly_chart(fig_wti, use_container_width=True)

        st.markdown("---")
        
        # ----------------------------------------
        # --- 3층: 🦅 미국 거시경제 경기 지표 ---
        # ----------------------------------------
        st.markdown("### 🦅 미국 거시경제 경기 지표 (최근 5년 트렌드)")
        col5, col6 = st.columns(2)
        
        with col5:
            st.markdown("#### 🏢 미국 실질 GDP (분기별)")
            if not fred_data["미국 실질 GDP"].empty:
                s = fred_data["미국 실질 GDP"]
                f_val, l_val = s.iloc[0], s.iloc[-1]
                chg = ((l_val - f_val) / f_val) * 100
                st.write(f"🔹 시작: {f_val:,.0f} ➔ 최신: {l_val:,.0f} (증감률: **{chg:+.1f}%**)")
                
                fig_gdp = go.Figure(go.Scatter(x=s.index, y=s, mode='lines+markers', line=dict(color='#8E44AD', width=2)))
                fig_gdp.add_trace(go.Scatter(x=[s.index[0], s.index[-1]], y=[f_val, l_val], mode='markers+text', text=[f"{f_val:,.0f}", f"{l_val:,.0f}"], textposition=["top right", "top left"], marker=dict(size=8, color='#8E44AD')))
                fig_gdp.update_layout(height=280, margin=dict(l=20, r=20, t=10, b=10), plot_bgcolor='white', showlegend=False, xaxis=dict(showgrid=True, gridcolor='lightgray'), yaxis=dict(showgrid=True, gridcolor='lightgray'))
                st.plotly_chart(fig_gdp, use_container_width=True)
                
        with col6:
            st.markdown("#### 👕 미국 의류 소비자물가지수(CPI)")
            if not fred_data["미국 의류 소비자물가지수(CPI)"].empty:
                s = fred_data["미국 의류 소비자물가지수(CPI)"]
                f_val, l_val = s.iloc[0], s.iloc[-1]
                chg = ((l_val - f_val) / f_val) * 100
                st.write(f"🔹 시작: {f_val:,.1f} ➔ 최신: {l_val:,.1f} (증감률: **{chg:+.1f}%**)")
                
                fig_cpi = go.Figure(go.Scatter(x=s.index, y=s, line=dict(color='#D35400', width=2)))
                fig_cpi.add_trace(go.Scatter(x=[s.index[0], s.index[-1]], y=[f_val, l_val], mode='markers+text', text=[f"{f_val:,.1f}", f"{l_val:,.1f}"], textposition=["top right", "top left"], marker=dict(size=8, color='#D35400')))
                fig_cpi.update_layout(height=280, margin=dict(l=20, r=20, t=10, b=10), plot_bgcolor='white', showlegend=False, xaxis=dict(showgrid=True, gridcolor='lightgray'), yaxis=dict(showgrid=True, gridcolor='lightgray'))
                st.plotly_chart(fig_cpi, use_container_width=True)

        st.markdown("---")

        # ----------------------------------------
        # --- 4층: 📦 패션 소매 재고 및 판매 균형 (밸런스 매칭 🧩) ---
        # ----------------------------------------
        st.markdown("### 📊 미국 의류 소매업 공급망 지표 (최근 5년 트렌드)")
        col7, col8 = st.columns(2)
        
        with col7:
            st.markdown("#### 📦 미국 소매업 재고율 (Inventory-to-Sales)")
            if not fred_data["미국 소매업 재고율"].empty:
                s = fred_data["미국 소매업 재고율"]
                f_val, l_val = s.iloc[0], s.iloc[-1]
                chg = ((l_val - f_val) / f_val) * 100
                st.write(f"🔹 시작: {f_val:.2f} ➔ 최신: {l_val:.2f} (증감률: **{chg:+.1f}%**)")
                
                fig_inv = go.Figure(go.Scatter(x=s.index, y=s, fill='tozeroy', line=dict(color='#16A085', width=2)))
                fig_inv.add_trace(go.Scatter(x=[s.index[0], s.index[-1]], y=[f_val, l_val], mode='markers+text', text=[f"{f_val:.2f}", f"{l_val:.2f}"], textposition=["top right", "top left"], marker=dict(size=8, color='#16A085')))
                fig_inv.update_layout(height=280, margin=dict(l=20, r=20, t=10, b=10), plot_bgcolor='white', showlegend=False, xaxis=dict(showgrid=True, gridcolor='lightgray'), yaxis=dict(showgrid=True, gridcolor='lightgray'))
                st.plotly_chart(fig_inv, use_container_width=True)
                
        with col8:
            st.markdown("#### 🛍️ 미국 의류 소매 판매액 (의류 매장 매출 총액)")
            if not fred_data["미국 의류 소매판매액"].empty:
                s = fred_data["미국 의류 소매판매액"]
                f_val, l_val = s.iloc[0], s.iloc[-1]
                chg = ((l_val - f_val) / f_val) * 100
                st.write(f"🔹 시작: ${f_val:,.0f}M ➔ 최신: ${l_val:,.0f}M (증감률: **{chg:+.1f}%**)")
                
                fig_sales = go.Figure(go.Scatter(x=s.index, y=s, line=dict(color='#E74C3C', width=2)))
                fig_sales.add_trace(go.Scatter(x=[s.index[0], s.index[-1]], y=[f_val, l_val], mode='markers+text', text=[f"${f_val:,.0f}M", f"${l_val:,.0f}M"], textposition=["top right", "top left"], marker=dict(size=8, color='#E74C3C')))
                fig_sales.update_layout(height=280, margin=dict(l=20, r=20, t=10, b=10), plot_bgcolor='white', showlegend=False, xaxis=dict(showgrid=True, gridcolor='lightgray'), yaxis=dict(showgrid=True, gridcolor='lightgray'))
                st.plotly_chart(fig_sales, use_container_width=True)

    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")

# ==========================================
# [Tab 5] 🛡️ 신용 리스크 & 바이어 매트릭스 (최종 완료판 🚀)
# ==========================================

# 💡 1. Tab 5 전용 금융 데이터 수집 함수
@st.cache_data(ttl=3600)
def get_tab5_financial_data():
    import pandas as pd
    import requests
    import yfinance as yf
    
    FRED_API_KEY = "7cbd5f701c3b7e514e3dfcb6810d2fb7"
    headers = {'User-Agent': 'Mozilla/5.0'}
    start_date = pd.Timestamp.today() - pd.DateOffset(years=5)
    
    try:
        sp500 = yf.Ticker("^GSPC").history(period="1y")['Close']
    except:
        sp500 = pd.Series()
        
    try:
        url = f"https://api.stlouisfed.org/fred/series/observations?series_id=BAA10Y&api_key={FRED_API_KEY}&file_type=json"
        res = requests.get(url, headers=headers, timeout=30)
        df = pd.DataFrame(res.json()['observations'])
        df['date'] = pd.to_datetime(df['date'])
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        df = df.set_index('date')['value'].dropna()
        moodys = df[df.index >= start_date]
    except:
        moodys = pd.Series()
        
    return sp500, moodys

# 💡 2. 11개 바이어의 실시간 주가 매트릭스 수집 함수
@st.cache_data(ttl=3600)
def get_all_buyers_matrix_stock():
    import yfinance as yf
    import pandas as pd
    
    buyer_tickers = {
        "Walmart": "WMT",
        "Target Corp.": "TGT",
        "Kohl's": "KSS",
        "Michaels Cos. Inc. (The)": None, 
        "Fast Retailing Co. Ltd.": "FRCOY",
        "Victoria's Secret & Co.": "VSCO",
        "Gap Inc.": "GAP",
        "UNDER ARMOUR": "UAA",
        "Abercrombie & Fitch Co.": "ANF",
        "Carter's, Inc.": "CRI",
        "PVH": "PVH"
    }
    
    results = {}
    for name, ticker in buyer_tickers.items():
        if ticker:
            try:
                stock = yf.Ticker(ticker).history(period="1y")
                if not stock.empty:
                    current_price = stock['Close'].iloc[-1]
                    start_price = stock['Close'].iloc[0]
                    chg = ((current_price - start_price) / start_price) * 100
                    results[name] = {"주가": f"${current_price:,.2f}", "변동률": f"{chg:+.1f}%"}
                else:
                    results[name] = {"주가": "N/A", "변동률": "-"}
            except:
                results[name] = {"주가": "N/A", "변동률": "-"}
        else:
            results[name] = {"주가": "비상장 (Private)", "변동률": "-"}
    return results


with tab5:
    st.subheader("🛡️ 바이어 신용 리스크 및 주요 고객사 통합 매트릭스")
    st.caption("무디스(Moody's) 및 S&P의 장기(LT) 신용등급 기준표와 실시간 자본시장 지표를 연동하여 바이어 부도 및 대금 미수 리스크를 종합 관리합니다.")
    
    try:
        import plotly.graph_objects as go
        import pandas as pd
        
        sp500_data, moodys_data = get_tab5_financial_data()
        
        # --- 1층: 거시 신용 스프레드 및 S&P 500 나란히 배치 ---
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📉 무디스 BAA 회사채 신용 스프레드 (최근 5년)")
            if not moodys_data.empty:
                s = moodys_data
                f_val, l_val = s.iloc[0], s.iloc[-1]
                st.write(f"🔹 시작: {f_val:.2f}%p ➔ 최신: {l_val:.2f}%p (변동 폭: **{l_val-f_val:+.2f}%p**)")
                st.caption("※ 높을수록 글로벌 기업들의 자금 조달 리스크(부도 위험)가 커짐을 의미합니다.")
                
                fig_spread = go.Figure(go.Scatter(x=s.index, y=s, line=dict(color='#C0392B', width=2)))
                fig_spread.add_trace(go.Scatter(x=[s.index[0], s.index[-1]], y=[f_val, l_val], mode='markers+text', text=[f"{f_val:.2f}%p", f"{l_val:.2f}%p"], textposition=["top right", "top left"], marker=dict(size=8, color='#C0392B')))
                fig_spread.update_layout(height=260, margin=dict(l=20, r=20, t=10, b=10), plot_bgcolor='white', showlegend=False, xaxis=dict(showgrid=True, gridcolor='lightgray'), yaxis=dict(showgrid=True, gridcolor='lightgray'))
                st.plotly_chart(fig_spread, use_container_width=True)
            else:
                st.info("신용 스프레드 데이터를 불러올 수 없습니다.")
                
        with col2:
            st.markdown("#### 🇺🇸 미국 S&P 500 주가지수 (최근 1년)")
            if not sp500_data.empty:
                s = sp500_data
                f_val, l_val = s.iloc[0], s.iloc[-1]
                chg = ((l_val - f_val) / f_val) * 100
                st.write(f"🔹 시작: {f_val:,.1f} ➔ 최신: {l_val:,.1f} (증감률: **{chg:+.1f}%**)")
                st.caption("※ 미국 전반적인 경기 상태와 자본 시장의 펀더멘탈 체력을 반영합니다.")
                
                fig_sp = go.Figure(go.Scatter(x=s.index, y=s, line=dict(color='#27AE60', width=2)))
                fig_sp.add_trace(go.Scatter(x=[s.index[0], s.index[-1]], y=[f_val, l_val], mode='markers+text', text=[f"{f_val:,.1f}", f"{l_val:,.1f}"], textposition=["top right", "top left"], marker=dict(size=8, color='#27AE60')))
                fig_sp.update_layout(height=260, margin=dict(l=20, r=20, t=10, b=10), plot_bgcolor='white', showlegend=False, xaxis=dict(showgrid=True, gridcolor='lightgray'), yaxis=dict(showgrid=True, gridcolor='lightgray'))
                st.plotly_chart(fig_sp, use_container_width=True)
            else:
                st.info("S&P 500 지수 데이터를 불러올 수 없습니다.")
                
        st.markdown("---")
        
        # --- 2층: 📊 글로벌 바이어 장기(LT) 신용등급 & 주가 통합 매트릭스 ---
        st.markdown("### 📊 글로벌 바이어 장기(LT) 신용등급 & 주가 통합 매트릭스")
        st.caption("※ 아래 표는 무디스 및 S&P가 공식 발표한 바이어별 최신 장기(Long-Term) 신용등급 리스크 보드입니다.")
        
        # 💡 요청하신 3개 기업(Fast Retailing, A&F, Carter's)의 무디스 등급을 n/a로 깔끔하게 수정했습니다.
        matrix_rows = [
            {"BUYER (고객사)": "Walmart", "Moody's 등급 (LT)": "Aa2 ('96.03)", "S&P 등급 (LT)": "AA ('20.05)"},
            {"BUYER (고객사)": "Target Corp.", "Moody's 등급 (LT)": "A2 ('19.01)", "S&P 등급 (LT)": "A ('20.03)"},
            {"BUYER (고객사)": "Kohl's", "Moody's 등급 (LT)": "B2 ('25.05)", "S&P 등급 (LT)": "B+ ('25.09)"},
            {"BUYER (고객사)": "Michaels Cos. Inc. (The)", "Moody's 등급 (LT)": "B3 ('23.04)", "S&P 등급 (LT)": "B- ('24.04)"},
            {"BUYER (고객사)": "Fast Retailing Co. Ltd.", "Moody's 등급 (LT)": "n/a", "S&P 등급 (LT)": "A+ ('20.06)"},
            {"BUYER (고객사)": "Victoria's Secret & Co.", "Moody's 등급 (LT)": "Ba3 ('21.06)", "S&P 등급 (LT)": "BB- ('21.06)"},
            {"BUYER (고객사)": "Gap Inc.", "Moody's 등급 (LT)": "Ba2 ('25.02)", "S&P 등급 (LT)": "BB+ ('25.12)"},
            {"BUYER (고객사)": "UNDER ARMOUR", "Moody's 등급 (LT)": "B1 ('25.12)", "S&P 등급 (LT)": "BB- ('24.05)"},
            {"BUYER (고객사)": "Abercrombie & Fitch Co.", "Moody's 등급 (LT)": "n/a", "S&P 등급 (LT)": "BB ('24.04)"},
            {"BUYER (고객사)": "Carter's, Inc.", "Moody's 등급 (LT)": "n/a", "S&P 등급 (LT)": "BB+ ('20.04)"},
            {"BUYER (고객사)": "PVH", "Moody's 등급 (LT)": "Baa3 ('19.04)", "S&P 등급 (LT)": "BBB- ('18.05)"}
        ]
        df_matrix = pd.DataFrame(matrix_rows)
        
        stock_map = get_all_buyers_matrix_stock()
        df_matrix["현재 주가 (USD)"] = df_matrix["BUYER (고객사)"].map(lambda x: stock_map.get(x, {}).get("주가", "N/A"))
        df_matrix["최근 1년 변동률"] = df_matrix["BUYER (고객사)"].map(lambda x: stock_map.get(x, {}).get("변동률", "-"))
        
        st.dataframe(df_matrix, use_container_width=True, hide_index=True)
        
        st.info("💡 **신용등급 가이드:** 투자적격등급(Moody's Baa3 이상 / S&P BBB- 이상)의 바이어는 상대적으로 안정적인 대금 회수가 가능하나, 투기등급(B 또는 BB 계열 이하)에 속한 바이어는 신용 스프레드 추이를 상시 모니터링하여 미수금 한도를 선제적으로 관리해야 합니다.")
            
    except Exception as e:
        st.error(f"데이터 매트릭스를 구성하는 중 오류가 발생했습니다: {e}")