"""1달러가 원화로 얼마인지 터미널에 보여 줍니다."""
import os
from datetime import timezone, timedelta
from email.utils import parsedate_to_datetime

import requests
from dotenv import load_dotenv

load_dotenv()  # .env 금고에서 키를 읽어 옴

API = {
    "환율": "https://v6.exchangerate-api.com/v6/latest/USD",  # 🔌 ExchangeRate-API 환율 (기준 통화 USD)
}

KST = timezone(timedelta(hours=9))  # 한국 시간

ERRORS = {
    "invalid-key": "환율 키가 틀렸어요.",
    "inactive-account": "환율 사이트 가입 인증 메일을 확인해 주세요.",
    "quota-reached": "이번 달 무료 사용량(1,500번)을 다 썼어요.",
}


def main():
    key = os.getenv("EXCHANGERATE_API_KEY")
    if not key:
        print(".env에 EXCHANGERATE_API_KEY가 없어요. .env.example을 보고 채워 주세요.")
        return

    headers = {"Authorization": f"Bearer {key}"}  # 키는 주소가 아니라 헤더로 보냄
    try:
        res = requests.get(API["환율"], headers=headers, timeout=10)  # 🔌 API 호출
    except requests.RequestException:
        # 에러 내용에 요청 정보가 들어 있을 수 있어 출력하지 않음
        print("환율 서버에 연결하지 못했어요. 인터넷을 확인하고 다시 해 주세요.")
        return

    try:
        data = res.json()
    except ValueError:
        print(f"환율을 가져오지 못했어요. (오류 코드 {res.status_code})")
        return

    if data.get("result") != "success":
        error_type = data.get("error-type")  # data["error-type"] = 오류 종류
        print(ERRORS.get(error_type, f"환율을 가져오지 못했어요. ({error_type})"))
        return

    krw = data["conversion_rates"]["KRW"]  # data["conversion_rates"]["KRW"] = 1달러가 몇 원인지
    updated = parsedate_to_datetime(data["time_last_update_utc"])  # data["time_last_update_utc"] = 환율 기준 시각(UTC)
    updated_kst = updated.astimezone(KST).strftime("%Y-%m-%d %H:%M")

    print(f"1 USD = {krw:,.2f} KRW")
    print(f"기준 시각: {updated_kst} (한국 시간)")
    print("출처: ExchangeRate-API")


if __name__ == "__main__":
    main()
