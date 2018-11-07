#!/usr/bin/env python
# -*- coding: utf-8 -*-

from core import log, TEAMS

########
# Hand #
########

class Hand(object):
    """
    """
    def __init__(self, deal, seat, pos, cards):
        self.deal        = deal
        self.seat        = seat
        self.pos         = pos
        self.cards       = cards
        self.next_pos    = (pos + 1) % 4
        self.partner_pos = (pos + 2) % 4
        self.prev_pos    = (pos + 3) % 4

    @property
    def team_idx(self):
        return self.seat['idx'] & 0x01

    def next(self):
        return self.deal.hands[self.next_pos]

########
# Card #
########

class Card(object):
    """Represents an instance of a card that is part of a deal; the "basecard"
    is the underlying immutable card identity (e.g. rank, suit, and name) that is
    independent of deal status, trump, etc.
    """
    def __init__(self, basecard):
        self.base = basecard
        self.is_trump = None

    def __getattr__(self, key):
        try:
            return self.base[key]
        except KeyError:
            raise AttributeError()
