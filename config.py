import sys
import pygame
import os

is_web = sys.platform == 'emscripten'

APP_NAME_JP = "メルドエイト"
APP_NAME_EN = "Meld8"
APP_VERSION = "v1.0"

SCREEN_WIDTH = 0
SCREEN_HEIGHT = 0
SCALE = 1.0
L = {}
screen = None

BG_COLOR = (0, 100, 50)       
CARD_BG = (255, 255, 255)     
CARD_BORDER = (180, 180, 180) 
TEXT_COLOR = (255, 255, 255)
RED = (220, 30, 30)      
BLACK = (20, 20, 20)     
GOLD = (255, 215, 0)
CYAN_HIGHLIGHT = (50, 200, 255)
BUTTON_COLOR = (40, 120, 200)
BUTTON_HOVER = (60, 140, 240)
QUIT_BUTTON_COLOR = (180, 40, 40)
QUIT_BUTTON_HOVER = (220, 60, 60)
CONFIRM_YES_COLOR = (200, 50, 50)
CONFIRM_NO_COLOR = (60, 160, 60)
TSUMO_BADGE_BG = GOLD
TSUMO_BADGE_TEXT = BLACK

font_giant_title = None
font_large = None
font_mid = None
font_small = None
font_tiny = None
font_agari_title = None

LANG = "JP"

