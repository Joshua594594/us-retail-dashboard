import pandas as pd

def main():
    print("🌐 OTEXA 수입 데이터 처리를 시작합니다...")
    
    try:
        # 다운로드 받은 otexa.csv 파일 읽기
        df = pd.read_csv('otexa.csv')
    except Exception as e:
        print("❌ otexa.csv 파일을 찾을 수 없습니다. 같은 폴더에 있는지 확인해주세요.")
        return

    # 날짜(Date) 통합 컬럼 생성
    df['Date'] = pd.to_datetime(df['Year'].astype(str) + '-' + df['Month'].astype(str) + '-01')
    
    # 데이터셋의 가장 최신 날짜 파악 (자동 네이밍용)
    max_date = df['Date'].max()
    max_yr = max_date.year
    max_mo = max_date.month
    month_abbr = max_date.strftime('%b') # 1, 2, 3월을 Jan, Feb, Mar로 변환
    
    print(f"✅ 데이터 스캔 완료: 최신 데이터는 {max_yr}년 {max_mo}월({month_abbr}) 입니다.")

    # ========================================================
    # 1. 국가별 수입 비중 (Market Share) 계산
    # ========================================================
    share_countries = ['China', 'Vietnam', 'Indonesia', 'Cambodia', 'Nicaragua', 'Guatemala']
    df_share = df[df['Country'].isin(share_countries + ['World'])].copy()
    
    # 연도별/국가별 수입액(Value) 합계 계산
    yearly_val = df_share.groupby(['Year', 'Country'])['Value'].sum().unstack()
    
    # % 계산 (각 국가 수입액 / World 수입액)
    for c in share_countries:
        yearly_val[c] = (yearly_val[c] / yearly_val['World']) * 100
        
    yearly_share = yearly_val[share_countries].T.reset_index()
    yearly_share.columns.name = None # 거슬리는 인덱스 이름 제거
    
    # 2026년 컬럼을 '2026 (Jan-Mar)' 형태로 알아서 예쁘게 변경
    yearly_share = yearly_share.rename(columns={max_yr: f"{max_yr} (Jan-{month_abbr})"})
    yearly_share.to_csv('otexa_share.csv', index=False)
    print("💾 저장 완료: otexa_share.csv (비중 데이터 추출 완료)")

    # ========================================================
    # 2. 국가별 전년 동월대비 증감률 (YoY) 계산
    # ========================================================
    yoy_countries = ['World', 'China', 'Vietnam', 'Indonesia', 'Cambodia', 'Nicaragua', 'Guatemala', 'Bangladesh', 'India', 'Jordan', 'El Salvador', 'Egypt']
    df_yoy = df[df['Country'].isin(yoy_countries)].copy()
    
    pivot_yoy = df_yoy.pivot_table(index='Date', columns='Country', values='Value', aggfunc='sum')
    
    # 'Others' (기타 국가) 계산: World - (우리가 지정한 주요 국가들의 합)
    specified_countries = [c for c in yoy_countries if c != 'World']
    pivot_yoy['Others'] = pivot_yoy['World'] - pivot_yoy[specified_countries].sum(axis=1)
    
    # 표에 나올 국가 순서를 이미지와 동일하게 정렬
    yoy_countries_final = ['World', 'China', 'Vietnam', 'Indonesia', 'Cambodia', 'Nicaragua', 'Guatemala', 'Bangladesh', 'India', 'Jordan', 'El Salvador', 'Egypt', 'Others']
    pivot_yoy = pivot_yoy[yoy_countries_final]
    
    # 12개월 전 대비 증감률(%) 계산 후 최근 12개월만 자르기
    pct_yoy = pivot_yoy.pct_change(periods=12) * 100
    pct_yoy_tail = pct_yoy.tail(12).T.reset_index()
    pct_yoy_tail.columns.name = None
    
    # 표의 맨 위 날짜 컬럼을 "'25 / 3" 형태로 예쁘게 변경
    new_cols = []
    for c in pct_yoy_tail.columns:
        if isinstance(c, str):
            new_cols.append(c)
        else:
            new_cols.append(f"'{str(c.year)[-2:]} / {c.month}")
            
    pct_yoy_tail.columns = new_cols
    pct_yoy_tail.to_csv('otexa_yoy.csv', index=False)
    print("💾 저장 완료: otexa_yoy.csv (YoY 증감률 데이터 추출 완료)")
    print("🎉 OTEXA ETL 프로세스가 완벽하게 끝났습니다!")

if __name__ == "__main__":
    main()