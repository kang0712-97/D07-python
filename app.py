"""오늘의 브리핑 웹 화면 (Streamlit). 실행: streamlit run app.py"""
import os
from datetime import timedelta, timezone
from email.utils import parsedate_to_datetime

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()  # .env 금고에서 키를 읽어 옴

API = {
    "지오코딩": "https://api.openweathermap.org/geo/1.0/direct",  # 🔌 OpenWeather 도시 → 위도·경도
    "날씨": "https://api.openweathermap.org/data/2.5/weather",  # 🔌 OpenWeather 현재 날씨
    "환율": "https://v6.exchangerate-api.com/v6/latest/USD",  # 🔌 ExchangeRate-API 환율 (기준 USD)
}

KST = timezone(timedelta(hours=9))  # 한국 시간
CURRENCIES = ["USD", "JPY", "EUR", "CNY"]


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


def get_key(name):
    key = os.getenv(name)
    if not key:
        raise ShowError(f".env에 {name}가 없어요. .env.example을 보고 채워 주세요.")
    return key


@st.cache_data(ttl=600)  # 날씨는 10분 동안 다시 부르지 않음
def get_weather(city):
    key = get_key("OPENWEATHER_API_KEY")
    status, places = call_api(API["지오코딩"], params={"q": city, "limit": 1, "appid": key})
    if status == 401:
        raise ShowError("날씨 키가 틀렸거나 아직 켜지지 않았어요. (가입 후 최대 2시간)")
    if status == 429:
        raise ShowError("1분에 너무 많이 불렀어요. 잠시 뒤에 다시 해 주세요.")
    if status != 200:
        raise ShowError(f"도시를 찾지 못했어요. (오류 코드 {status})")
    if not places:
        raise ShowError("그 도시를 찾지 못했어요. 영문 이름으로도 입력해 보세요.")
    lat, lon = places[0]["lat"], places[0]["lon"]  # places[0] = 가장 비슷한 도시의 위도·경도

    params = {"lat": lat, "lon": lon, "appid": key, "units": "metric", "lang": "kr"}
    status, data = call_api(API["날씨"], params=params)
    if status != 200:
        raise ShowError(f"날씨를 가져오지 못했어요. (오류 코드 {status})")
    return {
        "temp": data["main"]["temp"],  # data["main"]["temp"] = 지금 기온(℃)
        "feels": data["main"]["feels_like"],  # data["main"]["feels_like"] = 체감 온도(℃)
        "humidity": data["main"]["humidity"],  # data["main"]["humidity"] = 습도(%)
        "desc": data["weather"][0]["description"],  # data["weather"][0]["description"] = 날씨 설명
    }


@st.cache_data(ttl=3600)  # 환율은 1시간 동안 다시 부르지 않음 (무료 한 달 1,500번)
def get_rates():
    key = get_key("EXCHANGERATE_API_KEY")
    status, data = call_api(API["환율"], headers={"Authorization": f"Bearer {key}"})
    if data.get("result") != "success":
        errors = {
            "invalid-key": "환율 키가 틀렸어요.",
            "inactive-account": "환율 사이트 가입 인증 메일을 확인해 주세요.",
            "quota-reached": "이번 달 무료 사용량(1,500번)을 다 썼어요.",
        }
        error_type = data.get("error-type")  # data["error-type"] = 오류 종류
        raise ShowError(errors.get(error_type, f"환율을 가져오지 못했어요. ({error_type})"))
    updated = parsedate_to_datetime(data["time_last_update_utc"])  # data["time_last_update_utc"] = 환율 기준 시각(UTC)
    return {
        "rates": data["conversion_rates"],  # data["conversion_rates"] = 1달러가 각 통화로 얼마인지
        "updated": updated.astimezone(KST).strftime("%Y-%m-%d %H:%M"),
    }


st.set_page_config(page_title="오늘의 브리핑", page_icon="☀️")
st.title("오늘의 브리핑")

with st.sidebar:
    city = st.text_input("도시", value="Seoul")
    amount = st.number_input("금액", min_value=0.0, value=100.0, step=10.0)
    currency = st.selectbox("통화", CURRENCIES)
    if st.button("새로 불러오기"):
        st.cache_data.clear()  # 이 버튼에서만 캐시를 비움

left, right = st.columns(2)  # 칸마다 따로 불러서 한 칸이 실패해도 다른 칸은 보임

with left:
    st.subheader(f"{city} 날씨")
    try:
        w = get_weather(city)
        st.metric("기온", f"{w['temp']}°C")
        st.metric("체감 온도", f"{w['feels']}°C")
        st.metric("습도", f"{w['humidity']}%")
        st.write(f"날씨: {w['desc']}")
    except ShowError as e:
        st.error(str(e))

with right:
    st.subheader("환율")
    try:
        r = get_rates()
        krw_per_usd = r["rates"]["KRW"]  # 1달러 = 몇 원
        krw = amount * krw_per_usd / r["rates"][currency]  # 입력 통화 → 달러 → 원
        st.metric(f"{amount:,.0f} {currency}", f"{krw:,.0f} 원")
        st.write(f"기준 시각: {r['updated']} (한국 시간)")
    except ShowError as e:
        st.error(str(e))

st.caption("출처: 날씨 OpenWeather · 환율 ExchangeRate-API")
