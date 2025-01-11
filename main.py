from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from routers.properties import properties
from routers.price import price
from routers.find import find
from routers.aptprice import aptprice
import uvicorn

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # 허용할 도메인
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
 # 비슷한 아파트 추천 라우터 등록
app.include_router(properties) 
# price 라우터 등록
app.include_router(price)
# find 라우터 등록
app.include_router(find)
# aptprice 라우터 등록
app.include_router(aptprice)


@app.get("/")
def home():
    return {"msg": "Main router is working!"}

# FastAPI 실행 (로컬 개발용)
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)