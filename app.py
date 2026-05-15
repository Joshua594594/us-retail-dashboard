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
        
        # 💡 [요청사항 1] 원하는 순서대로 강제 정렬 (오타 방지를 위해 부분 일치 검색 포함)
        custom_order_keywords = [
            "Retail Trade Total",
            "Nonstore Retailers",
            "Sporting Goods",
            "General Merchandise",
            "Furniture",
            "Electronics",
            "Clothing",
            "Motor Vehicle",
            "Building",
            "Food and Beverage",
            "Health",
            "Gasoline",
            "Miscellaneous",
            "Offline" # Store(Offline)
        ]
        
        # 실제 데이터프레임의 카테고리명과 매칭하여 정렬 리스트 생성
        ordered_categories = []
        for keyword in custom_order_keywords:
            for cat in ytd_growth['Category'].unique():
                if keyword.lower() in cat.lower() and cat not in ordered_categories:
                    ordered_categories.append(cat)
                    
        # 나머지 카테고리가 있다면 맨 밑에 추가
        for cat in ytd_growth['Category'].unique():
            if cat not in ordered_categories:
                ordered_categories.append(cat)

        # 데이터프레임 정렬 적용 (Plotly는 아래서부터 위로 그리므로 순서를 뒤집어줌)
        ytd_growth['Category'] = pd.Categorical(ytd_growth['Category'], categories=ordered_categories, ordered=True)
        ytd_growth = ytd_growth.sort_values('Category', ascending=False)
        
        # 기본 막대 색상 설정 (양수 파랑, 음수 빨강)
        colors = ['#CC0000' if val < 0 else '#0070C0' for val in ytd_growth['Growth']]
        
        # 💡 [요청사항 2] Clothing 카테고리에만 '빨간색 박스(테두리)' 칠하기
        line_colors = ['red' if 'Clothing' in cat else 'rgba(0,0,0,0)' for cat in ytd_growth['Category']]
        line_widths = [3 if 'Clothing' in cat else 0 for cat in ytd_growth['Category']]
        
        fig = go.Figure(go.Bar(
            x=ytd_growth['Growth'],
            y=ytd_growth['Category'],
            orientation='h',
            text=ytd_growth['Growth'].apply(lambda x: f"{x:.1f}%"),
            textposition='outside',
            marker_color=colors,
            marker_line_color=line_colors, # 테두리 색상
            marker_line_width=line_widths  # 테두리 두께
        ))
        
        fig.update_layout(
            plot_bgcolor='white', 
            height=600, 
            margin=dict(l=0, r=0, t=30, b=0),
            yaxis=dict(categoryorder='array', categoryarray=ordered_categories[::-1])
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("📋 미국 소매 카테고리 별 전년 동월대비 증감률(%)")
        
        df_pivot = df.pivot(index='Date', columns='Category', values='Sales')
        yoy_df = df_pivot.pct_change(periods=12) * 100
        table_df = yoy_df.tail(12).T
        
        # 💡 [요청사항 1] 표(Table)에도 동일한 커스텀 순서 적용
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