import random
import re
from card import Card, SUITS, RANKS, RANK_ORDER

ITTSUU_RANK_WINDOWS = [
    ("A", "2", "3", "4", "5", "6", "7", "8"),
    ("2", "3", "4", "5", "6", "7", "8", "9"),
    ("3", "4", "5", "6", "7", "8", "9", "10"),
    ("4", "5", "6", "7", "8", "9", "10", "J"),
    ("5", "6", "7", "8", "9", "10", "J", "Q"),
    ("6", "7", "8", "9", "10", "J", "Q", "K"),
]
ROYAL_RANK_WINDOW = ("7", "8", "9", "10", "J", "Q", "K", "A")

def create_deck():
    deck = [Card(s, r) for s in SUITS for r in RANKS]
    deck.append(Card(None, None, is_joker=True))
    random.shuffle(deck)
    return deck

def determine_dealer():
    deck = [Card(s, r) for s in SUITS for r in RANKS]
    deck.append(Card(None, None, is_joker=True))
    random.shuffle(deck)
    draws = [(i, deck.pop()) for i in range(3)]
    draws.sort(key=lambda x: x[1].get_dealer_strength(), reverse=True)
    return draws

def get_dora_card(dora_marker):
    if not dora_marker or dora_marker.is_joker: return None, None
    curr_idx = RANK_ORDER[dora_marker.rank]
    next_idx = (curr_idx + 1) % 13
    return dora_marker.suit, RANKS[next_idx]

def rank_to_num(rank):
    if rank == "A": return 1
    if rank == "J": return 11
    if rank == "Q": return 12
    if rank == "K": return 13
    return int(rank)

def calculate_score(fan, is_parent):
    if fan >= 10: return 20000 if not is_parent else 30000
    return fan * 2000

def same_suit_cards(cards):
    suits = {c.suit for c in cards if c.suit}
    return len(suits) == 1 and len(cards) == 8

def has_rank_window(cards, window):
    if len(cards) != 8 or any(c.is_joker or c.rank is None for c in cards): return False
    return same_suit_cards(cards) and set(c.rank for c in cards) == set(window)

def has_ittsuu_window(cards):
    if len(cards) != 8 or any(c.rank is None for c in cards): return False
    if not same_suit_cards(cards): return False
    ranks = set(c.rank for c in cards)
    return any(ranks == set(window) for window in ITTSUU_RANK_WINDOWS)

def has_royal_window(cards):
    return has_rank_window(cards, ROYAL_RANK_WINDOW)

def meld_uses_joker_rep(meld, joker_rep):
    return joker_rep is not None and any(c is joker_rep for c in meld)

def is_pinfu_ryanmen(seq_cards, agari_card):
    if not agari_card or agari_card.rank is None or agari_card.suit is None: return False
    if not any(c.rank == agari_card.rank and c.suit == agari_card.suit for c in seq_cards): return False
    vals = sorted([rank_to_num(c.rank) for c in seq_cards])
    av = rank_to_num(agari_card.rank)
    if vals == [1, 2, 3]: return av == 1
    if vals == [11, 12, 13]: return av == 13
    return av == vals[0] or av == vals[2]

def check_three_cards(three):
    if not (three[0].rank and three[1].rank and three[2].rank): return False
    if three[0].rank == three[1].rank == three[2].rank: return True
    if three[0].suit == three[1].suit == three[2].suit: 
        vals = sorted([rank_to_num(c.rank) for c in three])
        if vals[1] == vals[0] + 1 and vals[2] == vals[1] + 1: return True
    return False

def valid_chi_combos(hand, discard_card):
    if discard_card.rank is None or discard_card.is_joker: return []
    combos = []
    num_cards = [c for c in hand if c.suit == discard_card.suit and not c.is_joker]
    for i in range(len(num_cards)):
        for j in range(i + 1, len(num_cards)):
            three = [discard_card, num_cards[i], num_cards[j]]
            if check_three_cards(three): combos.append((num_cards[i], num_cards[j]))
    return combos