MSG = {
    "APP_DESC": {"EN": "Meld Eight / Mahjong-like card game", "JP": "メルドエイト / 麻雀風トランプゲーム"},
    "START_GAME": {"EN": "START GAME", "JP": "ゲームスタート"},
    "QUICK_GUIDE": {"EN": "RULES", "JP": "ルール説明"},
    "QUIT_GAME": {"EN": "QUIT GAME", "JP": "ゲーム終了"},
    "LANG_BTN": {"EN": "Language: EN (Click to JP)", "JP": "言語: 日本語 (Click to EN)"},
    "DEALER_DRAW_TITLE": {"EN": "DEALER DRAW RESULTS", "JP": "親決めドロー結果"},
    "DREW": {"EN": "drew:", "JP": "引いたカード:"},
    "WINNER_DEALER": {"EN": "WINNER (Dealer)", "JP": "親 (Dealer)"},
    "START_ROUND": {"EN": "START ROUND", "JP": "ラウンド開始"},
    "QUIT_CONFIRM_TITLE": {"EN": "QUIT GAME?", "JP": "ゲームを終了しますか？"},
    "QUIT_CONFIRM_DESC": {"EN": "Current progress will be lost.", "JP": "現在の進行状況は失われます。"},
    "YES_QUIT": {"EN": "YES, QUIT", "JP": "はい、終了する"},
    "NO_RETURN": {"EN": "NO, RETURN", "JP": "いいえ、戻る"},
    "ROUND_REQ_2": {"EN": "Round: {}/6 (2 Fan Req)", "JP": "局: {}/6 (2翻縛り)"},
    "ROUND_REQ_1": {"EN": "Round: {}/6 (Min 1 Fan)", "JP": "局: {}/6 (1翻縛り)"},
    "DECK": {"EN": "Deck: {}", "JP": "山札: {}"},
    "DORA": {"EN": "Dora:", "JP": "ドラ:"},
    "NONE": {"EN": "None", "JP": "なし"},
    "BTN_QUIT": {"EN": "Quit", "JP": "終了"},
    "BTN_GUIDE": {"EN": "Rules", "JP": "ルール説明"},
    "BTN_SOUND_ON": {"EN": "♪ ON", "JP": "♪ ON"},
    "BTN_SOUND_OFF": {"EN": "♪ OFF", "JP": "♪ OFF"},
    "DEALER_TAG": {"EN": "(Dealer)", "JP": "(親)"},
    "SCORE": {"EN": "Score: {:,}", "JP": "スコア: {:,}"},
    "DISCARDS_COM": {"EN": "{} Discards:", "JP": "{} の捨て牌:"},
    "DISCARDS_YOURS": {"EN": "Your Discards:", "JP": "あなたの捨て牌:"},
    "YOU": {"EN": "You", "JP": "あなた"},
    "SORT_SEQ": {"EN": "Sort: Sequence", "JP": "ソート: 順子"},
    "SORT_TRIP": {"EN": "Sort: Triplet", "JP": "ソート: 刻子"},
    "DRAW_CARD": {"EN": "Draw Card", "JP": "ツモる"},
    "WAITS": {"EN": "Waits:", "JP": "待ち:"},
    "FURITEN": {"EN": "(Furiten)", "JP": "(フリテン)"},
    "TSUMO_TINY": {"EN": "Tsumo", "JP": "ツモ"},
    "BADGE_DRAW": {"EN": "DRAW", "JP": "ツモ"},
    "BADGE_CALL": {"EN": "CALL", "JP": "鳴き"},
    "RON": {"EN": "RON", "JP": "ロン"},
    "PONG": {"EN": "PONG", "JP": "ポン"},
    "CHI": {"EN": "CHI", "JP": "チー"},
    "PASS": {"EN": "PASS", "JP": "パス"},
    "TSUMO_BTN": {"EN": "TSUMO", "JP": "ツモ"},
    "COMBO_SEL_TITLE": {"EN": "SELECT CARDS FOR {}", "JP": "{} に使用するカードを選択"},
    "COMBO_SEL_TARGET": {"EN": "Target:", "JP": "対象牌:"},
    "SELECT": {"EN": "SELECT", "JP": "選択"},
    "CANCEL": {"EN": "CANCEL", "JP": "キャンセル"},
    "ALERT_LATE": {"EN": "LATE ROUND WARNING", "JP": "後半戦 警告"},
    "ALERT_FINAL": {"EN": "FINAL ROUND WARNING", "JP": "最終局 警告"},
    "ALERT_DESC1": {"EN": "2 Yaku Fan Minimum is active!", "JP": "2翻縛りが有効です！"},
    "ALERT_DESC2": {"EN": "Dora, Dealer Bonus, and Pure Seq Bonus do not count for shibari.", "JP": "ドラ、親ボーナス、順子ボーナスは縛りの翻数に含みません。"},
    "ACKNOWLEDGE": {"EN": "ACKNOWLEDGE", "JP": "確認"},
    "WIN_TSUMO": {"EN": "WIN: {} (TSUMO)", "JP": "アガリ: {} (ツモ)"},
    "WIN_RON": {"EN": "WIN: {} (RON from {})", "JP": "アガリ: {} ({} からロン)"},
    "TOTAL_SCORE_PTS": {"EN": "Total Score: {:,} pts", "JP": "合計スコア: {:,} 点"},
    "NEXT_ROUND": {"EN": "NEXT ROUND", "JP": "次局へ"},
    "SHOW_RESULTS": {"EN": "SHOW RESULTS", "JP": "結果を見る"},
    "DRAW_TITLE": {"EN": "EXHAUSTIVE DRAW", "JP": "流局"},
    "DRAW_DESC": {"EN": "Deck ran out of available cards.", "JP": "山札がなくなりました。"},
    "RETRY_ROUND": {"EN": "RETRY ROUND", "JP": "この局をやり直す"},
    "FINAL_RESULTS": {"EN": "FINAL RESULTS", "JP": "最終結果"},
    "RANK": {"EN": "Rank {}: {}", "JP": "第{}位: {}"},
    "FINAL_SCORE_DETAIL": {"EN": "Score: {:,} | Uma: {:+,} -> Total: {:,}", "JP": "素点: {:,} | ウマ: {:+,} -> 最終: {:,}"},
    "RETURN_TITLE": {"EN": "RETURN TO TITLE", "JP": "タイトルへ戻る"},
    "GUIDE_TITLE": {"EN": "Meld8 Rules", "JP": "Meld8 ルール説明"},
    "GUIDE_CLOSE": {"EN": "CLOSE", "JP": "閉じる"},
    "ETC": {"EN": "etc.", "JP": "など"}
}

GUIDE_TEXTS_EN = [
    ("1. Basic Rules", GOLD),
    (" - 3 Players. 52 cards + 1 Joker.", TEXT_COLOR),
    ("   Basic Hand: 3-card meld + 3-card meld + 2-card pair.", TEXT_COLOR),
    (" - Fixed 6 rounds. Round 6 requires a strict min of 2 Fan.", TEXT_COLOR),
    ("2. Cards & Jokers", GOLD),
    (" - A, J, Q, K act like Honor tiles (Yakuhai). 2-10 are Simples.", TEXT_COLOR),
    (" - Joker is wild but CANNOT be discarded or used in a Pair.", TEXT_COLOR),
    ("3. Calling (Naki) & Scoring", GOLD),
    (" - Calling (Pong/Chi) is limited to ONCE per round.", TEXT_COLOR),
    (" - Base Score = Total Fan x 2000 pts.", TEXT_COLOR)
]

