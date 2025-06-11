# app.py

import streamlit as st
from log_util import Logger
from streamlit_keyword_extractor import step1_upload_csv
from streamlit_naver_api import collect_trend_data
from streamlit_visualizer import plot_line_chart, plot_bar_chart, plot_wordcloud
from streamlit_predictor import step4_forecast

# 로그 초기화
logger = Logger()
logger.log("앱 실행 시작됨")

# Streamlit 설정
st.set_page_config(layout="wide", page_title="키워드 흥행력 예측")
st.title("🔍 키워드 트렌드 분석 및 흥행 예측 웹앱")

# Step 1: Google Trends CSV 업로드 및 키워드 추출
keywords = step1_upload_csv()
if keywords:
    st.session_state["keywords"] = keywords
    logger.log(f">>>>>> CSV에서 키워드 {len(keywords)}개 추출됨")

# Step 2: Naver API 호출하여 트렌드 데이터 수집
if "keywords" in st.session_state:
    trend_df = collect_trend_data(st.session_state["keywords"])
    if trend_df is not None:
        st.session_state["trend_df"] = trend_df
        logger.log(f">>>>>> 네이버 API로 시계열 데이터 수집 완료: {trend_df['group'].nunique()}개 그룹")

# Step 3: 시각화
if "trend_df" in st.session_state:
    plot_line_chart(st.session_state["trend_df"])
    plot_bar_chart(st.session_state["trend_df"])
    plot_wordcloud(st.session_state["trend_df"])
    logger.log(">>>>>> 키워드 시각화 완료")

# Step 4: 향후 3일/7일 예측
if "trend_df" in st.session_state:
    step4_forecast(st.session_state["trend_df"])
    logger.log(">>>>>> 흥행력 예측 완료")
