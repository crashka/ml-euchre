#!/usr/bin/env python
# -*- coding: utf-8 -*-

def bid(hand):
    """
    :return: suit or None (meaning "pass")
    """
    deal = hand.deal
    bid_rnd = len(deal.bids) // 4 + 1
    turnsuit = deal.turncard.suit

    if bid_rnd == 1:
        return turnsuit if hand.biddable(turnsuit, 1) else None
    elif bid_rnd == 2:
        bestsuit = hand.bestsuit(turnsuit)
        return bestsuit if hand.biddable(bestsuit, 2) else None
