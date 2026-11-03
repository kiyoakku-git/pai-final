# brain_test.py   R6-1

import json
from transformers import pipeline
llm = pipeline("text-generation", model="Qwen/Qwen2.5-1.5B-Instruct")

rules = """あなたは、ロボットを制御するための指示を出すAIです。
ユーザーからの指示を受けてAIが行うべき動作をJSON形式で返してください。
1. 返事は JSON だけにすること（説明文は付けない）
2. 返事のキーは steps だけ。steps は手順のリストで、各手順は pick と place_on を持つ辞書
3. 色は英語で "red block" のように書くこと
4. 使える名前は red block, yellow block, green block, blue block の 4 つだけ
5. 指示に出てくる順番に並べる
"""
example_answer = """{"steps": [
  {"pick": "red block",   "place_on": "yellow block"},
  {"pick": "green block", "place_on": "red block"}
]}"""
messages = [
    {"role": "system",    "content": rules},
    {"role": "user",      "content": "赤を黄色の上に置け。次に緑を赤の上に置け。"},
    {"role": "assistant", "content": example_answer},
    {"role": "user",      "content": "青を緑の上に置け。次に黄色を青の上に置け。"},
]

out = llm(messages, max_new_tokens=128, do_sample=False)
answer = out[0]["generated_text"][-1]["content"]

print (answer)
plan = json.loads(answer)

print("steps    =", plan["steps"])
print("len steps=", len(plan["steps"]))
