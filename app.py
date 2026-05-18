import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import yfinance as yf # 👈 금융 데이터 호출용

# 1. 페이지 설정 및 제목
st.set_page_config(page_title="US Market & Trade Dashboard", layout="wide")
st.title("📊 US Market & Trade & Company Dashboard")

# 2. 탭 생성 (이제 탭이 3개입니다!)
tab1, tab2, tab3 = st.tabs([
    "🛒 미국 소매 판매 현황 (FRED)", 
    "🌐 미국 의류 수입 현황 (OTEXA)", 
    "🏢 글로벌 패션·유통 기업 모니터링"
])

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
# [Tab 3] 글로벌 패션·유통 기업 모니터링 (1년 주가 추세 + 분기 실적 + 뉴스 번역 + 무적 캐싱)
# ==========================================
with tab3:
    st.subheader("🏢 요청 기업 실시간 주가 및 정보 모니터링")
    
    # 💡 주가, 분기 재무제표, 뉴스를 한 번에 불러와 10분간 캐싱하는 무적의 함수
    @st.cache_data(ttl=600)
    def get_complete_company_data(ticker_symbol, selected_company):
        ticker = yf.Ticker(ticker_symbol)
        
        # 1. 1년치 주가 데이터 가져오기 (요청사항 1 반영)
        try:
            hist = ticker.history(period="1y")
        except Exception:
            hist = pd.DataFrame()
            
        # 2. 분기 실적 데이터 가져오기 (요청사항 4 반영 - 캐싱 처리로 먹통 걱정 제로!)
        financials_df = pd.DataFrame()
        try:
            q_fin = ticker.quarterly_financials
            if q_fin is not None and not q_fin.empty:
                # 야후 파이낸스 고유 계정명 매칭 (매출액 및 영업이익)
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
                    financials_df = q_fin.loc[rows_to_extract].copy()
                    financials_df.index = row_labels
                    financials_df = financials_df.iloc[:, :4] # 최근 4개 분기만 컷
                    financials_df = financials_df.iloc[:, ::-1] # 과거에서 현재 순으로 컬럼 뒤집기
        except Exception:
            pass
            
        # 3. 기업 기본 정보 가져오기 (통화 정보 파악용)
        info_dict = {}
        try:
            info_dict = ticker.info
        except Exception:
            pass
            
        if ".KS" in ticker_symbol or ".KQ" in ticker_symbol:
            info_dict['currency'] = "KRW"
        elif ".T" in ticker_symbol:
            info_dict['currency'] = "JPY"
        else:
            info_dict['currency'] = "USD"
                
        # 4. 뉴스 데이터 가져오기 및 번역
        from deep_translator import GoogleTranslator
        raw_news = []
        try:
            raw_news = ticker.news
        except Exception:
            pass
            
        translated_news = []
        valid_news_count = 0
        
        if raw_news:
            for item in raw_news:
                title = item.get('title')
                link = item.get('link')
                publisher = item.get('publisher', 'Unknown Source')
                if title and link:
                    try:
                        ko_title = GoogleTranslator(source='auto', target='ko').translate(title)
                        display_title = f"[{publisher}] {ko_title}"
                    except Exception:
                        display_title = f"[{publisher}] {title}"
                    translated_news.append({"title": display_title, "orig_title": title, "link": link})
                    valid_news_count += 1
                if valid_news_count >= 5:
                    break

        if valid_news_count == 0:
            try:
                import xml.etree.ElementTree as ET
                import urllib.request
                import urllib.parse
                
                search_term = ticker_symbol.split('.')[0] if '.' in ticker_symbol else selected_company.split(' ')[0]
                url = f"https://news.google.com/rss/search?q={urllib.parse.quote(search_term)}&hl=en-US&gl=US&ceid=US:en"
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                xml_data = urllib.request.urlopen(req).read()
                
                root = ET.fromstring(xml_data)
                for item in root.findall('.//item')[:5]:
                    g_title = item.find('title').text
                    g_link = item.find('link').text
                    g_pub = item.find('source').text if item.find('source') is not None else 'Google News'
                    if g_title and g_link:
                        try:
                            ko_g_title = GoogleTranslator(source='auto', target='ko').translate(g_title)
                            display_title = f"[{g_pub}] {ko_g_title}"
                        except Exception:
                            display_title = f"[{g_pub}] {g_title}"
                        translated_news.append({"title": display_title, "orig_title": g_title, "link": g_link})
                        valid_news_count += 1
            except Exception:
                pass
                
        return info_dict, hist, financials_df, translated_news

    # 대상 기업 리스트
    companies = {
        "Walmart (월마트)": "WMT", "Target (타겟)": "TGT", "Kohl's (콜스)": "KSS",
        "Victoria's Secret (빅토리아 시크릿)": "VSCO", "Abercrombie & Fitch (아베크롬비)": "ANF",
        "Carter's (카터스)": "CRI", "Fast Retailing (유니클로 모기업)": "9983.T",
        "Under Armour (언더아머)": "UA", "Amazon (아마존)": "AMZN", "Alibaba (알리바바)": "BABA",
        "한세실업": "105630.KS", "영원무역": "111770.KS", "노브랜드": "145170.KQ", 
        "TP inc. (태평양물산)": "007980.KS", "Shinwon (신원)": "009270.KS", "제이에스코퍼레이션": "194370.KS"
    }
    
    selected_company = st.selectbox("분석할 기업을 선택하세요", list(companies.keys()))
    ticker_symbol = companies[selected_company]
    
    try:
        # 무적 캐싱 함수 가동
        info, hist, financials_df, final_news = get_complete_company_data(ticker_symbol, selected_company)
        
        # 1. 현재 주가 및 화폐 단위 셋팅 (요청사항 2 반영)
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
            
        # 💡 [요청사항 3] 최근 한 달의 월별 평균 주가 전월 대비 증감률(MoM) 계산 로직
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
        
        # 주가 상단 배치 (시가총액은 제거함)
        st.metric(label="현재 주가", value=price_formatted, delta=delta_formatted)
        
        # 2. 1년치 주가추세 차트 (요청사항 1 반영 + 크기 고정으로 스크롤 버그 원천 해결)
        st.markdown("### 📈 최근 1년 주가 추세")
        if not hist.empty:
            fig_trend = go.Figure(go.Scatter(
                x=hist.index, y=hist['Close'],
                mode='lines', line=dict(color='#0070C0', width=2),
                name='종가'
            ))
            fig_trend.update_layout(
                plot_bgcolor='white',
                width=850, height=350, # 👈 가로크기를 픽셀로 고정하여 스크롤 쪼그라듦 완전 방어!
                margin=dict(l=50, r=40, t=20, b=30),
                xaxis=dict(showgrid=True, gridcolor='lightgray'),
                yaxis=dict(showgrid=True, gridcolor='lightgray', tickformat="," if currency != "USD" else ",.2f")
            )
            st.plotly_chart(fig_trend, use_container_width=False) # 👈 False 설정 필수
        else:
            st.info("주가 차트 데이터를 불러올 수 없습니다.")
            
        # 3. 최근 4개분기 매출액 & 영업이익 차트 (요청사항 4 반영)
        if not financials_df.empty:
            st.markdown("### 📊 최근 4개 분기 실적 실적")
            
            quarters = [str(col).split(' ')[0] for col in financials_df.columns]
            
            # 국가별 화폐 단위에 따른 스케일링 설정
            if currency == "KRW":
                scale, unit = 1e8, "(단위: 억 원)"
            elif currency == "JPY":
                scale, unit = 1e8, "(단위: 억 엔)"
            else:
                scale, unit = 1e6, "(단위: 백만 달러 / $M)"
                
            st.caption(unit)
            
            fig_fin = go.Figure()
            
            if '매출액' in financials_df.index:
                fig_fin.add_trace(go.Bar(
                    x=quarters, y=financials_df.loc['매출액'] / scale,
                    name='매출액', marker_color='#1f497d',
                    text=(financials_df.loc['매출액'] / scale).apply(lambda x: f"{x:,.1f}"),
                    textposition='outside'
                ))
            if '영업이익' in financials_df.index:
                fig_fin.add_trace(go.Bar(
                    x=quarters, y=financials_df.loc['영업이익'] / scale,
                    name='영업이익', marker_color='#ed7d31',
                    text=(financials_df.loc['영업이익'] / scale).apply(lambda x: f"{x:,.1f}"),
                    textposition='outside'
                ))
                
            fig_fin.update_layout(
                barmode='group', plot_bgcolor='white',
                width=850, height=350, # 👈 분기 차트도 스크롤 버그 방지를 위해 고정 크기 지정
                margin=dict(l=50, r=40, t=30, b=30),
                xaxis=dict(type='category'),
                yaxis=dict(showgrid=True, gridcolor='lightgray'),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_fin, use_container_width=False)
        else:
            st.info("최근 분기 실적 데이터를 공급하지 않거나 야후 금융 API 과부하로 차트가 일시 제한되었습니다.")
            
        # 4. 최신 뉴스 리스트 (한글)
        st.markdown("---")
        st.markdown(f"### 📰 {selected_company} 관련 최신 글로벌 뉴스 (한글 번역)")
        
        if final_news:
            for item in final_news:
                with st.expander(item['title']):
                    st.write(f"**원본 제목:** {item['orig_title']}")
                    st.write(f"[기사 원문 링크]({item['link']})")
        else:
            st.info("현재 해당 기업과 관련된 최신 뉴스 기사를 불러올 수 없습니다.")
            
    except Exception as e:
        st.error(f"데이터를 처리하는 중 일시적인 오류가 발생했습니다: {e}")