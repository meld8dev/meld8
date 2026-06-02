import pygame
import random
import sys
import time
import asyncio
import os

import config
import sound
import logic
from card import Card, SORT_SUIT_ORDER, RANK_ORDER

is_web = sys.platform == 'emscripten'

random.seed(int(time.time() * 1000) ^ id(object()))

pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=1)

sound.sm.init_sounds()
config.apply_resolution()

def translate_yaku(yaku_str, lang):
    if lang == "EN": return yaku_str
    
    trans = {
        "Spade Royal Straight (Double Yakuman)": "スペード・ロイヤル (ダブル役満)",
        "Royal Straight (Yakuman)": "ロイヤルストレート (役満)",
        "Four Crowns Pure Color (Double Yakuman)": "四冠対・純色形 (ダブル役満)",
        "Four Crowns (Yakuman)": "四冠対 (役満)",
        "Kazoe Yakuman (10+ Fan Stacked)": "数え役満 (10翻以上)",
        "Tenho (4 Fan)": "天和 (4翻)",
        "Chiho (4 Fan)": "地和 (4翻)",
        "Concealed Self-Draw (1 Fan)": "面前ツモ (1翻)",
        "Haitei (1 Fan)": "海底 (1翻)",
        "Pure Straight (": "一気通貫 (",
        "Four Pairs (": "四対子 (",
        "Tanyao (": "タンヤオ (",
        "Junchan (": "純チャンタ (",
        "All Red (": "赤一色 (",
        "All Black (": "黒一色 (",
        "Dual Kan-Gantsu (": "両槓子 (",
        "Chanta (": "チャンタ (",
        "Honor Value:": "役牌:",
        "Pure Seq Bonus (+": "順子ボーナス (+",
        "Double Sequence (": "同順子 (",
        "Pinfu (": "ピンフ (",
        "Toitoi (": "トイトイ (",
        "Dora Bonus (+": "ドラ (+",
        "Dealer Bonus (+1 Fan)": "親ボーナス (+1翻)"
    }
    
    res = yaku_str
    for k, v in trans.items():
        res = res.replace(k, v)
        
    res = res.replace(" Fan)", "翻)")
    res = res.replace(" Fan", "翻")
    return res

def create_meld8_icon_surface(size=256):
    scale = 4
    base_size = size * scale
    surf = pygame.Surface((base_size, base_size), pygame.SRCALPHA)
    
    white = (255, 255, 255)
    black = (20, 20, 20)
    red = (220, 10, 10)

    rect = pygame.Rect(0, 0, base_size, base_size)
    corner_radius = int(base_size * 0.15)
    pygame.draw.rect(surf, white, rect, border_radius=corner_radius)
    border_w = max(scale, int(base_size * 0.025))
    pygame.draw.rect(surf, black, rect, width=border_w, border_radius=corner_radius)

    bar_top = int(base_size * 0.22)
    bar_bottom = int(base_size * 0.78)
    bar_w = int(base_size * 0.085)
    bar_gap = int(base_size * 0.05)
    slant = int(base_size * 0.09)
    x0 = int(base_size * 0.12)

    def draw_bar(x, color, slant_down=True):
        if slant_down:
            pts = [(x, bar_top), (x + bar_w, bar_top + slant), (x + bar_w, bar_bottom), (x, bar_bottom)]
        else:
            pts = [(x, bar_top + slant), (x + bar_w, bar_top), (x + bar_w, bar_bottom), (x, bar_bottom)]
        pygame.draw.polygon(surf, color, pts)

    draw_bar(x0, black, slant_down=True)
    draw_bar(x0 + bar_w + bar_gap, red, slant_down=True)
    draw_bar(x0 + 2 * (bar_w + bar_gap), black, slant_down=False)

    eight_cx = int(base_size * 0.72)
    line_w = int(base_size * 0.08)

    r_top = int(base_size * 0.14)
    cy_top = int(base_size * 0.38)
    pygame.draw.circle(surf, black, (eight_cx, cy_top), r_top, line_w)

    r_bot = int(base_size * 0.16)
    cy_bot = int(base_size * 0.62)
    pygame.draw.circle(surf, black, (eight_cx, cy_bot), r_bot, line_w)

    return pygame.transform.smoothscale(surf, (size, size))

pygame.display.set_icon(create_meld8_icon_surface(256))
pygame.display.set_caption(f"{config.APP_NAME_EN} / {config.APP_NAME_JP} {config.APP_VERSION}")
clock = pygame.time.Clock()

