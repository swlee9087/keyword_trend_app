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
    future_results = []

    for group in df['group'].unique():
        group_df = df[df['group'] == group].sort_values("period")
        last_day = group_df['period'].max()

        for d in days:
            future_date = last_day + timedelta(days=d)
            row = pd.DataFrame({
                "period": [future_date],
                "group": [group]
            })
            row = create_features(row)
            features = ['dayofweek', 'week', 'month', 'day', 'is_weekend']
            pred = model.predict(row[features])[0]
            future_results.append({
                "group": group,
                f"pred_{d}d": pred
            })

    pred_df = pd.DataFrame(future_results)
    # pred_3 = pred_df.pivot(index="group", columns=None, values="pred_3d")
    # pred_7 = pred_df.pivot(index="group", columns=None, values="pred_7d")
    # final_df = pd.concat([pred_3, pred_7], axis=1)
    # final_df.columns = ["3일 예측", "7일 예측"]
    pred_df = pred_df.set_index('group')
    final_df = pred_df.rename(columns={
        'pred_3d': '3일 예측',
        'pred_7d': '7일 예측'
    }).reset_index()
    
    return final_df

def step4_forecast(trend_df):
    st.subheader("🔮 향후 검색량 예측 (흥행력)")
    # 입력 데이터 로깅
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
        fig = px.bar(
            pred_df.sort_values("3일 예측", ascending=False),
            x="group", y=["3일 예측","7일 예측"],
            barmode="group",
            title="예측된 키워드별 향후 검색량",
            labels={"value":"예측 검색비율","group":"키워드"},
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
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
        logger.log(">>>>>> 예측 결과 시각화 완료")
        
    except Exception as e:
        tb = traceback.format_exc()
        st.error(f"예측 실패: {e}\n{tb}")
        logger.log(f">>> 예측 실패: {e}\n{tb}")
