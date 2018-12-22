#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random

from core import log, ace, right, left

def play(hand, plays, winning):
    """
    :param hand:
    :param plays: [(player, card), ...]
    :param winning: (player, card)
    :return: Card
    """
    deal = hand.deal
    play_rnd = len(deal.tricks) + 1

    if not plays:
        play_func = init_lead if play_rnd == 1 else subseq_lead
    else:
        partner_winning = hand.is_partner(winning[0])
        play_func = play_part_winning if partner_winning else play_opp_winning

    return hand.play_card(play_func(hand, plays, winning))

def init_lead(hand, plays, winning):
    """
    """
    deal      = hand.deal
    tru_cards = hand.trump_cards
    off_aces  = hand.off_aces

    # next call logic (weaker hand)
    """
      * The best first lead on a next call is a small trump, this is especially
        true if you hold an off-suit Ace. By leading a small trump you stand the
        best chance of hitting your partner's hand. Remember, the odds are that
        he will have at least one bower in his hand
      * Leading the right may not be the best move. Your partner may only have
        one bower in his hand and you don't want them to clash. When you are
        holding a right/ace combination it's usually best to lead the ace. If
        the other bower has been turned down, then it is okay to lead the right.
      * In a hand where you only hold two small cards in next but no power, try
        leading an off suit that you think your partner may be able to trump.
        You may need the trump to make your point.
      * If your partner calls next and leads a trump, DO NOT lead trump back.
    """
    if deal.is_next_call:
        if not hand.has_bower:
            log.debug("No bower, leading small trump")
            return tru_cards[0]
        elif len(tru_cards) > 1:
            if tru_cards[-1].rank == right and tru_cards[-2].rank == ace:
                log.debug("Leading ace from right-ace")
                return tru_cards[-2]
            if tru_cards[-1].level < ace['level']:
                grn_suitcards = hand.green_suitcards
                if grn_suitcards[0]:
                    log.debug("Leading from longest green suit")
                    return grn_suitcards[0][0]

    # draw trump if caller (strong hand), or flush out bower
    if hand == deal.caller:
        if len(tru_cards) >= 3:
            log.debug("Drawing trump (or flushing out bower)")
            return tru_cards[-1]

    # off-ace (short suit, or green if defending?)
    if off_aces:
        # TODO: choose more wisely if more than one!!!
        log.debug("Lead an off-ace (random for now)")
        return random.choice(off_aces)

    # lead bower if partner is caller (green suit)?
    if hand.has_bower and hand.is_partner(deal.caller):
        log.debug("Leading bower to partner's call")
        return tru_cards[-1]

    # lead low from long suit (favor green if defeending?)
    suitcards = hand.suitcards.copy()
    suitcards.sort(key=lambda s: len(s))
    # TODO: a little more logic in choosing suit!!!
    log.debug("Leading low from longest suit")
    return suitcards[-1][0]

def subseq_lead(hand, plays, winning):
    """
    """
    deal      = hand.deal
    tru_cards = hand.trump_cards
    off_aces  = hand.off_aces

    # TEMP!!!
    return play_random(hand, plays, winning)

def play_part_winning(hand, plays, winning):
    """
    """
    lead_card = plays[0][1]
    play_pos  = len(plays)  # 0 = lead, etc.

    # follow suit low
    # create void (if early in deal)
    # throw off lowest card (similar to discard logic)

    # TEMP!!!
    return play_random(hand, plays, winning)

def play_opp_winning(hand, plays, winning):
    """
    """
    lead_card = plays[0][1]
    play_pos  = len(plays)  # 0 = lead, etc.

    # follow suit high
    # trump low
    # create void (if early in deal)
    # throw off lowest card (similar to discard logic)

    # TEMP!!!
    return play_random(hand, plays, winning)

def play_random(hand, plays, winning):
    """Play random card, but follow suit if possible
    """
    if plays:
        lead_card = plays[0][1]
        suit_idx = lead_card.suit['idx']
        if hand.suitcards[suit_idx]:
            log.debug("Play random card (follow suit)")
            return random.choice(hand.suitcards[suit_idx])

    log.debug("Play random card")
    return random.choice(hand.cards)
