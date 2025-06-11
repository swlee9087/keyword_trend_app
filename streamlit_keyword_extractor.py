# streamlit_keyword_extractor.py

import streamlit as st
import pandas as pd
from log_util import logger

def extract_keywords_from_csv(csv_file):
    """
    Google Trends CSV에서
    1) '트렌드' 컬럼
    2) '트렌드 분석' 컬럼
    3) 첫 번째 데이터 행(인덱스 1)의 나머지 셀
    순으로 키워드를 수집한 뒤 중복 제거하여 반환합니다.
    """
    df = pd.read_csv(csv_file, encoding="utf-8")
    # keyword_candidates = list(df.columns[1:])  # 첫 번째 컬럼은 날짜 or 시간일 확률 높음
    # keyword_candidates = [kw for kw in keyword_candidates if isinstance(kw, str) and kw.strip()]
    cols = df.columns.tolist()
    logger.log(f">>>>>> CSV columns: {cols}")
    
    keywords = []
    if '트렌드' in df.columns:
        kws = (
            df['트렌드']
            .dropna()
            .astype(str)
            .str.strip()
            .tolist()
        )
        logger.log(f"'트렌드' 컬럼에서 {len(kws)}개 추출")
        keywords.extend(kws)

    # 2) '트렌드 분석' 컬럼
    if '트렌드 분석' in df.columns:
        kws = (
            df['트렌드 분석']
            .dropna()
            .astype(str)
            .str.strip()
            .tolist()
        )
        logger.log(f"'트렌드 분석' 컬럼에서 {len(kws)}개 추출")
        keywords.extend(kws)
    
    # 3) 첫 번째 데이터 행 (인덱스 1)의 나머지 셀
    if df.shape[0] > 1 and df.shape[1] >= 2:
        first_data_row = df.iloc[1, 1:]  # 두 번째 행, 두 번째 열 이후
        kws = [str(x).strip() for x in first_data_row.dropna().tolist()]
        logger.log(f"첫 번째 데이터 행에서 {len(kws)}개 추가 추출")
        keywords.extend(kws)
    else:
        logger.log("첫 번째 데이터 행에서 키워드를 추출할 수 없음")

    # 4) 중복 제거, 빈 문자열 제거
    cleaned = []
    for kw in keywords:
        if kw and kw not in cleaned:
            cleaned.append(kw)
    logger.log(f"최종 키워드 수 (중복 제거 후): {len(cleaned)}")

    return cleaned

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
