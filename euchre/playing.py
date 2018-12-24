#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
from enum import Enum, auto

from core import log, ace, right, left

class Strategy(Enum):
    DRAW_TRUMP     = auto()
    PRESERVE_TRUMP = auto()
    NO_MORE_TRUMP  = auto()
    TAKE_TRICKS    = auto()

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
    deal       = hand.deal
    tru_idx    = deal.contract['idx']
    tru_cards  = hand.trump_cards
    off_aces   = hand.off_aces
    singletons = [s[0] for s in hand.suitcards
                  if len(s) == 1 and s[0].suit['idx'] != tru_idx]

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
            hand.strategy.append(Strategy.PRESERVE_TRUMP)
            return tru_cards[0]
        elif len(tru_cards) > 1:
            if tru_cards[-1].rank == right and tru_cards[-2].rank == ace:
                log.debug("Leading ace from right-ace")
                hand.strategy.append(Strategy.DRAW_TRUMP)
                return tru_cards[-2]
            if tru_cards[-1].level < ace['level']:
                grn_suitcards = hand.green_suitcards
                if grn_suitcards[0]:
                    log.debug("Leading from longest green suit")
                    hand.strategy.append(Strategy.PRESERVE_TRUMP)
                    return grn_suitcards[0][0]

    # draw trump if caller (strong hand), or flush out bower
    if hand == deal.caller:
        if len(tru_cards) >= 3:
            hand.strategy.append(Strategy.DRAW_TRUMP)
            log.debug("Drawing trump (or flushing out bower)")
            return tru_cards[-1]

    # off-ace (short suit, or green if defending?)
    if off_aces:
        if len(off_aces) == 1:
            log.debug("Lead off-ace")
            return off_aces[0]
        else:
            # TODO: choose more wisely if more than one!!!
            log.debug("Lead off-ace (random choice)")
            return random.choice(off_aces)

    # lead bower if partner is caller (esp. in green suit)?
    if hand.has_bower and hand.is_partner(deal.caller):
        log.debug("Leading bower to partner's call")
        return tru_cards[-1]

    # if trump in hand, try and void a suit
    if tru_cards and singletons:
        if len(singletons) == 1:
            log.debug("Lead singleton to void suit")
            return singletons[0]
        else:
            # REVISIT: add some logic for choosing if more than one singleton!!!
            log.debug("Lead singleton to void suit (random choice)")
            return random.choice(singletons)

    # lead low from long suit (favor green if defeending?)
    suitcards = hand.suitcards.copy()
    suitcards.sort(key=lambda s: len(s))
    # TODO: a little more logic in choosing suit!!!
    log.debug("Leading low from longest suit")
    return suitcards[-1][0]

