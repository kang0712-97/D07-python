"""OpenAI 채팅 화면 (Streamlit). 실행: streamlit run chat.py"""
import os

import openai
import streamlit as st
from dotenv import load_dotenv

load_dotenv()  # .env 금고에서 키를 읽어 옴

MODEL = "gpt-4o-mini"  # 사용할 모델 (바꾸려면 여기만 수정)
SYSTEM = "너는 친절한 도우미야. 항상 쉬운 한국어로 짧고 분명하게 답해."

st.set_page_config(page_title="AI 채팅", page_icon="💬")
st.title("AI 채팅")
st.caption(f"모델: {MODEL}")

key = os.getenv("OPENAI_API_KEY")
if not key:
    st.error(".env에 OPENAI_API_KEY가 없어요. .env.example을 보고 채워 주세요.")
    st.stop()

# Streamlit은 입력할 때마다 파일 전체를 다시 실행하므로, 대화는 session_state에 보관
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    if st.button("대화 지우기"):
        st.session_state.messages = []
        st.rerun()

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])

if prompt := st.chat_input("메시지를 입력하세요"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        try:
            client = openai.OpenAI(api_key=key)
            res = client.chat.completions.create(  # 🔌 API 호출
                model=MODEL,
                messages=[{"role": "system", "content": SYSTEM}] + st.session_state.messages,
                timeout=30,
            )
            answer = res.choices[0].message.content  # res.choices[0].message.content = AI의 답
            st.write(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
        except openai.AuthenticationError:
            st.error("OpenAI 키가 틀렸어요.")
        except openai.RateLimitError:
            st.error("사용 한도나 크레딧을 확인해 주세요. (platform.openai.com → Billing)")
        except openai.APIConnectionError:
            st.error("OpenAI 서버에 연결하지 못했어요. 인터넷을 확인해 주세요.")
        except openai.APIError:
            st.error("OpenAI에서 오류가 났어요. 잠시 뒤에 다시 해 주세요.")
