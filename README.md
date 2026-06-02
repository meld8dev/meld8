# Meld8

[日本語 (Japanese)](#meld8-日本語) / [English](#meld8-english)

---

## Meld8 [日本語]

Meld8は、トランプを用いた麻雀風のメルドゲームです（ルールも含めてオリジナル）。
本リポジトリでは、Meld8のルールに準拠し、コンピューター（CPU）と対戦できるゲームのソースコードを公開しています。本システムはPythonおよびPygameで開発されており、pygbagを用いてWebAssemblyにコンパイルすることで、ブラウザ上で動作するWebアプリケーションとして配信しています。

### 配信URL
[https://meld8dev.github.io/meld8/]

---

### ゲーム概要

* プレイ人数: 3人（プレイヤー1人、CPU2人）
* 使用カード: 52枚の標準トランプ ＋ Joker1枚（計53枚）
* 勝利条件: 全6局終了時、最終的な持ち点（素点に順位点を加減した値）が最も多いプレイヤーの勝利
* 基本システム: 7枚の配牌からスタートし、ツモと打牌を繰り返して「面子2組＋対子1組」などの計8枚のアガリ形を構築します。

麻雀の戦略性をベースに、トランプの特性を活かした順子ボーナスや赤・黒のスート指定、Jokerの万能性と制限事項を融合させた新しいボードゲームです。

### 公式ルール詳細

役の一覧、Jokerの制限、点数計算および対人戦・2人プレイ用の補足ルールについては、以下の公式ルールブックを参照してください。
* meld8_official_rules_v100.ja.md （本リポジトリ内に同梱）

### 技術スタック

* 開発言語: Python 3
* 主要ライブラリ: Pygame (または Pygame-CE)
* Webコンパイル環境: pygbag (WebAssembly / Emscripten)

### 必須フォントの配置について

本ゲームは、多言語および日本語の正確なテキスト描画を行うため、Google Fontsの **Noto Sans JP (Bold)** を使用します。
ソースコードをローカル環境で実行、またはビルドする場合は、事前に以下の手順でフォントファイルを配置してください。

1. [Google Fonts: Noto Sans JP](https://fonts.google.com/specimen/Noto+Sans+JP) からフォントデータをダウンロードします。
2. ZIPファイルを解凍し、NotoSansJP-Bold.ttf ファイルを main.py と同じルートディレクトリに配置してください。

* 補足: Noto Sans JPは [SIL Open Font License 1.1 (OFL)](https://scripts.sil.org/OFL) に基づきライセンスされているため、本リポジトリへ同梱しています。

### ローカル環境での実行およびビルド手順

#### 1. ネイティブ環境（Python）での直接実行

    # 必要ライブラリのインストール
    pip install pygame

    # ゲームの起動
    python main.py

#### 2. ローカルブラウザ環境（pygbag）でのテスト実行

    # pygbagのインストール
    pip install pygbag

    # ローカルWebサーバーの起動
    pygbag .

起動後、ターミナルに表示されるURL（例: http://localhost:8000 ）にブラウザでアクセスしてください。

### 今後の展開（Androidアプリ化について）

現在、本Webアプリケーション（pygbag環境）をWebView化し、モバイル端末で動作するAndroidアプリとしての配信を準備中です。なお、同Androidアプリ内には広告（マネタイズ要素）を導入する予定です。

### 開発・検証環境に関する付記

本プロジェクトにおけるゲームロジックのコーディング、ルールの精査、アルゴリズムの検証、およびドキュメントの校正にあたり、開発補助ツールとして生成AIを活用しています。

### ライセンス

本プロジェクトは、構成要素に応じて以下の2つのライセンスを適用しています。いずれも著作者の明記を条件に、自由な利用・改変・再配布が可能です。

1. **ソースコード（プログラム）: MIT License**
   * 本リポジトリ内のソースコードには [MIT ライセンス](https://opensource.org/licenses/MIT) が適用されます。
   * Copyright (c) 2026 Hidetaka Yoshida

2. **ゲームルールおよびドキュメント: CC BY 4.0**
   * 本リポジトリ内のルール説明文（.md）およびそのアイデアには、[クリエイティブ・コモンズ 表示 4.0 国際 ライセンス](https://creativecommons.org/licenses/by/4.0/deed.ja) が適用されます。
   * 著作者のクレジット（例: "Original Game Rules by Hidetaka Yoshida"）を明記することで、自由に利用および派生ゲームの作成が可能です。

*(※同梱する NotoSansJP-Bold.ttf については、SIL Open Font License 1.1 が適用されます)*

---

## Meld8 [English]

Meld8 is a mahjong-style melde game using playing cards (including the rules, it was created originally).
This repository contains the source code for the game, built with Python (Pygame) and compiled into a WebAssembly browser app using pygbag.

### Deployment URL
[https://meld8dev.github.io/meld8/]

---

### Game Overview

* Players: 3 players (1 Human vs 2 CPU)
* Cards Used: 52 standard playing cards + 1 Joker (53 cards total)
* Rounds: A full game consists of 6 rounds. The player with the highest final score at the end wins.
* Core Mechanic: Draw and discard to build an 8-card winning hand (e.g., 2 Melds + 1 Pair).

Meld8 combines the deep strategy of Mahjong with the unique properties of playing cards, including sequence bonuses, Red/Black suit constraints, and a Joker that acts as a wild card with specific limitations.

### Official Rules

For a complete list of Yaku (winning patterns), Joker restrictions, and scoring mechanics, please refer to the official rulebook:
* meld8_official_rules_v100.md (Included in this repository)

### Tech Stack

* Language: Python 3
* Framework: Pygame (or Pygame-CE)
* Web Build Tool: pygbag (WebAssembly compiler)

### Font Requirement

To display text and Japanese characters correctly, this game requires the **Noto Sans JP (Bold)** font. If you are running or building the game locally, please ensure the font file is present.

1. Download the font from [Google Fonts: Noto Sans JP](https://fonts.google.com/specimen/Noto+Sans+JP).
2. Extract the ZIP and place the NotoSansJP-Bold.ttf file in the same root directory as main.py.

* Note: Noto Sans JP is licensed under the [SIL Open Font License 1.1 (OFL)], which allows it to be freely bundled and distributed with Open Source projects.

### How to Run & Build Locally

#### 1. Run Natively (Python)

    # Install Pygame
    pip install pygame

    # Run the game
    python main.py

#### 2. Run in Browser (using pygbag)

    # Install pygbag
    pip install pygbag

    # Start the local testing server
    pygbag .

Open your browser and navigate to the provided local URL (e.g., http://localhost:8000).

### Future Roadmap (Android Application)

An Android application version, constructed by wrapping the web application (pygbag environment) via WebView, is currently under development for mobile platforms. Please note that this mobile application is planned to integrate advertisements for monetization.

### Development and Verification Notes

Generative AI tools were utilized as development assistants for writing game logic, auditing rules, verifying algorithms, and proofreading documentation in this project.

### License

This project applies the following two licenses depending on the component. Both allow free use, modification, and redistribution provided that attribution is given to the author.

1. **Source Code (Program): MIT License**
   * The source code in this repository is licensed under the [MIT License](https://opensource.org/licenses/MIT).
   * Copyright (c) 2026 Hidetaka Yoshida

2. **Game Rules and Documentation: CC BY 4.0**
   * The game rules and their core concepts in the .md documents are licensed under the [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/).
   * You are free to use and create derivative works as long as appropriate credit is given (e.g., "Original Game Rules by Hidetaka Yoshida").

*(Note: The bundled NotoSansJP-Bold.ttf font file is distributed under the SIL Open Font License 1.1).*