def subseq_lead(hand, plays, winning):
    """
    """
    # deal stats
    deal          = hand.deal
    play_rnd      = len(deal.tricks) + 1
    tru_idx       = deal.contract['idx']
    trump_seen    = deal.stats.seen[tru_idx]
    trump_unseen  = deal.stats.unseen[tru_idx]

    # hand stats
    tru_cards     = hand.trump_cards
    off_aces      = hand.off_aces
    singletons    = [s[0] for s in hand.suitcards
                     if len(s) == 1 and s[0].suit['idx'] != tru_idx]
    missing_trump = set(trump_unseen).difference(tru_cards)  # note: set!!!
    my_high_cards = [c for c in deal.stats.high_cards
                     if c in hand.cards and c.suit['idx'] != tru_idx]

    if len(hand.cards) == 1:
        log.debug("Lead last card")
        return hand.cards[0]

    # if drawing trump (as caller)
    if hand == deal.caller and missing_trump:
        if Strategy.DRAW_TRUMP in hand.strategy:
            if len(tru_cards) > 2:
                log.debug("Continue drawing trump")
                return tru_cards[-1]
            elif len(tru_cards) >= 2:
                log.debug("Last round of drawing trump")
                hand.strategy.remove(Strategy.DRAW_TRUMP)
                return tru_cards[-1]
        elif len(tru_cards) >= 3:
            hand.strategy.append(Strategy.DRAW_TRUMP)
            log.debug("Drawing trump (or flushing out bower)")
            return tru_cards[-1]

    # no trump seen with parter as caller
    if hand.is_partner(deal.caller) and not trump_seen:
        if tru_cards:
            if hand.has_bower:
                log.debug("Leading bower to partner's call")
                return tru_cards[-1]
            elif len(tru_cards) > 1:
                log.debug("Leading low trump to partner's call")
                return tru_cards[0]
            elif singletons:
                if len(singletons) == 1:
                    log.debug("Lead singleton to void suit")
                    return singletons[0]
                else:
                    # REVISIT: not sure we should do this, but if so, add some logic for
                    # choosing if more than one singleton!!!
                    log.debug("Lead singleton to void suit (random choice)")
                    return random.choice(singletons)

    # off-ace (short suit, or green if defending?)
    if off_aces:
        if len(off_aces) == 1:
            log.debug("Lead off-ace")
            return off_aces[0]
        else:
            # TODO: choose more wisely if more than one, or possible preserve ace to
            # avoid being trumped!!!
            log.debug("Lead off-ace (random choice)")
            return random.choice(off_aces)

    # try to lead winner (non-trump)
    if my_high_cards:
        my_high_cards.sort(key=lambda c: c.efflevel[tru_idx])
        log.debug("Try and lead a winner (though may get trumped)")
        # REVISIT: is this the right logic (perhaps makes no sense if preceded by
        # off-ace rule)???
        return my_high_cards[-1] if play_rnd <= 3 else my_high_cards[0]

    # if trump in hand, try and void a suit
    if tru_cards and singletons:
        if len(singletons) == 1:
            log.debug("Lead singleton to void suit")
            return singletons[0]
        else:
            # REVISIT: perhaps only makes sense in earlier rounds (2 and 3), and otherwise
            # add some logic for choosing if more than one singleton!!!
            log.debug("Lead singleton to void suit (random for now)")
            return random.choice(singletons)

    # if still trump in hand, lead lowest card (non-trump)
    if tru_cards and len(tru_cards) < len(hand.cards):
        # NOTE: this will always pick the "lowest" suit in case multiple cards at min level
        non_trump_cards = [c for c in hand.cards if c.suit['idx'] != tru_idx]
        non_trump_cards.sort(key=lambda c: c.efflevel[tru_idx])
        log.debug("Lead lowest non-trump")
        return non_trump_cards[0]

    # catchall...
    log.debug("Lead random card")
    return random.choice(hand.cards)

def play_part_winning(hand, plays, winning):
    """
    """
    # deal stats
    deal          = hand.deal
    play_rnd      = len(deal.tricks) + 1
    play_pos      = len(plays)  # 0 = lead, etc.
    tru_idx       = deal.contract['idx']
    lead_card     = plays[0][1]
    lead_idx      = lead_card.suit['idx']

    # hand stats
    tru_cards     = hand.trump_cards
    singletons    = [s[0] for s in hand.suitcards
                     if len(s) == 1 and s[0].suit['idx'] != tru_idx]

    if len(hand.cards) == 1:
        log.debug("Play last card")
        return hand.cards[0]

    # follow suit low
    if hand.suitcards[lead_idx]:
        # REVISIT: are there cases where we want to try and take the lead???
        log.debug("Follow suit low")
        return hand.suitcards[lead_idx][0]

    # create void (if early in deal)
    if tru_cards and singletons:
        # REVISIT: perhaps only makes sense in earlier rounds (2 and 3), and also
        # reconsider selection if multiple (currently lowest valued)!!!
        singletons.sort(key=lambda c: c.efflevel[tru_idx])
        log.debug("Throw off singleton to void suit (lowest)")
        return singletons[0]

    # throw off lowest non-trump card
    if len(tru_cards) < len(hand.cards):
        # NOTE: this will always pick the "lowest" suit in case multiple cards at min level
        non_trump_cards = [c for c in hand.cards if c.suit['idx'] != tru_idx]
        non_trump_cards.sort(key=lambda c: c.efflevel[tru_idx])
        log.debug("Throw-off lowest non-trump")
        return non_trump_cards[0]

    # play lowest trump
    if tru_cards:
        # REVISIT: are there cases where we want to play a higher trump???
        log.debug("Play lowest trump")
        return tru_cards[0]

    # catchall...
    return play_random(hand, plays, winning)

