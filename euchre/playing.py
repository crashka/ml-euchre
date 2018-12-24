#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
from enum import Enum, auto

from core import log, ace, right, left

class Strategy(Enum):
    DRAW_TRUMP     = auto()
    PRESERVE_TRUMP = auto()

def play(hand, plays, winning):
    """
    :param hand:
    :param plays: [(player, card), ...]
    :param winning: (player, card)
    :return: Card
    """
    # deal stats
    deal          = hand.deal
    trick_no      = len(deal.tricks) + 1
    play_pos      = len(plays)  # 0 = lead, etc.
    tru_idx       = deal.contract['idx']
    trump_seen    = deal.stats.seen[tru_idx]
    trump_unseen  = deal.stats.unseen[tru_idx]
    if plays:
        lead_card    = plays[0][1]
        lead_idx     = lead_card.suit['idx']
        winning_card = winning[1]
        lead_trumped = lead_card.suit['idx'] != tru_idx and winning_card.suit['idx'] == tru_idx

    # hand stats
    trump_cards   = hand.trump_cards
    off_aces      = hand.off_aces
    singletons    = [s[0] for s in hand.suitcards
                     if len(s) == 1 and s[0].suit['idx'] != tru_idx]
    missing_trump = set(trump_unseen).difference(trump_cards)  # note: set!!!
    my_high_cards = [c for c in deal.stats.high_cards
                     if c in hand.cards and c.suit['idx'] != tru_idx]

    ########################
    # play selection rules #
    ########################

    #-----------------#
    # Lead Card Plays #
    #-----------------#

    def lead_last_card():
        """
        """
        if len(hand.cards) == 1:
            log.debug("Lead last card")
            return hand.cards[0]

    def next_call_lead():
        """Especially if calling with weaker hand...
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
                log.debug("No bower, lead small trump")
                hand.strategy.append(Strategy.PRESERVE_TRUMP)
                return trump_cards[0]
            elif len(trump_cards) > 1:
                if trump_cards[-1].rank == right and trump_cards[-2].rank == ace:
                    log.debug("Lead ace from right-ace")
                    hand.strategy.append(Strategy.DRAW_TRUMP)
                    return trump_cards[-2]
                if trump_cards[-1].level < ace['level']:
                    grn_suitcards = hand.green_suitcards
                    if grn_suitcards[0]:
                        log.debug("Lead from longest green suit")
                        hand.strategy.append(Strategy.PRESERVE_TRUMP)
                        return grn_suitcards[0][0]

    def draw_trump():
        """Draw trump if caller (strong hand), or flush out bower
        """
        if hand == deal.caller and missing_trump:
            if Strategy.DRAW_TRUMP in hand.strategy:
                if len(trump_cards) > 2:
                    log.debug("Continue drawing trump")
                    return trump_cards[-1]
                elif len(trump_cards) >= 2:
                    log.debug("Last round of drawing trump")
                    hand.strategy.remove(Strategy.DRAW_TRUMP)
                    return trump_cards[-1]
            elif len(trump_cards) >= 3:
                hand.strategy.append(Strategy.DRAW_TRUMP)
                log.debug("Draw trump (or flush out bower)")
                return trump_cards[-1]

    def lead_off_ace():
        """Off-ace (short suit, or green if defending?)
        """
        if off_aces:
            # TODO: choose more wisely if more than one, or possibly preserve ace to
            # avoid being trumped!!!
            if len(off_aces) == 1:
                log.debug("Lead off-ace")
                return off_aces[0]
            else:
                log.debug("Lead off-ace (random choice)")
                return random.choice(off_aces)

    def lead_to_partner_call():
        """No trump seen with parter as caller
        """
        if hand.is_partner(deal.caller):
            if trump_cards and not trump_seen:
                if hand.has_bower:
                    log.debug("Lead bower to partner's call")
                    return trump_cards[-1]
                elif len(trump_cards) > 1:
                    log.debug("Lead low trump to partner's call")
                    return trump_cards[0]
                elif singletons:
                    # REVISIT: not sure we should do this, but if so, add some logic for
                    # choosing if more than one singleton!!!
                    if len(singletons) == 1:
                        log.debug("Lead singleton to void suit")
                        return singletons[0]
                    else:
                        log.debug("Lead singleton to void suit (random choice)")
                        return random.choice(singletons)

    def lead_to_create_void():
        """If trump in hand, try and void a suit
        """
        if trump_cards and singletons:
            # REVISIT: perhaps only makes sense in earlier rounds (2 and 3), and otherwise
            # add some logic for choosing if more than one singleton!!!
            if len(singletons) == 1:
                log.debug("Lead singleton to void suit")
                return singletons[0]
            else:
                log.debug("Lead singleton to void suit (random for now)")
                return random.choice(singletons)

    def lead_suit_winner():
        """Try to lead winner (non-trump)
        """
        if my_high_cards:
            my_high_cards.sort(key=lambda c: c.efflevel[tru_idx])
            log.debug("Try and lead suit winner")
            # REVISIT: is this the right logic (perhaps makes no sense if preceded by
            # off-ace rule)???  Should also examine remaining cards in suit!!!
            return my_high_cards[-1] if trick_no <= 3 else my_high_cards[0]

    def lead_low_non_trump():
        """If still trump in hand, lead lowest card (non-trump)
        """
        if trump_cards and len(trump_cards) < len(hand.cards):
            # NOTE: will always pick the "lowest" suit if multiple cards at min level
            non_trump_cards = [c for c in hand.cards if c.suit['idx'] != tru_idx]
            non_trump_cards.sort(key=lambda c: c.efflevel[tru_idx])
            log.debug("Lead lowest non-trump")
            return non_trump_cards[0]

    def lead_low_from_long_suit():
        """Lead low from long suit (favor green if defeending?)

        Note: always returns value, can be last in ruleset
        """
        suitcards = hand.suitcards.copy()
        suitcards.sort(key=lambda s: len(s))
        # TODO: a little more logic in choosing suit!!!
        log.debug("Lead low from longest suit")
        return suitcards[-1][0]

    def lead_random_card():
        """This is a catchall, though we should look at cases where this happens and
        see if there is a better rule to insert before

        Note: always returns value, can be last in ruleset
        """
        log.debug("Lead random card")
        return random.choice(hand.cards)

    #-------------------#
    # Follow Card Plays #
    #-------------------#

    def play_last_card():
        """
        """
        if len(hand.cards) == 1:
            log.debug("Play last card")
            return hand.cards[0]

    def follow_suit_low():
        """Follow suit low
        """
        if hand.suitcards[lead_idx]:
            # REVISIT: are there cases where we want to try and take the lead???
            log.debug("Follow suit low")
            return hand.suitcards[lead_idx][0]

    def throw_off_to_create_void():
        """Create void (if early in deal)--NOTE: this only matters if we've decided not
        to trump (e.g. to preserve for later)
        """
        if trump_cards and singletons:
            if len(singletons) == 1:
                log.debug("Throw off singleton to void suit (lowest)")
                return singletons[0]
            else:
                # REVISIT: perhaps only makes sense in earlier rounds (2 and 3), and also
                # reconsider selection if multiple (currently lowest valued)!!!
                singletons.sort(key=lambda c: c.efflevel[tru_idx])
                log.debug("Throw off singleton to void suit (lowest)")
                return singletons[0]

    def throw_off_low():
        """Throw off lowest non-trump card
        """
        if len(trump_cards) < len(hand.cards):
            # NOTE: this will always pick the "lowest" suit in case multiple cards at min level
            non_trump_cards = [c for c in hand.cards if c.suit['idx'] != tru_idx]
            non_trump_cards.sort(key=lambda c: c.efflevel[tru_idx])
            log.debug("Throw-off lowest non-trump")
            return non_trump_cards[0]

    def play_low_trump():
        """Play lowest trump (assumes no non-trump remaining)
        """
        if trump_cards and len(trump_cards) == len(hand.cards):
            # REVISIT: are there cases where we want to play a higher trump???
            log.debug("Play lowest trump")
            return trump_cards[0]

    def follow_suit_high():
        """Follow suit (high if can lead trick, low otherwise)
        """
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

    def trump_low():
        """Trump (low) to lead trick
        """
        if trump_cards:
            if lead_trumped:
                if trump_cards[-1].level > winning_card.level:
                    # REVISIT: are there cases where we don't want to try and take the trick,
                    # or not play???
                    if play_pos == 3:
                        for card in trump_cards:
                            if card.level > winning_card.level:
                                log.debug("Overtrump, take winner")
                                return card
                    else:
                        log.debug("Overtrump high")
                        return trump_cards[-1]
            else:
                # hold onto highest remaining trump (sure winner later), otherwise try and
                # take the trick
                # REVISIT: are there cases where we want to play a higher trump, or other
                # reasons to throw off (esp. if pos == 1 and partner yet to play)???
                if len(trump_cards) > 1 or trump_cards[0] not in deal.stats.high_cards:
                    log.debug("Play lowest trump, to lead trick")
                    return trump_cards[0]

    def play_random_card():
        """Play random card, but follow suit if possible

        Note: always returns value, can be last in ruleset
        """
        if plays:
            lead_card = plays[0][1]
            suit_idx = lead_card.suit['idx']
            if hand.suitcards[suit_idx]:
                log.debug("Follow suit, random card")
                return random.choice(hand.suitcards[suit_idx])

        log.debug("Play random card")
        return random.choice(hand.cards)

    ###################
    # play strategies #
    ###################

    # Note, these are static for now, but later could be created dynamically based
    # on game or deal scenario
    init_lead    = [next_call_lead,
                    draw_trump,
                    lead_off_ace,
                    lead_to_partner_call,
                    lead_to_create_void,
                    lead_low_from_long_suit]

    subseq_lead  = [lead_last_card,
                    draw_trump,
                    # maybe swap the next two...
                    lead_to_partner_call,
                    lead_off_ace,
                    lead_suit_winner,
                    lead_to_create_void,
                    lead_low_non_trump,
                    lead_low_from_long_suit]

    part_winning = [play_last_card,
                    follow_suit_low,
                    throw_off_to_create_void,
                    throw_off_low,
                    play_low_trump,
                    play_random_card]

    opp_winning  = [play_last_card,
                    follow_suit_high,
                    trump_low,
                    throw_off_to_create_void,
                    throw_off_low,
                    play_random_card]

    def apply(strategy):
        """
        """
        res = None
        for rule in strategy:
            res = rule()
            if res:
                break
        if not res:
            raise LogicError("Strategy did not produce valid result")
        return res

    ##########################
    # pick strategy and play #
    ##########################

    if not plays:
        play_strategy = init_lead if trick_no == 1 else subseq_lead
    else:
        cur_winning = hand.is_partner(winning[0])
        play_strategy = part_winning if cur_winning else opp_winning

    return hand.play_card(apply(play_strategy))
