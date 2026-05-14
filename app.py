import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 페이지 설정 (넓은 화면)
st.set_page_config(page_title="US Retail Dashboard", layout="wide")

try:
    # 2. 데이터 불러오기 및 전처리
    df = pd.read_csv('retail_output.csv')
    df['Date'] = pd.to_datetime(df['Date'])
    
    # 가장 최신 날짜 파악
    latest_date = df['Date'].max()
    current_year = latest_date.year
    prev_year = current_year - 1
    max_month = latest_date.month # 최신 데이터가 몇 월까지 있는지 확인 (예: 3월)

    st.title("📊 US Retail Sales Report")
    
    # ==========================================
    # 상단: 누적 성장률 (YTD) 바 차트
    # ==========================================
    st.subheader(f"📈 미국 소매 카테고리 별 성장률 (1-{max_month}월) {prev_year} vs {current_year} (%)")
    
    # 올해 1월~최신월 데이터
    df_curr = df[(df['Date'].dt.year == current_year) & (df['Date'].dt.month <= max_month)]
    sum_curr = df_curr.groupby('Category')['Sales'].sum()
    
    # 작년 1월~동일월 데이터
    df_prev = df[(df['Date'].dt.year == prev_year) & (df['Date'].dt.month <= max_month)]
    sum_prev = df_prev.groupby('Category')['Sales'].sum()
    
    # 성장률 계산 (%)
    ytd_growth = ((sum_curr / sum_prev) - 1) * 100
    ytd_growth = ytd_growth.dropna().reset_index()
    ytd_growth.columns = ['Category', 'Growth']
    
    # 이미지처럼 위아래 순서를 맞추기 위해 역순 정렬 (원하는 순서가 있다면 커스텀 가능)
    ytd_growth = ytd_growth.sort_values('Category', ascending=False)
    
    # 색상 지정: 양수는 파란색, 음수는 빨간색
    colors = ['#CC0000' if val < 0 else '#0070C0' for val in ytd_growth['Growth']]
    
    # Plotly 바 차트 그리기
    fig = go.Figure(go.Bar(
        x=ytd_growth['Growth'],
        y=ytd_growth['Category'],
        orientation='h',
        text=ytd_growth['Growth'].apply(lambda x: f"{x:.1f}%"),
        textposition='outside',
        marker_color=colors
    ))
    
    # 차트 배경 하얗게 & 디자인 다듬기
    fig.update_layout(
        plot_bgcolor='white',
        height=600,
        xaxis=dict(showgrid=True, gridcolor='lightgray', zeroline=True, zerolinecolor='black'),
        yaxis=dict(showgrid=False),
        margin=dict(l=0, r=0, t=30, b=0)
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # ==========================================
    # 하단: 최근 12개월 전년 동월 대비 증감률 표
    # ==========================================
    st.subheader("📋 미국 소매 카테고리 별 전년 동월대비 증감률(%)")
    
    # 데이터를 넓은 형태(Wide Format)로 변환: 행=Date, 열=Category
    df_pivot = df.pivot(index='Date', columns='Category', values='Sales')
    
    # 12개월 전과 비교하여 증감률 계산
    yoy_df = df_pivot.pct_change(periods=12) * 100
    
    # 가장 최근 12개월만 추출
    last_12_months = yoy_df.tail(12)
    
    # 행과 열을 뒤집기 (Category가 행, Date가 열이 되도록)
    table_df = last_12_months.T
    
    # 컬럼(날짜) 이름을 보기 좋게 변경 (예: '24 / 4, 5, 6...)
    formatted_cols = []
    for d in table_df.columns:
        formatted_cols.append(f"'{str(d.year)[-2:]} / {d.month}")
    table_df.columns = formatted_cols
    
    # Pandas Styler를 사용해 의류 카테고리 강조 및 % 포맷팅
    def highlight_clothing(row):
        # 의류 행을 찾아서 빨간 테두리와 약간의 배경색 적용
        if 'Clothing' in row.name:
            return ['background-color: #ffe6e6; border-top: 2px solid red; border-bottom: 2px solid red'] * len(row)
        return [''] * len(row)

    styled_table = (
        table_df.style
        .apply(highlight_clothing, axis=1)
        .format("{:.1f}%", na_rep="-")
    )
    
    # Streamlit에 표 렌더링
    st.dataframe(styled_table, use_container_width=True, height=550)

except FileNotFoundError:
    st.error("앗! `retail_output.csv` 파일을 찾을 수 없습니다. ETL 스크립트를 먼저 실행해주세요.")
except Exception as e:
    st.error(f"대시보드를 렌더링하는 중 오류가 발생했습니다: {e}")