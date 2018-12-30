#!/usr/bin/env python
# -*- coding: utf-8 -*-

from core import log, SUITS, ace, king, ten, nine, right, left
from hand import OFF_ACE_VALUE

BID_THRESHOLD = right['level'] + left['level'] + ten['level'] + OFF_ACE_VALUE
DEALER_VALUE  = nine['level']

def discard(hand, turncard):
    """
    """
    trump = turncard.suit
    tru_idx = trump['idx']
    nxt_idx = tru_idx ^ 0x03
    hand_anl = hand.analysis[tru_idx]
    suitcount = hand_anl.suitcount
    suitcards = hand_anl.suitcards

    # Handle all trump case (get it out of the way)
    if suitcount[tru_idx] == len(hand.cards):
        discard = min(suitcards[tru_idx][0], turncard, key=lambda c: c.level)
        log.debug("Discard %s if %s trump, lowest trump" % (discard.tag, trump['tag']))
        return discard

    # Create void if possible
    if suitcount.count(1) > 0:
        mincard = None
        minlevel = 10
        for idx in range(len(suitcount)):
            if idx == tru_idx or suitcount[idx] != 1:
                continue
            # for now, we just pick the first card found at the lowest level
            # LATER: favor voiding next or green, depending on opponent tendencies
            # (always void next if loner called from pos = 2)!!!
            if suitcards[idx][0].level < minlevel and suitcards[idx][0].rank != ace:
                mincard = suitcards[idx][0]
                minlevel = mincard.level
        if mincard:
            log.debug("Discard %s if %s trump, voiding suit" % (mincard.tag, trump['tag']))
            return mincard

    # Create doubletons, if possible (favor over creating singletons)
    if suitcount.count(3) > 0:
        idx = suitcount.index(3)
        # REVISIT: perhaps only do if high card in suit is actually viable (like
        # queen or higher)!!!
        if idx != tru_idx:
            # note that first element is the loweest (cards sorted ascending)
            discard = suitcards[idx][0]
            log.debug("Discard %s if %s trump, creating doubleton" % (discard.tag, trump['tag']))
            return discard

    # Discard next if loner call from third seat (REVISIT: not sure it makes sense
    # to extend this to the general, non-voiding, non-third-seat-loner case!!!)
    if suitcount[nxt_idx] == 2:
        # don't unguard doubleton king or break up A-K
        if king not in (c.rank for c in suitcards[nxt_idx]):
            discard = suitcards[nxt_idx][0]
            log.debug("Discard %s if %s trump, reducing next" % (discard.tag, trump['tag']))
            return discard

    # Discard lowest card, any suit (last resort)
    mincard = None
    minlevel = ace['level']
    savecards = []  # attempt to preserve, only discard if no alternatives
    for idx in range(len(suitcards)):
        if idx == tru_idx:
            continue
        # avoid unguarding doubleton king, while making sure that A-K doubleton
        # takes precedence (if also present)
        if suitcount[idx] == 2 and king in (c.rank for c in suitcards[idx]):
            savecards.append(suitcards[idx][0])
            continue
        # otherwise we just pick the first card found at the lowest level; chances
        # are that there is no other meaninful logic to apply here (e.g. choosing
        # between green suit doubletons)
        if suitcards[idx]:
            if suitcards[idx][0].level < minlevel:
                mincard = suitcards[idx][0]
                minlevel = mincard.level
            elif suitcards[idx][0].level == minlevel:
                # may need to stow an ace, if only outstanding card
                savecards.append(suitcards[idx][0])
    assert mincard or savecards
    if not mincard:
        mincard = min(savecards, key=lambda c: c.level)
        log.debug("Have to unguard doubleton king or discard from A/A-K, oh well...")
    log.debug("Discard %s if %s trump, lowest card" % (mincard.tag, trump['tag']))
    return mincard

def bid(hand):
    """
    :return: suit or None (meaning "pass")
    """
    deal = hand.deal
    bid_pos = len(deal.bids)  # 0-7
    turnsuit = deal.turncard.suit

    if bid_pos < 4:
        return turnsuit if biddable(hand, turnsuit, bid_pos) else None
    else:
        suit = bestsuit(hand, turnsuit)
        return suit if biddable(hand, suit, bid_pos) else None

def bestsuit(hand, exclude = None):
    """
    :param hand: Hand
    :param exclude: dict (SUITS[i])
    :return: suit (dict)
    """
    suits = SUITS.copy()
    if exclude:
        del suits[exclude['idx']]
    # TODO: add tie-breaker in the case of equal scores!!!
    return max(suits, key=lambda s: hand.analysis[s['idx']].hand_score)

def biddable(hand, trump, bid_pos):
    """
    TEMP TEMP TEMP: this is just a stand-in for dev purposes!!!!!!!
    :param hand: Hand
    :param trump: dict (SUITS[i])
    :param bid_pos: int
    :return: bool
    """
    idx = trump['idx']
    thresh = BID_THRESHOLD
    if bid_pos == 3:
        # NOTE: this is currently not built into hand_score
        thresh -= DEALER_VALUE
    elif bid_pos > 3:
        thresh -= hand.pos  # or whatever...
    log.debug("  Hand score: %d (with %s as trump), threshold: %d" %
              (hand.analysis[idx].hand_score, trump['tag'], thresh))
    return hand.analysis[idx].hand_score > thresh
