import pandas as pd
import numpy as np
from typing import List
from pymongo import MongoClient
from fastapi import FastAPI, Query, HTTPException,APIRouter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder
import scipy.sparse as sp

# APT라우터 설정
properties = APIRouter(prefix='/apt')

# MongoDB 클라이언트 연결
client = MongoClient("mongodb://localhost:27017")
db = client["zipte"]
collection = db["db2"]

# 데이터 로드 함수
def load_data() -> pd.DataFrame:
    """MongoDB에서 데이터를 로드하여 DataFrame으로 반환."""
    data = pd.DataFrame.from_records(collection.find())
    return data

# 데이터 컬럼명 전처리 함수
def preprocess_data(data: pd.DataFrame) -> pd.DataFrame:
    """데이터 전처리 및 결합된 텍스트 생성."""
    # 컬럼 한글 이름으로 변경
    data.columns = [
    '_id',
    '단지코드',
    '평균평당가격',
    '주소',
    '135_세대수',
    '136_세대수',
    '60_세대수',
    '85_세대수',
    '단지명',
    '좌표',
    '편의시설', 
    '교육시설',
    '지상_주차공간_수',
    '지하_주차공간_수',    
    '버스시간', 
    '지하철시간', 
    '지하철노선', 
    '지하철역', 
    '복지시설']

    return data

# 시설 특징 TF-IDF 처리
def calculate_amenties(data: pd.DataFrame) -> pd.DataFrame:
    data["교육시설"] = data["교육시설"].fillna("교육시설_없음")
    data["편의시설"] = data["편의시설"].fillna("편의시설_없음")
    data["복지시설"] = data["복지시설"].fillna("복지시설_없음")

    # TF-IDF를 위한 텍스트 합치기
    data['시설_통합'] = data['교육시설'] + ' ' + data['편의시설'] + ' ' + data['복지시설']

    # 기존 컬럼 제거
    data = data.drop(columns=["_id","교육시설", "편의시설", "복지시설"])
    return data

# 주차장 수 합치기
def calculate_parking_lot(data: pd.DataFrame) -> pd.DataFrame:
    for col in ['지상_주차공간_수', '지하_주차공간_수']:
        data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0).astype(int)

    
    data["60_세대수"] = data["60_세대수"].fillna(0).astype(int)
    data["85_세대수"] = data["85_세대수"].fillna(0).astype(int)
    data["135_세대수"] = data["135_세대수"].fillna(0).astype(int)
    data["136_세대수"] = data["136_세대수"].fillna(0).astype(int)

    data["주차공간"] = data["지상_주차공간_수"] + data["지하_주차공간_수"]
    data["총_세대수"] = data["60_세대수"] + data["85_세대수"] + data["135_세대수"] + data["136_세대수"]

    # 기존 컬럼 제거
    data = data.drop(columns=["지상_주차공간_수", "지하_주차공간_수","60_세대수","85_세대수","135_세대수","136_세대수"])
    return data

# 교통 시간 변환 및 정규화
def transform_transport_time(data: pd.DataFrame) -> pd.DataFrame:
    time_mapping = {
        '5분이내': 2.5,
        '5~10분이내': 7.5,
        '10~15분이내': 12.5,
        '15~20분이내': 17.5,
        np.nan: np.nan
    }
    data["지하철시간_정규화"] = data["지하철시간"].map(time_mapping)
    data["버스시간_정규화"] = data["버스시간"].map(time_mapping)

    data = data.drop(columns=["버스시간", "지하철시간"])
    return data



# 유사도 계산 함수
def calculate_similarity(data: pd.DataFrame, target_idx: int) -> List[float]:
    """TF-IDF를 기반으로 코사인 유사도를 계산."""
    tfidf = TfidfVectorizer()
    tfidf_matrix = tfidf.fit_transform(data["시설_통합"])

    cosine_matrix = cosine_similarity(tfidf_matrix)
    return cosine_matrix[target_idx]

# 결합된 특징 벡터 생성 함수
def add_all_features(data: pd.DataFrame, tfidf_matrix) -> sp.csr_matrix:
    scaler = MinMaxScaler()
    numeric_features = ['총_세대수','평균평당가격' ,'주차공간', '지하철시간_정규화', '버스시간_정규화']
    data[numeric_features] = scaler.fit_transform(data[numeric_features])

    encoder = OneHotEncoder()
    subway_features = encoder.fit_transform(data[['지하철노선', '지하철역']])

    # TF-IDF + Numeric Features + Encoded Subway Features
    combined_features = sp.hstack([tfidf_matrix, data[numeric_features], subway_features])
    return combined_features


# 추천결과 말하기
def print_recommendations(apartment_name: str, data: pd.DataFrame, top_n: int) -> dict:
    # 아파트명으로 인덱스 찾기
    if apartment_name not in data['단지명'].values:
        raise HTTPException(status_code=404, detail="해당 아파트를 찾을 수 없습니다.")

    target_idx = data[data['단지명'] == apartment_name].index[0]

    # 유사도 계산
    similarities = calculate_similarity(data, target_idx)

    # 유사도 높은 순서로 정렬
    recommendations = sorted(list(enumerate(similarities)), key=lambda x: x[1], reverse=True)

    # 상위 추천 아파트 추출 (자신 제외)
    recommended_apartments_with_scores = [
        (data.iloc[idx], score) for idx, score in recommendations[1:top_n + 1]
    ]

    # 반환용 추천 아파트 리스트 생성
    recommended_apartments = [
        {"단지명": row['단지명'], "주소": row.get('주소', '주소 정보 없음')} 
        for row, _ in recommended_apartments_with_scores
    ]

    return {"추천 아파트": recommended_apartments}



# 추천 엔드포인트 정의
@properties.get("/",tags=['properties'])
def get_recommendations(
    apartment_name: str,
    top_n: int = Query(5, ge=1, le=10)
):
    """주어진 아파트명을 기준으로 추천 목록을 반환."""
    # 데이터 로드 및 전처리
    data = load_data()
    data = preprocess_data(data)
    data = calculate_amenties(data)
    data = calculate_parking_lot(data)
    data = transform_transport_time(data)

    # 추천 계산
    try:
        recommendations = print_recommendations(apartment_name, data, top_n)
    except HTTPException as e:
        raise e

    return recommendations
