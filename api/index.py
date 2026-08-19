from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 파이썬 백엔드 앱 생성
app = FastAPI()

# Vercel 환경에서 화면과 데이터가 잘 통신하도록 허용(CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 데이터 요청이 들어오면 응답할 내용
@app.get("/api/hello")
def read_root():
    return {
        "status": "success",
        "message": "파이썬 백엔드 서버가 24시간 정상 작동 중입니다! 🚀"
    }