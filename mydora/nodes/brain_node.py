# brain_node.py R6-4

import os
import json
from transformers import pipeline
from dora import Node 
import pyarrow as pa

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
    {"role": "user",   "content": os.environ["INSTRUCTION"]},
]
send_message = False
node = Node()
for event in node:
    if event["type"] == "STOP":
        break
    if event["type"] == "INPUT":

        if event["id"] == "tick": # 最初のtickの合図のみ受ける
            if not send_message:
                send_message = True

                out = llm(messages, max_new_tokens=64, do_sample=False)
                answer = out[0]["generated_text"][-1]["content"]

                print("LLM:", answer)
                out_msg = json.loads(answer)
                node.send_output("plan", pa.array([json.dumps(out_msg)]))   



