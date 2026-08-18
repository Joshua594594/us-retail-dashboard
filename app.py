import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import yfinance as yf

# ==========================================
# 1. 페이지 설정
# ==========================================
st.set_page_config(page_title="US Market & Trade Dashboard", layout="wide")

# ==========================================
# 디자인 시스템 (최소한의 톤 통일만: 카드형 패널, 딥블루 탭, 테이블 헤더 색상)
# 장식적인 KPI 카드/아이콘/뱃지는 요청에 따라 제거했습니다.
# ==========================================
DESIGN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&display=swap');

:root{
  --blue:#2563EB; --blue-d:#1E3A8A;
  --green:#059669; --red:#DC2626; --amber:#D97706;
  --gray3:#E2E8F0; --gray5:#64748B; --gray1:#F8FAFC;
  --text:#0F172A;
}

html, body, [class*="css"] { font-family:'Noto Sans KR',sans-serif; }
.stApp{ background:var(--gray1); }
#MainMenu{visibility:hidden;} footer{visibility:hidden;}

/* 와이드 화면 폭을 그대로 사용 (임의로 좁히지 않음) */
.block-container{ padding-top:1.2rem; padding-bottom:2.5rem; max-width:100%; }

/* 탭을 딥블루 톤으로 */
.stTabs [data-baseweb="tab-list"]{
  background:var(--blue-d); padding:5px 8px; border-radius:8px; gap:2px; margin-bottom:14px;
}
.stTabs [data-baseweb="tab"]{
  color:rgba(255,255,255,.6); font-weight:600; font-size:13px;
  padding:9px 16px; border-radius:6px 6px 0 0; border:none !important;
}
.stTabs [data-baseweb="tab"]:hover{ color:#fff; }
.stTabs [aria-selected="true"]{
  color:#fff !important; background:rgba(255,255,255,.08) !important;
  border-bottom:3px solid #60A5FA !important;
}

/* 차트/표를 감싸는 카드 패널 (장식 없이 테두리+그림자만) */
div[data-testid="stVerticalBlockBorderWrapper"]{
  background:#fff; border:1px solid var(--gray3) !important; border-radius:10px !important;
  box-shadow:0 1px 4px rgba(0,0,0,.05);
}

/* 섹션 소제목 (아이콘 없이 텍스트만, 좌측 얇은 컬러 바) */
.ctitle{
  font-size:13px; font-weight:700; color:var(--text);
  margin:2px 0 10px 0; padding-left:9px; border-left:3px solid var(--blue);
}

/* 표 헤더 색상 통일 */
[data-testid="stDataFrame"] thead tr th{
  background:var(--blue-d) !important; color:#fff !important; font-weight:600 !important;
}

/* st.metric 기본 컴포넌트를 살짝만 카드처럼 */
[data-testid="stMetric"]{
  background:#fff; border:1px solid var(--gray3); border-radius:8px; padding:12px 16px;
}

hr{ border-color:var(--gray3) !important; }
</style>
"""
st.markdown(DESIGN_CSS, unsafe_allow_html=True)

st.title("📊 US Market & Trade & Company Dashboard")

PALETTE = {
    "blue": "#2563EB", "blue_d": "#1E3A8A",
    "green": "#059669", "red": "#DC2626", "amber": "#D97706",
    "grid": "#E2E8F0",
}

def card_title(text):
    st.markdown(f'<div class="ctitle">{text}</div>', unsafe_allow_html=True)

# 2. 탭 생성
tab1, tab2, tab3, tab4 = st.tabs(["📈 FRED 소매 판매", "🚢 OTEXA 수입 데이터", "🏢 기업 모니터링", "🌐 거시경제 및 원가"])

# ==========================================
# [Tab 1] 미국 소매 판매 현황
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
            "Electronics and Appliance Stores": "RSEAS",
            "Building Material and Garden Equipment and Supplies Dealers": "RSBMGESD",
            "Food and Beverage Stores": "RSDBS",
            "Health and Personal Care Stores": "RSHPCS",
            "Gasoline Stations": "RSGASS",
            "Clothing and Clothing Accessories Stores": "RSCCAS",
            "Sporting Goods, Hobby, Musical Instrument, and Book Stores": "RSSGHBMS",
            "General Merchandise Stores": "RSGMS",
            "Miscellaneous Store Retailers": "RSMSR"
        }

        FRED_API_KEY = "7cbd5f701c3b7e514e3dfcb6810d2fb7"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        all_data = []
        last_error = None

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
                        last_error = f"{cat}({ticker}) → HTTP {response.status_code}: {response.text[:200]}"
                        time.sleep(2)
                except Exception as ex:
                    last_error = f"{cat}({ticker}) → {type(ex).__name__}: {ex}"
                    if attempt < 2:
                        time.sleep(2)

        if not all_data:
            st.session_state["_fred_last_error"] = last_error
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
            last_err = st.session_state.get("_fred_last_error")
            if last_err:
                st.caption(f"상세 원인: {last_err}")
            st.caption("※ FRED_API_KEY가 만료/차단되었거나, api.stlouisfed.org로의 네트워크 접근이 막혀 있을 수 있습니다.")
        else:
            latest_date = df['Date'].max()
            current_year = latest_date.year
            prev_year = current_year - 1
            max_month = latest_date.month

            df_curr = df[(df['Date'].dt.year == current_year) & (df['Date'].dt.month <= max_month)]
            sum_curr = df_curr.groupby('Category')['Sales'].sum()

            df_prev = df[(df['Date'].dt.year == prev_year) & (df['Date'].dt.month <= max_month)]
            sum_prev = df_prev.groupby('Category')['Sales'].sum()

            ytd_growth = ((sum_curr / sum_prev) - 1) * 100

            with st.container(border=True):
                card_title(f"미국 소매 카테고리 별 성장률 (1-{max_month}월) {prev_year} vs {current_year} (%)")

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
                    "Offline"
                ]

                ytd_growth = ytd_growth.reindex(exact_14_order).fillna(0).reset_index()
                ytd_growth.columns = ['Category', 'Growth']

                ytd_growth['Category'] = pd.Categorical(ytd_growth['Category'], categories=exact_14_order, ordered=True)
                ytd_growth = ytd_growth.sort_values('Category', ascending=False)

                colors = [PALETTE["red"] if val < 0 else PALETTE["blue"] for val in ytd_growth['Growth']]

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
                        line=dict(color=PALETTE["red"], width=2),
                        fillcolor="rgba(220, 38, 38, 0.05)", layer="below"
                    )

                fig.update_layout(
                    plot_bgcolor='white', paper_bgcolor='white',
                    height=600,
                    margin=dict(l=350, r=50, t=10, b=0),
                    xaxis=dict(showgrid=True, gridcolor=PALETTE["grid"]),
                    yaxis=dict(categoryorder='array', categoryarray=exact_14_order[::-1], automargin=True)
                )
                st.plotly_chart(fig, width='stretch')

            st.write("")
            with st.container(border=True):
                card_title("미국 소매 카테고리 별 전년 동월대비 증감률(%)")

                df_pivot_table = df.pivot(index='Date', columns='Category', values='Sales')
                yoy_df = df_pivot_table.pct_change(periods=12) * 100
                table_df = yoy_df.tail(12).T

                table_df = table_df.reindex(exact_14_order)

                formatted_cols = [f"'{str(d.year)[-2:]} / {d.month}" for d in table_df.columns]
                table_df.columns = formatted_cols

                def highlight_clothing(row):
                    if 'Clothing' in str(row.name):
                        return ['background-color: #FEF2F2; border-top: 2px solid #DC2626; border-bottom: 2px solid #DC2626'] * len(row)
                    return [''] * len(row)

                styled_table = table_df.style.apply(highlight_clothing, axis=1).format("{:.1f}%", na_rep="-")

                st.dataframe(
                    styled_table,
                    width='stretch',
                    height=len(table_df) * 35 + 50
                )

    except Exception as e:
        st.error(f"소매 판매 데이터를 처리하는 중 오류가 발생했습니다: {e}")

# ==========================================
# [Tab 2] 미국 의류 수입 현황 (OTEXA)
# ==========================================
with tab2:
    @st.cache_data(ttl=3600)
    def load_otexa_data():
        import pandas as pd
        import os

        if os.path.exists('otexa_share.csv') and os.path.exists('otexa_yoy.csv'):
            return pd.read_csv('otexa_share.csv'), pd.read_csv('otexa_yoy.csv')
        else:
            raise FileNotFoundError("로컬에 otexa_share.csv 또는 otexa_yoy.csv 파일이 없습니다. ETL 스크립트를 먼저 실행해주세요.")

    try:
        df_share, df_yoy = load_otexa_data()

        with st.container(border=True):
            card_title("미국 의류 수입 국가별 비중 (%)")
            st.caption("※ OTEXA 데이터 (ETL 배치 작업을 통해 생성된 최신 파일을 불러옵니다.)")

            fig_share = go.Figure()
            colors_years = ['#1E3A8A', '#2563EB', '#60A5FA', '#93C5FD', '#BFDBFE', '#EFF6FF']
            years = df_share.columns[1:]

            for idx, year in enumerate(years):
                fig_share.add_trace(go.Bar(
                    x=df_share['Country'],
                    y=df_share[year],
                    name=str(year),
                    marker_color=colors_years[idx % len(colors_years)],
                    text=df_share[year].apply(lambda x: f"{x:.1f}%" if pd.notnull(x) else ""),
                    textposition='outside'
                ))

            fig_share.update_layout(
                barmode='group', plot_bgcolor='white', paper_bgcolor='white',
                height=400, margin=dict(t=20),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_share, width='stretch')

        st.write("")
        with st.container(border=True):
            card_title("미국 의류 수입 국가별 전년 동월대비 증감률(%)")

            df_yoy = df_yoy.set_index('Country')

            def style_country_bg(row):
                color_map = {
                    'World': 'background-color: #64748B; color: white; font-weight: bold;',
                    'China': 'background-color: #D97706; color: white; font-weight: bold;',
                    'Vietnam': 'background-color: #059669; color: white; font-weight: bold;',
                    'Indonesia': 'background-color: #2563EB; color: white; font-weight: bold;',
                    'Cambodia': 'background-color: #1E3A8A; color: white; font-weight: bold;',
                    'Nicaragua': 'background-color: #DC2626; color: white; font-weight: bold;',
                    'Guatemala': 'background-color: #0D9488; color: white; font-weight: bold;'
                }
                bg = color_map.get(row.name, '')
                return [bg] * len(row)

            styled_yoy = df_yoy.style.format("{:.1f}%", na_rep="-").apply(style_country_bg, axis=1)

            total_rows_tab2 = len(df_yoy)
            row_height = 35
            header_height = 50
            calculated_height_tab2 = (total_rows_tab2 * row_height) + header_height

            st.dataframe(styled_yoy, width='stretch', height=calculated_height_tab2)

    except Exception as e:
        st.error(f"OTEXA 데이터를 불러올 수 없습니다. 오류 내용: {e}")

# ==========================================
# [Tab 3] 글로벌 패션·유통 기업 모니터링
# ==========================================
with tab3:
    st.subheader("🏢 요청 기업 실시간 주가 및 정보 모니터링")

    @st.cache_data(ttl=600)
    def get_complete_company_data(ticker_symbol, selected_company, search_keyword):
        ticker = yf.Ticker(ticker_symbol)

        try:
            hist = ticker.history(period="1y")
        except Exception:
            hist = pd.DataFrame()

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

                    growth_df = raw_fin.pct_change(periods=1, axis=1) * 100
                    financials_df = growth_df.iloc[:, -4:]
        except Exception:
            pass

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

        if raw_news:
            for item in raw_news:
                title = item.get('title', '')
                link = item.get('link', '')
                publisher = item.get('publisher', 'Unknown Source')

                if title and link:
                    t_lower = title.lower()
                    if keyword_lower in t_lower or ticker_core in t_lower:
                        try:
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

        if valid_news_count < 5:
            try:
                import xml.etree.ElementTree as ET
                import urllib.request
                import urllib.parse

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

                            if not any(n['link'] == g_link for n in translated_news):
                                translated_news.append({"title": display_title, "orig_title": g_title, "link": g_link})
                                valid_news_count += 1

                    if valid_news_count >= 5:
                        break
            except Exception:
                pass

        return info_dict, hist, financials_df, translated_news

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
        info, hist, financials_df, final_news = get_complete_company_data(ticker_symbol, selected_company, search_keyword)

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

        st.markdown("### 📈 최근 1년 주가 추세")
        with st.container(border=True):
            if not hist.empty:
                fig_trend = go.Figure(go.Scatter(
                    x=hist.index, y=hist['Close'],
                    mode='lines', line=dict(color=PALETTE["blue"], width=2),
                    name='종가'
                ))
                fig_trend.update_layout(
                    plot_bgcolor='white', paper_bgcolor='white',
                    height=350,
                    margin=dict(l=50, r=40, t=20, b=30),
                    xaxis=dict(showgrid=True, gridcolor=PALETTE["grid"]),
                    yaxis=dict(showgrid=True, gridcolor=PALETTE["grid"], tickformat="," if currency != "USD" else ",.2f")
                )
                st.plotly_chart(fig_trend, width='stretch')
            else:
                st.info("주가 차트 데이터를 불러올 수 없습니다.")

        if not financials_df.empty:
            st.markdown("### 📊 최근 4개 분기 실적 증감률")
            with st.container(border=True):
                st.caption("※ 전분기 대비 (QoQ, %)")

                quarters = [str(col).split(' ')[0] for col in financials_df.columns]

                fig_fin = go.Figure()

                if '매출액' in financials_df.index:
                    fig_fin.add_trace(go.Bar(
                        x=quarters, y=financials_df.loc['매출액'],
                        name='매출 증감률', marker_color=PALETTE["blue_d"],
                        text=financials_df.loc['매출액'].apply(lambda x: f"{x:+.1f}%" if pd.notnull(x) else "-"),
                        textposition='outside'
                    ))
                if '영업이익' in financials_df.index:
                    fig_fin.add_trace(go.Bar(
                        x=quarters, y=financials_df.loc['영업이익'],
                        name='영업이익 증감률', marker_color=PALETTE["amber"],
                        text=financials_df.loc['영업이익'].apply(lambda x: f"{x:+.1f}%" if pd.notnull(x) else "-"),
                        textposition='outside'
                    ))

                fig_fin.update_layout(
                    barmode='group', plot_bgcolor='white', paper_bgcolor='white',
                    height=350,
                    margin=dict(l=50, r=40, t=30, b=30),
                    xaxis=dict(type='category'),
                    yaxis=dict(showgrid=True, gridcolor=PALETTE["grid"], title="증감률 (%)"),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_fin, width='stretch')
        else:
            st.info("최근 분기 실적 데이터를 공급하지 않거나 야후 금융 API 과부하로 차트가 일시 제한되었습니다.")

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
# [Tab 4] 거시경제 및 원가 지표
# ==========================================

@st.cache_data(ttl=3600)
def get_macro_data_complete_final():
    import pandas as pd
    import requests
    import yfinance as yf

    FRED_API_KEY = "7cbd5f701c3b7e514e3dfcb6810d2fb7"
    headers = {'User-Agent': 'Mozilla/5.0'}
    start_date = pd.Timestamp.today() - pd.DateOffset(years=5)

    yf_tickers = {"원/달러 환율": "KRW=X", "글로벌 면화(Cotton)": "CT=F", "WTI 국제 유가": "CL=F"}
    yf_data = {}
    for name, ticker in yf_tickers.items():
        try:
            yf_data[name] = yf.Ticker(ticker).history(period="1y")['Close']
        except Exception:
            yf_data[name] = pd.Series()

    fred_tickers = {
        "미국 실질 GDP": "GDPC1",
        "미국 의류 소비자물가지수(CPI)": "CPIAPPSL",
        "미국 의류 소매재고율": "MRTSIR448USS",
        "미국 기준금리": "FEDFUNDS",
        "한국 기준금리": "KORINTPA01STSAM",
        "미국 의류 소매판매액": "RSCCASN"
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
        except Exception:
            fred_data[name] = pd.Series()

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


with tab4:
    st.subheader("🌐 글로벌 거시경제 및 패션 원가 지표 모니터링")
    st.caption("환율, 금리, 원자재 및 미국 거시경제 지표를 실시간으로 가져옵니다.")

    try:
        yf_data, fred_data = get_macro_data_complete_final()

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 💱 원/달러 환율 (최근 1년)")
            with st.container(border=True):
                if not yf_data["원/달러 환율"].empty:
                    s = yf_data["원/달러 환율"]
                    f_val, l_val = s.iloc[0], s.iloc[-1]
                    chg = ((l_val - f_val) / f_val) * 100
                    st.write(f"🔹 시작: {f_val:,.1f}원 ➔ 최신: {l_val:,.1f}원 (증감률: **{chg:+.1f}%**)")

                    fig_krw = go.Figure(go.Scatter(x=s.index, y=s, line=dict(color=PALETTE["blue"], width=2)))
                    fig_krw.add_trace(go.Scatter(x=[s.index[0], s.index[-1]], y=[f_val, l_val], mode='markers+text', text=[f"{f_val:,.1f}", f"{l_val:,.1f}"], textposition=["top right", "top left"], marker=dict(size=8, color=PALETTE["blue"])))
                    fig_krw.update_layout(height=280, margin=dict(l=20, r=20, t=10, b=10), plot_bgcolor='white', paper_bgcolor='white', showlegend=False, xaxis=dict(showgrid=True, gridcolor=PALETTE["grid"]), yaxis=dict(showgrid=True, gridcolor=PALETTE["grid"]))
                    st.plotly_chart(fig_krw, width='stretch')
                else:
                    st.info("데이터를 불러올 수 없습니다.")

        with col2:
            st.markdown("#### 🏦 한·미 기준금리 추이 (최근 5년)")
            with st.container(border=True):
                us_s, kr_s = fred_data["미국 기준금리"], fred_data["한국 기준금리"]
                if not us_s.empty and not kr_s.empty:
                    f_us, l_us = us_s.iloc[0], us_s.iloc[-1]
                    f_kr, l_kr = kr_s.iloc[0], kr_s.iloc[-1]
                    st.write(f"🇺🇸 미국: {f_us:.2f}% ➔ {l_us:.2f}% ({l_us-f_us:+.2f}%p) | 🇰🇷 한국: {f_kr:.2f}% ➔ {l_kr:.2f}% ({l_kr-f_kr:+.2f}%p)")

                    fig_rate = go.Figure()
                    fig_rate.add_trace(go.Scatter(x=us_s.index, y=us_s, name='미국 (Fed)', line=dict(color=PALETTE["red"], width=2.5)))
                    fig_rate.add_trace(go.Scatter(x=kr_s.index, y=kr_s, name='한국 (BOK)', line=dict(color=PALETTE["blue"], width=2.5)))
                    fig_rate.add_trace(go.Scatter(x=[us_s.index[0], us_s.index[-1]], y=[f_us, l_us], mode='markers+text', text=[f"{f_us:.1f}%", f"{l_us:.1f}%"], textposition="top center", marker=dict(size=6, color=PALETTE["red"]), showlegend=False))
                    fig_rate.add_trace(go.Scatter(x=[kr_s.index[0], kr_s.index[-1]], y=[f_kr, l_kr], mode='markers+text', text=[f"{f_kr:.1f}%", f"{l_kr:.1f}%"], textposition="bottom center", marker=dict(size=6, color=PALETTE["blue"]), showlegend=False))
                    fig_rate.update_layout(height=280, margin=dict(l=20, r=20, t=10, b=10), plot_bgcolor='white', paper_bgcolor='white', showlegend=True, legend=dict(orientation="h", y=1.15), xaxis=dict(showgrid=True, gridcolor=PALETTE["grid"]), yaxis=dict(showgrid=True, gridcolor=PALETTE["grid"]))
                    st.plotly_chart(fig_rate, width='stretch')
                else:
                    st.info("데이터를 불러올 수 없습니다.")

        st.markdown("---")
        st.markdown("### 🛢️ 핵심 원자재 가격 동향 (최근 1년)")
        col3, col4 = st.columns(2)

        with col3:
            st.markdown("#### 🌱 국제 면화 선물 가격")
            with st.container(border=True):
                if not yf_data["글로벌 면화(Cotton)"].empty:
                    s = yf_data["글로벌 면화(Cotton)"]
                    f_val, l_val = s.iloc[0], s.iloc[-1]
                    chg = ((l_val - f_val) / f_val) * 100
                    st.write(f"🔹 시작: ${f_val:,.1f} ➔ 최신: ${l_val:,.1f} (증감률: **{chg:+.1f}%**)")

                    fig_ct = go.Figure(go.Scatter(x=s.index, y=s, line=dict(color=PALETTE["amber"], width=2)))
                    fig_ct.add_trace(go.Scatter(x=[s.index[0], s.index[-1]], y=[f_val, l_val], mode='markers+text', text=[f"${f_val:,.1f}", f"${l_val:,.1f}"], textposition=["top right", "top left"], marker=dict(size=8, color=PALETTE["amber"])))
                    fig_ct.update_layout(height=280, margin=dict(l=20, r=20, t=10, b=10), plot_bgcolor='white', paper_bgcolor='white', showlegend=False, xaxis=dict(showgrid=True, gridcolor=PALETTE["grid"]), yaxis=dict(showgrid=True, gridcolor=PALETTE["grid"]))
                    st.plotly_chart(fig_ct, width='stretch')
                else:
                    st.info("데이터를 불러올 수 없습니다.")

        with col4:
            st.markdown("#### ⚓ WTI 국제 유가")
            with st.container(border=True):
                if not yf_data["WTI 국제 유가"].empty:
                    s = yf_data["WTI 국제 유가"]
                    f_val, l_val = s.iloc[0], s.iloc[-1]
                    chg = ((l_val - f_val) / f_val) * 100
                    st.write(f"🔹 시작: ${f_val:,.1f} ➔ 최신: ${l_val:,.1f} (증감률: **{chg:+.1f}%**)")

                    fig_wti = go.Figure(go.Scatter(x=s.index, y=s, line=dict(color=PALETTE["blue_d"], width=2)))
                    fig_wti.add_trace(go.Scatter(x=[s.index[0], s.index[-1]], y=[f_val, l_val], mode='markers+text', text=[f"${f_val:,.1f}", f"${l_val:,.1f}"], textposition=["top right", "top left"], marker=dict(size=8, color=PALETTE["blue_d"])))
                    fig_wti.update_layout(height=280, margin=dict(l=20, r=20, t=10, b=10), plot_bgcolor='white', paper_bgcolor='white', showlegend=False, xaxis=dict(showgrid=True, gridcolor=PALETTE["grid"]), yaxis=dict(showgrid=True, gridcolor=PALETTE["grid"]))
                    st.plotly_chart(fig_wti, width='stretch')
                else:
                    st.info("데이터를 불러올 수 없습니다.")

        st.markdown("---")
        st.markdown("### 🦅 미국 거시경제 경기 지표 (최근 5년 트렌드)")
        col5, col6 = st.columns(2)

        with col5:
            st.markdown("#### 🏢 미국 실질 GDP (분기별)")
            with st.container(border=True):
                if not fred_data["미국 실질 GDP"].empty:
                    s = fred_data["미국 실질 GDP"]
                    f_val, l_val = s.iloc[0], s.iloc[-1]
                    chg = ((l_val - f_val) / f_val) * 100
                    st.write(f"🔹 시작: {f_val:,.0f} ➔ 최신: {l_val:,.0f} (증감률: **{chg:+.1f}%**)")

                    fig_gdp = go.Figure(go.Scatter(x=s.index, y=s, mode='lines+markers', line=dict(color="#7C3AED", width=2)))
                    fig_gdp.add_trace(go.Scatter(x=[s.index[0], s.index[-1]], y=[f_val, l_val], mode='markers+text', text=[f"{f_val:,.0f}", f"{l_val:,.0f}"], textposition=["top right", "top left"], marker=dict(size=8, color="#7C3AED")))
                    fig_gdp.update_layout(height=280, margin=dict(l=20, r=20, t=10, b=10), plot_bgcolor='white', paper_bgcolor='white', showlegend=False, xaxis=dict(showgrid=True, gridcolor=PALETTE["grid"]), yaxis=dict(showgrid=True, gridcolor=PALETTE["grid"]))
                    st.plotly_chart(fig_gdp, width='stretch')
                else:
                    st.info("데이터를 불러올 수 없습니다.")

        with col6:
            st.markdown("#### 👕 미국 의류 소비자물가지수(CPI)")
            with st.container(border=True):
                if not fred_data["미국 의류 소비자물가지수(CPI)"].empty:
                    s = fred_data["미국 의류 소비자물가지수(CPI)"]
                    f_val, l_val = s.iloc[0], s.iloc[-1]
                    chg = ((l_val - f_val) / f_val) * 100
                    st.write(f"🔹 시작: {f_val:,.1f} ➔ 최신: {l_val:,.1f} (증감률: **{chg:+.1f}%**)")

                    fig_cpi = go.Figure(go.Scatter(x=s.index, y=s, line=dict(color=PALETTE["amber"], width=2)))
                    fig_cpi.add_trace(go.Scatter(x=[s.index[0], s.index[-1]], y=[f_val, l_val], mode='markers+text', text=[f"{f_val:,.1f}", f"{l_val:,.1f}"], textposition=["top right", "top left"], marker=dict(size=8, color=PALETTE["amber"])))
                    fig_cpi.update_layout(height=280, margin=dict(l=20, r=20, t=10, b=10), plot_bgcolor='white', paper_bgcolor='white', showlegend=False, xaxis=dict(showgrid=True, gridcolor=PALETTE["grid"]), yaxis=dict(showgrid=True, gridcolor=PALETTE["grid"]))
                    st.plotly_chart(fig_cpi, width='stretch')
                else:
                    st.info("데이터를 불러올 수 없습니다.")

        st.markdown("---")
        st.markdown("### 📊 미국 의류 소매업 공급망 지표 (최근 5년 트렌드)")
        col7, col8 = st.columns(2)

        with col7:
            st.markdown("#### 📦 미국 의류 소매재고율 (Inventory-to-Sales)")
            with st.container(border=True):
                if not fred_data["미국 의류 소매재고율"].empty:
                    s = fred_data["미국 의류 소매재고율"]
                    f_val, l_val = s.iloc[0], s.iloc[-1]
                    chg = ((l_val - f_val) / f_val) * 100
                    st.write(f"🔹 시작: {f_val:.2f}개월 ➔ 최신: {l_val:.2f}개월 (증감률: **{chg:+.1f}%**)")

                    fig_inv = go.Figure(go.Scatter(x=s.index, y=s, fill='tozeroy', line=dict(color=PALETTE["green"], width=2)))
                    fig_inv.add_trace(go.Scatter(x=[s.index[0], s.index[-1]], y=[f_val, l_val], mode='markers+text', text=[f"{f_val:.2f}", f"{l_val:.2f}"], textposition=["top right", "top left"], marker=dict(size=8, color=PALETTE["green"])))
                    fig_inv.update_layout(height=280, margin=dict(l=20, r=20, t=10, b=10), plot_bgcolor='white', paper_bgcolor='white', showlegend=False, xaxis=dict(showgrid=True, gridcolor=PALETTE["grid"]), yaxis=dict(showgrid=True, gridcolor=PALETTE["grid"]))
                    st.plotly_chart(fig_inv, width='stretch')
                else:
                    st.info("데이터를 불러올 수 없습니다.")

        with col8:
            st.markdown("#### 🛍️ 미국 의류 소매 판매액 (의류 매장 매출 총액)")
            with st.container(border=True):
                if not fred_data["미국 의류 소매판매액"].empty:
                    s = fred_data["미국 의류 소매판매액"]
                    f_val, l_val = s.iloc[0], s.iloc[-1]
                    chg = ((l_val - f_val) / f_val) * 100
                    st.write(f"🔹 시작: ${f_val:,.0f}M ➔ 최신: ${l_val:,.0f}M (증감률: **{chg:+.1f}%**)")

                    fig_sales = go.Figure(go.Scatter(x=s.index, y=s, line=dict(color=PALETTE["red"], width=2)))
                    fig_sales.add_trace(go.Scatter(x=[s.index[0], s.index[-1]], y=[f_val, l_val], mode='markers+text', text=[f"${f_val:,.0f}M", f"${l_val:,.0f}M"], textposition=["top right", "top left"], marker=dict(size=8, color=PALETTE["red"])))
                    fig_sales.update_layout(height=280, margin=dict(l=20, r=20, t=10, b=10), plot_bgcolor='white', paper_bgcolor='white', showlegend=False, xaxis=dict(showgrid=True, gridcolor=PALETTE["grid"]), yaxis=dict(showgrid=True, gridcolor=PALETTE["grid"]))
                    st.plotly_chart(fig_sales, width='stretch')
                else:
                    st.info("데이터를 불러올 수 없습니다.")

    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")