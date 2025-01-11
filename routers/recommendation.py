import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import OneHotEncoder
import joblib

# === 데이터 전처리 및 모델 학습 ===
def train_base_model(df):
    # 데이터 전처리 (결측치 채우기 및 원핫 인코딩 등)
    df['지하철시간_정규화'] = df['지하철시간_정규화'].fillna(20)
    df['버스시간_정규화'] = df['버스시간_정규화'].fillna(20)
    df['복지시설'] = df['복지시설'].fillna('없음')

    encoder = OneHotEncoder(sparse=False)
    encoded_location = encoder.fit_transform(df[['시군구']])
    encoded_location_df = pd.DataFrame(encoded_location, columns=encoder.get_feature_names_out(['시군구']))
    df = pd.concat([df, encoded_location_df], axis=1)

    # 기본 가중치를 사용해 타겟 점수 생성
    default_weights = {
        '편의시설': 0.2, '복지': 0.3, '교육': 0.3, '지하철': 1, '버스': 2, '시군구': 20, '가격': 10, '면적': 10
    }

    # 타겟 점수 계산
    df['target_score'] = df.apply(
        lambda row: (
            row['편의시설_개수'] * default_weights['편의시설'] +
            row['복지시설_개수'] * default_weights['복지'] +
            row['교육시설_개수'] * default_weights['교육'] +
            row['지하철시간_정규화'] * default_weights['지하철'] +
            row['버스시간_정규화'] * default_weights['버스']
        ),
        axis=1
    )

    # 모델 학습
    X = df.drop(columns=['target_score', '거래 일자', 'coordinates', '편의시설', '교육시설', '복지시설', 
                         '지하철노선', '지하철역', '단지코드', '시군구', '단지명'])
    y = df['target_score']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = xgb.XGBRegressor(objective='reg:squarederror', n_estimators=100, max_depth=7, learning_rate=0.05)
    model.fit(X_train, y_train)

    # 모델 저장
    joblib.dump(model, 'base_model.pkl')

    # 테스트 평가
    y_pred = model.predict(X_test)
    rmse = mean_squared_error(y_test, y_pred, squared=False)
    print(f"Base Model RMSE: {rmse}")
    return model

# === 점수 계산 함수 ===
def calculate_similarity(row, user_input):
    location_similarity = 1 if row['시군구'] == user_input['시군구'] else 0
    price_diff = abs(row['거래 금액 (만원)'] - user_input['목표 금액'])
    price_similarity = max(0, 1 - (price_diff / user_input['가격 허용치']))
    area_diff = abs(row['전용 면적 (㎡)'] - user_input['목표 면적'])
    area_similarity = max(0, 1 - (area_diff / user_input['면적 허용치']))
    return location_similarity, price_similarity, area_similarity

def calculate_custom_score(row, weights, user_input):
    location_similarity, price_similarity, area_similarity = calculate_similarity(row, user_input)
    score = (
        row['편의시설_개수'] * weights['편의시설'] +
        row['복지시설_개수'] * weights['복지'] +
        row['교육시설_개수'] * weights['교육'] +
        row['지하철시간_정규화'] * weights['지하철'] +
        row['버스시간_정규화'] * weights['버스'] +
        location_similarity * weights['시군구'] +
        price_similarity * weights['가격'] +
        area_similarity * weights['면적']
    )
    return score

# === 예측 및 사용자 조건 반영 ===
def predict_with_custom_weights(df, model_path, user_input, weights, top_n=10):
    # 사전 학습된 모델 로드
    model = joblib.load(model_path)

    # 원본 데이터에서 예측
    X = df.drop(columns=['target_score', '거래 일자', 'coordinates', '편의시설', '교육시설', '복지시설', 
                         '지하철노선', '지하철역', '단지코드', '시군구', '단지명'])
    df['base_score'] = model.predict(X)

    # 사용자 조건에 따라 점수 조정
    df['adjusted_score'] = df.apply(
        lambda row: (
            row['base_score'] +
            row['편의시설_개수'] * weights['편의시설'] +
            row['복지시설_개수'] * weights['복지'] +
            row['교육시설_개수'] * weights['교육'] +
            row['지하철시간_정규화'] * weights['지하철'] +
            row['버스시간_정규화'] * weights['버스']
        ),
        axis=1
    )

    # 상위 N개의 추천 목록
    recommended = df.sort_values(by='adjusted_score', ascending=False).head(top_n)
    return recommended

# === 실행 예시 ===
if __name__ == "__main__":
    # 데이터 로드 (예시 데이터)
    data = {
        '거래 금액 (만원)': [80000, 85000, 70000, 90000],
        '전용 면적 (㎡)': [85, 90, 80, 95],
        '편의시설_개수': [5, 3, 4, 2],
        '복지시설_개수': [2, 3, 1, 4],
        '교육시설_개수': [3, 2, 4, 5],
        '지하철시간_정규화': [15, 20, 25, 10],
        '버스시간_정규화': [20, 15, 30, 25],
        '시군구': ['성남분당구', '서울강남구', '성남분당구', '서울송파구'],
    }
    df = pd.DataFrame(data)

    # 모델 학습
    model = train_base_model(df)

    # 사용자 조건 변경 후 예측
    user_input = {
        '편의시설': 4,
        '지하철': 4,
        '버스': 3,
        '복지': 4,
        '교육': 4,
        '시군구': '서울강남구',
        '공원': False,
        '목표 금액': 100000,
        '목표 면적': 90,
        '가격 허용치': 5000,
        '면적 허용치': 15
    }

    new_weights = {
        '편의시설': 0.3,
        '복지': 0.25,
        '교육': 0.25,
        '지하철': 1.2,
        '버스': 1.8,
        '시군구': 25,
        '가격': 12,
        '면적': 12
    }

    # 추천 결과 생성
    recommended_apartments = predict_with_custom_weights(df, 'base_model.pkl', user_input, new_weights, top_n=5)

    # 결과 출력
    print(recommended_apartments[['거래 금액 (만원)', '전용 면적 (㎡)', '시군구', 'adjusted_score']])