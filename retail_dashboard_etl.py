import pandas as pd
import requests
import io
import warnings

warnings.filterwarnings('ignore')

# 연준(FRED)의 고유 시리즈 코드와 대시보드에 쓰일 카테고리 이름 매핑
# (엑셀의 복잡한 이름 매칭이 필요 없이, 고유 코드로 정확히 1:1 매칭됩니다)
FRED_SERIES = {
    'RSAFS': 'Retail and food services sales, total',
    'RSFSXMV': 'Retail sales and food services excl motor vehicle and parts',
    'RSXFS': 'Retail Trade Total',
    'RSMVPD': 'Motor Vehicle and Parts Dealers',
    'RSFHFS': 'Furniture and Home Furnishings Stores',
    'RSEAS': 'Electronics and Appliance Stores',
    'RSBMGESD': 'Building Mat. and Garden Equip. and Supplies Dealers',
    'RSDBS': 'Food and Beverage Stores',
    'RSHPCS': 'Health and Personal Care Stores',
    'RSGASS': 'Gasoline Stations',
    'RSCCAS': 'Clothing and Clothing Access. Stores',
    'RSSGHBMS': 'Sporting Goods, Hobby, Musical Instrument, and Book Stores',
    'RSGMS': 'General Merchandise Stores',
    'RSMSR': 'Miscellaneous Store Retailers',
    'RSNSR': 'Nonstore Retailers'
}

def main():
    print("🌐 미국 연방준비은행(FRED) 데이터베이스에서 최신 속보치(Advance)를 다이렉트로 가져옵니다...")
    
    all_dfs = []
    # FRED는 방화벽이 관대해서 단순한 위장만으로도 100% 통과합니다.
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    for series_id, category_name in FRED_SERIES.items():
        print(f"🔄 [{category_name}] 데이터 호출 중...")
        # FRED의 CSV 다운로드 API (가장 빠르고 절대 막히지 않음)
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # 엑셀을 열고 자시고 할 필요 없이, 텍스트를 바로 데이터로 변환
            df = pd.read_csv(io.StringIO(response.text))
            
            # 다운받은 데이터의 컬럼은 ['DATE', 'RSAFS(값)'] 으로 되어 있음
            df.columns = ['Date', 'Sales']
            df['Category'] = category_name
            
            # 간혹 존재하는 에러값('.') 처리
            df['Sales'] = pd.to_numeric(df['Sales'], errors='coerce')
            df = df.dropna(subset=['Sales'])
            
            all_dfs.append(df)
            
        except Exception as e:
            print(f"❌ {category_name} 호출 에러: {e}")

    if not all_dfs:
        print("❌ 데이터를 하나도 가져오지 못했습니다.")
        return

    print("🚀 수집된 데이터를 대시보드 규격에 맞게 변환합니다...")
    
    # 15개 카테고리 하나로 합치기
    combined = pd.concat(all_dfs, ignore_index=True)
    combined['Date'] = pd.to_datetime(combined['Date'], errors='coerce')
    combined = combined.dropna(subset=['Date'])
    
    # 오프라인(Store) 계산을 위해 날짜/카테고리별로 가로 배치 (Pivot)
    pivot_df = combined.pivot_table(index='Date', columns='Category', values='Sales', aggfunc='sum')
    
    # Store(Offline) = Total - Nonstore 수식 계산
    if 'Retail Trade Total' in pivot_df.columns and 'Nonstore Retailers' in pivot_df.columns:
        pivot_df['Store(Offline)'] = pivot_df['Retail Trade Total'] - pivot_df['Nonstore Retailers']
    
    # 대시보드에서 인식할 수 있도록 다시 세로형(Melt) 포맷으로 복구
    final_df = pivot_df.reset_index().melt(id_vars='Date', var_name='Category', value_name='Sales')
    final_df = final_df.dropna(subset=['Sales'])
    
    # 10년 치 필터링 (FRED는 1992년부터 수십 년 치를 주기 때문에 최근 10년만 자름)
    max_date = final_df['Date'].max()
    cutoff = max_date - pd.DateOffset(years=10)
    final_df = final_df[final_df['Date'] >= cutoff]
    
    # 정렬 및 날짜 텍스트 변환
    final_df = final_df.sort_values(['Date', 'Category'], ascending=[False, True])
    final_df['Date'] = final_df['Date'].dt.strftime('%Y-%m-%d')
    
    # 저장
    final_df.to_csv("retail_output.csv", index=False)
    
    print(f"🎉 연준(FRED) 데이터 수집 완료! 가장 최신 월: {max_date.strftime('%Y-%m')}")
    print(f"💾 저장 완료: {len(final_df)}행 -> retail_output.csv")

if __name__ == "__main__":
    main()