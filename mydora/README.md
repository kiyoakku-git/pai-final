# mydora：カメラで見つけたブロックを運ぶ（dora-rs × Genesis × OWLv2）

## 概要
Genesis シミュレータ上の Franka Panda アームが、カメラ画像から赤いブロックを見つけ、つかんで目標位置 (0.4, -0.3) へ運びます。
ブロックの位置はコードに書かず、OWLv2 による物体検出と点群から求めています。
各機能は dora-rs の3つのノードに分けています。

## ノード構成
```
timer --tick--> planner --look-----> sim --image--> detector
                planner <--detection-------------- detector
                planner --command--> sim
                planner <--done----- sim
```

| ノード | 役割 |
|---|---|
| planner | 最初の tick で撮影を依頼し、検出位置から pick / place の指示を作る。最後に結果を表示する |
| sim | Genesis でシーンを動かす。カメラ画像と点群を送り、指示どおりにアームを動かして録画する |
| detector | OWLv2 で「red block」を検出し、box の中心ピクセルの点群から 3 次元の位置を求める |

| 矢印 | 流れるもの |
|---|---|
| look | 撮影の合図（中身なし） |
| image | RGB と点群をまとめた (480, 640, 6) の配列（shape は metadata） |
| detection | 検出した位置 [x, y, z] |
| command | pick と place の位置 |
| done | 運んだ後のブロックの位置 |

## ファイル
- `r3.yml`：本体のデータフロー（これを実行する）
- `nodes/planner_node.py`, `nodes/sim_node.py`, `nodes/detector_node.py`
- `dataflow.yml`, `r2.yml`, `r4.yml`, `nodes/arm_test.py`, `nodes/det_test.py`：途中段階の練習用（r4.yml は現在のノードでは動きません）

## 動かし方
```
conda activate genesis
cd mydora
dora run r3.yml
```
「ブロックの位置」が表示されたら Ctrl + C で止めます。動画は `r3_demo.mp4` に保存されます。

動作確認環境：macOS / dora-rs 1.0.1 / Genesis 1.4.3 / OWLv2（google/owlv2-base-patch16-ensemble）

## 結果
- 検出位置のずれ：約 8 mm（box にブロックの側面が含まれるため）
- 置いた位置：(0.4012, -0.2973, 0.0199)、目標からの誤差 約 3 mm
- 2 回の実行で同じ値（再現性あり）
- 動画：https://youtu.be/3n01PTKiKNk