class TrumpMahjongGUI:
    def __init__(self):
        self.phase = "TITLE"
        self.player_names = ["COM1", "COM2"]
        self.scores = [30000, 30000, 30000]
        self.round = 1
        self.button_rects = {}
        self.parent_idx = 0
        self.sort_mode = "NORMAL"
        self.current_action_act = None
        self.prompt_sound_played = False
        self.tsumo_agari_sound_played = False
        self.pending_tsumo_agari = None
        self.show_guide = False
        self.my_waits_cache = None
        self.my_waits_cache_hash = None
        self.update_layout_refs()

    def update_layout_refs(self):
        self.player_card_w = config.L["PLAYER_CARD_W"]
        self.player_card_h = config.L["PLAYER_CARD_H"]
        self.player_card_gap = config.L["PLAYER_CARD_GAP"]
        self.player_cards_y = config.L["PLAYER_CARDS_Y"]

    def start_match(self):
        self.dealer_draws = logic.determine_dealer()
        self.parent_idx = self.dealer_draws[0][0]
        self.scores = [30000, 30000, 30000]
        self.round = 1
        self.phase = "DEALER_DRAW"
        sound.sm.play('action')

    def init_round(self):
        self.deck = logic.create_deck()
        self.hands = [[] for _ in range(3)]
        self.melds = [[] for _ in range(3)]
        self.has_naki = [False] * 3
        self.discards = [[] for _ in range(3)]
        self.discard_pile = [] 
        self.last_discarder = None
        self.first_discard_done = False
        self.dora_marker = None
        self.dora_suit = None
        self.dora_rank = None
        self.is_first_turn = [True] * 3
        self.any_naki_occurred = False 
        self.last_tsumo_card = [None] * 3
        
        self.turn = self.parent_idx
        self.pending_actions = []
        self.com_timer = 0
        
        self.phase = "DEALING"
        self.deal_target = self.parent_idx
        self.deal_round = 0
        self.deal_timer = pygame.time.get_ticks()

    def is_dora_card(self, card):
        if not card or card.is_joker or card.rank is None: return False
        return card.suit == self.dora_suit and card.rank == self.dora_rank

    def sort_hand(self, idx):
        if self.sort_mode == "NORMAL":
            self.hands[idx] = sorted(self.hands[idx], key=lambda c: (c.is_joker, SORT_SUIT_ORDER.get(c.suit, 4), RANK_ORDER.get(c.rank, 0)))
        else:
            rc = {}
            for c in self.hands[idx]:
                if not c.is_joker and c.rank: rc[c.rank] = rc.get(c.rank, 0) + 1
            self.hands[idx] = sorted(self.hands[idx], key=lambda c: (c.is_joker, -rc.get(c.rank, 0) if not c.is_joker else 0, RANK_ORDER.get(c.rank, 0) if not c.is_joker else 0, SORT_SUIT_ORDER.get(c.suit, 4)))

    def get_waits_for_player(self, p_idx):
        hand = self.hands[p_idx]
        melds = self.melds[p_idx]
        if len(hand) + sum(len(m) for m in melds) != 7 or len(hand) % 3 != 1: return []
            
        is_furiten = self.is_furiten(p_idx)
        deck_left = len(self.deck)
        req_fan = 2 if self.round >= 4 else 1
        is_parent = (p_idx == self.parent_idx)
        
        owned_cards = set()
        for c in hand:
            if not c.is_joker: owned_cards.add((c.suit, c.rank))
        for m in melds:
            for c in m:
                if not c.is_joker: owned_cards.add((c.suit, c.rank))
        
        waits = []
        for s in logic.SUITS:
            for r in logic.RANKS:
                if (s, r) in owned_cards: continue
                tc = Card(s, r)
                if logic.has_agari_shape(hand + [tc], melds):
                    can_ron = False
                    res_r, fan_r, _, _, _ = logic.check_agari_and_yaku(
                        hand + [tc], melds, False, not self.has_naki[p_idx],
                        self.dora_suit, self.dora_rank, tc, deck_left,
                        self.is_first_turn[p_idx], self.any_naki_occurred, is_parent, req_fan
                    )
                    if res_r and not is_furiten: can_ron = True

                    can_tsumo = False
                    res_t, fan_t, _, _, _ = logic.check_agari_and_yaku(
                        hand + [tc], melds, True, not self.has_naki[p_idx],
                        self.dora_suit, self.dora_rank, tc, deck_left,
                        self.is_first_turn[p_idx], self.any_naki_occurred, is_parent, req_fan
                    )
                    if res_t: can_tsumo = True

                    if can_ron or can_tsumo:
                        tsumo_only = is_furiten or (can_tsumo and not can_ron)
                        waits.append((tc, tsumo_only))
        return waits

    def update_waits_cache(self):
        state_str = "".join(sorted([f"{c.suit}{c.rank}" for c in self.hands[0]])) + str(len(self.discard_pile))
        if getattr(self, "my_waits_cache_hash", None) == state_str: return self.my_waits_cache
        waits = self.get_waits_for_player(0)
        self.my_waits_cache = waits
        self.my_waits_cache_hash = state_str
        return waits

    def update_game(self):
        current_time = pygame.time.get_ticks()
        if self.phase == "DEALING":
            if current_time - self.deal_timer > 50:
                self.hands[self.deal_target].append(self.deck.pop(0))
                sound.sm.play('deal')
                self.deal_timer = current_time
                self.deal_target = (self.deal_target + 1) % 3
                if self.deal_target == self.parent_idx: self.deal_round += 1
                if self.deal_round == 7:
                    self.sort_hand(0)
                    if self.round >= 4: self.phase = "FINAL_ROUND_ALERT"
                    else: self.phase = "TSUMO"
                    self.prompt_sound_played = False
                    self.tsumo_agari_sound_played = False
            return

        if self.phase == "ACTION_WAIT" and not self.prompt_sound_played:
            acts = [a for a in self.get_top_pending_actions() if a["p_idx"] == 0]
            if any(a["action"] == "RON" for a in acts): sound.play_ron_sound()
            elif any(a["action"] == "PONG" for a in acts): sound.play_pong_sound()
            elif any(a["action"] == "CHI" for a in acts): sound.play_chi_sound()
            self.prompt_sound_played = True
            
        if self.phase == "TSUMO" and self.turn == 0 and not self.prompt_sound_played:
            if len(self.deck) > 0: sound.sm.play('my_turn')
            self.prompt_sound_played = True
            
        if getattr(self, "phase", "") == "TSUMO_AGARI_WAIT" and not getattr(self, 'tsumo_agari_sound_played', False):
            sound.sm.play('action')
            self.tsumo_agari_sound_played = True

        if self.phase in ["TITLE", "DEALER_DRAW", "AGARI_SHOW", "ROUND_END", "GAME_OVER", "ACTION_WAIT", "QUIT_CONFIRM", "COMBO_SELECT", "TSUMO_AGARI_WAIT", "FINAL_ROUND_ALERT", "HALTED"]: 
            return

        if self.phase == "TSUMO" and len(self.deck) == 0:
            sound.sm.play('draw')
            self.phase = "ROUND_END"
            return

        if self.phase == "TSUMO" and self.turn != 0:
            if self.com_timer == 0: self.com_timer = current_time
            if current_time - self.com_timer < 600: return
            self.com_timer = 0
            tsumo = self.deck.pop(0)
            self.hands[self.turn].append(tsumo)
            self.last_tsumo_card[self.turn] = tsumo
            
            is_m = not self.has_naki[self.turn]
            is_p = (self.turn == self.parent_idx)
            req = 2 if self.round >= 4 else 1
            
            agari, sc, yk, mult, kaze = logic.check_agari_and_yaku(self.hands[self.turn], self.melds[self.turn], True, is_m, self.dora_suit, self.dora_rank, tsumo, len(self.deck), self.is_first_turn[self.turn], self.any_naki_occurred, is_p, required_total_fan=req)
            if agari:
                self.process_win(self.turn, self.turn, sc, yk, mult, kaze, True, tsumo)
                return
            
            self.is_first_turn[self.turn] = False
            disc_idx = logic.evaluate_com_discard_scores(self.hands[self.turn])
            discarded = self.hands[self.turn].pop(disc_idx)
            self.last_tsumo_card[self.turn] = None
            self.process_discard(self.turn, discarded)

        elif self.phase == "CHECK_RON":
            if self.com_timer == 0: self.com_timer = current_time
            if current_time - self.com_timer < 600: return
            self.com_timer = 0
            self.execute_pending()

    def process_discard(self, drawer_idx, card):
        self.last_discard = card
        self.last_discarder = drawer_idx
        self.discards[drawer_idx].append(card)
        self.discard_pile.append(card)

        is_dealer_first_discard = (drawer_idx == self.parent_idx and not self.first_discard_done)
        if not self.first_discard_done:
            self.dora_marker = card
            self.dora_suit, self.dora_rank = logic.get_dora_card(card)
            self.first_discard_done = True

        self.pending_actions = []
        req = 2 if self.round >= 4 else 1

        for offset in [1, 2]:
            i = (drawer_idx + offset) % 3
            agari, sc, yk, mult, kaze = logic.check_agari_and_yaku(
                self.hands[i] + [card], self.melds[i], False,
                not self.has_naki[i], self.dora_suit, self.dora_rank,
                card, len(self.deck), self.is_first_turn[i],
                self.any_naki_occurred, i == self.parent_idx, required_total_fan=req
            )
            if agari and not self.is_furiten(i):
                self.pending_actions.append({
                    "p_idx": i, "action": "RON", "distance": offset,
                    "score": sc, "yaku": yk, "mult": mult, "kazee": kaze
                })

        can_call = len(self.deck) > 0 and not is_dealer_first_discard
        if can_call:
            for offset in [1, 2]:
                i = (drawer_idx + offset) % 3
                if not self.has_naki[i]:
                    p_combos = logic.valid_pong_combos(self.hands[i], card)
                    if p_combos:
                        do_call = True if i == 0 else random.random() < 0.4
                        if do_call: self.pending_actions.append({"p_idx": i, "action": "PONG", "distance": offset, "combos": p_combos})

            next_p = (drawer_idx + 1) % 3
            if not self.has_naki[next_p] and card.rank and not card.is_joker:
                combos = logic.valid_chi_combos(self.hands[next_p], card)
                if combos:
                    do_call = True if next_p == 0 else random.random() < 0.4
                    if do_call: self.pending_actions.append({"p_idx": next_p, "action": "CHI", "distance": 1, "combos": combos})

        self.resolve_pending_phase()

    def is_furiten(self, p_idx):
        pool = logic.get_shape_waiting_pool(self.hands[p_idx], self.melds[p_idx])
        return any(disc.rank == wait_rank and disc.suit == wait_suit for disc in self.discards[p_idx] for wait_rank, wait_suit, _ in pool)

    def get_top_pending_actions(self):
        if not self.pending_actions: return []
        for action_name in ["RON", "PONG", "CHI"]:
            acts = [a for a in self.pending_actions if a["action"] == action_name]
            if acts:
                min_dist = min(a.get("distance", 99) for a in acts)
                return [a for a in acts if a.get("distance", 99) == min_dist]
        return []

    def resolve_pending_phase(self):
        top_actions = self.get_top_pending_actions()
        if top_actions and any(a["p_idx"] == 0 for a in top_actions):
            self.phase = "ACTION_WAIT"
            self.prompt_sound_played = False
        else:
            self.phase = "CHECK_RON"

    def remove_called_discard_from_furiten_history(self):
        if self.last_discarder is None: return
        history = self.discards[self.last_discarder]
        for idx in range(len(history) - 1, -1, -1):
            if history[idx] is self.last_discard:
                del history[idx]
                break
        for idx in range(len(self.discard_pile) - 1, -1, -1):
            if self.discard_pile[idx] is self.last_discard:
                del self.discard_pile[idx]
                break

    def perform_pong(self, act):
        p = act["p_idx"]
        self.last_tsumo_card[p] = None
        if p != 0: sound.play_pong_sound()
        self.prompt_sound_played = False
        c1, c2 = act["combos"][0]
        if c1 not in self.hands[p] or c2 not in self.hands[p]:
            self.pending_actions = []
            self.phase = "CHECK_RON"
            return
        self.remove_called_discard_from_furiten_history()
        self.hands[p].remove(c1); self.hands[p].remove(c2)
        self.melds[p].append([self.last_discard, c1, c2])
        self.has_naki[p] = True
        self.any_naki_occurred = True
        self.is_first_turn[p] = False
        self.turn = p
        if p != 0:
            disc_idx = logic.evaluate_com_discard_scores(self.hands[p])
            self.process_discard(p, self.hands[p].pop(disc_idx))
        else: self.phase = "DISCARD_WAIT"

    def perform_chi(self, act):
        p = act["p_idx"]
        self.last_tsumo_card[p] = None
        if p != 0: sound.play_chi_sound()
        self.prompt_sound_played = False
        c1, c2 = act["combos"][0]
        if c1 not in self.hands[p] or c2 not in self.hands[p]:
            self.pending_actions = []
            self.phase = "CHECK_RON"
            return
        self.remove_called_discard_from_furiten_history()
        self.hands[p].remove(c1); self.hands[p].remove(c2)
        self.melds[p].append([self.last_discard, c1, c2])
        self.has_naki[p] = True
        self.any_naki_occurred = True
        self.is_first_turn[p] = False
        self.turn = p
        if p != 0:
            disc_idx = logic.evaluate_com_discard_scores(self.hands[p])
            self.process_discard(p, self.hands[p].pop(disc_idx))
        else: self.phase = "DISCARD_WAIT"

    def execute_pending(self):
        top_actions = self.get_top_pending_actions()
        if top_actions:
            act = top_actions[0]
            if act["action"] == "RON":
                self.process_win(act["p_idx"], self.last_discarder, act["score"], act["yaku"], act["mult"], act["kazee"], False, self.last_discard)
                return
            if act["action"] == "PONG": self.perform_pong(act); return
            if act["action"] == "CHI": self.perform_chi(act); return

        if self.last_discarder is not None:
            self.is_first_turn[self.last_discarder] = False
            self.turn = (self.last_discarder + 1) % 3
        else:
            self.is_first_turn[self.turn] = False
            self.turn = (self.turn + 1) % 3
        self.phase = "TSUMO"
        self.prompt_sound_played = False

    def process_win(self, winner, loser, fan_count, yaku, mult, is_kazee, is_tsumo, agari_card):
        if is_tsumo: sound.sm.play('tsumo_win_fanfare')
        else:
            if winner != 0: sound.sm.play('ron_win_fanfare')
            else: sound.sm.play('win_fanfare')

        is_parent = (winner == self.parent_idx)
        
        if mult > 0: 
            base = 20000 if not is_parent else 30000
            final_pts = base * min(mult, 2)
        else: 
            final_pts = logic.calculate_score(fan_count, is_parent)

        hand_cards = list(self.hands[winner])
        if is_tsumo:
            for i in range(len(hand_cards)-1, -1, -1):
                if hand_cards[i] is agari_card:
                    hand_cards.pop(i)
                    break

        is_seq_yaku = any(y.startswith("Pinfu") or "Sequence" in y or "Straight" in y or "Chanta" in y or "Junchan" in y for y in yaku)
        if any(c.is_joker for c in hand_cards) and is_seq_yaku:
            hand_cards.sort(key=lambda c: (c.is_joker, SORT_SUIT_ORDER.get(c.suit, 4), RANK_ORDER.get(c.rank, 0)))
        else:
            rc = {}
            for c in hand_cards:
                if not c.is_joker and c.rank: rc[c.rank] = rc.get(c.rank, 0) + 1
            hand_cards.sort(key=lambda c: (c.is_joker, -rc.get(c.rank, 0) if not c.is_joker else 0, RANK_ORDER.get(c.rank, 0) if not c.is_joker else 0, SORT_SUIT_ORDER.get(c.suit, 4)))

        self.agari_data = {
            "winner": winner, "loser": loser, "is_tsumo": is_tsumo, 
            "yaku": yaku, "final_points": final_pts,
            "hand_cards": hand_cards, "agari_card": agari_card,
            "melds": list(self.melds[winner])
        }
        
        if is_tsumo:
            pay = final_pts // 2
            for i in range(3):
                if i == winner: self.scores[i] += final_pts
                else: self.scores[i] -= pay
        else:
            self.scores[winner] += final_pts
            self.scores[loser] -= final_pts

        self.phase = "AGARI_SHOW"

    def process_game_over(self):
        s_idx = sorted(range(3), key=lambda k: self.scores[k], reverse=True)
        self.uma = [0]*3
        if self.scores[s_idx[0]] == self.scores[s_idx[1]] == self.scores[s_idx[2]]: pass
        elif self.scores[s_idx[1]] == self.scores[s_idx[2]]: 
            self.uma[s_idx[0]], self.uma[s_idx[1]], self.uma[s_idx[2]] = 6000, -3000, -3000
        elif self.scores[s_idx[0]] == self.scores[s_idx[1]]: 
            self.uma[s_idx[0]], self.uma[s_idx[1]], self.uma[s_idx[2]] = 2000, 2000, -4000
        else: 
            self.uma[s_idx[0]], self.uma[s_idx[1]], self.uma[s_idx[2]] = 6000, -2000, -4000
            
        self.final_scores = [self.scores[i] + self.uma[i] for i in range(3)]
        self.phase = "GAME_OVER"

    def get_pname(self, idx):
        if idx == 0: return config.MSG["YOU"][config.LANG]
        return self.player_names[idx - 1]

    def handle_click(self, pos):
        if self.phase == "HALTED":
            return
            
        if getattr(self, "show_guide", False):
            if self.button_rects.get("CLOSE_GUIDE") and self.button_rects["CLOSE_GUIDE"].collidepoint(pos):
                sound.sm.play('action'); self.show_guide = False
            return
            
        if self.button_rects.get("TOGGLE_SOUND") and self.button_rects["TOGGLE_SOUND"].collidepoint(pos):
            sound.sm.toggle_mute()
            sound.sm.play('action')
            return

        if self.button_rects.get("GUIDE") and self.button_rects["GUIDE"].collidepoint(pos):
            if self.phase not in ["DEALER_DRAW", "QUIT_CONFIRM", "COMBO_SELECT", "FINAL_ROUND_ALERT", "AGARI_SHOW", "ROUND_END", "GAME_OVER"]:
                sound.sm.play('action')
                self.show_guide = True
                return

        if self.phase == "TITLE":
            if self.button_rects.get("LANG_TOGGLE") and self.button_rects["LANG_TOGGLE"].collidepoint(pos):
                sound.sm.play('action')
                config.LANG = "EN" if config.LANG == "JP" else "JP"
                return
            if self.button_rects.get("BTN_START") and self.button_rects["BTN_START"].collidepoint(pos):
                sound.sm.play('action')
                self.start_match()
            elif self.button_rects.get("BTN_GUIDE_TITLE") and self.button_rects["BTN_GUIDE_TITLE"].collidepoint(pos):
                sound.sm.play('action')
                self.show_guide = True
            elif self.button_rects.get("QUIT_TITLE") and self.button_rects["QUIT_TITLE"].collidepoint(pos):
                sound.sm.play('com_win')
                self.pre_quit_phase = self.phase
                self.phase = "QUIT_CONFIRM"
            return
            
        elif self.phase == "FINAL_ROUND_ALERT":
            if self.button_rects.get("ACK_FINAL_ROUND") and self.button_rects["ACK_FINAL_ROUND"].collidepoint(pos):
                sound.sm.play('draw'); self.phase = "TSUMO"
            return

        if self.phase == "QUIT_CONFIRM":
            if self.button_rects.get("CONFIRM_YES") and self.button_rects["CONFIRM_YES"].collidepoint(pos):
                if is_web:
                    self.phase = "HALTED"
                    try:
                        import js
                        js.window.eval("window.close();")
                    except Exception:
                        pass
                else:
                    pygame.quit()
                    sys.exit()
            elif self.button_rects.get("CONFIRM_NO") and self.button_rects["CONFIRM_NO"].collidepoint(pos):
                sound.sm.play('draw')
                self.phase = getattr(self, "pre_quit_phase", "TITLE")
            return
            
        elif self.phase == "COMBO_SELECT":
            if self.button_rects.get("CANCEL_SELECT") and self.button_rects["CANCEL_SELECT"].collidepoint(pos):
                sound.sm.play('action'); self.phase = "ACTION_WAIT"; self.prompt_sound_played = False; return
            for i in range(len(self.current_action_act["combos"])):
                if self.button_rects.get(f"SEL_{i}") and self.button_rects[f"SEL_{i}"].collidepoint(pos):
                    sound.sm.play('action')
                    self.current_action_act["combos"] = [self.current_action_act["combos"][i]]
                    if self.current_action_act["action"] == "PONG": self.perform_pong(self.current_action_act)
                    else: self.perform_chi(self.current_action_act)
                    return

        elif self.phase == "TSUMO_AGARI_WAIT":
            if self.button_rects.get("TSUMO_WIN") and self.button_rects["TSUMO_WIN"].collidepoint(pos):
                a = self.pending_tsumo_agari
                self.process_win(0, 0, a["score"], a["yaku"], a["mult"], a["kazee"], True, a["card"])
                return
            elif self.button_rects.get("PASS_TSUMO") and self.button_rects["PASS_TSUMO"].collidepoint(pos):
                self.phase = "DISCARD_WAIT"
                return

        if self.phase == "DEALER_DRAW" and self.button_rects.get("START_GAME").collidepoint(pos): self.init_round()
        elif self.phase == "AGARI_SHOW" and self.button_rects.get("NEXT").collidepoint(pos):
            if self.round < 6: self.round += 1; self.parent_idx = (self.parent_idx + 1) % 3; self.init_round()
            else: self.process_game_over()
        elif self.phase == "ROUND_END" and self.button_rects.get("NEXT").collidepoint(pos):
            self.init_round()
        elif self.phase == "GAME_OVER" and self.button_rects.get("RESTART").collidepoint(pos):
            sound.sm.play('action')
            self.phase = "TITLE"
            
        elif self.button_rects.get("QUIT_GAME") and self.button_rects["QUIT_GAME"].collidepoint(pos):
            sound.sm.play('com_win')
            self.pre_quit_phase = self.phase
            self.phase = "QUIT_CONFIRM"
            return
            
        elif self.button_rects.get("SORT_MODE") and self.button_rects["SORT_MODE"].collidepoint(pos):
            sound.sm.play('draw'); self.sort_mode = "COUNT" if self.sort_mode == "NORMAL" else "NORMAL"; self.sort_hand(0); return

        elif self.phase == "DISCARD_WAIT" and self.turn == 0:
            w, h, gap = self.player_card_w, self.player_card_h, self.player_card_gap
            sx = (config.SCREEN_WIDTH // 2) - ((len(self.hands[0]) * (w + gap) - gap) // 2)
            y = self.player_cards_y
            for i in range(len(self.hands[0])):
                if pygame.Rect(sx + i*(w+gap), y, w, h).collidepoint(pos):
                    if self.hands[0][i].is_joker: sound.sm.play('com_win'); return 
                    self.process_discard(0, self.hands[0].pop(i))
                    self.sort_hand(0) 
                    return

        elif self.phase == "TSUMO" and self.turn == 0 and self.button_rects.get("DRAW").collidepoint(pos):
            self.prompt_sound_played = False
            sound.sm.play('draw')
            tsmo = self.deck.pop(0)
            self.hands[0].append(tsmo)
            self.last_tsumo_card[0] = tsmo
            
            req = 2 if self.round >= 4 else 1
            agari, sc, yk, ml, kz = logic.check_agari_and_yaku(self.hands[0], self.melds[0], True, not self.has_naki[0], self.dora_suit, self.dora_rank, tsmo, len(self.deck), self.is_first_turn[0], self.any_naki_occurred, self.parent_idx == 0, required_total_fan=req)
            
            if agari: 
                self.pending_tsumo_agari = {"score": sc, "yaku": yk, "mult": ml, "kazee": kz, "card": tsmo}
                self.phase = "TSUMO_AGARI_WAIT"
                self.tsumo_agari_sound_played = False
            else: self.phase = "DISCARD_WAIT"
            self.is_first_turn[0] = False

        elif self.phase == "ACTION_WAIT" and self.turn != 0: 
            acts = [a for a in self.get_top_pending_actions() if a["p_idx"] == 0]
            if not acts: self.resolve_pending_phase(); return
            if any(a["action"] == "RON" for a in acts):
                if self.button_rects.get("RON") and self.button_rects["RON"].collidepoint(pos):
                    a = [x for x in acts if x["action"] == "RON"][0]
                    self.process_win(0, self.last_discarder, a["score"], a["yaku"], a["mult"], a["kazee"], False, self.last_discard)
                    return
            if any(a["action"] == "PONG" for a in acts):
                if self.button_rects.get("PONG") and self.button_rects["PONG"].collidepoint(pos):
                    a = [x for x in acts if x["action"] == "PONG"][0]
                    if len(a["combos"]) > 1: self.phase = "COMBO_SELECT"; self.current_action_act = a
                    else: self.perform_pong(a)
                    return
            if any(a["action"] == "CHI" for a in acts):
                if self.button_rects.get("CHI") and self.button_rects["CHI"].collidepoint(pos):
                    a = [x for x in acts if x["action"] == "CHI"][0]
                    if len(a["combos"]) > 1: self.phase = "COMBO_SELECT"; self.current_action_act = a
                    else: self.perform_chi(a)
                    return
            if self.button_rects.get("PASS") and self.button_rects["PASS"].collidepoint(pos):
                self.pending_actions = [a for a in self.pending_actions if a not in acts]
                self.prompt_sound_played = False
                self.resolve_pending_phase()
                return

    def draw_button(self, label, rect, pos, key, c1=config.BUTTON_COLOR, c2=config.BUTTON_HOVER):
        self.button_rects[key] = rect
        pygame.draw.rect(config.screen, c2 if rect.collidepoint(pos) else c1, rect, border_radius=config.S(6))
        txt = config.font_small.render(label, True, config.TEXT_COLOR)
        config.screen.blit(txt, (rect.x + (rect.width - txt.get_width())//2, rect.y + (rect.height - txt.get_height())//2))

    def draw_guide_overlay(self, pos):
        """(ゲーム内の簡易ルールガイド)"""
        overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        config.screen.blit(overlay, (0, 0))
        pw, ph = config.S(840), config.S(820)
        px, py = (config.SCREEN_WIDTH - pw) // 2, (config.SCREEN_HEIGHT - ph) // 2
        pygame.draw.rect(config.screen, (25, 35, 45), (px, py, pw, ph), border_radius=config.S(16))
        pygame.draw.rect(config.screen, config.GOLD, (px, py, pw, ph), width=config.S(3), border_radius=config.S(16))
        
        t = config.font_large.render(config.MSG["GUIDE_TITLE"][config.LANG], True, config.GOLD)
        config.screen.blit(t, (px + (pw - t.get_width()) // 2, py + config.S(40)))
        
        guide_texts = config.GUIDE_TEXTS_EN if config.LANG == "EN" else config.GUIDE_TEXTS_JP
        sy = py + config.S(120)
        for line, color in guide_texts:
            if color == config.GOLD:
                txt = config.font_mid.render(line, True, color)
                config.screen.blit(txt, (px + config.S(40), sy))
                sy += config.S(45)
            else:
                txt = config.font_small.render(line, True, color)
                config.screen.blit(txt, (px + config.S(60), sy))
                sy += config.S(35)
            if line.startswith("3. "): sy += config.S(15)
        self.draw_button(config.MSG["GUIDE_CLOSE"][config.LANG], pygame.Rect(px + (pw - config.S(250)) // 2, py + ph - config.S(90), config.S(250), config.S(60)), pos, "CLOSE_GUIDE", config.QUIT_BUTTON_COLOR, config.QUIT_BUTTON_HOVER)

    def draw_screen(self, pos):
        if self.phase == "HALTED":
            config.screen.fill((20, 20, 25))
            msg1 = "ゲームを終了しました" if config.LANG == "JP" else "Game Terminated."
            msg2 = "ブラウザのタブを閉じてください" if config.LANG == "JP" else "Please close the browser tab."
            t1 = config.font_large.render(msg1, True, config.TEXT_COLOR)
            t2 = config.font_mid.render(msg2, True, config.TEXT_COLOR)
            config.screen.blit(t1, ((config.SCREEN_WIDTH - t1.get_width()) // 2, config.SCREEN_HEIGHT // 2 - config.S(50)))
            config.screen.blit(t2, ((config.SCREEN_WIDTH - t2.get_width()) // 2, config.SCREEN_HEIGHT // 2 + config.S(30)))
            return

        config.screen.fill(config.BG_COLOR)

        if self.phase == "TITLE":
            logo_size = config.S(350)
            base_y = config.SCREEN_HEIGHT // 2 - config.S(180)
            
            logo = create_meld8_icon_surface(logo_size)
            config.screen.blit(logo, ((config.SCREEN_WIDTH - logo_size)//2, base_y - config.S(250)))
            t1 = config.font_giant_title.render(f"{config.APP_NAME_EN} {config.APP_VERSION}", True, config.GOLD)
            t2 = config.font_mid.render(config.MSG["APP_DESC"][config.LANG], True, config.TEXT_COLOR)
            config.screen.blit(t1, ((config.SCREEN_WIDTH - t1.get_width())//2, base_y + config.S(120)))
            config.screen.blit(t2, ((config.SCREEN_WIDTH - t2.get_width())//2, base_y + config.S(200)))
            
            sy = base_y + config.S(280)
            self.draw_button(config.MSG["START_GAME"][config.LANG], pygame.Rect((config.SCREEN_WIDTH-config.S(550))//2, sy, config.S(550), config.S(70)), pos, "BTN_START")
            self.draw_button(config.MSG["QUICK_GUIDE"][config.LANG], pygame.Rect((config.SCREEN_WIDTH-config.S(550))//2, sy + config.S(90), config.S(550), config.S(70)), pos, "BTN_GUIDE_TITLE")
            self.draw_button(config.MSG["LANG_BTN"][config.LANG], pygame.Rect((config.SCREEN_WIDTH-config.S(550))//2, sy + config.S(180), config.S(550), config.S(70)), pos, "LANG_TOGGLE", (100, 150, 100), (120, 180, 120))
            
            rect_sound = pygame.Rect((config.SCREEN_WIDTH-config.S(550))//2, sy + config.S(270), config.S(550), config.S(70))
            s_color1 = (100, 150, 100)
            s_color2 = (120, 180, 120)
            s_color = s_color2 if rect_sound.collidepoint(pos) else s_color1
            snd_msg = config.MSG["BTN_SOUND_OFF"][config.LANG] if sound.sm.muted else config.MSG["BTN_SOUND_ON"][config.LANG]
            self.draw_button(snd_msg, rect_sound, pos, "TOGGLE_SOUND", s_color, s_color)

            self.draw_button(config.MSG["QUIT_GAME"][config.LANG], pygame.Rect((config.SCREEN_WIDTH-config.S(550))//2, sy + config.S(360), config.S(550), config.S(70)), pos, "QUIT_TITLE", config.QUIT_BUTTON_COLOR, config.QUIT_BUTTON_HOVER)

            if getattr(self, "show_guide", False): self.draw_guide_overlay(pos)
            return

        if self.phase == "DEALER_DRAW":
            pw, ph = config.S(900), config.S(750)
            px, py = (config.SCREEN_WIDTH - pw) // 2, (config.SCREEN_HEIGHT - ph) // 2
            pygame.draw.rect(config.screen, (20, 20, 30), (px, py, pw, ph), border_radius=config.S(16))
            pygame.draw.rect(config.screen, config.GOLD, (px, py, pw, ph), width=config.S(3), border_radius=config.S(16))
            t = config.font_large.render(config.MSG["DEALER_DRAW_TITLE"][config.LANG], True, config.GOLD)
            config.screen.blit(t, (px + (pw - t.get_width()) // 2, py + config.S(50)))
            for i, (p_idx, card) in enumerate(self.dealer_draws):
                text = config.font_mid.render(f"{self.get_pname(p_idx)} {config.MSG['DREW'][config.LANG]}", True, config.TEXT_COLOR)
                config.screen.blit(text, (px + config.S(80), py + config.S(150) + i * config.S(120)))
                card.draw(config.screen, px + config.S(400), py + config.S(130) + i * config.S(120), config.S(70), config.S(105))
                if i == 0:
                    winner_text = config.font_mid.render(config.MSG["WINNER_DEALER"][config.LANG], True, config.GOLD)
                    config.screen.blit(winner_text, (px + config.S(500), py + config.S(160) + i * config.S(120)))
            self.draw_button(config.MSG["START_ROUND"][config.LANG], pygame.Rect(px + (pw - config.S(350)) // 2, py + ph - config.S(100), config.S(350), config.S(70)), pos, "START_GAME")
            return

        if self.phase == "QUIT_CONFIRM":
            pw, ph = config.S(750), config.S(350)
            px, py = (config.SCREEN_WIDTH-pw)//2, (config.SCREEN_HEIGHT-ph)//2
            pygame.draw.rect(config.screen, (25, 25, 35), (px, py, pw, ph), border_radius=config.S(16))
            pygame.draw.rect(config.screen, config.GOLD, (px, py, pw, ph), width=config.S(3), border_radius=config.S(16))
            t1 = config.font_large.render(config.MSG["QUIT_CONFIRM_TITLE"][config.LANG], True, config.RED)
            t2 = config.font_mid.render(config.MSG["QUIT_CONFIRM_DESC"][config.LANG], True, config.TEXT_COLOR)
            config.screen.blit(t1, (px+(pw-t1.get_width())//2, py+config.S(50)))
            config.screen.blit(t2, (px+(pw-t2.get_width())//2, py+config.S(120)))
            self.draw_button(config.MSG["YES_QUIT"][config.LANG], pygame.Rect(px+config.S(80), py+config.S(220), config.S(240), config.S(70)), pos, "CONFIRM_YES", (150,30,30), config.CONFIRM_YES_COLOR)
            self.draw_button(config.MSG["NO_RETURN"][config.LANG], pygame.Rect(px+pw-config.S(320), py+config.S(220), config.S(240), config.S(70)), pos, "CONFIRM_NO", (40,120,40), config.CONFIRM_NO_COLOR)
            return

        # ================= UI HEADER AREA =================
        pygame.draw.rect(config.screen, (0, 80, 40), (0, 0, config.SCREEN_WIDTH, config.S(80)))
        pygame.draw.line(config.screen, config.GOLD, (0, config.S(80)), (config.SCREEN_WIDTH, config.S(80)), max(1, config.S(2)))
        
        req_msg = config.MSG["ROUND_REQ_2"][config.LANG] if self.round >= 4 else config.MSG["ROUND_REQ_1"][config.LANG]
        round_txt = config.font_mid.render(req_msg.format(self.round), True, config.TEXT_COLOR)
        basic_info_y = (config.S(80) - round_txt.get_height()) // 2
        config.screen.blit(round_txt, (config.S(20), basic_info_y))
        
        deck_txt = config.font_mid.render(config.MSG["DECK"][config.LANG].format(len(self.deck)), True, config.TEXT_COLOR)
        config.screen.blit(deck_txt, (config.S(20) + round_txt.get_width() + config.S(20), basic_info_y))
        
        dora_lbl = config.font_mid.render(config.MSG["DORA"][config.LANG], True, config.TEXT_COLOR)
        dora_x = config.S(20) + round_txt.get_width() + config.S(20) + deck_txt.get_width() + config.S(20)
        config.screen.blit(dora_lbl, (dora_x, basic_info_y))
        
        if self.dora_marker and self.dora_rank:
            dora_card = Card(self.dora_suit, self.dora_rank)
            dora_card.draw(config.screen, dora_x + dora_lbl.get_width() + config.S(10), config.S(10), config.S(40), config.S(60), is_dora=True) 
        else:
            dora_none_txt = config.font_mid.render(config.MSG["NONE"][config.LANG], True, config.TEXT_COLOR)
            config.screen.blit(dora_none_txt, (dora_x + dora_lbl.get_width() + config.S(10), basic_info_y))

        rect_quit = pygame.Rect(config.SCREEN_WIDTH-config.S(110), config.S(14), config.S(90), config.S(52))
        q_color = config.QUIT_BUTTON_HOVER if rect_quit.collidepoint(pos) else config.QUIT_BUTTON_COLOR
        self.draw_button(config.MSG["BTN_QUIT"][config.LANG], rect_quit, pos, "QUIT_GAME", q_color, q_color)

        rect_guide = pygame.Rect(config.SCREEN_WIDTH-config.S(220), config.S(14), config.S(100), config.S(52))
        g_color = config.BUTTON_HOVER if rect_guide.collidepoint(pos) else config.BUTTON_COLOR
        self.draw_button(config.MSG["BTN_GUIDE"][config.LANG], rect_guide, pos, "GUIDE", g_color, g_color)

        rect_sound = pygame.Rect(config.SCREEN_WIDTH-config.S(330), config.S(14), config.S(100), config.S(52))
        s_color = config.BUTTON_HOVER if rect_sound.collidepoint(pos) else config.BUTTON_COLOR
        snd_msg = config.MSG["BTN_SOUND_OFF"][config.LANG] if sound.sm.muted else config.MSG["BTN_SOUND_ON"][config.LANG]
        self.draw_button(snd_msg, rect_sound, pos, "TOGGLE_SOUND", s_color, s_color)

        # ================= COM HANDS & PANELS =================
        for i in [1, 2]:
            bx = config.L["COM1_PANEL_X"] if i == 1 else config.L["COM2_PANEL_X"]
            by = config.L["COM1_PANEL_Y"] if i == 1 else config.L["COM2_PANEL_Y"]
            panel_rect = pygame.Rect(bx, by, config.L["PANEL_W"], config.L["PANEL_H"])
            pygame.draw.rect(config.screen, (0, 70, 35), panel_rect, border_radius=config.S(12))
            if self.turn == i: pygame.draw.rect(config.screen, config.RED, panel_rect, width=config.S(4), border_radius=config.S(12))

            dlr_tag = f' {config.MSG["DEALER_TAG"][config.LANG]}' if self.parent_idx==i else ''
            config.screen.blit(config.font_mid.render(f"{self.player_names[i-1]}{dlr_tag}", True, config.GOLD if self.turn==i else config.TEXT_COLOR), (bx+config.S(20), by+config.S(15)))
            config.screen.blit(config.font_small.render(config.MSG["SCORE"][config.LANG].format(self.scores[i]), True, config.TEXT_COLOR), (bx+config.S(20), by+config.S(50)))
            for j in range(len(self.hands[i])): 
                pygame.draw.rect(config.screen, (30, 80, 150), (bx+config.S(20)+j*config.S(36), by+config.S(85), config.S(34), config.S(50)), border_radius=config.S(4))
            for mj, m in enumerate(self.melds[i]):
                for cj, c in enumerate(m): 
                    c.draw(config.screen, bx+config.S(20)+mj*config.S(120)+cj*config.S(36), by+config.S(145), config.S(34), config.S(50), is_dora=self.is_dora_card(c))

        # ================= DISCARD PILES =================
        discard_w, discard_h = config.L["DISCARD_W"], config.L["DISCARD_H"]
        discard_gap_x, discard_gap_y = config.L["DISCARD_GAP_X"], config.L["DISCARD_GAP_Y"]

        bx1, sy1 = config.L["DISCARD1_X"], config.L["DISCARD1_Y"]
        config.screen.blit(config.font_mid.render(config.MSG["DISCARDS_COM"][config.LANG].format(self.player_names[0]), True, config.TEXT_COLOR), (bx1, sy1 - config.S(40)))
        for j, c in enumerate(self.discards[1]):
            is_latest = (c is getattr(self, "last_discard", None))
            c.draw(config.screen, bx1 + (j % 6) * discard_gap_x, sy1 + (j // 6) * discard_gap_y, discard_w, discard_h, highlighted=is_latest, highlight_color=config.CYAN_HIGHLIGHT, is_dora=self.is_dora_card(c))

        bx2, sy2 = config.L["DISCARD2_X"], config.L["DISCARD2_Y"]
        config.screen.blit(config.font_mid.render(config.MSG["DISCARDS_COM"][config.LANG].format(self.player_names[1]), True, config.TEXT_COLOR), (bx2, sy2 - config.S(40)))
        for j, c in enumerate(self.discards[2]):
            is_latest = (c is getattr(self, "last_discard", None))
            c.draw(config.screen, bx2 + (j % 6) * discard_gap_x, sy2 + (j // 6) * discard_gap_y, discard_w, discard_h, highlighted=is_latest, highlight_color=config.CYAN_HIGHLIGHT, is_dora=self.is_dora_card(c))

        bx0, sy0 = config.L["DISCARD0_X"], config.L["DISCARD0_Y"]
        yd_text = config.font_mid.render(config.MSG["DISCARDS_YOURS"][config.LANG], True, config.TEXT_COLOR)
        config.screen.blit(yd_text, ((config.SCREEN_WIDTH - yd_text.get_width()) // 2, sy0 - config.S(40)))
        for j, c in enumerate(self.discards[0]):
            is_latest = (c is getattr(self, "last_discard", None))
            c.draw(config.screen, bx0 + (j % 6) * discard_gap_x, sy0 + (j // 6) * discard_gap_y, discard_w, discard_h, highlighted=is_latest, highlight_color=config.CYAN_HIGHLIGHT, is_dora=self.is_dora_card(c))

        # ================= PLAYER HAND & INFO =================
        player_rect = pygame.Rect(config.L["PLAYER_PANEL_X"], config.L["PLAYER_PANEL_Y"], config.L["PLAYER_PANEL_W"], config.L["PLAYER_PANEL_H"])
        pygame.draw.rect(config.screen, (0, 70, 35), player_rect, border_radius=config.S(12))
        if self.turn == 0: pygame.draw.rect(config.screen, config.RED, player_rect, width=config.S(4), border_radius=config.S(12))

        py = config.L["PLAYER_PANEL_Y"]
        dlr_tag = f' {config.MSG["DEALER_TAG"][config.LANG]}' if self.parent_idx==0 else ''
        config.screen.blit(config.font_large.render(f"{config.MSG['YOU'][config.LANG]}{dlr_tag}", True, config.GOLD if self.turn==0 else config.TEXT_COLOR), (config.L["PLAYER_PANEL_X"]+config.S(20), py+config.S(20)))
        config.screen.blit(config.font_mid.render(config.MSG["SCORE"][config.LANG].format(self.scores[0]), True, config.TEXT_COLOR), (config.L["PLAYER_PANEL_X"]+config.S(20), py+config.S(70)))
        
        sort_lbl = config.MSG["SORT_SEQ"][config.LANG] if self.sort_mode == "NORMAL" else config.MSG["SORT_TRIP"][config.LANG]
        self.draw_button(sort_lbl, pygame.Rect(config.L["PLAYER_PANEL_X"]+config.S(20), py+config.S(120), config.S(160), config.S(46)), pos, "SORT_MODE")
        
        if self.phase == "TSUMO" and self.turn == 0: 
            self.draw_button(config.MSG["DRAW_CARD"][config.LANG], pygame.Rect(config.L["PLAYER_PANEL_X"]+config.S(200), py+config.S(120), config.S(160), config.S(46)), pos, "DRAW")
        
        if len(self.hands[0]) % 3 in [1, 2] and self.phase not in ["AGARI_SHOW", "ROUND_END", "GAME_OVER", "DEALER_DRAW", "TITLE", "DEALING", "QUIT_CONFIRM"]:
            if len(self.hands[0]) % 3 == 1:
                waits = self.update_waits_cache()
            else:
                waits = self.my_waits_cache
            
            if waits:
                wait_x, wait_y = config.L["WAITS_X"], config.L["WAITS_Y"]
                wait_lbl = config.font_mid.render(config.MSG["WAITS"][config.LANG], True, config.GOLD)
                config.screen.blit(wait_lbl, (wait_x, wait_y))
                
                offset_x = wait_lbl.get_width() + config.S(10)
                if self.is_furiten(0): 
                    fur_lbl = config.font_small.render(config.MSG["FURITEN"][config.LANG], True, config.RED)
                    config.screen.blit(fur_lbl, (wait_x + offset_x, wait_y + config.S(5)))
                
                cw, ch = config.S(44), config.S(66)
                gap_x = config.S(12)
                
                start_x = wait_x + config.S(10)
                available_w = config.SCREEN_WIDTH - start_x - config.S(60)
                if available_w <= config.S(100): available_w = config.S(200)
                
                max_cols = max(1, int(available_w // (cw + gap_x)))
                max_rows = 2
                max_display = max_cols * max_rows
                
                display_waits = waits[:max_display]
                has_more = len(waits) > max_display
                
                for i, (wc, t_only) in enumerate(display_waits):
                    col = i % max_cols
                    row = i // max_cols
                    cx = start_x + col * (cw + gap_x)
                    cy = wait_y + config.S(40) + row * (ch + config.S(25))
                    
                    wc.draw(config.screen, cx, cy, cw, ch, is_dora=self.is_dora_card(wc))
                    if t_only:
                        t_txt = config.font_tiny.render(config.MSG["TSUMO_TINY"][config.LANG], True, config.GOLD)
                        config.screen.blit(t_txt, (cx + cw//2 - t_txt.get_width()//2, cy + ch + config.S(1)))

                if has_more:
                    last_i = len(display_waits) - 1
                    last_col = last_i % max_cols
                    last_row = last_i // max_cols
                    etc_cx = start_x + (last_col + 1) * (cw + gap_x)
                    etc_cy = wait_y + config.S(40) + last_row * (ch + config.S(25)) + ch // 2
                    
                    etc_txt = config.font_small.render(config.MSG["ETC"][config.LANG], True, config.TEXT_COLOR)
                    config.screen.blit(etc_txt, (etc_cx, etc_cy - etc_txt.get_height()//2))

        w, h, gap = self.player_card_w, self.player_card_h, self.player_card_gap
        sx = (config.SCREEN_WIDTH//2) - ((len(self.hands[0])*(w+gap)-gap)//2)
        y_pos = self.player_cards_y

        for i, c in enumerate(self.hands[0]):
            is_hl = (c == self.last_tsumo_card[0] and self.phase in ["DISCARD_WAIT", "TSUMO_AGARI_WAIT"])
            c.draw(config.screen, sx+i*(w+gap), y_pos, w, h, highlighted=is_hl, highlight_color=config.GOLD, is_dora=self.is_dora_card(c))
            if is_hl:
                badge_txt_surf = config.font_small.render(config.MSG["BADGE_DRAW"][config.LANG], True, config.TSUMO_BADGE_TEXT)
                badge_w, badge_h = badge_txt_surf.get_size()
                pygame.draw.rect(config.screen, config.TSUMO_BADGE_BG, (sx+i*(w+gap)+(w-(badge_w+config.S(16)))//2, y_pos-badge_h-config.S(10), badge_w+config.S(16), badge_h+config.S(4)), border_radius=config.S(4))
                config.screen.blit(badge_txt_surf, (sx+i*(w+gap)+(w-(badge_w+config.S(16)))//2+config.S(8), y_pos-badge_h-config.S(8)))

        # --- 鳴きカード(MELDS)描画 ---
        for mj, m in enumerate(self.melds[0]):
            meld_w = config.S(50) + 2 * config.S(40) 
            naki_start_x = config.SCREEN_WIDTH - config.S(60) - (mj + 1) * meld_w - mj * config.S(15)
            naki_y = self.player_cards_y + config.L["PLAYER_CARD_H"] - config.S(75)
            
            naki_lbl = config.font_small.render(config.MSG["BADGE_CALL"][config.LANG], True, (100, 200, 255))
            lbl_x = naki_start_x + meld_w // 2 - naki_lbl.get_width() // 2
            lbl_y = naki_y - config.S(25)
            config.screen.blit(naki_lbl, (lbl_x, lbl_y))
            
            for cj, c in enumerate(m): 
                c.draw(config.screen, naki_start_x + cj*config.S(40), naki_y, config.S(50), config.S(75), is_dora=self.is_dora_card(c))

        # ================= ACTION & SELECT POPUPS =================
        if self.phase == "ACTION_WAIT":
            acts = [a for a in self.get_top_pending_actions() if a["p_idx"] == 0]
            btn_width = sum([config.S(200) for a in ["RON", "PONG", "CHI"] if any(x["action"]==a for x in acts)]) + config.S(140)
            bx, by = (config.SCREEN_WIDTH - btn_width) // 2, config.L["ACTION_Y"]
            
            if any(a["action"] == "RON" for a in acts): self.draw_button(config.MSG["RON"][config.LANG], pygame.Rect(bx, by, config.S(180), config.S(80)), pos, "RON"); bx += config.S(200)
            if any(a["action"] == "PONG" for a in acts): self.draw_button(config.MSG["PONG"][config.LANG], pygame.Rect(bx, by, config.S(180), config.S(80)), pos, "PONG"); bx += config.S(200)
            if any(a["action"] == "CHI" for a in acts): self.draw_button(config.MSG["CHI"][config.LANG], pygame.Rect(bx, by, config.S(180), config.S(80)), pos, "CHI"); bx += config.S(200)
            self.draw_button(config.MSG["PASS"][config.LANG], pygame.Rect(bx, by, config.S(120), config.S(80)), pos, "PASS")

        elif self.phase == "TSUMO_AGARI_WAIT":
            bx, by = (config.SCREEN_WIDTH - config.S(360)) // 2, config.L["ACTION_Y"]
            self.draw_button(config.MSG["TSUMO_BTN"][config.LANG], pygame.Rect(bx, by, config.S(200), config.S(80)), pos, "TSUMO_WIN")
            self.draw_button(config.MSG["PASS"][config.LANG], pygame.Rect(bx+config.S(220), by, config.S(140), config.S(80)), pos, "PASS_TSUMO")

        if self.phase == "COMBO_SELECT":
            pw, ph = config.S(880), config.S(550)
            px, py = (config.SCREEN_WIDTH - pw) // 2, (config.SCREEN_HEIGHT - ph) // 2
            pygame.draw.rect(config.screen, (30, 40, 50), (px, py, pw, ph), border_radius=config.S(16))
            pygame.draw.rect(config.screen, config.GOLD, (px, py, pw, ph), width=config.S(3), border_radius=config.S(16))
            
            act_name = config.MSG[self.current_action_act['action']][config.LANG]
            t = config.font_large.render(config.MSG["COMBO_SEL_TITLE"][config.LANG].format(act_name), True, config.GOLD)
            config.screen.blit(t, (px + (pw - t.get_width()) // 2, py + config.S(30)))
            config.screen.blit(config.font_mid.render(config.MSG["COMBO_SEL_TARGET"][config.LANG], True, config.TEXT_COLOR), (px + config.S(50), py + config.S(100)))
            self.last_discard.draw(config.screen, px + config.S(150), py + config.S(90), config.S(55), config.S(82), is_dora=self.is_dora_card(self.last_discard))
            
            start_y = py + config.S(190)
            for i, combo in enumerate(self.current_action_act["combos"]):
                row, col = i // 2, i % 2
                cx, cy = px + config.S(50) + col * config.S(400), start_y + row * config.S(120)
                combo[0].draw(config.screen, cx, cy, config.S(55), config.S(82), is_dora=self.is_dora_card(combo[0]))
                combo[1].draw(config.screen, cx + config.S(65), cy, config.S(55), config.S(82), is_dora=self.is_dora_card(combo[1]))
                self.draw_button(config.MSG["SELECT"][config.LANG], pygame.Rect(cx + config.S(140), cy + config.S(15), config.S(120), config.S(55)), pos, f"SEL_{i}", (60, 160, 60), (80, 200, 80))
            self.draw_button(config.MSG["CANCEL"][config.LANG], pygame.Rect(px + (pw - config.S(200)) // 2, py + ph - config.S(80), config.S(200), config.S(60)), pos, "CANCEL_SELECT", config.QUIT_BUTTON_COLOR, config.QUIT_BUTTON_HOVER)

        if self.phase == "FINAL_ROUND_ALERT":
            pw, ph = config.S(800), config.S(400)
            px, py = (config.SCREEN_WIDTH - pw) // 2, (config.SCREEN_HEIGHT - ph) // 2
            pygame.draw.rect(config.screen, (40, 20, 20), (px, py, pw, ph), border_radius=config.S(16))
            pygame.draw.rect(config.screen, config.RED, (px, py, pw, ph), width=config.S(3), border_radius=config.S(16))
            
            title_str = config.MSG["ALERT_LATE"][config.LANG] if self.round < 6 else config.MSG["ALERT_FINAL"][config.LANG]
            t1 = config.font_large.render(title_str, True, config.GOLD)
            t2 = config.font_mid.render(config.MSG["ALERT_DESC1"][config.LANG], True, config.TEXT_COLOR)
            t3 = config.font_small.render(config.MSG["ALERT_DESC2"][config.LANG], True, config.TEXT_COLOR)
            
            config.screen.blit(t1, (px + (pw - t1.get_width()) // 2, py + config.S(50)))
            config.screen.blit(t2, (px + (pw - t2.get_width()) // 2, py + config.S(140)))
            config.screen.blit(t3, (px + (pw - t3.get_width()) // 2, py + config.S(200)))
            self.draw_button(config.MSG["ACKNOWLEDGE"][config.LANG], pygame.Rect(px + (pw - config.S(280)) // 2, py + ph - config.S(90), config.S(280), config.S(60)), pos, "ACK_FINAL_ROUND", (200, 50, 50), (250, 80, 80))

        if self.phase in ["AGARI_SHOW", "ROUND_END", "GAME_OVER"]:
            if self.phase == "AGARI_SHOW": pw, ph = config.S(920), config.S(750)
            elif self.phase == "ROUND_END": pw, ph = config.S(700), config.S(400)
            else: pw, ph = config.S(800), config.S(750)
                
            px, py = (config.SCREEN_WIDTH-pw)//2, (config.SCREEN_HEIGHT-ph)//2
            pygame.draw.rect(config.screen, (20,20,30), (px, py, pw, ph), border_radius=config.S(16))
            pygame.draw.rect(config.screen, config.GOLD, (px, py, pw, ph), width=config.S(3), border_radius=config.S(16))
            
            if self.phase == "AGARI_SHOW":
                if self.agari_data['is_tsumo']:
                    win_text = config.MSG["WIN_TSUMO"][config.LANG].format(self.get_pname(self.agari_data['winner']))
                else:
                    win_text = config.MSG["WIN_RON"][config.LANG].format(self.get_pname(self.agari_data['winner']), self.get_pname(self.agari_data['loser']))
                    
                config.screen.blit(config.font_agari_title.render(win_text, True, config.GOLD), (px+config.S(30), py+config.S(30)))
                cx, cy = px + config.S(40), py + config.S(110)
                
                for c in self.agari_data["hand_cards"]:
                    c.draw(config.screen, cx, cy, config.S(55), config.S(82), is_dora=self.is_dora_card(c))
                    cx += config.S(60)
                cx += config.S(10)
                self.agari_data["agari_card"].draw(config.screen, cx, cy, config.S(55), config.S(82), highlighted=True, highlight_color=config.GOLD, is_dora=self.is_dora_card(self.agari_data["agari_card"]))
                
                badge_str = config.MSG["TSUMO_BTN"][config.LANG] if self.agari_data["is_tsumo"] else config.MSG["RON"][config.LANG]
                badge = config.font_small.render(badge_str, True, config.GOLD)
                config.screen.blit(badge, (cx + config.S(27) - badge.get_width()//2, cy - config.S(25)))
                cx += config.S(70)
                
                if self.agari_data["melds"]:
                    cx += config.S(15)
                    for m in self.agari_data["melds"]:
                        naki_start_x = cx
                        for c in m:
                            c.draw(config.screen, cx, cy, config.S(55), config.S(82), is_dora=self.is_dora_card(c))
                            cx += config.S(22) 
                        naki_lbl = config.font_small.render(config.MSG["BADGE_CALL"][config.LANG], True, (100, 200, 255))
                        config.screen.blit(naki_lbl, (naki_start_x + (config.S(55) + 2 * config.S(22)) // 2 - naki_lbl.get_width() // 2, cy - config.S(25)))
                        cx += config.S(40) 
                
                for i, y in enumerate(self.agari_data["yaku"]): 
                    trans_y = translate_yaku(y, config.LANG)
                    config.screen.blit(config.font_mid.render(f"- {trans_y}", True, config.TEXT_COLOR), (px+config.S(40), py+config.S(220)+i*config.S(35)))
                
                config.screen.blit(config.font_large.render(config.MSG["TOTAL_SCORE_PTS"][config.LANG].format(self.agari_data['final_points']), True, (100, 255, 100)), (px+config.S(40), py+ph-config.S(160)))
                
                btn_str = config.MSG["NEXT_ROUND"][config.LANG] if self.round < 6 else config.MSG["SHOW_RESULTS"][config.LANG]
                self.draw_button(btn_str, pygame.Rect(px+(pw-config.S(300))//2, py+ph-config.S(90), config.S(300), config.S(60)), pos, "NEXT")
            
            elif self.phase == "ROUND_END":
                t1 = config.font_large.render(config.MSG["DRAW_TITLE"][config.LANG], True, config.RED)
                t2 = config.font_mid.render(config.MSG["DRAW_DESC"][config.LANG], True, config.TEXT_COLOR)
                config.screen.blit(t1, (px+(pw-t1.get_width())//2, py+config.S(70)))
                config.screen.blit(t2, (px+(pw-t2.get_width())//2, py+config.S(160)))
                self.draw_button(config.MSG["RETRY_ROUND"][config.LANG], pygame.Rect(px+(pw-config.S(300))//2, py+ph-config.S(90), config.S(300), config.S(60)), pos, "NEXT")

            elif self.phase == "GAME_OVER":
                title = config.font_agari_title.render(config.MSG["FINAL_RESULTS"][config.LANG], True, config.GOLD)
                config.screen.blit(title, (px+(pw-title.get_width())//2, py+config.S(40)))
                s_idx = sorted(range(3), key=lambda k: self.scores[k], reverse=True)
                for i, p in enumerate(s_idx):
                    config.screen.blit(config.font_mid.render(config.MSG["RANK"][config.LANG].format(i+1, self.get_pname(p)), True, config.GOLD if i==0 else config.TEXT_COLOR), (px+config.S(60), py+config.S(150)+i*config.S(120)))
                    config.screen.blit(config.font_small.render(config.MSG["FINAL_SCORE_DETAIL"][config.LANG].format(self.scores[p], self.uma[p], self.final_scores[p]), True, config.TEXT_COLOR), (px+config.S(60), py+config.S(195)+i*config.S(120)))
                self.draw_button(config.MSG["RETURN_TITLE"][config.LANG], pygame.Rect(px+(pw-config.S(320))//2, py+ph-config.S(100), config.S(320), config.S(60)), pos, "RESTART")
        
        if getattr(self, "show_guide", False): self.draw_guide_overlay(pos)

    def step(self):
        pos = pygame.mouse.get_pos()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1: 
                self.handle_click(pos)
                
        self.update_game()
        self.draw_screen(pos)
        pygame.display.flip()
        clock.tick(30)

    async def run_async(self):
        while True:
            self.step()
            await asyncio.sleep(0)

    def run_sync(self):
        while True:
            self.step()

async def main_loop():
    game = TrumpMahjongGUI()
    await game.run_async()

if __name__ == "__main__":
    if is_web:
        asyncio.run(main_loop())
    else:
        game = TrumpMahjongGUI()
        game.run_sync()