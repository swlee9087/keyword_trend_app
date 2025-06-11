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
    
    #인증
    try:
        client_id, client_secret = load_naver_credentials()
        st.caption("✅ .env에서 인증 정보를 성공적으로 불러왔습니다.")
        logger.log(">>>>>> 인증 정보 로드 성공")
    except Exception as e:
        st.error(str(e))
        logger.log(f">>> 인증 정보 로드 실패: {e}")
        return None

    # 날짜 
    today = datetime.today().date()
    start_date = (today - timedelta(days=days)).isoformat()
    end_date = today.isoformat()
    logger.log(f">>>>>> 데이터 수집 기간: {start_date} ~ {end_date}, 총 키워드 수: {len(keywords)}")

    # 키워드 그룹 배치
    keyword_batches = chunk_keywords(keywords)
    logger.log(f">>>>>> 키워드 그룹 배치 수: {len(keyword_batches)}")
    
    # API 호출
    all_data = []
    with st.spinner("네이버 API로 데이터 수집 중..."):
        for idx, batch in enumerate(keyword_batches, 1):
            names = [g["groupName"] for g in batch]
            logger.log(f"▶️ 배치 {idx}/{len(keyword_batches)} 호출: {names}")
            # logger.log(f">>>>>> [배치 {batch}/{len(keyword_batches)}] 호출할 그룹: {[g['groupName'] for g in batch]}")
            try:
                result = fetch_naver_trends(batch, start_date, end_date, client_id, client_secret)
                for group in result['results']:
                    df = pd.DataFrame(group['data'])
                    df['group'] = group['title']
                    all_data.append(df)
                # logger.log(f">>>>>>그룹 '{group['title']}' 데이터 수집: {len(group['data'])}건")
                logger.log(f">>>>>> 배치 {idx} 완료, rows: {sum(len(g['data']) for g in result['results'])}")
            except Exception as e:
                st.warning(f"❌ 배치 {idx} 실패: {e}")
                logger.log(f">>>>>> 배치 {idx} exception: {e}")

    if all_data:
        full_df = pd.concat(all_data, ignore_index=True)
        
        # 칼럼 정리
        cols_before = full_df.columns.tolist()
        # 칼럼명 정리. 리턴된 칼럼명에 포함된 따옴표, 공백 제거
        cleaned_cols = [c.strip().strip('"').strip("'") for c in cols_before]
        full_df.columns = cleaned_cols
        st.write("⚙️ 수집된 컬럼들:", cleaned_cols)
        logger.log(f"sanitized columns: {cleaned_cols}")
        # logger.log(f">>>>>> collect_trend_data columns: {full_df.columns.tolist()}")
    
        # period/date 통일
        cols = full_df.columns.tolist()
        #period 또는 date계열 컬럼 탐색
        date_cand = [c for c in cols if c.lower() in ('period', 'date')]
        if not date_cand: 
            st.error(f"❌ 'period' 또는 'date' 컬럼을 찾을 수 없습니다. 사용 가능한 컬럼: {cols}")
            logger.log(f">>> period column missing, cols={cols}")
            return None
        src = date_cand[0]
        if src != 'period':
            full_df = full_df.rename(columns={src: 'period'})
            logger.log(f">>>>>> '{src}' → 'period' 변환 완료")
        full_df['period'] = pd.to_datetime(full_df['period'], errors="coerce")
        logger.log(">>>>>> 'period' datetime 변환 완료")
        
        # ratio 통일
        if "ratio" not in full_df.columns:
            num_cols = full_df.select_dtypes(include="number").columns.tolist()
            num_cols = [c for c in num_cols if c != "period"]
            if not num_cols:
                st.error(f"❌ 'ratio' 컬럼이 없고, 숫자형 컬럼도 없습니다: {cols}")
                logger.log(f"❌ ratio missing & no numeric: {cols}")
                return None
            full_df = full_df.rename(columns={num_cols[0]: "ratio"})
            logger.log(f"🔄 '{num_cols[0]}' → 'ratio'")
        # to numeric
        full_df["ratio"] = pd.to_numeric(full_df["ratio"], errors="coerce")
        logger.log("🔢 'ratio' numeric 변환 완료")

        # group 통일
        if "group" not in full_df.columns:
            title_cand = [c for c in cols if "title" in c.lower()]
            if title_cand:
                full_df = full_df.rename(columns={title_cand[0]: "group"})
                logger.log(f"🔄 '{title_cand[0]}' → 'group'")
            else:
                st.error(f"❌ 'group' 컬럼을 찾을 수 없습니다: {cols}")
                logger.log(f"❌ group missing: {cols}")
                return None
            
        # 9) 완료
        valid_rows = len(full_df)
        st.success(f"✅ 데이터 수집 완료 ({valid_rows} rows)")
        logger.log(f">>>>>> NAVER 전체 수집 완료: {valid_rows} rows")
        return full_df
    
    else:
        st.error("❌ 수집된 데이터가 없습니다.")
        logger.log(">>> 전체 데이터 수집 실패")
        return None
