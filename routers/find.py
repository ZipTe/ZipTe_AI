from fastapi import APIRouter, HTTPException
import pymongo

find = APIRouter(prefix='/find')

# MongoDB 설정
conn = pymongo.MongoClient('mongodb://localhost:27017')
zipte = conn.zipte
zipte_db = zipte.db2

# 찾기
@find.get("/", tags=['find'])
def get_one(kaptName: str):
    # MongoDB에서 데이터 검색
    result = zipte_db.find_one({"kaptName": kaptName})
    
    if not result:  # 데이터가 없을 경우 예외 처리
        raise HTTPException(status_code=404, detail="Data not found")
    
    # '_id' 필드 제거
    result.pop("_id", None)
    
    return result
