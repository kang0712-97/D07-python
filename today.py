"""오늘의 아침 브리핑: 날씨 → 환율 → 공휴일을 차례로 불러 한 화면에 보여 줍니다."""
import os
import unicodedata
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import requests
from dotenv import load_dotenv

load_dotenv()  # .env 금고에서 키를 읽어 옴

API = {
    "날씨": "https://api.openweathermap.org/data/2.5/weather",  # 🔌 OpenWeather 현재 날씨
    "환율": "https://v6.exchangerate-api.com/v6/latest/USD",  # 🔌 ExchangeRate-API 환율
    "공휴일": "https://date.nager.at/api/v3/NextPublicHolidays/KR",  # 🔌 Nager.Date 다음 공휴일 (키 없음)
}

SEOUL = {"lat": 37.5665, "lon": 126.9780}  # 서울 위도·경도
KST = timezone(timedelta(hours=9))  # 한국 시간


class BriefingError(Exception):
    """화면에 그대로 보여 줘도 되는 한국어 안내 메시지를 담는 에러."""


def get_json(url, **kwargs):
    """API를 부르고 JSON을 돌려준다. 실패하면 한국어 안내(BriefingError)를 낸다."""
    try:
        res = requests.get(url, timeout=10, **kwargs)  # 🔌 API 호출
    except requests.RequestException:
        # 에러 내용에 요청 주소(키 포함)가 들어 있을 수 있어 출력하지 않음
        raise BriefingError("서버에 연결하지 못했어요. 인터넷을 확인해 주세요.")
    try:
        return res.status_code, res.json()
    except ValueError:
        raise BriefingError(f"응답을 읽지 못했어요. (오류 코드 {res.status_code})")


def get_key(name):
    key = os.getenv(name)
    if not key:
        raise BriefingError(f".env에 {name}가 없어요. .env.example을 보고 채워 주세요.")
    return key


def weather():
    key = get_key("OPENWEATHER_API_KEY")
    params = {**SEOUL, "appid": key, "units": "metric", "lang": "kr"}
    status, data = get_json(API["날씨"], params=params)
    if status == 401:
        raise BriefingError("날씨 키가 틀렸거나 아직 켜지지 않았어요. (가입 후 최대 2시간)")
    if status == 429:
        raise BriefingError("1분에 너무 많이 불렀어요. 잠시 뒤에 다시 해 주세요.")
    if status != 200:
        raise BriefingError(f"날씨를 가져오지 못했어요. (오류 코드 {status})")
    temp = data["main"]["temp"]  # data["main"]["temp"] = 지금 기온(℃)
    desc = data["weather"][0]["description"]  # data["weather"][0]["description"] = 날씨 설명
    return f"서울 {temp}°C, {desc}"


def exchange_rate():
    key = get_key("EXCHANGERATE_API_KEY")
    status, data = get_json(API["환율"], headers={"Authorization": f"Bearer {key}"})
    if data.get("result") != "success":
        errors = {
            "invalid-key": "환율 키가 틀렸어요.",
            "inactive-account": "환율 사이트 가입 인증 메일을 확인해 주세요.",
            "quota-reached": "이번 달 무료 사용량(1,500번)을 다 썼어요.",
        }
        error_type = data.get("error-type")  # data["error-type"] = 오류 종류
        raise BriefingError(errors.get(error_type, f"환율을 가져오지 못했어요. ({error_type})"))
    krw = data["conversion_rates"]["KRW"]  # data["conversion_rates"]["KRW"] = 1달러가 몇 원인지
    updated = parsedate_to_datetime(data["time_last_update_utc"])  # data["time_last_update_utc"] = 환율 기준 시각(UTC)
    updated_kst = updated.astimezone(KST).strftime("%m-%d %H:%M")
    return f"1 USD = {krw:,.2f} KRW (기준 {updated_kst}, 한국 시간)"


def next_holiday():
    status, data = get_json(API["공휴일"])  # 키 없음
    if status != 200 or not data:
        raise BriefingError(f"공휴일을 가져오지 못했어요. (오류 코드 {status})")
    first = data[0]  # data[0] = 가장 가까운 다음 공휴일
    name = first["localName"]  # first["localName"] = 한국어 공휴일 이름
    day = date.fromisoformat(first["date"])  # first["date"] = 공휴일 날짜
    left = (day - datetime.now(KST).date()).days
    d_day = "D-day" if left == 0 else f"D-{left}"
    return f"{name} {day:%m-%d} ({d_day})"


# (표시 이름, 함수, 출처) 순서대로 하나씩 부름
STEPS = [
    ("날씨", weather, "OpenWeather"),
    ("환율", exchange_rate, "ExchangeRate-API"),
    ("공휴일", next_holiday, "Nager.Date"),
]


def pad(text, width):
    """한글은 영문 두 칸 너비라서, 보이는 너비 기준으로 오른쪽에 공백을 채운다."""
    shown = sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)
    return text + " " * (width - shown)


def main():
    print("=== 오늘의 아침 브리핑 ===")
    sources = []
    for title, func, source in STEPS:
        try:
            line = func()
            sources.append(f"{title}: {source}")
        except BriefingError as e:
            line = f"(건너뜀) {e}"  # 하나가 실패해도 다음 API로 계속 진행
        print(f"{pad(title, 8)}: {line}")
    print()
    print("출처 - " + ", ".join(sources) if sources else "출처 - 없음")


if __name__ == "__main__":
    main()
