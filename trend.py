"""날씨·환율 변동 그래프 화면 (Streamlit). 실행: streamlit run trend.py"""
import os
from datetime import date, datetime, timedelta, timezone

import pandas as pd  # 표(DataFrame)를 만드는 도구 (streamlit 설치 때 같이 설치됨)
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()  # .env 금고에서 키를 읽어 옴

API = {
    "지오코딩": "https://api.openweathermap.org/geo/1.0/direct",  # 🔌 OpenWeather 도시 → 위도·경도
    "예보": "https://api.openweathermap.org/data/2.5/forecast",  # 🔌 OpenWeather 5일 예보 (3시간 간격)
    "환율기록": "https://api.frankfurter.dev/v1",  # 🔌 Frankfurter 과거 환율 (키 없음)
}

KST = timezone(timedelta(hours=9))  # 한국 시간
CURRENCIES = {"USD": 1, "JPY": 100, "EUR": 1, "CNY": 1}  # 통화: 몇 단위 기준으로 보여 줄지 (엔은 100엔)
PERIODS = {"7일": 7, "30일": 30, "90일": 90}


class ShowError(Exception):
    """화면에 그대로 보여 줘도 되는 한국어 안내 메시지를 담는 에러."""


def call_api(url, **kwargs):
    """API를 부르고 (상태 코드, JSON)을 돌려준다. 실패하면 한국어 안내를 낸다."""
    try:
        res = requests.get(url, timeout=10, **kwargs)  # 🔌 API 호출
    except requests.RequestException:
        # 에러 내용에 요청 주소(키 포함)가 들어 있을 수 있어 화면에 내보내지 않음
        raise ShowError("서버에 연결하지 못했어요. 인터넷을 확인해 주세요.")
    try:
        return res.status_code, res.json()
    except ValueError:
        raise ShowError(f"응답을 읽지 못했어요. (오류 코드 {res.status_code})")


@st.cache_data(ttl=600)  # 날씨는 10분 동안 다시 부르지 않음
def get_forecast(city):
    key = os.getenv("OPENWEATHER_API_KEY")
    if not key:
        raise ShowError(".env에 OPENWEATHER_API_KEY가 없어요. .env.example을 보고 채워 주세요.")

    # 1) 도시 이름 → 위도·경도 (1번 응답의 lat, lon이 2번 주소에 들어감)
    status, places = call_api(API["지오코딩"], params={"q": city, "limit": 1, "appid": key})
    if status == 401:
        raise ShowError("날씨 키가 틀렸거나 아직 켜지지 않았어요. (가입 후 최대 2시간)")
    if status == 429:
        raise ShowError("1분에 너무 많이 불렀어요. 잠시 뒤에 다시 해 주세요.")
    if status != 200 or not places:
        raise ShowError("그 도시를 찾지 못했어요. 영문 이름으로도 입력해 보세요.")
    lat, lon = places[0]["lat"], places[0]["lon"]  # places[0] = 가장 비슷한 도시의 위도·경도

    # 2) 5일 예보 (3시간 간격, 40개)
    params = {"lat": lat, "lon": lon, "appid": key, "units": "metric", "lang": "kr"}
    status, data = call_api(API["예보"], params=params)
    if status != 200:
        raise ShowError(f"예보를 가져오지 못했어요. (오류 코드 {status})")

    rows = []
    for item in data["list"]:  # data["list"] = 3시간마다 하나씩 있는 예보 목록
        when = datetime.fromtimestamp(item["dt"], KST)  # item["dt"] = 예보 시각(초) → 한국 시간
        rows.append({
            "시각": when,
            "기온": item["main"]["temp"],  # item["main"]["temp"] = 기온(℃)
            "체감 온도": item["main"]["feels_like"],  # item["main"]["feels_like"] = 체감 온도(℃)
            "습도": item["main"]["humidity"],  # item["main"]["humidity"] = 습도(%)
        })
    return pd.DataFrame(rows).set_index("시각")


@st.cache_data(ttl=3600)  # 환율 기록은 1시간 동안 다시 부르지 않음
def get_rate_history(currency, days):
    end = date.today()
    start = end - timedelta(days=days)
    # 통화 1단위가 몇 원인지: 기준 통화를 currency, 비교 통화를 KRW로
    url = f"{API['환율기록']}/{start}..{end}"
    status, data = call_api(url, params={"base": currency, "symbols": "KRW"})
    if status != 200 or "rates" not in data:
        raise ShowError(f"환율 기록을 가져오지 못했어요. (오류 코드 {status})")

    unit = CURRENCIES[currency]  # 엔은 100엔 기준으로 보여 줌
    series = {
        day: values["KRW"] * unit  # values["KRW"] = 그날 1단위가 몇 원인지
        for day, values in data["rates"].items()  # data["rates"] = {날짜: {KRW: 값}}
    }
    df = pd.DataFrame({"원": series})
    df.index = pd.to_datetime(df.index)
    return df.sort_index()


st.set_page_config(page_title="날씨·환율 변동", page_icon="📈", layout="wide")
st.title("날씨·환율 변동")

with st.sidebar:
    city = st.text_input("도시", value="Seoul")
    currency = st.selectbox("통화", list(CURRENCIES))
    period = st.radio("환율 기간", list(PERIODS), horizontal=True)
    if st.button("새로 불러오기"):
        st.cache_data.clear()  # 이 버튼에서만 캐시를 비움

left, right = st.columns(2)  # 칸마다 따로 불러서 한 칸이 실패해도 다른 칸은 보임

with left:
    st.subheader(f"{city} 5일 기온 변화")
    try:
        weather = get_forecast(city)
        st.line_chart(weather[["기온", "체감 온도"]], y_label="℃")
        c1, c2, c3 = st.columns(3)
        c1.metric("최고 기온", f"{weather['기온'].max():.1f}°C")
        c2.metric("최저 기온", f"{weather['기온'].min():.1f}°C")
        c3.metric("평균 습도", f"{weather['습도'].mean():.0f}%")
        st.caption("3시간 간격 예보 · 한국 시간")
    except ShowError as e:
        st.error(str(e))

with right:
    unit = CURRENCIES[currency]
    label = f"{unit}{currency}" if unit > 1 else f"1 {currency}"
    st.subheader(f"{label} 환율 변화 ({period})")
    try:
        rates = get_rate_history(currency, PERIODS[period])
        st.line_chart(rates, y_label="원")
        first, last = rates["원"].iloc[0], rates["원"].iloc[-1]
        change = (last - first) / first * 100  # 기간 시작 대비 변동률(%)
        c1, c2, c3 = st.columns(3)
        c1.metric("가장 최근", f"{last:,.1f}원", f"{change:+.2f}%")
        c2.metric("최고", f"{rates['원'].max():,.1f}원")
        c3.metric("최저", f"{rates['원'].min():,.1f}원")
        st.caption(f"기준일: {rates.index[-1]:%Y-%m-%d} · 주말·공휴일은 전 영업일 값")
    except ShowError as e:
        st.error(str(e))

st.caption("출처: 날씨 OpenWeather · 환율 Frankfurter")
