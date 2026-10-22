"""서울의 지금 날씨(기온·체감 온도·습도·설명)를 터미널에 보여 줍니다."""
import os

import requests
from dotenv import load_dotenv

load_dotenv()  # .env 금고에서 키를 읽어 옴

API = {
    "날씨": "https://api.openweathermap.org/data/2.5/weather",  # 🔌 OpenWeather 현재 날씨
}

SEOUL = {"lat": 37.5665, "lon": 126.9780}  # 서울 위도·경도

ERRORS = {
    401: "날씨 키가 틀렸거나 아직 켜지지 않았어요. (가입 후 최대 2시간)",
    404: "그 도시를 찾지 못했어요.",
    429: "1분에 너무 많이 불렀어요. 잠시 뒤에 다시 해 주세요.",
}


def main():
    key = os.getenv("OPENWEATHER_API_KEY")
    if not key:
        print(".env에 OPENWEATHER_API_KEY가 없어요. .env.example을 보고 채워 주세요.")
        return

    params = {**SEOUL, "appid": key, "units": "metric", "lang": "kr"}
    try:
        res = requests.get(API["날씨"], params=params, timeout=10)  # 🔌 API 호출
    except requests.RequestException:
        # 에러 내용에 요청 주소(키 포함)가 들어 있을 수 있어 출력하지 않음
        print("날씨 서버에 연결하지 못했어요. 인터넷을 확인하고 다시 해 주세요.")
        return

    if res.status_code != 200:
        print(ERRORS.get(res.status_code, f"날씨를 가져오지 못했어요. (오류 코드 {res.status_code})"))
        return

    data = res.json()
    temp = data["main"]["temp"]  # data["main"]["temp"] = 지금 기온(℃)
    feels = data["main"]["feels_like"]  # data["main"]["feels_like"] = 체감 온도(℃)
    humidity = data["main"]["humidity"]  # data["main"]["humidity"] = 습도(%)
    desc = data["weather"][0]["description"]  # data["weather"][0]["description"] = 날씨 설명

    print("=== 서울 현재 날씨 ===")
    print(f"기온      : {temp}°C")
    print(f"체감 온도 : {feels}°C")
    print(f"습도      : {humidity}%")
    print(f"날씨      : {desc}")
    print("날씨: OpenWeather")  # 데이터 출처


if __name__ == "__main__":
    main()
