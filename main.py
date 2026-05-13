import pygame
import os
import random

# -----------------------------
# INIT
# -----------------------------
pygame.init()
pygame.font.init()

WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Blackjack")

font = pygame.font.SysFont(None, 36)
big_font = pygame.font.SysFont(None, 60)

DEAL_DELAY = 500

# -----------------------------
# STATE
# -----------------------------
start_screen = True
start_input = ""
start_error = ""

bet_screen = False
bet_input = ""
bet_error = ""
bet = 0

chips = 0
bankrupt = False

game_over = False
show_dealer = False
end_message = ""

insurance_screen = False
insurance_error = ""
insurance_bet = 0

# ===== ADDED FOR DOUBLE DOWN =====
player_locked = False

# -----------------------------
# CUT CARD
# -----------------------------
cut_triggered = False
cut_position = 0

def set_cut_card():
    global CUT_CARD_PERCENT, cut_position
    CUT_CARD_PERCENT = random.uniform(0.25, 0.35)
    cut_position = int(len(deck) * CUT_CARD_PERCENT)

def check_cut_card():
    global cut_triggered
    if len(deck) <= cut_position:
        cut_triggered = True

def reshuffle_deck():
    global deck, cut_triggered
    deck = [(r, s) for s in suits for r in ranks]
    random.shuffle(deck)
    set_cut_card()
    cut_triggered = False

# -----------------------------
# LOAD ASSETS
# -----------------------------
card_folder = "assets/cards"
card_images = {}

card_back = pygame.image.load("assets/cards/card_back.png")
card_back = pygame.transform.scale(card_back, (96, 144))

table_img = pygame.image.load("assets/cards/table.jpg")
table_img = pygame.transform.scale(table_img, (WIDTH, HEIGHT))

suits = ["hearts", "diamonds", "clubs", "spades"]
ranks = ["2","3","4","5","6","7","8","9","10","Jack","Queen","King","Ace"]

for suit in suits:
    for rank in ranks:
        key = f"{rank}_of_{suit}"
        path = os.path.join(card_folder, f"{key}.png")
        img = pygame.image.load(path)

        w, h = img.get_size()
        new_w = 100
        new_h = int(h * (new_w / w))
        card_images[key] = pygame.transform.scale(img, (new_w, new_h))

card_values = {
    "2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,"10":10,
    "Jack":10,"Queen":10,"King":10,"Ace":11
}

# -----------------------------
# BUTTONS
# -----------------------------
hit_rect = pygame.Rect(1100, 610, 100, 50)
stand_rect = pygame.Rect(1100, 540, 100, 50)
play_again_rect = pygame.Rect(560, 400, 180, 60)

# ===== ADDED DOUBLE BUTTON =====
double_rect = pygame.Rect(1100, 470, 100, 50)
insurance_yes_rect = pygame.Rect(450, 350, 120, 60)
insurance_no_rect = pygame.Rect(700, 350, 120, 60)

hit_text = font.render("Hit", True, (255,255,255))
stand_text = font.render("Stand", True, (255,255,255))
play_again_text = font.render("Play Again", True, (255,255,255))

# ===== ADDED =====
double_text = font.render("Double", True, (255,255,255))

insurance_yes_text = font.render("Yes", True, (255,255,255))
insurance_no_text = font.render("No", True, (255,255,255))
# -----------------------------
# GAME STATE
# -----------------------------
deck = []
player_hand = []
dealer_hand = []

set_cut_card()

# -----------------------------
# HELPERS
# -----------------------------
def card_key(card):
    r, s = card
    return f"{r}_of_{s}"

def draw_panel(text, pos, color=(0,0,0), alpha=180, text_color=(255,255,255), f=font, draw=True):
    surf = f.render(text, True, text_color)
    w, h = surf.get_size()

    box = pygame.Surface((w + 20, h + 20), pygame.SRCALPHA)
    box.fill((*color, alpha))

    if draw:
        screen.blit(box, pos)
        screen.blit(surf, (pos[0] + 10, pos[1] + 10))

    return w + 20, h + 20