def play_opp_winning(hand, plays, winning):
    """
    """
    # deal stats
    deal          = hand.deal
    play_rnd      = len(deal.tricks) + 1
    play_pos      = len(plays)  # 0 = lead, etc.
    tru_idx       = deal.contract['idx']
    lead_card     = plays[0][1]
    lead_idx      = lead_card.suit['idx']
    winning_card  = winning[1]
    lead_trumped  = lead_card.suit['idx'] != tru_idx and winning_card.suit['idx'] == tru_idx

    # hand stats
    tru_cards     = hand.trump_cards
    singletons    = [s[0] for s in hand.suitcards
                     if len(s) == 1 and s[0].suit['idx'] != tru_idx]

    if len(hand.cards) == 1:
        log.debug("Play last card")
        return hand.cards[0]

    # follow suit (high if can lead trick, low otherwise)
    if hand.suitcards[lead_idx]:
        if lead_trumped:
            log.debug("Follow suit low")
            return hand.suitcards[lead_idx][0]
        if hand.suitcards[lead_idx][-1].level > winning_card.level:
            # REVISIT: are there cases where we don't want to try and take the trick,
            # or not play???
            if play_pos == 3:
                for card in hand.suitcards[lead_idx]:
                    if card.level > winning_card.level:
                        log.debug("Follow suit, take winner")
                        return card
            else:
                log.debug("Follow suit high")
                return hand.suitcards[lead_idx][-1]

        log.debug("Follow suit low")
        return hand.suitcards[lead_idx][0]

    # trump (low) to lead trick
    if tru_cards:
        if lead_trumped:
            if tru_cards[-1].level > winning_card.level:
                # REVISIT: are there cases where we don't want to try and take the trick,
                # or not play???
                if play_pos == 3:
                    for card in tru_cards:
                        if card.level > winning_card.level:
                            log.debug("Overtrump, take winner")
                            return card
                else:
                    log.debug("Overtrump high")
                    return tru_cards[-1]
        else:
            # REVISIT: are there cases where we want to play a higher trump, or throw off???
            log.debug("Play lowest trump, to lead trick")
            return tru_cards[0]

    # create void (if early in deal)--NOTE: this only matters if we've decided not to
    # trump (e.g. to preserve for later)
    if tru_cards and singletons:
        # REVISIT: perhaps only makes sense in earlier rounds (2 and 3), and also
        # reconsider selection if multiple (currently lowest valued)!!!
        singletons.sort(key=lambda c: c.efflevel[tru_idx])
        log.debug("Throw off singleton to void suit (lowest)")
        return singletons[0]

    # throw off lowest non-trump card
    if len(tru_cards) < len(hand.cards):
        # NOTE: this will always pick the "lowest" suit in case multiple cards at min level
        non_trump_cards = [c for c in hand.cards if c.suit['idx'] != tru_idx]
        non_trump_cards.sort(key=lambda c: c.efflevel[tru_idx])
        log.debug("Throw-off lowest non-trump")
        return non_trump_cards[0]

    # catchall...
    return play_random(hand, plays, winning)

def play_random(hand, plays, winning):
    """Play random card, but follow suit if possible
    """
    if plays:
        lead_card = plays[0][1]
        suit_idx = lead_card.suit['idx']
        if hand.suitcards[suit_idx]:
            log.debug("Follow suit, random card")
            return random.choice(hand.suitcards[suit_idx])

    log.debug("Play random card")
    return random.choice(hand.cards)
