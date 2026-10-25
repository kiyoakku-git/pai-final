# 言葉で指示するお片付けロボット / A Robot That Tidies Up from Language Instructions

Physical AI 応用編1 最終課題のコードです。英語の指示文を受け取ったロボットアーム（Franka）が、カメラで対象のブロックを見つけてトレーへ運び、入ったかどうかをもう一度カメラで確かめます。

- 動画: https://youtu.be/GkUuEWGcj8k
- シミュレータ: Genesis 1.4.3 ／ 物体検出: OWLv2 ／ ノードのつなぎ: dora-rs 1.0.1

## 構成

```
planner --look, command--> sim --image--> detector --detection--> planner
sim --done--> planner
detector --detection--> recorder <--done-- sim   (結果を results.csv に記録)
```

| ノード | 役割 |
| --- | --- |
| planner | 指示文から対象のブロックを決め、1個ずつ「見る」「つかんで運ぶ」を指示する。置いた後に入っていなければやり直す（最大 MAX_TRIES 回） |
| sim | Genesis でアームを動かし、カメラ画像と動作の完了を送る |
| detector | OWLv2 で色ごとにブロックを検出し、深度から上面の点を選んで3次元位置を求める |
| recorder | 置いた後のカメラの判定と、シミュレータの正解を CSV に記録する |

## 動かし方

必要なもの: Python 3、genesis-world 1.4.3、dora-rs 1.0.1（CLI と Python パッケージ）、transformers、torch、numpy、pyarrow、Pillow

```
cd dora
dora run dataflow.yml
```

設定は `dora/dataflow.yml` の env で変えます。

| 設定 | 意味 |
| --- | --- |
| INSTRUCTION | 指示文（例: `clean up all the blocks`、`put the red and yellow blocks in the tray`）。planner と recorder の2か所を同じにする |
| MAX_TRIES | 1個のブロックをやり直す最大回数（既定 2） |
| RANDOM | `"1"` でブロックをランダム配置（seed をログに表示）、`"0"` で固定配置 |

動画は `outputs/dora/video.mp4`、記録は `outputs/dora/results.csv` に保存されます。

dora を使わずに1本のスクリプトで動かす場合:

```
python scripts/run_task.py "clean up all the blocks"
```

## 結果

| 実験 | 結果 | 記録 |
| --- | --- | --- |
| ランダム配置10回（ブロック40個） | 40/40 成功、カメラの判定と正解が 40/40 一致 | results/random10.csv |
| 位置推定の誤差（4個） | 約2mm（枠の中心1ピクセルを使う単純法は約11mm） | scripts/detect_check.py |
| KP を1/10にした比較 | 8回すべて失敗。カメラも全件「入っていない」と判定 | results/kp_test.csv |

## ファイル

- `src/` シーン、検出、アーム制御、指示文の解釈
- `dora/` dataflow.yml と各ノード
- `scripts/` 動作確認用のスクリプト
- `results/` 実験の記録
