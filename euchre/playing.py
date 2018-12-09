#!/usr/bin/env python
# -*- coding: utf-8 -*-

from core import log

def play(hand, plays, winning):
    """
    :param hand:
    :param plays: [(player, card), ...]
    :param winning: (player, card)
    :return: Card
    """
    if not plays:
        play_func = lead
    else:
        lead_card       = plays[0][1]
        winning_hand    = winning[0]
        partner_winning = hand.is_partner(winning_hand)
        play_pos        = len(plays)  # 0 = lead, etc.

        play_func = play_partner_winning if partner_winning else play_opponent_winning

    return play_func(hand, plays, winning)
    

def lead(hand, plays, winning):
    """
    """
    # next call logic (weaker hand)
    """
        ◦ The best first lead on a next call is a small trump, this is especially
          true if you hold an off-suit Ace. By leading a small trump you stand the
          best chance of hitting your partner's hand. Remember, the odds are that
          he will have at least one bower in his hand
        ◦ Leading the right may not be the best move. Your partner may only have
          one bower in his hand and you don't want them to clash. When you are
          holding a right/ace combination it's usually best to lead the ace. If
          the other bower has been turned down, then it is okay to lead the right.
        ◦ In a hand where you only hold two small cards in next but no power, try
          leading an off suit that you think your partner may be able to trump.
          You may need the trump to make your point.
        ◦ If your partner calls next and leads a trump, DO NOT lead trump back.
    """

    # draw trump if caller (strong hand), or flush out bower

    # off-ace (short suit, or green if defending?)

    # lead low from long suit (favor green if defeending?)

    # lead bower if partner is caller (green suit)?

    # TEMP: for now, just return first card (remove from hand)!!!
    return hand.cards.pop(0)

def play_partner_winning(hand, plays, winning):
    """
    """
    # follow suit low
    # create void (if early in deal)
    # throw off lowest card (similar to discard logic)

    # TEMP: for now, just return first card (remove from hand)!!!
    return hand.cards.pop(0)

def play_opponent_winning(hand, plays, winning):
    """
    """
    # follow suit high
    # trump low
    # create void (if early in deal)
    # throw off lowest card (similar to discard logic)

    # TEMP: for now, just return first card (remove from hand)!!!
    return hand.cards.pop(0)

def play_random(hand, plays, winning):
    """
    """
    # NOTE: this is just a stand-in and does not necessarily make
    # legal play
    return hand.cards.pop(0)
