# env_loader.py
from dotenv import load_dotenv
import os
from log_util import logger

def load_naver_credentials():
    load_dotenv()
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")

    if not client_id or not client_secret:
        logger.log(">>> .env에서 NAVER_CLIENT_ID 또는 NAVER_CLIENT_SECRET 누락")
        raise ValueError("❌ .env 파일에 NAVER_CLIENT_ID 또는 NAVER_CLIENT_SECRET가 누락됨")
    
    logger.log(">>>>>> .env에서 NAVER API 인증 정보 로드 성공")
    return client_id, client_secret
