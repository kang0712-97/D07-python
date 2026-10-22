"""OpenAI 채팅 화면 (Streamlit). 실행: streamlit run chat.py"""
import os  # .env에서 읽은 키를 꺼낼 때 사용

import openai  # OpenAI API를 부르는 도구
import streamlit as st  # 파이썬으로 웹 화면을 만드는 도구
from dotenv import load_dotenv  # .env 파일을 읽는 도구

load_dotenv()  # .env 금고에서 키를 읽어 옴

API = {
    "chat": "https://api.openai.com/v1",  # 🔌 OpenAI 챗봇 (기본 주소)
}
MODEL = "gpt-4o-mini"  # 사용할 모델 (바꾸려면 여기만 수정)
SYSTEM = "너는 친절한 도우미야. 항상 쉬운 한국어로 짧고 분명하게 답해."  # AI의 역할과 말투를 정하는 안내문

# 브라우저 탭 제목과 화면 맨 위 제목
st.set_page_config(page_title="AI 채팅", page_icon="💬")
st.title("AI 채팅")
st.caption(f"모델: {MODEL}")  # 제목 아래 작은 글씨로 모델 이름 표시

# 키가 .env에 있는지 확인 (키 값은 화면에 보여 주지 않음)
key = os.getenv("OPENAI_API_KEY")
if not key:
    st.error(".env에 OPENAI_API_KEY가 없어요. .env.example을 보고 채워 주세요.")
    st.stop()  # 키가 없으면 여기서 멈춤 (아래 코드는 실행하지 않음)

# Streamlit은 입력할 때마다 파일 전체를 다시 실행하므로, 대화는 session_state에 보관
if "messages" not in st.session_state:
    st.session_state.messages = []  # 처음에는 빈 대화

# 왼쪽 사이드바
with st.sidebar:
    if st.button("대화 지우기"):
        st.session_state.messages = []  # 저장된 대화를 비움
        st.rerun()  # 화면을 처음부터 다시 그림

# 지금까지의 대화를 화면에 다시 보여 줌 (role: user = 나, assistant = AI)
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])

# 아래 입력창에 메시지를 입력하고 Enter를 누르면 prompt에 글이 담김
if prompt := st.chat_input("메시지를 입력하세요"):
    # 내 메시지를 대화에 저장하고 화면에 보여 줌
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # AI의 답을 받아서 보여 줌
    with st.chat_message("assistant"):
        try:
            client = openai.OpenAI(api_key=key, base_url=API["chat"])  # 접속 주소는 위 API에서 가져옴
            res = client.chat.completions.create(  # 🔌 API 호출
                model=MODEL,
                # 안내문 + 지금까지의 대화 전체를 보내야 AI가 앞 내용을 기억해서 답함
                messages=[{"role": "system", "content": SYSTEM}] + st.session_state.messages,
                timeout=30,  # 30초 안에 답이 없으면 포기
            )
            answer = res.choices[0].message.content  # res.choices[0].message.content = AI의 답
            st.write(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})  # AI의 답도 대화에 저장
        # 실패하면 영어 에러 대신 한국어 한 줄로 알림 (에러 내용에 키가 섞일 수 있어 그대로 보여 주지 않음)
        except openai.AuthenticationError:
            st.error("OpenAI 키가 틀렸어요.")
        except openai.RateLimitError:
            st.error("사용 한도나 크레딧을 확인해 주세요. (platform.openai.com → Billing)")
        except openai.APIConnectionError:
            st.error("OpenAI 서버에 연결하지 못했어요. 인터넷을 확인해 주세요.")
        except openai.APIError:
            st.error("OpenAI에서 오류가 났어요. 잠시 뒤에 다시 해 주세요.")
