import pygame
import config

SUITS = ["H", "D", "S", "C"] 
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
RANK_ORDER = {r: i for i, r in enumerate(RANKS)}
SORT_SUIT_ORDER = {"S": 0, "C": 1, "D": 2, "H": 3}

DEALER_RANK_STR = {r: i for i, r in enumerate(["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"])}
DEALER_SUIT_STR = {"H": 0, "D": 1, "C": 2, "S": 3}

def _draw_heart(surface, cx, cy, size, color):
    r = size * 0.28
    pygame.draw.circle(surface, color, (int(cx - r), int(cy - size * 0.15)), int(r))
    pygame.draw.circle(surface, color, (int(cx + r), int(cy - size * 0.15)), int(r))
    pts = [(cx - size * 0.53, cy - size * 0.15), (cx + size * 0.53, cy - size * 0.15), (cx, cy + size * 0.55)]
    pygame.draw.polygon(surface, color, pts)

def _draw_diamond(surface, cx, cy, size, color):
    pts = [(cx, cy - size * 0.55), (cx + size * 0.40, cy), (cx, cy + size * 0.55), (cx - size * 0.40, cy)]
    pygame.draw.polygon(surface, color, pts)

def _draw_spade(surface, cx, cy, size, color):
    pts_stem = [
        (cx, cy + size * 0.20), 
        (cx - size * 0.10, cy + size * 0.50), 
        (cx + size * 0.10, cy + size * 0.50)
    ]
    pygame.draw.polygon(surface, color, pts_stem)
    
    r = size * 0.26
    pygame.draw.circle(surface, color, (int(cx - r), int(cy + size * 0.12)), int(r))
    pygame.draw.circle(surface, color, (int(cx + r), int(cy + size * 0.12)), int(r))
    
    pts = [
        (cx - size * 0.52, cy + size * 0.12), 
        (cx + size * 0.52, cy + size * 0.12), 
        (cx, cy - size * 0.50)
    ]
    pygame.draw.polygon(surface, color, pts)

def _draw_club(surface, cx, cy, size, color):
    pts_stem = [
        (cx, cy + size * 0.10), 
        (cx - size * 0.06, cy + size * 0.45), 
        (cx + size * 0.06, cy + size * 0.45)
    ]
    pygame.draw.polygon(surface, color, pts_stem)
    
    r = size * 0.23
    pygame.draw.circle(surface, color, (int(cx), int(cy - size * 0.20)), int(r))
    pygame.draw.circle(surface, color, (int(cx - size * 0.24), int(cy + size * 0.10)), int(r))
    pygame.draw.circle(surface, color, (int(cx + size * 0.24), int(cy + size * 0.10)), int(r))
    
    pygame.draw.circle(surface, color, (int(cx), int(cy)), int(r * 0.8))

def draw_suit_icon(surface, suit, cx, cy, size, color):
    if suit == "H": _draw_heart(surface, cx, cy, size, color)
    elif suit == "D": _draw_diamond(surface, cx, cy, size, color)
    elif suit == "S": _draw_spade(surface, cx, cy, size, color)
    elif suit == "C": _draw_club(surface, cx, cy, size, color)

class Card:
    def __init__(self, suit, rank, is_joker=False):
        self.suit = suit
        self.rank = rank
        self.is_joker = is_joker

    def is_red(self): return self.suit in ["H", "D"]
    def is_black(self): return self.suit in ["S", "C"]
    
    def get_dealer_strength(self):
        if self.is_joker: return 999
        return DEALER_RANK_STR[self.rank] * 4 + DEALER_SUIT_STR[self.suit]

    def draw(self, surface, x, y, width=None, height=None, highlighted=False, highlight_color=config.GOLD, is_dora=False):
        if width is None: width = config.S(80)
        if height is None: height = config.S(120)
        
        rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, config.CARD_BG, rect, border_radius=config.S(8))
        
        border_c = highlight_color if highlighted else config.CARD_BORDER
        border_w = config.S(4) if highlighted else max(1, config.S(2))
        pygame.draw.rect(surface, border_c, rect, width=border_w, border_radius=config.S(8))

        if self.is_joker:
            txt = config.font_mid.render("JK", True, config.RED)
            surface.blit(txt, (x + width//2 - txt.get_width()//2, y + height//2 - txt.get_height()//2))
        else:
            text_color = config.RED if self.is_red() else config.BLACK
            suit_color = text_color
            
            if self.suit == "S":
                text_color, suit_color = (0, 0, 0), (0, 0, 0)
            elif self.suit == "C":
                text_color, suit_color = (20, 80, 40), (20, 80, 40)
            elif self.suit == "H":
                text_color, suit_color = (240, 80, 120), (240, 80, 120)
            elif self.suit == "D":
                text_color, suit_color = (255, 0, 0), (255, 0, 0)

            if width > config.S(60):
                rank_txt = config.font_mid.render(self.rank, True, text_color)
                surface.blit(rank_txt, (x + config.S(8), y + config.S(4)))
                icon_size = width * 0.56
                draw_suit_icon(surface, self.suit, x + width // 2, y + height // 2 + config.S(10), icon_size, suit_color)
            elif width > config.S(40):
                rank_txt = config.font_small.render(self.rank, True, text_color)
                surface.blit(rank_txt, (x + config.S(6), y + config.S(2)))
                icon_size = width * 0.62
                draw_suit_icon(surface, self.suit, x + width // 2, y + height // 2 + config.S(6), icon_size, suit_color)
            else:
                rank_txt = config.font_small.render(self.rank, True, text_color)
                surface.blit(rank_txt, (x + config.S(4), y + config.S(1)))
                icon_size = width * 0.66
                draw_suit_icon(surface, self.suit, x + width // 2, y + height // 2 + config.S(5), icon_size, suit_color)
                
        if is_dora and not self.is_joker:
            radius = max(config.S(4), int(width * 0.15))
            cx, cy = x + width - radius - config.S(4), y + radius + config.S(4)
            pygame.draw.circle(surface, config.GOLD, (cx, cy), radius)
            pygame.draw.circle(surface, config.BLACK, (cx, cy), radius, max(1, config.S(1)))