from fastapi import APIRouter
import pandas as pd
import pymongo
import re
from datetime import datetime
from fastapi.responses import JSONResponse

price = APIRouter(prefix='/price')

# MongoDB 설정
conn = pymongo.MongoClient('mongodb://localhost:27017')
zipte = conn.zipte
zipte_price = zipte.price2

# 데이터프레임 생성
def load_data():
    df = pd.DataFrame.from_records(zipte_price.find())
    df = df.drop("_id", axis=1)

    df.columns[
        "거래_금액_(만원)",	
        "거래 일자",
        "아파트 이름",
        "전용 면적 (㎡)",
        "층",
        "location",
        "주소",
    ]

    df.drop("location",axis=1)

    df["전용_면적 (㎡)"] = df["전용_면적_(㎡)"].astype(float)
    df["층"] = df["층"].astype(int)
    df["거래_금액_(만원)"] = df["거래_금액_(만원)"].str.replace(",", "").astype(int)
    df["평당_가격_(만원)"] = df["거래_금액_(만원)"] / df["전용_면적_(㎡)"]
    df["평당_가격_(만원)"].fillna(0, inplace=True)

    return df

# 특정 동 가격 변화 시각화 (예시: 개포동)
@price.get("/change/{dong}",tags=['price'])
async def price_change(dong: str):
    df = load_data()
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

    return JSONResponse(content=monthly_avg.to_dict(orient="records"))

# 특정 동과 특정 평수 기준 가격 시각화
@price.get("/change/{dong}/{size}",tags=['price'])
async def price_change_size(dong: str, size: str):
    df = load_data()
    df['읍면동'] = df['주소'].apply(lambda address: re.search(r'\b(\w+동)\b', address).group(1) if re.search(r'\b(\w+동)\b', address) else None)
    df["거래_일자"] = pd.to_datetime(df["거래 일자"])

    # 면적 범주화
    bins = [0, 15, 25, 40, float('inf')]
    labels = ['15평_이하', '15~25평', '25~40평', '40평_초과']
    df['면적_범주'] = pd.cut(df['전용 면적 (㎡)'] / 3.3, bins=bins, labels=labels, right=False)
    

    # 거래 일자, 읍면동, 면적 범주 기준으로 평균 평당 가격 계산
    df_grouped = df.groupby(['거래_일자', '읍면동', '면적_범주'])['평당_가격_(만원)'].mean().reset_index()
    selected_data = df_grouped[(df_grouped["읍면동"] == dong) & (df_grouped["면적 범주"] == size)]

    # 월별 평균 계산
    selected_data['연월'] = selected_data['거래_일자'].dt.to_period('M')
    monthly_size_avg = selected_data.groupby(['연월', '면적_범주'])['평당_가격_(만원)'].mean().reset_index()

    # Period를 문자열로 변환
    monthly_size_avg['연월'] = monthly_size_avg['연월'].astype(str)

    return JSONResponse(content=monthly_size_avg.to_dict(orient="records"))