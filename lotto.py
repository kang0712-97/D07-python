"""로또 번호 생성기: 버튼을 누르면 6개 숫자 5세트와 날짜가 나옵니다."""
import random
import tkinter as tk
from datetime import datetime

SETS = 5
PICKS = 6

# 동행복권 공 색상 규칙: 번호 구간별 색
COLOR_RANGES = [
    (10, "#FBC400", "black"),   # 1~10  노랑
    (20, "#69C8F2", "black"),   # 11~20 파랑
    (30, "#FF7272", "black"),   # 21~30 빨강
    (40, "#AAAAAA", "black"),   # 31~40 회색
    (45, "#B0D840", "black"),   # 41~45 초록
]


def ball_color(number):
    for limit, bg, fg in COLOR_RANGES:
        if number <= limit:
            return bg, fg


def make_sets():
    return [sorted(random.sample(range(1, 46), PICKS)) for _ in range(SETS)]


def draw():
    date_label.config(text=datetime.now().strftime("%Y년 %m월 %d일 %H:%M:%S 추첨"))
    for row, numbers in zip(rows, make_sets()):
        for label, number in zip(row, numbers):
            bg, fg = ball_color(number)
            label.config(text=str(number), bg=bg, fg=fg)


root = tk.Tk()
root.title("로또 번호 생성기")
root.resizable(False, False)

date_label = tk.Label(root, text="버튼을 눌러 번호를 뽑아 보세요", font=("Helvetica", 14))
date_label.pack(padx=20, pady=(16, 8))

board = tk.Frame(root)
board.pack(padx=20, pady=8)

rows = []
for r in range(SETS):
    tk.Label(board, text=f"{chr(65 + r)} 세트", font=("Helvetica", 12, "bold"), width=6).grid(row=r, column=0, pady=4)
    row = []
    for c in range(PICKS):
        ball = tk.Label(board, text="-", width=4, height=2, font=("Helvetica", 14, "bold"), bg="#EEEEEE", relief="groove")
        ball.grid(row=r, column=c + 1, padx=3, pady=4)
        row.append(ball)
    rows.append(row)

tk.Button(root, text="번호 뽑기", font=("Helvetica", 14), command=draw).pack(pady=(8, 16))

# macOS에서 창이 다른 창 뒤에 숨는 일을 막기 위해 맨 앞으로 올림
root.update()
root.lift()
root.attributes("-topmost", True)
root.after(500, lambda: root.attributes("-topmost", False))
root.focus_force()

root.mainloop()
