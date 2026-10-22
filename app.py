"""날씨·환율 통합 앱 (Streamlit). 실행: streamlit run app.py

화면 두 개를 왼쪽 메뉴로 오가요.
- 오늘의 브리핑 (briefing.py): 지금 날씨 + 금액 환산
- 날씨·환율 변동 (trend.py): 기온·환율 변화 그래프
"""
import streamlit as st

pages = [
    st.Page("briefing.py", title="오늘의 브리핑", icon="☀️", default=True),
    st.Page("trend.py", title="날씨·환율 변동", icon="📈"),
]

st.navigation(pages).run()  # 고른 페이지 파일을 실행
