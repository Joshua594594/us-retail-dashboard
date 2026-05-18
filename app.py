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
# [Tab 3] 글로벌 패션·유통 기업 모니터링 (월간 평균 주가 + 스크롤 버그 해결 + 뉴스 번역)
# ==========================================
with tab3:
    st.subheader("🏢 요청 기업 실시간 주가 및 정보 모니터링")
    
    @st.cache_data(ttl=600)
    def get_complete_company_data(ticker_symbol, selected_company):
        ticker = yf.Ticker(ticker_symbol)
        
        # 1. 차트 데이터 가져오기 (가장 안전한 API)
        try:
            hist = ticker.history(period="6mo")
        except Exception:
            hist = pd.DataFrame()
            
        # 2. 기업 정보 가져오기 (시총/통화 등)
        info_dict = {}
        try:
            info_dict = ticker.info
        except Exception:
            pass
            
        # 백업용 주가 계산 및 통화 하드코딩
        if not info_dict and not hist.empty:
            info_dict['currentPrice'] = hist['Close'].iloc[-1]
            info_dict['previousClose'] = hist['Close'].iloc[-2] if len(hist) > 1 else hist['Close'].iloc[-1]
            if ".KS" in ticker_symbol or ".KQ" in ticker_symbol:
                info_dict['currency'] = "KRW"
            elif ".T" in ticker_symbol:
                info_dict['currency'] = "JPY"
            else:
                info_dict['currency'] = "USD"
                
        # 3. 뉴스 데이터 우회 수집
        raw_news = []
        try:
            raw_news = ticker.news
        except Exception:
            pass
            
        # 4. 번역 프로세스
        from deep_translator import GoogleTranslator
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
                
        return info_dict, hist, translated_news

    # 기업 리스트
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
        info, hist, final_news = get_complete_company_data(ticker_symbol, selected_company)
        
        # 💡 [개선 1] 시가총액 유무에 따라 상단 레이아웃 분기 (시총 없으면 깔끔하게 숨김)
        market_cap = info.get('marketCap', 0)
        currency = info.get('currency', 'USD')
        current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
        previous_close = info.get('previousClose', 1)
        price_change = current_price - previous_close
        price_change_pct = (price_change / previous_close) * 100 if previous_close != 0 else 0

        if market_cap > 0:
            col1, col2 = st.columns(2)
            if currency == "KRW":
                market_cap_formatted = f"{market_cap // 100000000:,} 억 원"
            elif currency == "JPY":
                market_cap_formatted = f"¥ {market_cap // 100000000:,} 억 엔"
            else:
                market_cap_formatted = f"$ {market_cap / 1000000000:,.2f} B"
                
            with col1:
                st.metric(
                    label=f"현재 주가 ({currency})", 
                    value=f"{current_price:,.2f}" if currency != "KRW" else f"{int(current_price):,}", 
                    delta=f"{price_change:,.2f} ({price_change_pct:.2f}%)" if currency != "KRW" else f"{int(price_change):,} ({price_change_pct:.2f}%)"
                )
            with col2:
                st.metric(label="시가총액", value=market_cap_formatted)
        else:
            st.metric(
                label=f"현재 주가 ({currency}) - *서버 과부하로 시가총액 일시 숨김*", 
                value=f"{current_price:,.2f}" if currency != "KRW" else f"{int(current_price):,}", 
                delta=f"{price_change:,.2f} ({price_change_pct:.2f}%)" if currency != "KRW" else f"{int(price_change):,} ({price_change_pct:.2f}%)"
            )
            
        # 💡 [개선 2] 각 달의 평균값을 구하고 전월 대비(MoM, %) 차트 계산
        st.markdown("### 📊 월별 평균 주가 전월 대비 증감률 (MoM, %)")
        if not hist.empty:
            # 날짜를 인덱스에서 컬럼으로 빼고 월별 그룹화
            hist_df = hist.reset_index()
            hist_df['YearMonth'] = hist_df['Date'].dt.to_period('M')
            
            # 월별 주가 평균값 계산
            monthly_avg = hist_df.groupby('YearMonth')['Close'].mean().reset_index()
            # 전월 대비 증감률 계산
            monthly_avg['MoM'] = monthly_avg['Close'].pct_change() * 100
            # 첫 달은 전월 데이터가 없으므로 제거
            monthly_avg = monthly_avg.dropna()
            
            # 차트용 텍스트 포맷 (예: 2026-03)
            monthly_avg['YearMonth_str'] = monthly_avg['YearMonth'].astype(str)
            
            # 💡 [개선 3] 스크롤 시 쪼그라듦 방지를 위해 Plotly 객체 직접 생성 및 크기 고정
            bar_colors = ['#CC0000' if val < 0 else '#0070C0' for val in monthly_avg['MoM']]
            fig_monthly = go.Figure(go.Bar(
                x=monthly_avg['YearMonth_str'],
                y=monthly_avg['MoM'],
                text=monthly_avg['MoM'].apply(lambda x: f"{x:.1f}%"),
                textposition='outside',
                marker_color=bar_colors
            ))
            
            fig_monthly.update_layout(
                plot_bgcolor='white',
                # 픽셀 너비를 800 이상으로 고정하여 스크롤 시 무너지지 않게 방어합니다.
                width=850, 
                height=350,
                margin=dict(l=40, r=40, t=30, b=30),
                yaxis=dict(title="증감률 (%)", showgrid=True, gridcolor='lightgray'),
                xaxis=dict(type='category')
            )
            # 고정형 차트 출력 (use_container_width를 False로 하여 스크롤 버그 원천 차단)
            st.plotly_chart(fig_monthly, use_container_width=False)
        else:
            st.info("주가 차트 데이터를 불러올 수 없습니다.")
        
        # 3. 최신 뉴스 리스트 (한글)
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