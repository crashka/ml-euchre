#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os.path
import logging
import logging.handlers
import random

from core import cfg, env, log, dbg_hand

#########
# Setup #
#########

# TEMP/DEV: hardwire the seed for initial dev/testing
random.seed(3)

def validatebasedata(basedata):
    for elem in basedata:
        assert elem['idx'] == basedata.index(elem)

##############
# Cards/Deck #
##############

"""
Suits
    C - 0
    D - 1
    H - 2
    S - 3

Companion suit
    suit ^ 0x3

Cards (id and rank)
    9  - 0-3   (0)
    10 - 4-7   (1)
    J  - 8-11  (2)
    Q  - 12-15 (3)
    K  - 16-19 (4)
    A  - 20-23 (5)

    L  - 24-27 (6)
    R  - 28-31 (7)

Suit
    card % 4

Rank
    card // 4
"""

nine     = {'idx' : 0, 'name': 'nine',  'tag': '9'}
ten      = {'idx' : 1, 'name': 'ten',   'tag': '10'}
jack     = {'idx' : 2, 'name': 'jack',  'tag': 'J'}
queen    = {'idx' : 3, 'name': 'queen', 'tag': 'Q'}
king     = {'idx' : 4, 'name': 'king',  'tag': 'K'}
ace      = {'idx' : 5, 'name': 'ace',   'tag': 'A'}

RANKS    = [nine, ten, jack, queen, king, ace]

clubs    = {'idx' : 0, 'name': 'clubs',    'tag': '\u2663'}
diamonds = {'idx' : 1, 'name': 'diamonds', 'tag': '\u2666'}
hearts   = {'idx' : 2, 'name': 'hearts',   'tag': '\u2665'}
spades   = {'idx' : 3, 'name': 'spades',   'tag': '\u2660'}

SUITS    = [clubs, diamonds, hearts, spades]

CARDS = []
for idx in range(0, 24):
    rank = RANKS[idx // 4]
    suit = SUITS[idx % 4]
    card = {'idx' : idx,
            'rank': rank,
            'suit': suit,
            'name': "%s of %s" % (rank['name'].capitalize(),
                                  suit['name'].capitalize()),
            'tag' : "%s%s" % (rank['tag'], suit['tag'])
    }
    CARDS.append(card)

validatebasedata(RANKS)
validatebasedata(SUITS)
validatebasedata(CARDS)

###############
# Seats/Table #
###############

west     = {'idx' : 0, 'name': 'west',  'tag': 'W'}
north    = {'idx' : 1, 'name': 'north', 'tag': 'N'}
east     = {'idx' : 2, 'name': 'east',  'tag': 'E'}
south    = {'idx' : 3, 'name': 'south', 'tag': 'S'}

SEATS    = [west, north, east, south]

validatebasedata(SEATS)

###############
# Games/Match #
###############

MATCH_GAMES_DFLT = 2

# TEMP: until flipforjacks() is implemented!!!
INIT_DEALER_DFLT = south

class Match(object):
    """Represents a set of games (race to 2, by default) played by two teams
    """
    def __init__(self, match_games = MATCH_GAMES_DFLT):
        self.match_games = match_games
        self.games       = []
        self.deals       = []
        self.dealer      = None

    def nextdealer(self):
        """
        :return: void (sets self.dealer)
        """
        if self.dealer:
            dealer_seat = SEATS.index(self.dealer)
            self.dealer = SEATS[(dealer_seat + 1) % 4]
        else:
            self.flipforjacks()
            assert self.dealer in SEATS

    def flipforjacks(self):
        """
        :return: void (sets self.dealer)
        """
        self.dealer = INIT_DEALER_DFLT

# TEMP: make this global for now (LATER, can be subordinate to higher-level entities, such as
# tables, tournaments, etc.)!!!
MATCH = Match()

##############
# Deal/Hands #
##############

class Deal(object):
    """Represents a single shuffle, deal, bidding, and playing of the cards

    Note: our notion of a "deal" is also popularly called a "hand", but we are reserving that
    word to mean the holding of five dealt cards by a player during a deal
    """
    def __init__(self, match = MATCH):
        self.match    = match
        self.dealer   = match.dealer
        self.pos      = None  # [first to bid, dealer partner, third position, dealer]
        self.deck     = None  # [card, ...] (shuffled)
        self.hands    = None  # [[card, ...], [card, ...], ...]
        self.bury     = None  # [card, ...] (len 3 during first round bids, otherwise len 4)
        self.turncard = None  # card
        self.trump    = None  # suit
        self.caller   = None  # seat
        self.call_pos = None  # pos

        match.deals.append(self)

    def shuffle(self, force = False):
        """
        :return: void
        """
        if self.deck and not force:
            raise RuntimeError("Cannot shuffle if deck is already shuffled")
        self.deck = random.sample(CARDS, k=len(CARDS))

    def deal(self, force = False):
        """
        :return: void (sets obj instance state)
        """
        if self.hands and not force:
            raise RuntimeError("Cannot deal when hands have been dealt")
        if not self.deck:
            raise RuntimeError("Deck must be shuffled in order to deal")
        if not self.dealer:
            raise RuntimeError("Dealer must be set in order to deal")

        cardno  = 0
        self.hands = []
        for seat in SEATS:
            pos   = (seat['idx'] - self.dealer['idx'] - 1) % 4
            cards = self.deck[cardno:cardno+5]
            hand  = Hand(self, seat, pos, cards)
            self.hands.append(hand)
            cardno += 5

        self.hands.sort(key=lambda h: h.pos)
        self.bury = self.deck[cardno:]
        self.turncard = self.bury.pop()

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

###########
# Testing #
###########

debug = 1
if debug > 0:
    log.setLevel(logging.DEBUG)
    log.addHandler(dbg_hand)

def printdeal(deal):
    print("\nDeal #%d" % (len(deal.match.deals)))
    print("  Dealer: %s" % (deal.dealer['name']))

    print("\n  Hands:")
    for hand in deal.hands:
        print("    %-5s (%d): %s" % (hand.seat['name'], hand.pos, [c['tag'] for c in hand.cards]))

    print("\n  Turncard: %s" % (deal.turncard['tag']))
    print("  Buried: %s" % ([c['tag'] for c in deal.bury]))

if __name__ == '__main__':
    m = Match()

    for i in range(0, 4):
        m.nextdealer()
        d = Deal(m)
        d.shuffle()
        d.deal()

        printdeal(d)