def center_pos(width, height):
    return (WIDTH // 2 - width // 2, HEIGHT // 2 - height // 2)

def draw_button(rect, color, text):
    pygame.draw.rect(screen, color, rect)

    text_rect = text.get_rect(center=rect.center)
    screen.blit(text, text_rect)

def draw_hand(hand, x, y, hide_second=False, diagonal=False):
    for i, card in enumerate(hand):

        if diagonal:
            draw_x = x + i * 40
            draw_y = y - i * 20
        else:
            draw_x = x + i * 40
            draw_y = y

        if hide_second and i == 1:
            screen.blit(card_back, (draw_x, draw_y))
        else:
            screen.blit(card_images[card_key(card)], (draw_x, draw_y))

def calculate_hand_total(hand):
    total = 0
    aces = 0

    for r, s in hand:
        total += card_values[r]
        if r == "Ace":
            aces += 1

    while total > 21 and aces:
        total -= 10
        aces -= 1

    return total

def is_soft(hand):
    total = sum(card_values[r] for r, s in hand)
    aces = sum(1 for r, s in hand if r == "Ace")
    return aces > 0 and total <= 21

def dealer_has_blackjack():
    a, b = dealer_hand[0][0], dealer_hand[1][0]
    return (
        (a == "Ace" and b in ["10","Jack","Queen","King"]) or
        (b == "Ace" and a in ["10","Jack","Queen","King"])
    )

# ===== ADDED =====
def end_round(message):
    global game_over, show_dealer, end_message, player_locked, bankrupt

    show_dealer = True
    game_over = True
    player_locked = True
    end_message = message

    if chips <= 0: 
        bankrupt = True

# -----------------------------
# RENDER
# -----------------------------
def render():
    screen.blit(table_img, (0, 0))

    draw_hand(dealer_hand, 603, 15, hide_second=not show_dealer)
    draw_hand(player_hand, 603, 505, diagonal=True)

    draw_panel(f"Player: {calculate_hand_total(player_hand)}", (590, 425))

    if len(dealer_hand) > 0:
        dealer_val = calculate_hand_total(dealer_hand) if show_dealer else card_values[dealer_hand[0][0]]
    else:
        dealer_val = 0    
    
    draw_panel(f"Dealer: {dealer_val}", (590, 205))

    draw_panel(f"Chips: {chips}", (25, 20))
    draw_panel(f"Bet: {bet}", (25, 60))

    if not game_over:
        draw_button(hit_rect, (200,0,0), hit_text)
        draw_button(stand_rect, (0,0,200), stand_text)

        # ===== ADDED DOUBLE BUTTON RENDER =====
        if len(player_hand) == 2:
            draw_button(double_rect, (200,150,0), double_text)

    else:
        size = draw_panel(end_message, (0, 0), color=(0,0,0), alpha=200, text_color=(255,255,0), f=big_font, draw=False)
        pos = center_pos(*size)
        draw_panel(end_message, pos, color=(0,0,0), alpha=200, text_color=(255,255,0), f=big_font)
        pygame.draw.rect(screen, (0,150,0), play_again_rect)
        screen.blit(play_again_text, (play_again_rect.x + 20, play_again_rect.y + 15))

# ===== INSURANCE PROMPT =====
    if insurance_screen:

        draw_panel(
            "INSURANCE? Dealer shows Ace",
            (420, 250),
            text_color=(255,255,0),
            f=big_font
        )

        draw_button(insurance_yes_rect, (0,150,0), insurance_yes_text)
        draw_button(insurance_no_rect, (150,0,0), insurance_no_text)
    pygame.display.flip()

    if insurance_error:
        draw_panel(insurance_error, (400, 250), text_color=(255,0,0))
# -----------------------------
# DEAL
# -----------------------------
def deal(hand):
    card = random.choice(deck)
    deck.remove(card)
    hand.append(card)
    check_cut_card()

    render()
    pygame.time.delay(DEAL_DELAY)

# ===== ADDED DOUBLE DOWN =====
def double_down():
    global chips, bet, player_locked

    if player_locked:
        return

    if len(player_hand) != 2:
        return

    if chips < bet:
        return

    player_locked = True

    chips -= bet
    bet *= 2

    deal(player_hand)

    if calculate_hand_total(player_hand) > 21:
        end_round("You Bust! Dealer Wins")
    else:
        dealer_play()

def resume_after_insurance():
    global chips

    p_total = calculate_hand_total(player_hand)

    if dealer_has_blackjack():
        if p_total == 21:
            chips += bet
            end_round("Push")
        else:
            end_round("Dealer Blackjack!")
        return

    # normal blackjack check after insurance
    if p_total == 21:
        winnings = bet * 2.5
        chips += winnings
        end_round(f"Blackjack! You won {winnings} chips!")

# -----------------------------
# RESET ROUND
# -----------------------------
def reset_round():
    global player_hand, dealer_hand, game_over, show_dealer, player_locked
    global insurance_screen, insurance_bet

    player_hand = []
    dealer_hand = []
    game_over = False
    show_dealer = False
    player_locked = False
    insurance_screen = False
    insurance_bet = 0 
    insurance_error = ""

    if cut_triggered:
        reshuffle_deck()

# -----------------------------
# START ROUND
# -----------------------------
def start_round():
    global chips, bet, insurance_screen

    reset_round()

    # Casino-style dealing
    deal(player_hand)
    deal(dealer_hand)
    deal(player_hand)
    deal(dealer_hand)
    # FORCE DEALER UP CARD TO ACE (TESTING ONLY)
    dealer_hand[0] = ("Ace", dealer_hand[0][1])

# ===== INSURANCE CHECK (ONLY IF PLAYER CAN AFFORD IT) =====
    if dealer_hand[0][0] == "Ace":

        max_insurance = bet // 2

        # only show insurance if player can actually afford it
        if chips >= max_insurance:
            insurance_screen = True
            return

        # otherwise skip insurance entirely
        insurance_screen = False

    p_total = calculate_hand_total(player_hand)

    if (p_total == 21 and len(player_hand) == 2) or dealer_has_blackjack():
        if dealer_has_blackjack() and p_total != 21:
            result = "Dealer Blackjack!"
        elif p_total == 21:
            winnings = bet * 2.5
            chips += winnings
            result = f"Blackjack! You won {winnings} chips!"
        else:
            chips += bet
            result = "Push"

        end_round(result)
# -----------------------------
# DEALER
# -----------------------------
def dealer_play():
    global chips, show_dealer

    show_dealer = True

    player_total = calculate_hand_total(player_hand)

    if player_total > 21:
        end_round("You Bust! Dealer Wins")
        return

    render()
    pygame.time.delay(DEAL_DELAY)

    while True:
        total = calculate_hand_total(dealer_hand)

        if total < 17 or (total == 17 and is_soft(dealer_hand)):
            deal(dealer_hand)
        else:
            break

    dealer_total = calculate_hand_total(dealer_hand)

    if dealer_total > 21:
        winnings = bet * 2
        chips += winnings
        result = f"Dealer busts! You won {winnings} chips!"
    elif player_total > dealer_total:
        winnings = bet * 2
        chips += winnings
        result = f"You won {winnings} chips!"
    elif player_total < dealer_total:
        result = "Dealer Wins"
    else:
        result = "Push"
        chips += bet

    end_round(result)

# -----------------------------
# INIT DECK
# -----------------------------
deck = [(r, s) for s in suits for r in ranks] * 6
random.shuffle(deck)
set_cut_card()

# -----------------------------
# MAIN LOOP
# -----------------------------
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # -------- START SCREEN --------
        if start_screen:

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_BACKSPACE:
                    start_input = start_input[:-1]
                    start_error = ""

                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):

                    if start_input.isdigit():
                        value = int(start_input)

                        if value <= 0:
                            start_input = ""
                            start_error = "Enter a valid amount"
                            continue

                        chips = value
                        start_screen = False
                        bet_screen = True

                elif event.unicode.isdigit():
                    start_input += event.unicode

        # -------- BET SCREEN --------
        elif bet_screen:

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_BACKSPACE:
                    bet_input = ""
                    bet_error = ""

                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):

                    if bet_input.isdigit():
                        value = int(bet_input)

                        if value <= 0:
                            bet_input = ""
                            bet_error = "Enter a valid bet"
                            continue

                        if value > chips:
                            bet_input = ""
                            bet_error = "Bet exceeds chips"
                            continue

                        bet_error = ""
                        bet = value
                        chips -= bet

                        bet_screen = False
                        start_round()

                elif event.unicode.isdigit():
                    bet_input += event.unicode

        # -------- GAME --------
        else:

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos

# ===== INSURANCE CLICK HANDLING =====
                if insurance_screen:

                    if insurance_yes_rect.collidepoint(mx, my):

                        insurance_bet = bet // 2
                        chips -= insurance_bet
                        insurance_screen = False

                        if dealer_has_blackjack():
                            chips += insurance_bet * 3
                            end_round("Insurance Wins! Dealer Blackjack")
                        else:
                            resume_after_insurance()

                        continue


                    elif insurance_no_rect.collidepoint(mx, my):

                        insurance_bet = 0
                        insurance_screen = False

                        resume_after_insurance()

                        continue


                # ===== NORMAL GAME CLICK HANDLING =====
                if game_over:
                    if play_again_rect.collidepoint(mx, my):
                        bet_screen = True
                        bet_input = ""
                        bet_error = ""
                else:

                    if hit_rect.collidepoint(mx, my):
                        if player_locked:
                            continue

                        deal(player_hand)

                        total = calculate_hand_total(player_hand)

                        if total > 21:
                            end_round("You Bust! Dealer Wins")

                        elif total == 21:
                            player_locked = True   
                            dealer_play()


                    elif stand_rect.collidepoint(mx, my):
                        if player_locked:
                            continue

                        dealer_play()

                    elif double_rect.collidepoint(mx, my):
                        if (not game_over) and (not player_locked) and len(player_hand) == 2:
                            double_down()

    # -----------------------------
    # RENDER
    # -----------------------------

    # -------- START SCREEN --------
    if start_screen:
        screen.blit(table_img, (0, 0))

        title_w, title_h = big_font.render("Starting Chips:", True, (255,255,255)).get_size()
        input_w, input_h = big_font.render(start_input if start_input else " ", True, (255,255,0)).get_size()

        block_width = max(title_w, input_w) + 20
        block_height = title_h + input_h + 30

        x, y = center_pos(block_width, block_height)

        draw_panel("Starting Chips:", (x, y), f=big_font)
        draw_panel(start_input, (x+75, y + title_h + 25), text_color=(255,255,0), f=big_font)

        if start_error:
            draw_panel(start_error, (520, 400), text_color=(255,0,0))

        pygame.display.flip()

    # -------- BET SCREEN --------
    elif bet_screen:
        screen.blit(table_img, (0, 0))

        if bankrupt:
            title_w, title_h = font.render("OUT OF CHIPS", True, (255,0,0)).get_size()
            sub_w, sub_h = font.render("Restart game to play again", True, (255,255,255)).get_size()

            block_width = max(title_w, sub_w) + 20
            block_height = (title_h + sub_h) + 30

            x, y = center_pos(block_width, block_height)

            draw_panel("OUT OF CHIPS", (x, y), text_color=(255,0,0), f=big_font)
            draw_panel("Restart game to play again", (x, y + 70))
        else:
            title_w, title_h = big_font.render("Enter Bet:", True, (255,255,255)).get_size()
            input_w, input_h = big_font.render(bet_input if bet_input else " ", True, (255,255,0)).get_size()

            block_width = max(title_w, input_w) + 20
            block_height = title_h + input_h + 30

            x, y = center_pos(block_width, block_height)

            draw_panel("Enter Bet:", (x, y), f=big_font)
            draw_panel(bet_input, (x+75, y + title_h + 25), text_color=(255,255,0), f=big_font)

        draw_panel(f"Chips: {chips}", (25, 20))

        if bet_error:
            draw_panel(bet_error, (520, 400), text_color=(255,0,0))

        pygame.display.flip()

    else:
        render()

pygame.quit()