def valid_pong_combos(hand, discard_card):
    if discard_card.rank is None or discard_card.is_joker: return []
    combos = []
    num_cards = [c for c in hand if c.rank == discard_card.rank and not c.is_joker]
    for i in range(len(num_cards)):
        for j in range(i + 1, len(num_cards)):
            combos.append((num_cards[i], num_cards[j]))
    return combos

def find_all_melds_decomp(cards):
    if len(cards) == 0: return [[]]
    results = []
    for i in range(1, len(cards)):
        for j in range(i + 1, len(cards)):
            three = [cards[0], cards[i], cards[j]]
            if check_three_cards(three):
                rem = [cards[k] for k in range(len(cards)) if k not in [0, i, j]]
                sub_decomps = find_all_melds_decomp(rem)
                for sd in sub_decomps:
                    results.append([three] + sd)
    return results

def get_all_normal_patterns(hand_cards):
    patterns = []
    needed_mentzu = len(hand_cards) // 3
    for i in range(len(hand_cards)):
        for j in range(i + 1, len(hand_cards)):
            if hand_cards[i].rank == hand_cards[j].rank:
                rem = [hand_cards[k] for k in range(len(hand_cards)) if k != i and k != j]
                decomps = find_all_melds_decomp(rem)
                for d in decomps:
                    if len(d) == needed_mentzu:
                        patterns.append({"toitsu": hand_cards[i].rank, "toitsu_cards": [hand_cards[i], hand_cards[j]], "mentzu": d})
    return patterns

def has_agari_shape(hand, melds):
    joker_present = any(c.is_joker for c in hand)
    forbidden = set((c.suit, c.rank) for c in hand + [x for m in melds for x in m] if not c.is_joker)
    reps = [Card(s, r, is_joker=False) for s in SUITS for r in RANKS if (s, r) not in forbidden] if joker_present else [None]

    for rep in reps:
        curr_hand = [rep if c.is_joker else c for c in hand]
        if len(melds) == 0 and not joker_present:
            ranks = [c.rank for c in curr_hand]
            if len(set(ranks)) == 4 and all(ranks.count(r) == 2 for r in set(ranks)): return True
        if len(melds) == 0:
            if has_royal_window(curr_hand) and not joker_present: return True
            if has_ittsuu_window(curr_hand): return True
        if len(melds) == 0:
            rc = {}
            for c in curr_hand: rc[c.rank] = rc.get(c.rank, 0) + 1
            if sorted(rc.values()) == [4, 4]: return True
        patterns = get_all_normal_patterns(curr_hand)
        for p in patterns:
            if joker_present and rep and any(c is rep for c in p.get("toitsu_cards", [])): continue
            return True
    return False

