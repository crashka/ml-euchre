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

    if bid_rnd == 1:
        hand.analyze()
        turnsuit = deal.turncard.suit
        hand.analysis(turnsuit)
        # TEMP: random for now (pass 87.5% of the time)!!!
        return random.choice([turnsuit] + [None] * 7)
    elif bid_rnd == 2:
        # TEMP: random for now (pass 66.7% of the time)!!!
        return random.choice(SUITS + [None] * 8)
