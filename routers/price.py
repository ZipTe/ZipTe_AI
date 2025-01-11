from fastapi import APIRouter, Query
import pandas as pd
import pymongo
import re
from datetime import datetime
from fastapi.responses import JSONResponse

# 법정동별 가격 가져오기

price = APIRouter(prefix='/price')

# MongoDB 설정
conn = pymongo.MongoClient('mongodb://localhost:27017')
zipte = conn.zipte
zipte_price = zipte.price2

# 비어 있는 값과 음수 값 처리
def clean_floor(value):
    value = str(value).strip()  # 공백 제거
    if value.isdigit() and int(value) > 0:  # 양수만 허용
        return int(value)
    else:
        return pd.NA  # 변환 불가능한 값은 NaN으로 대체

def load_data():
    df = pd.DataFrame.from_records(zipte_price.find())
    df = df.drop("_id", axis=1)

    # 열 이름 설정
    df.columns = [
        "거래_금액_(만원)",    
        "거래_일자",
        "아파트_이름",
        "전용_면적_(㎡)",
        "층",
        "location",
        "주소",
    ]

    # 필요 없는 열 제거
    df = df.drop("location", axis=1)

    # 데이터 타입 변환
    df["전용_면적_(㎡)"] = df["전용_면적_(㎡)"].astype(float)

    # '층' 열 전처리
    df["층"] = df["층"].apply(clean_floor)

    # NaN 값 처리 (필요에 따라 0으로 채우거나 제거)
    df["층"] = df["층"].fillna(0).astype(int)  # NaN을 0으로 대체

    df["거래_금액_(만원)"] = df["거래_금액_(만원)"].str.replace(",", "").astype(int)

    # 평당 가격 계산
    df["평당_가격_(만원)"] = df["거래_금액_(만원)"] / (df["전용_면적_(㎡)"] / 3.3)

    # NaN과 Infinity 값 처리
    df["평당_가격_(만원)"].replace([float('inf'), -float('inf')], None, inplace=True)
    df["평당_가격_(만원)"].fillna(0, inplace=True)

    return df

@price.get("/change", tags=['price'])
async def price_change(dong: str = Query(..., description="법정동 이름"), year: int = Query(..., description="몇개년")):
    df = load_data()

    # 읍면동 추출
    df['읍면동'] = df['주소'].apply(lambda address: re.search(r'\b(\w+동)\b', address).group(1) if re.search(r'\b(\w+동)\b', address) else None)
    df["거래_일자"] = pd.to_datetime(df["거래_일자"])

    # 거래 일자와 읍면동 기준으로 평균 평당 가격 계산
    df_grouped = df.groupby(["거래_일자", "읍면동"])["평당_가격_(만원)"].mean().reset_index()
    selected_data = df_grouped[df_grouped["읍면동"] == dong]

    # 월별 평균 계산
    selected_data['월'] = selected_data['거래_일자'].dt.to_period('M')
    monthly_avg = selected_data.groupby('월')['평당_가격_(만원)'].mean().reset_index()

    # Period를 문자열로 변환
    monthly_avg['월'] = monthly_avg['월'].astype(str)

    # 현재 연도 계산
    current_year = datetime.now().year

    # 기준 연도 계산
    target_year = current_year - year

    # 기준 연도 이후의 데이터 필터링
    filtered_months = monthly_avg[monthly_avg['월'].str[:4].astype(int) >= target_year]

    # 열 이름 변경
    filtered_months.columns = ["거래 일자", "평당 가격 (만원)"]

    # 결과 반환
    return JSONResponse(content=filtered_months.to_dict(orient="records"))

@price.get("/change/size", tags=['price'])
async def price_change_size(dong: str = Query(..., description="법정동 이름"), size: str = Query(..., description="면적 범주"), year: int = Query(..., description="몇개년")):
    df = load_data()

    # 읍면동 추출
    df['읍면동'] = df['주소'].apply(lambda address: re.search(r'\b(\w+동)\b', address).group(1) if re.search(r'\b(\w+동)\b', address) else None)
    df["거래_일자"] = pd.to_datetime(df["거래_일자"])

    # 면적 범주화
    bins = [0, 15, 25, 40, float('inf')]
    labels = ['15평_이하', '15~25평', '25~40평', '40평_초과']
    df['면적_범주'] = pd.cut(df['전용_면적_(㎡)'] / 3.3, bins=bins, labels=labels, right=False)
    # 면적 범주를 문자열로 변환 후 필터링
    df['면적_범주'] = df['면적_범주'].astype(str)

    # 거래 일자, 읍면동, 면적 범주 기준으로 평균 평당 가격 계산
    df_grouped = df.groupby(['거래_일자', '읍면동', '면적_범주'])['평당_가격_(만원)'].mean().reset_index()
    selected_data = df_grouped[(df_grouped["읍면동"] == dong) & (df_grouped["면적_범주"] == size)]

    # 월별 평균 계산
    selected_data['연월'] = selected_data['거래_일자'].dt.to_period('M')
    monthly_size_avg = selected_data.groupby(['연월', '면적_범주'])['평당_가격_(만원)'].mean().reset_index()

    # Period를 문자열로 변환
    monthly_size_avg['연월'] = monthly_size_avg['연월'].astype(str)

    # NaN, inf 값 처리
    monthly_size_avg.replace([float('inf'), -float('inf')], None, inplace=True)
    monthly_size_avg.fillna(0, inplace=True)

    # 현재 연도 계산
    current_year = datetime.now().year

    # 기준 연도 계산
    target_year = current_year - year

    # 기준 연도 이후의 데이터 필터링
    filtered_months = monthly_size_avg[monthly_size_avg['연월'].str[:4].astype(int) >= target_year]

    # 열 이름 변경
    filtered_months.columns = ["거래 일자", "면적 범주", "평당 가격 (만원)"]

    # 결과 반환
    return JSONResponse(content=filtered_months.to_dict(orient="records"))
