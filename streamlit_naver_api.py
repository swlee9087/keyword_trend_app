# streamlit_naver_api.py

import requests
import pandas as pd
import streamlit as st
import json
import math
from datetime import datetime, timedelta
from env_loader import load_naver_credentials
from log_util import logger

def chunk_keywords(keywords, chunk_size=5, group_size=20):
    """키워드 리스트를 Naver API에 맞게 그룹별로 나누기"""
    chunks = []
    for i in range(0, len(keywords), group_size):
        group_keywords = keywords[i:i+group_size]
        group_name = group_keywords[0]
        chunks.append({"groupName": group_name, "keywords": group_keywords})
    return [chunks[i:i+chunk_size] for i in range(0, len(chunks), chunk_size)]

def fetch_naver_trends(keyword_groups_batch, start_date, end_date, client_id, client_secret):
    url = "https://openapi.naver.com/v1/datalab/search"

    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
        "Content-Type": "application/json"
    }

    data = {
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": "date",
        "keywordGroups": keyword_groups_batch
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        logger.log(f">>>>>> Naver API 호출 성공: status_code={response.status_code}")
        return response.json()
    else:
        error_msg = f">>> Naver API 호출 실패: {response.status_code}, {response.text}"
        logger.log(error_msg)
        raise Exception(error_msg)

def collect_trend_data(keywords, days=7):
    st.subheader("🔍 네이버 검색어 트렌드 데이터 수집")
    try:
        client_id, client_secret = load_naver_credentials()
        # st.caption("✅ .env에서 인증 정보를 성공적으로 불러왔습니다.")
        logger.log(">>>>>> 인증 정보 로드 성공")
    except Exception as e:
        st.error(str(e))
        logger.log(f">>> 인증 정보 로드 실패: {e}")
        return None

    today = datetime.today().date()
    start_date = (today - timedelta(days=days)).isoformat()
    end_date = today.isoformat()
    logger.log(f">>>>>> 데이터 수집 기간: {start_date} ~ {end_date}")
    logger.log(f">>>>>> 총 키워드 수: {len(keywords)}")

    keyword_batches = chunk_keywords(keywords)
    logger.log(f">>>>>> 키워드 그룹 배치 수: {len(keyword_batches)}")
    
    all_data = []
    with st.spinner("네이버 API로 데이터 수집 중..."):
        for batch in keyword_batches:
            logger.log(f">>>>>> [배치 {batch}/{len(keyword_batches)}] 호출할 그룹: {[g['groupName'] for g in batch]}")
            try:
                result = fetch_naver_trends(batch, start_date, end_date, client_id, client_secret)
                for group in result['results']:
                    df = pd.DataFrame(group['data'])
                    df['group'] = group['title']
                    all_data.append(df)
                    logger.log(f">>>>>>그룹 '{group['title']}' 데이터 수집: {len(group['data'])}건")
            except Exception as e:
                st.warning(f"❌ 일부 그룹 호출 실패: {e}")
                logger.log(f">>> [배치 {batch_idx}] 일부 그룹 실패: {e}")

    if all_data:
        full_df = pd.concat(all_data, ignore_index=True)
        full_df['period'] = pd.to_datetime(full_df['period'])
        st.success("✅ 데이터 수집 완료")
        logger.log(f">>>>>> 전체 데이터 수집 완료: 총 {len(full_df)}행")
        return full_df
    else:
        st.error("❌ 수집된 데이터가 없습니다.")
        logger.log(">>> 데이터 수집 결과: 0행")
        return None
