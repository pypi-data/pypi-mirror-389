# suggested_card.py

"""Suggested card for Card Player."""
from bridgeobjects import Card, SEATS
from bfgdealer import Board

import bfgcardplay.global_variables as global_vars
from bfgcardplay.player import Player
from bfgcardplay.opening_lead_card import opening_lead_card
from bfgcardplay.opening_lead_suit import opening_lead_suit
from bfgcardplay.first_seat_defender import FirstSeatDefender
from bfgcardplay.first_seat_declarer_suit import FirstSeatDeclarerSuit
from bfgcardplay.first_seat_declarer_nt import FirstSeatDeclarerNT
from bfgcardplay.second_seat_defender import SecondSeatDefender
from bfgcardplay.second_seat_declarer import SecondSeatDeclarer
from bfgcardplay.third_seat_defender import ThirdSeatDefender
from bfgcardplay.third_seat_declarer import ThirdSeatDeclarer
from bfgcardplay.fourth_seat_defender import FourthSeatDefender
from bfgcardplay.fourth_seat_declarer import FourthSeatDeclarer

# from .double_dummy import double_dummy_suggestion

MODULE_COLOUR = 'green'


def next_card(board: Board, use_double_dummy: bool = False) -> Card | None:
    """Return the suggested card from the current state of play."""
    card_to_play = _card_to_play(board)
    if not card_to_play:
        return None

    # if use_double_dummy and len(board.tricks[0].cards) > 0:
    #     double_dummy_card = double_dummy_suggestion(board, card_to_play)
    #     if double_dummy_card:
    #         # TODO Temporary print
    #         cprint(f'get card {card_to_play} {double_dummy_card}', 'red')
    #         return double_dummy_card

    return card_to_play


def _card_to_play(board: Board) -> Card | None:
    unplayed_cards_in_board = _unplayed_cards(board)

    if unplayed_cards_in_board == 52:
        return _opening_lead(board)

    if unplayed_cards_in_board == 0:
        return None

    return _next_card(board)


def _next_card(board: Board) -> Card:
    player = Player(board)
    trick_cards = len(board.tricks[-1].cards)
    if trick_cards in [0, 4]:
        return first_seat_card(player)
    if trick_cards == 1:
        return second_seat_card(player)
    if trick_cards == 2:
        return third_seat_card(player)
    if trick_cards == 3:
        return fourth_seat_card(player)
    raise ValueError(f'No card to return for {board}')


def _opening_lead(board: Board) -> Card:
    """Return the proposed opening lead for the board."""
    global_vars.initialize()
    if not board.contract.declarer:
        return None
    opening_suit = opening_lead_suit(board)
    leader = board.contract.leader
    leaders_cards = board.hands[leader].cards
    cards = [card for card in leaders_cards if card.suit == opening_suit]
    opening_card = opening_lead_card(cards, board.contract)
    return opening_card


def first_seat_card(player: Player) -> Card:
    """Return the card for the first seat."""
    if player.is_defender:
        selected_card = FirstSeatDefender(player).selected_card()
    else:
        if player.trump_suit:
            selected_card = FirstSeatDeclarerSuit(player).selected_card()
        else:
            selected_card = FirstSeatDeclarerNT(player).selected_card()
    return selected_card


def second_seat_card(player: Player) -> Card:
    """Return the card for the second seat."""
    if player.is_defender:
        selected_card = SecondSeatDefender(player).selected_card()
    else:
        selected_card = SecondSeatDeclarer(player).selected_card()
    return selected_card


def third_seat_card(player: Player) -> Card:
    """Return the card for the third seat."""
    if player.is_defender:
        selected_card = ThirdSeatDefender(player).selected_card()
    else:
        selected_card = ThirdSeatDeclarer(player).selected_card()
    return selected_card


def fourth_seat_card(player: Player) -> Card:
    """Return the card for the fourth seat."""
    if player.is_defender:
        selected_card = FourthSeatDefender(player).selected_card()
    else:
        selected_card = FourthSeatDeclarer(player).selected_card()
    return selected_card


def _unplayed_cards(board: Board):
    unplayed_cards = 0
    for seat in SEATS:
        unplayed_cards += len(board.hands[seat].unplayed_cards)
    return unplayed_cards