def check_agari_and_yaku(hand, melds, is_tsumo, is_menzen, dora_suit, dora_rank, agari_card, deck_left, is_first_turn=False, any_naki_occurred=False, is_parent=False, required_total_fan=1):
    joker_present = any(c.is_joker for c in hand)
    is_kuisagari = (not is_menzen) or joker_present
    all_cards = hand + [c for m in melds for c in m]
    if len(all_cards) != 8: return False, 0, [], 0, False

    yakuman_mult = 0
    yakuman_yaku = []
    yao = ["A", "J", "Q", "K"]

    if len(melds) == 0 and not joker_present:
        suits = {c.suit for c in hand if c.suit}
        ranks = {c.rank for c in hand}
        if has_royal_window(hand):
            if "S" in suits: yakuman_yaku.append("Spade Royal Straight (Double Yakuman)"); yakuman_mult += 2
            else: yakuman_yaku.append("Royal Straight (Yakuman)"); yakuman_mult += 1

        rc_chk = {}
        for c in hand: rc_chk[c.rank] = rc_chk.get(c.rank, 0) + 1
        if rc_chk.get("A", 0) == 2 and rc_chk.get("J", 0) == 2 and rc_chk.get("Q", 0) == 2 and rc_chk.get("K", 0) == 2:
            pairs = {"A": [], "J": [], "Q": [], "K": []}
            for c in hand: pairs[c.rank].append(c)
            if all((cs[0].is_red() and cs[1].is_red()) or (cs[0].is_black() and cs[1].is_black()) for cs in pairs.values()):
                if all(c.is_red() for c in hand) or all(c.is_black() for c in hand):
                    yakuman_yaku.append("Four Crowns Pure Color (Double Yakuman)"); yakuman_mult += 2
                else:
                    yakuman_yaku.append("Four Crowns (Yakuman)"); yakuman_mult += 1

    if yakuman_mult > 0:
        yakuman_mult = min(yakuman_mult, 2)
        return True, 0, yakuman_yaku, yakuman_mult, False

    d_cnt = sum(1 for c in all_cards if not c.is_joker and c.suit == dora_suit and c.rank == dora_rank)
    independent_yaku_fan = 0
    independent_yaku_names = []

    if is_tsumo and is_menzen and is_first_turn and not any_naki_occurred:
        if has_agari_shape(hand, melds):
            if is_parent:
                independent_yaku_fan += 4; independent_yaku_names.append("Tenho (4 Fan)")
            else:
                independent_yaku_fan += 4; independent_yaku_names.append("Chiho (4 Fan)")
    if is_tsumo and is_menzen:
        independent_yaku_fan += 1; independent_yaku_names.append("Concealed Self-Draw (1 Fan)")
    if deck_left == 0:
        independent_yaku_fan += 1; independent_yaku_names.append("Haitei (1 Fan)")
    parent_bonus_fan = 1 if is_parent else 0

    best_yaku_score = -1
    best_bonus_score = 0
    best_hand_yaku = []
    best_total_score = -1
    best_final_yaku_score = -1

    def consider_candidate(yaku_fan, bonus_fan, yaku_names):
        nonlocal best_yaku_score, best_bonus_score, best_hand_yaku, best_total_score, best_final_yaku_score
        final_yaku_fan = yaku_fan + independent_yaku_fan
        if final_yaku_fan <= 0 or final_yaku_fan < required_total_fan: return
            
        total_score_fan = final_yaku_fan + bonus_fan + d_cnt + parent_bonus_fan
        if (
            total_score_fan > best_total_score or
            (total_score_fan == best_total_score and final_yaku_fan > best_final_yaku_score) or
            (total_score_fan == best_total_score and final_yaku_fan == best_final_yaku_score and yaku_fan > best_yaku_score) or
            (total_score_fan == best_total_score and final_yaku_fan == best_final_yaku_score and yaku_fan == best_yaku_score and bonus_fan > best_bonus_score)
        ):
            best_yaku_score = yaku_fan; best_bonus_score = bonus_fan; best_hand_yaku = list(yaku_names)
            best_total_score = total_score_fan; best_final_yaku_score = final_yaku_fan
    
    forbidden = set((c.suit, c.rank) for c in all_cards if not c.is_joker)
    reps = [Card(s, r, is_joker=False) for s in SUITS for r in RANKS if (s, r) not in forbidden] if joker_present else [None]

    for rep in reps:
        curr_hand = [rep if c.is_joker else c for c in hand]

        if len(melds) == 0 and has_ittsuu_window(curr_hand):
            yaku_fan = 5 if joker_present else 6
            y = [f"Pure Straight ({yaku_fan} Fan)"]
            if is_menzen and all(c.rank in ["2","3","4","5","6","7","8","9","10"] for c in curr_hand):
                yaku_fan += 1; y.append("Tanyao (1 Fan)")
            consider_candidate(yaku_fan, 0, y)

        if len(melds) == 0 and not joker_present:
            ranks = [c.rank for c in curr_hand]
            if len(set(ranks)) == 4 and all(ranks.count(r) == 2 for r in set(ranks)):
                yaku_fan, y = 1, ["Four Pairs (1 Fan)"]
                if is_menzen and all(c.rank in ["2","3","4","5","6","7","8","9","10"] for c in curr_hand): yaku_fan += 1; y.append("Tanyao (1 Fan)")
                if all(r in yao for r in set(ranks)): yaku_fan += 3; y.append("Junchan (3 Fan)")
                if all(c.is_red() for c in curr_hand): yaku_fan += 2; y.append("All Red (2 Fan)")
                elif all(c.is_black() for c in curr_hand): yaku_fan += 2; y.append("All Black (2 Fan)")
                consider_candidate(yaku_fan, 0, y)

        if len(melds) == 0:
            rc = {}
            for c in curr_hand: rc[c.rank] = rc.get(c.rank, 0) + 1
            if sorted(rc.values()) == [4, 4]:
                yaku_fan = 5 if joker_present else 6
                y = [f"Dual Kan-Gantsu ({yaku_fan} Fan)"]
                if is_menzen and all(c.rank in ["2","3","4","5","6","7","8","9","10"] for c in curr_hand): yaku_fan += 1; y.append("Tanyao (1 Fan)")
                if all(r in yao for r in rc.keys()): yaku_fan += 2 if is_kuisagari else 3; y.append(f"Junchan ({2 if is_kuisagari else 3} Fan)")
                if all(c.is_red() for c in curr_hand): yaku_fan += 1 if is_kuisagari else 2; y.append(f"All Red ({1 if is_kuisagari else 2} Fan)")
                elif all(c.is_black() for c in curr_hand): yaku_fan += 1 if is_kuisagari else 2; y.append(f"All Black ({1 if is_kuisagari else 2} Fan)")
                consider_candidate(yaku_fan, 0, y)

        patterns = get_all_normal_patterns(curr_hand)
        for pat in patterns:
            if joker_present and rep and any(c is rep for c in pat.get("toitsu_cards", [])): continue
            yaku_fan, bonus_fan, y = 0, 0, []
            all_melds_list = pat["mentzu"] + melds
            all_cards_total = curr_hand + [x for m in melds for x in m]
            
            if is_menzen and all(c.rank in ["2","3","4","5","6","7","8","9","10"] for c in all_cards_total if c.rank): 
                yaku_fan += 1; y.append("Tanyao (1 Fan)")
            
            has_yao_in_all = True
            is_junchan = True
            for m in all_melds_list + [[Card(None, pat["toitsu"]), Card(None, pat["toitsu"])]]:
                ranks_in_m = [c.rank for c in m if c.rank]
                if not any(r in yao for r in ranks_in_m): has_yao_in_all = False
                if not all(r in yao for r in ranks_in_m): is_junchan = False
            
            if has_yao_in_all:
                if is_junchan:
                    cs = 2 if is_kuisagari else 3
                    yaku_fan += cs; y.append(f"Junchan ({cs} Fan)")
                else:
                    cs = 1 if is_kuisagari else 2
                    yaku_fan += cs; y.append(f"Chanta ({cs} Fan)")

            if all(c.is_red() for c in all_cards_total):
                cs = 1 if is_kuisagari else 2
                yaku_fan += cs; y.append(f"All Red ({cs} Fan)")
            elif all(c.is_black() for c in all_cards_total):
                cs = 1 if is_kuisagari else 2
                yaku_fan += cs; y.append(f"All Black ({cs} Fan)")

            k_cnt = 0
            pure_seq_cnt = 0
            seq_windows = []
            for m in all_melds_list:
                uses_joker_in_meld = meld_uses_joker_rep(m, rep)
                if m[0].rank == m[1].rank == m[2].rank:
                    k_cnt += 1
                    if m[0].rank in yao and not uses_joker_in_meld:
                        yaku_fan += 1; y.append(f"Honor Value:{m[0].rank} (1 Fan)")
                else:
                    seq_windows.append(tuple(sorted([rank_to_num(c.rank) for c in m if c.rank])))
                    if not uses_joker_in_meld: pure_seq_cnt += 1
            
            if pure_seq_cnt > 0:
                bonus_fan = min(pure_seq_cnt, 2)
                y.append(f"Pure Seq Bonus (+{bonus_fan} Fan)")

            if len(seq_windows) == 2 and seq_windows[0] == seq_windows[1]:
                dj_fan = 1 if is_kuisagari else 2
                yaku_fan += dj_fan; y.append(f"Double Sequence ({dj_fan} Fan)")

            pinfu_agari_card = rep if (agari_card and agari_card.is_joker and rep is not None) else agari_card
            if k_cnt == 0 and pinfu_agari_card:
                if any(m[0].rank != m[1].rank and is_pinfu_ryanmen(m, pinfu_agari_card) for m in pat["mentzu"]):
                    pf = 1 if is_kuisagari else 2
                    yaku_fan += pf; y.append(f"Pinfu ({pf} Fan)")

            if k_cnt >= 2:
                tt = 1 if is_kuisagari else 2
                yaku_fan += tt; y.append(f"Toitoi ({tt} Fan)")

            consider_candidate(yaku_fan, bonus_fan, y)

    if best_total_score >= 0:
        final_yaku_fan = max(0, best_yaku_score) + independent_yaku_fan
        final_bonus_fan = best_bonus_score
        
        normal_yakus = []
        pure_seq_str = None
        for y_str in best_hand_yaku + independent_yaku_names:
            if "Pure Seq Bonus" in y_str: pure_seq_str = y_str
            else: normal_yakus.append(y_str)
                
        def get_fan(s):
            m = re.search(r'\((\d+)\+? Fan\)', s)
            return int(m.group(1)) if m else 0

        normal_yakus.sort(key=get_fan)
        final_yaku = normal_yakus
        
        if d_cnt > 0: final_yaku.append(f"Dora Bonus (+{d_cnt} Fan)")
        if pure_seq_str: final_yaku.append(pure_seq_str)
        
        total_fan = final_yaku_fan + final_bonus_fan + d_cnt
        if is_parent:
            final_yaku.append("Dealer Bonus (+1 Fan)")
            total_fan += 1

        if total_fan >= 10: 
            final_yaku = ["Kazoe Yakuman (10+ Fan Stacked)"] + final_yaku
            return True, total_fan, final_yaku, 0, True

        return True, total_fan, final_yaku, 0, False
    return False, 0, [], 0, False

