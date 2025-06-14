# streamlit_predictor.py

import streamlit as st
import pandas as pd
import joblib
import traceback
from datetime import timedelta
import plotly.express as px
from log_util import logger

def create_features(df):
    df = df.copy()
    df['dayofweek'] = df['period'].dt.dayofweek
    df['week'] = df['period'].dt.isocalendar().week
    df['month'] = df['period'].dt.month
    df['day'] = df['period'].dt.day
    df['is_weekend'] = df['dayofweek'].isin([5, 6]).astype(int)
    return df

def predict_future(df, model, days=[3, 7]):
    """
    df: 원본 트렌드 데이터프레임 (period, group 컬럼 포함)
    model: 학습된 LightGBM 모델
    days: 예측할 future offset 리스트
    """
    future_results = []

    for group in df['group'].unique():
        # 해당 그룹의 가장 마지막 날짜 구하기 
        last_day = df[df['group']==group]['period'].max()

        # 그룹별 dict 생성
        row_dict = {'group': group}
        for d in days:
            future_date = last_day + timedelta(days=d)
            feat_row = create_features(
                pd.DataFrame({'period': [future_date], 'group': [group]})
            )
            features = ['dayofweek', 'week', 'month', 'day', 'is_weekend']
            pred = model.predict(feat_row[features])[0]
            row_dict[f'pred_{d}d'] = pred
            future_results.append(row_dict)

    # 결과 DataFrame으로 변환 후 컬럼명 정리
    final_df = pd.DataFrame(future_results)
    final_df = final_df.rename(columns={
        'pred_3d': '3일 예측',
        'pred_7d': '7일 예측'
    })
    
    return final_df

def step4_forecast(trend_df):
    st.subheader("🔮 향후 검색량 예측 (흥행력)")
    logger.log(f">>>>>> Predict called: trend_df.shape={getattr(trend_df,'shape',None)}, "
               f"columns={getattr(trend_df,'columns',None)}")
    
    # 모델 로드
    try:
        model = joblib.load("trained_lightgbm_allgroups.pkl")
        logger.log(">>>>>> 모델 로드 성공")
    except Exception as e:
        st.error(f"모델 로딩 실패: {e}")
        logger.log(f">>> 모델 로딩 실패: {e}")
        return

    # 예측 수행
    try:
        pred_df = predict_future(trend_df, model)
        
        # 예측 결과 유효성 검사
        if pred_df is None or pred_df.empty:
            st.error("❌ 예측 결과가 없습니다. 입력 데이터를 확인하세요.")
            logger.log(">>> predict_future 반환값이 None 혹은 빈 DataFrame")
            return
        
        # 결과 표시
        logger.log(f">>>>>> 예측 수행 완료: {len(pred_df)}개 그룹")
        st.dataframe(pred_df.style.format({"3일 예측": "{:.2f}", "7일 예측": "{:.2f}"}))
        
        # Top N 슬라이더 추가
        max_n = min(50, len(pred_df))
        top_n = st.slider("🔢 Top N 키워드 갯수", min_value=5, max_value=max_n, value=min(20, max_n))
        
        # 세로 바그래프
        # fig = px.bar(
        #     pred_df.sort_values("3일 예측", ascending=False),
        #     x="group", y=["3일 예측","7일 예측"],
        #     barmode="group",
        #     title="예측된 키워드별 향후 검색량",
        #     labels={"value":"예측 검색비율","group":"키워드"},
        #     height=500
        # )
        # st.plotly_chart(
        #     px.bar(
        #         pred_df.sort_values("3일 예측", ascending=False),
        #         x="group",
        #         y=["3일 예측", "7일 예측"],
        #         barmode="group",
        #         title="예측된 키워드별 향후 검색량",
        #         labels={"value": "예측 검색비율", "group": "키워드"},
        #         height=500
        #     ),
        #     use_container_width=True
        # )

        df_top = pred_df.sort_values("3일 예측", ascending=False).head(top_n)
        
        # 가로 바그래프
        # fig = px.bar(
        #     df_top.sort_values("3일 예측"),
        #     x=["3일 예측", "7일 예측"],
        #     y="group",
        #     orientation="h",
        #     barmode="group",
        #     title=f"예측된 키워드별 향후 검색량 (Top {top_n})",
        #     labels={"value": "예측 검색비율", "group": "키워드"},
        #     height=500
        # )
                
        # melt 해서 long 포맷으로 변환
        df_melt = df_top.melt(
            id_vars="group",
            value_vars=["3일 예측", "7일 예측"],
            var_name="기간",
            value_name="예측값"
        )

        # '기간' 컬럼에서 숫자만 뽑아 실제 x 축 값으로 사용
        df_melt["day_offset"] = df_melt["기간"].str.extract(r"(\d+)").astype(int)

        # 라인 차트
        fig = px.line(
            df_melt,
            x="day_offset",
            y="예측값",
            color="group",
            markers=True,
            title=f"예측된 키워드별 향후 검색량 (Top {top_n})",
            labels={"day_offset": "예측 일수(일)", "예측값": "검색비율", "group": "키워드"},
            height=700
        )
        # 선과 점 크기 조절
        fig.update_traces(line=dict(width=2), marker=dict(size=6))        
        
        # fig.update_layout(
        #     margin=dict(l=200, r=20, t=50, b=50),
        #     legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        # )
        # fig.update_traces(marker=dict(size=6), line=dict(width=2))
        
        # x축 눈금도 3,7 만 보이게
        fig.update_layout(
            xaxis=dict(tickmode="array", tickvals=[3,7], ticktext=["3일 뒤","7일 뒤"]),
            margin=dict(l=200, r=20, t=50, b=50),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        logger.log(">>>>>> 예측 결과 시각화 완료")
        
    except Exception as e:
        tb = traceback.format_exc()
        st.error(f"예측 실패: {e}\n{tb}")
        logger.log(f">>> 예측 실패: {e}\n{tb}")
