#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random

from core import log, SUITS

def bid(hand):
    """
    :return: suit or None (meaning "pass")
    """
    deal = hand.deal
    bid_rnd = len(deal.bids) // 4 + 1
    hand.analyze(deal.turncard)
    turnsuit = deal.turncard.suit

    if bid_rnd == 1:
        # this is a no-op, since we ignore the return value (just want to dump the
        # analysis info to debug log)
        hand.getanalysis(turnsuit)
        return turnsuit if hand.biddable(turnsuit, 1) else None
    elif bid_rnd == 2:
        bestsuit = hand.bestsuit(turnsuit)
        return bestsuit if hand.biddable(bestsuit, 2) else None