GUIDE_TEXTS_JP = [
    ("1. 基本ルール", GOLD),
    (" - 3人プレイ。トランプ52枚 + Joker1枚を使用します。", TEXT_COLOR),
    ("   基本アガリ形: 面子(3枚) + 面子(3枚) + 対子(2枚) の8枚。", TEXT_COLOR),
    (" - 全6局。第6局は2翻縛り（ドラ等は含まず通常役で2翻）となります。", TEXT_COLOR),
    ("2. カードとJoker", GOLD),
    (" - A, J, Q, K は役牌。2〜10 はタンヤオ対象の数字牌です。", TEXT_COLOR),
    (" - Jokerは万能ですが、捨てることと対子(ペア)への使用はできません。", TEXT_COLOR),
    ("3. 鳴き（ポン・チー）と得点", GOLD),
    (" - 鳴きは1局につき各プレイヤー1回のみ可能です。", TEXT_COLOR),
    (" - 基本得点 ＝ 合計翻数 × 2000点 です。", TEXT_COLOR)
]

def S(v):
    global SCALE
    return max(1, int(v * SCALE))

def load_fonts():
    global font_giant_title, font_large, font_mid, font_small, font_tiny, font_agari_title
    
    font_path = "NotoSansJP-Bold.ttf"
    
    def load_font(size):
        if os.path.exists(font_path):
            return pygame.font.Font(font_path, S(size))
        else:
            return pygame.font.SysFont("arial", S(size))
            
    font_giant_title = load_font(60)
    font_large = load_font(40)
    font_mid = load_font(26)
    font_small = load_font(18)
    font_tiny = load_font(13)
    font_agari_title = load_font(42)

def apply_resolution():
    global SCREEN_WIDTH, SCREEN_HEIGHT, SCALE, L, screen
    disp_w, disp_h = 1080, 1920
    
    try:
        if is_web:
            import js
            try:
                style = js.document.createElement("style")
                style.innerHTML = """
                    html, body, #status, #box, #canvas { 
                        background-color: #006432 !important; 
                        margin: 0; padding: 0;
                    }
                """
                js.document.head.appendChild(style)
            except Exception:
                pass

            dpr = 1.0
            try:
                dpr = float(js.window.devicePixelRatio)
            except Exception:
                pass
            disp_w = int(js.window.innerWidth * dpr)
            disp_h = int(js.window.innerHeight * dpr)
        else:
            info = pygame.display.Info()
            disp_w, disp_h = info.current_w, info.current_h
    except Exception:
        pass
        
    if disp_w <= 0 or disp_h <= 0:
        disp_w, disp_h = 1080, 1920

    internal_w = 1080
    internal_h = 1920
    
    scale_w = disp_w / internal_w
    scale_h = disp_h / internal_h
    SCALE = min(scale_w, scale_h)
    
    SCREEN_WIDTH = int(internal_w * SCALE)
    SCREEN_HEIGHT = int(internal_h * SCALE)
    
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    
    L = {
        "COM1_PANEL_X": S(40), "COM1_PANEL_Y": S(110),
        "COM2_PANEL_X": SCREEN_WIDTH - S(480), "COM2_PANEL_Y": S(110),
        "PANEL_W": S(440), "PANEL_H": S(240),
        "DISCARD1_X": S(40), "DISCARD1_Y": S(410),
        "DISCARD2_X": SCREEN_WIDTH - S(440), "DISCARD2_Y": S(410),
        "DISCARD0_X": (SCREEN_WIDTH - S(350)) // 2, "DISCARD0_Y": S(710),
        "PLAYER_PANEL_X": S(40), "PLAYER_PANEL_Y": SCREEN_HEIGHT - S(520),
        "PLAYER_PANEL_W": SCREEN_WIDTH - S(80), "PLAYER_PANEL_H": S(500),
        "PLAYER_CARDS_Y": SCREEN_HEIGHT - S(180),
        "PLAYER_MELDS_X": S(60), "PLAYER_MELDS_Y": SCREEN_HEIGHT - S(480),
        "WAITS_X": S(450), "WAITS_Y": SCREEN_HEIGHT - S(480),
        "ACTION_Y": SCREEN_HEIGHT - S(680),
        "CARD_W": S(60), "CARD_H": S(90),
        "DISCARD_W": S(50), "DISCARD_H": S(75),
        "DISCARD_GAP_X": S(55), "DISCARD_GAP_Y": S(82),
        "PLAYER_CARD_W": S(90), "PLAYER_CARD_H": S(135), "PLAYER_CARD_GAP": S(12),
    }
    
    load_fonts()