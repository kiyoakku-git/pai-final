# brain_test.py   R6-1

import json
from transformers import pipeline
llm = pipeline("text-generation", model="Qwen/Qwen2.5-1.5B-Instruct")


rules = """あなたは、ロボットを制御するための指示を出すAIです。
ユーザーからの指示を受けてAIが行うべき動作をJSON形式で返してください。
1. 返事は JSON だけにすること（説明文は付けない）
2. キーは pick と place_on にすること
3. 色は英語で "red block" のように書くこと
4. 返事の例：
{
  "pick": "red block",
  "place_on": "yellow block"
}
"""
messages = [
    {"role": "system", "content": rules},
    {"role": "user",   "content": "青色をピックアップして緑の上に置け"},
]

out = llm(messages, max_new_tokens=64, do_sample=False)
answer = out[0]["generated_text"][-1]["content"]

print (answer)
plan = json.loads(answer)
print(plan["pick"], plan["place_on"])
