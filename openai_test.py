"""OpenAI API 연결 확인: "안녕"이라고 보내고 답을 터미널에 보여 줍니다."""
import os

import openai
from dotenv import load_dotenv

load_dotenv()  # .env 금고에서 키를 읽어 옴

MODEL = "gpt-4o-mini"  # 사용할 모델 (바꾸려면 여기만 수정)


def main():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        print(".env에 OPENAI_API_KEY가 없어요. .env.example을 보고 채워 주세요.")
        return

    client = openai.OpenAI(api_key=key)
    try:
        res = client.chat.completions.create(  # 🔌 API 호출
            model=MODEL,
            messages=[{"role": "user", "content": "안녕! 한 문장으로 한국어로 인사해 줘."}],
            timeout=30,
        )
    except openai.AuthenticationError:
        print("OpenAI 키가 틀렸어요.")
        return
    except openai.RateLimitError:
        print("사용 한도나 크레딧을 확인해 주세요. (platform.openai.com → Billing)")
        return
    except openai.APIConnectionError:
        print("OpenAI 서버에 연결하지 못했어요. 인터넷을 확인해 주세요.")
        return
    except openai.APIError:
        print("OpenAI에서 오류가 났어요. 잠시 뒤에 다시 해 주세요.")
        return

    answer = res.choices[0].message.content  # res.choices[0].message.content = AI의 답
    print(f"모델: {MODEL}")
    print(f"답: {answer}")
    print("출처: OpenAI")


if __name__ == "__main__":
    main()
