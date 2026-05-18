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
# [Tab 3] 글로벌 패션·유통 기업 모니터링 (실시간 100% 자동)
# ==========================================
with tab3:
    st.subheader("🏢 요청 기업 실시간 주가 및 정보 모니터링")
    
    # 💡 요청하신 모든 기업의 야후 파이낸스 공식 티커 매핑
    # 한국 기업 코스피는 .KS, 코스닥은 .KQ / 일본 주식은 .T / 미국 주식은 심볼 그대로 사용
    companies = {
        "Walmart (월마트)": "WMT",
        "Target (타겟)": "TGT",
        "Kohl's (콜스)": "KSS",
        "Victoria's Secret (빅토리아 시크릿)": "VSCO",
        "Abercrombie & Fitch (아베크롬비)": "ANF",
        "Carter's (카터스)": "CRI",
        "Fast Retailing (유니클로 모기업)": "9983.T",
        "Under Armour (언더아머)": "UA",
        "Amazon (아마존)": "AMZN",
        "Alibaba (알리바바)": "BABA",
        "한세실업": "105630.KS",
        "영원무역": "111770.KS",
        "노브랜드": "145170.KQ", 
        "TP inc. (태평양물산)": "007980.KS",
        "Shinwon (신원)": "009270.KS",
        "제이에스코퍼레이션": "194370.KS"
    }
    
    selected_company = st.selectbox("분석할 기업을 선택하세요", list(companies.keys()))
    ticker_symbol = companies[selected_company]
    
    try:
        # 실시간 데이터 엔진 가동
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        # 1. 상단 미니 카드(Metrics) 배치
        col1, col2, col3 = st.columns(3)
        
        current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
        previous_close = info.get('previousClose', 1) # 0 나누기 방지
        price_change = current_price - previous_close
        price_change_pct = (price_change / previous_close) * 100
        
        # 시가총액 단위 환산 (국가별 통화 반영)
        market_cap = info.get('marketCap', 0)
        currency = info.get('