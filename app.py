import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# 1. 페이지 설정 (넓은 화면)
st.set_page_config(page_title="US Market & Trade Dashboard", layout="wide")
st.title("📊 US Market & Trade Dashboard")

# 2. 탭(Tab) 생성: 노트북 리소스 최적화를 위해 화면을 분리합니다.
tab1, tab2 = st.tabs(["🛒 미국 소매 판매 현황 (FRED)", "🌐 미국 의류 수입 현황 (OTEXA)"])

# ==========================================
# [Tab 1] 기존: 미국 소매 판매 현황 (FRED)
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
        ytd_growth = ytd_growth.sort_values('Category', ascending=False)
        
        colors = ['#CC0000' if val < 0 else '#0070C0' for val in ytd_growth['Growth']]
        
        fig = go.Figure(go.Bar(
            x=ytd_growth['Growth'],
            y=ytd_growth['Category'],
            orientation='h',
            text=ytd_growth['Growth'].apply(lambda x: f"{x:.1f}%"),
            textposition='outside',
            marker_color=colors
        ))
        fig.update_layout(plot_bgcolor='white', height=600, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("📋 미국 소매 카테고리 별 전년 동월대비 증감률(%)")
        
        df_pivot = df.pivot(index='Date', columns='Category', values='Sales')
        yoy_df = df_pivot.pct_change(periods=12) * 100
        table_df = yoy_df.tail(12).T
        
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
# [Tab 2] 신규: 미국 의류 수입 현황 (OTEXA)
# ==========================================
with tab2:
    st.markdown("### * 미국 의류 수입 국가별 비중 (%)")
    
    # 💡 팁: 실제 데이터 파이프라인(ETL)이 완성되기 전까지 화면을 테스트하기 위한 샘플 데이터입니다.
    # 나중에 otexa_share.csv 와 otexa_yoy.csv 를 만들어서 대체하면 완벽하게 연동됩니다.
    
    # 1. 국가별 비중 차트 데이터 생성 (이미지 참고)
    share_data = {
        'Country': ['China', 'Vietnam', 'Indonesia', 'Cambodia', 'Nicaragua', 'Guatemala'],
        '2022': [21.7, 18.3, 5.6, 4.4, 2.9, 1.9],
        '2023': [21.0, 18.2, 5.4, 4.3, 2.5, 1.9],
        '2024': [20.8, 18.9, 5.4, 4.8, 2.5, 2.0],
        '2025': [14.9, 23.5, 6.5, 6.8, 2.7, 2.1],
        '2026 (Jan-Feb)': [9.7, 23.9, 7.2, 6.5, 2.1, 1.8]
    }
    df_share = pd.DataFrame(share_data)
    
    # Plotly 그룹형 바 차트 그리기
    fig_share = go.Figure()
    
    # 연도별로 색상 톤을 다르게 설정 (Blues palette)
    colors_years = ['#1f497d', '#2e75b6', '#5b9bd5', '#9dc3e6', '#c6d9f1']
    years = ['2022', '2023', '2024', '2025', '2026 (Jan-Feb)']
    
    for idx, year in enumerate(years):
        fig_share.add_trace(go.Bar(
            x=df_share['Country'],
            y=df_share[year],
            name=year,
            marker_color=colors_years[idx],
            text=df_share[year].apply(lambda x: f"{x:.1f}%" if idx == 4 or idx == 0 else ""), # 처음과 끝 연도만 라벨 표시 (깔끔하게)
            textposition='outside'
        ))
        
    fig_share.update_layout(
        barmode='group',
        plot_bgcolor='white',
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        yaxis=dict(showgrid=True, gridcolor='lightgray', zeroline=True, zerolinecolor='black'),
        height=400,
        margin=dict(t=20)
    )
    st.plotly_chart(fig_share, use_container_width=True)
    
    st.markdown("---")
    st.markdown("### * 미국 의류 수입 국가별 전년 동월대비 증감률(%)")
    
    # 2. 국가별 YoY 표 데이터 생성 (이미지 참고)
    yoy_data = {
        'Country': ['World', 'China', 'Vietnam', 'Indonesia', 'Cambodia', 'Nicaragua', 'Guatemala', 'Bangladesh', 'India'],
        "'25 / 2": [3.3, 3.0, 2.2, -0.4, -6.5, -23.9, -4.5, 10.2, 19.2],
        "'25 / 3": [11.2, -8.9, 20.2, 22.9, 24.2, 9.0, 18.4, 26.7, 21.1],
        "'25 / 4": [9.7, -13.3, 23.4, 3.1, 38.6, -4.2, 0.7, 37.8, 10.1],
        "'25 / 5": [-7.4, -52.4, 17.6, 2.6, 9.1, -2.0, -8.8, -8.1, 4.0],
        "'25 / 6": [5.1, -39.9, 25.3, 44.9, 59.5, 16.4, 3.3, 45.6, 12.4],
        "'26 / 1": [-13.5, -62.3, 3.1, 7.2, 25.4, -11.8, -4.1, -0.9, -18.3] # 중간 생략
    }
    df_yoy = pd.DataFrame(yoy_data)
    df_yoy = df_yoy.set_index('Country')
    
    # 국가명 컬럼 색상 지정 (이미지 레이아웃 완벽 재현)
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
        # 기본 셀 서식
        row_style = [''] * len(row)
        return row_style

    # 국가 인덱스 색상 칠하기 (Pandas Styler 고급기법)
    styled_yoy = df_yoy.style.format("{:.1f}%").apply(style_country_bg, axis=1)
    
    st.dataframe(df_yoy.style.format("{:.1f}%"), use_container_width=True)