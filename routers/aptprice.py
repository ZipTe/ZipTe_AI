from fastapi import FastAPI, APIRouter, HTTPException, Query
from typing import Optional
import pandas as pd
import pymongo
from datetime import datetime
from fastapi.responses import JSONResponse

aptprice = APIRouter(prefix="/price", tags=["price"])

# MongoDB 설정
conn = pymongo.MongoClient('mongodb://localhost:27017')
zipte = conn.zipte
zipte_price = zipte.price2
zipte_db = zipte.db2

# 비어 있는 값과 음수 값 처리
def clean_floor(value):
    value = str(value).strip()  # 공백 제거
    if value.isdigit() and int(value) > 0:  # 양수만 허용
        return int(value)
    else:
        return pd.NA  # 변환 불가능한 값은 NaN으로 대체

def preprocessing_price(price_df:pd.DataFrame)-> pd.DataFrame:
    price_df = price_df.drop("_id", axis=1)

    # 문자열을 float로 변환
    price_df["전용 면적 (㎡)"] = price_df["전용 면적 (㎡)"].astype(float)  

    # '층' 열 전처리
    price_df["층"] = price_df["층"].apply(clean_floor)

    # NaN 값 처리 (필요에 따라 0으로 채우거나 제거)
    price_df["층"] = price_df["층"].fillna(0).astype(int)  # NaN을 0으로 대체

    # 문자열에서 쉼표 제거 후 int로 변환
    price_df["거래 금액 (만원)"] = price_df["거래 금액 (만원)"].str.replace(",", "").astype(int)
    
    return price_df

def preprocessing_db(db_df:pd.DataFrame)-> pd.DataFrame:
    db_df = db_df.drop("_id", axis=1)
    
    db_df.columns = [
        '단지코드', '평균평당가격', '주소정보', '135 세대수', '136 세대수', '60 세대수', '85 세대수',
        '단지명', '좌표', '편의시설', '교육시설', '지상_주차공간_수', '지하_주차공간_수',
        '버스시간', '지하철시간', '지하철노선', '지하철역', '복지시설'
    ]

    db_df = db_df[["단지코드",'주소정보','평균평당가격','단지명','좌표']]
    return db_df
# 데이터 불러오기
def load_data():
    price_df = pd.DataFrame.from_records(zipte_price.find())
    db_df = pd.DataFrame.from_records(zipte_db.find())

    # 데이터 전처리
    price_df = preprocessing_price(price_df)
    db_df= preprocessing_db(db_df)

    # 좌표 데이터 병합
    price_df['coordinates'] = price_df['location'].apply(lambda x: tuple(x['coordinates']))
    db_df['coordinates'] = db_df['좌표'].apply(lambda x: tuple(x['coordinates']))

    merged_df = pd.merge(price_df, db_df, on="coordinates", how="inner")
    
    final_df = merged_df[["단지코드", "단지명", "거래 일자", "주소정보", "전용 면적 (㎡)", "층", "거래 금액 (만원)"]]
    return final_df

@aptprice.get("/apt")
def get_average_price(apt_name: str, size: float, year:int):

    df= load_data()

    # 두 가지 조건을 동시에
    specific_data = df[(df["단지명"] == apt_name) & (df["전용 면적 (㎡)"] == size)]
    print(specific_data)
    
     # 현재 연도 계산
    current_year = datetime.now().year

    # 기준 연도 계산
    target_year = current_year - year

    # '거래 일자' 컬럼을 문자열로 변환
    specific_data['거래 일자'] = specific_data['거래 일자'].astype(str)

    # 기준 연도 이후의 데이터 필터링
    filtered_months = specific_data[specific_data['거래 일자'].str[:4].astype(int) >= target_year]

    # 거래 일자 순서대로 정렬
    sorted_data = filtered_months.sort_values(by='거래 일자')

    # 결과 출력
    return JSONResponse(content=sorted_data.to_dict(orient="records"))