def get_shape_waiting_pool(hand, melds):
    pool = set()
    for s in SUITS:
        for r in RANKS:
            test_card = Card(s, r)
            if has_agari_shape(hand + [test_card], melds): pool.add((r, s, "SHAPE_WAIT"))
    return list(pool)

def evaluate_com_discard_scores(hand):
    scores = []
    for idx, card in enumerate(hand):
        if card.is_joker:
            scores.append(99999); continue
        score = 10
        if card.rank in ["A", "J", "Q", "K"]: score += 5
        if card.rank in ["2","3","4","5","6","7","8","9","10"]: score += 3

        cnt = sum(1 for c in hand if c.rank == card.rank and not c.is_joker)
        if cnt >= 3: score += 40
        elif cnt == 2: score += 20

        val = rank_to_num(card.rank)
        for c in hand:
            if c.is_joker: continue
            if c.is_red() == card.is_red():
                v2 = rank_to_num(c.rank)
                if abs(val - v2) == 1: score += 12
                elif abs(val - v2) == 2: score += 6
        scores.append(score)

    legal_indices = [i for i, c in enumerate(hand) if not c.is_joker]
    if not legal_indices: return 0
    min_score = min(scores[i] for i in legal_indices)
    return random.choice([i for i in legal_indices if scores[i] == min_score])