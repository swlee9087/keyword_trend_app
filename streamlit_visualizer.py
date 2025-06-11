# streamlit_visualizer.py

import streamlit as st
import plotly.express as px
import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from log_util import logger

FONT_PATH = os.path.join(os.getcwd(), "fonts", "NotoSansKR-VF.ttf")

def plot_line_chart(df):
    st.subheader("📈 키워드별 검색 비율 (시간 흐름)")
    fig = px.line(
        df,
        x="period",
        y="ratio",
        color="group",
        markers=True,
        title="키워드별 시계열 변화",
        hover_data={"group": True, "period": True, "ratio": True}
    )
    fig.update_traces(line=dict(width=2))
    st.plotly_chart(fig, use_container_width=True)
    num_groups = df['group'].nunique()
    date_range = f"{df['period'].min().date()} to {df['period'].max().date()}"
    logger.log(f">>>>>> Line chart plotted: {num_groups} groups, period {date_range}")

def plot_bar_chart(df):
    st.subheader("📊 최근 날짜 기준 검색량 상위 키워드")
    latest_date = df['period'].max()
    latest_df = df[df['period'] == latest_date].sort_values("ratio", ascending=False)

    fig = px.bar(
        latest_df,
        x="group",
        y="ratio",
        text="ratio",
        title=f"{latest_date.strftime('%Y-%m-%d')} 기준 검색량",
        hover_data={"group": True, "ratio": True}
    )
    fig.update_traces(texttemplate='%{text:.2s}', textposition='outside')
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
    # top_groups = latest_df['group'].tolist()[:5]
    logger.log(f">>>>>> Bar chart plotted for date {latest_date.date()}")

def plot_wordcloud(df):
    st.subheader("☁️ 검색량 기반 워드클라우드")
    latest_date = df['period'].max()
    latest_df = df[df['period'] == latest_date]
    word_freq = dict(zip(latest_df['group'], latest_df['ratio']))
    wc = WordCloud(
        font_path=FONT_PATH,    # 한글 폰트 지정
        width=800,
        height=400,
        background_color='white',
        max_words=100,          # 최대 단어수
        collocations=False      # 키워드 분리
    ).generate_from_frequencies(word_freq)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wc, interpolation='bilinear')
    ax.axis('off')
    st.pyplot(fig)
    logger.log(f">>>>>> Wordcloud generated for date {latest_date.date()}, keywords count: {len(word_freq)}")
