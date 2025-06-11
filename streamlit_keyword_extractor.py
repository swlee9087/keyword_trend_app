# streamlit_keyword_extractor.py

import streamlit as st
import pandas as pd
from log_util import logger

def extract_keywords_from_csv(csv_file):
    df = pd.read_csv(csv_file, encoding="utf-8")
    # keyword_candidates = list(df.columns[1:])  # 첫 번째 컬럼은 날짜 or 시간일 확률 높음
    # keyword_candidates = [kw for kw in keyword_candidates if isinstance(kw, str) and kw.strip()]

    if df.shape[0] >= 1 and df.shape[1] >= 2:
        # 첫 번째 열은 날짜/시간이니까 제외
        first_row = df.iloc[0, 1:]
        # NaN 제거, 문자열로, 앞뒤 공백 제거
        keywords = (
            first_row
            .dropna()
            .astype(str)
            .str.strip()
            .tolist()
        )
        logger.log(f">>>>>> 첫 번째 행에서 {len(keywords)}개 키워드 추출 성공")
    else:
        keywords = []
        logger.log(">>> CSV에 키워드를 추출할 첫 번째 행이 없음")

    # return keyword_candidates
    return keywords

def step1_upload_csv():
    st.header("📁 Google 트렌드 CSV 업로드")
    uploaded_csv = st.file_uploader("최근 7일 한국 트렌드 데이터 CSV 파일을 업로드하세요", type="csv")

    if uploaded_csv is not None:
        logger.log(f">>>>>>CSV 업로드됨: {uploaded_csv.name}")
        try:
            keywords = extract_keywords_from_csv(uploaded_csv)
            st.success(f"✅ {len(keywords)}개 키워드를 추출했습니다.")
            st.write("추출된 키워드 예시:")
            st.write(keywords[:10])
            logger.log(f">>>>>> {len(keywords)}개 키워드 추출 성공")
            return keywords
        except Exception as e:
            st.error(f"❌ CSV 처리 중 오류 발생: {e}")
            logger.log(f">>> CSV 처리 오류: {e}")
            return None
    return None
