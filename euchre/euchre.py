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
    """Make sure that the embedded index for base data elements matches the position
    within the data structure

    :return: void (failed assert on validation error)
    """
    for elem in basedata:
        assert elem['idx'] == basedata.index(elem)

##############
# Base Cards #
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
# Table Seats #
###############

west     = {'idx' : 0, 'name': 'west',  'tag': 'W'}
north    = {'idx' : 1, 'name': 'north', 'tag': 'N'}
east     = {'idx' : 2, 'name': 'east',  'tag': 'E'}
south    = {'idx' : 3, 'name': 'south', 'tag': 'S'}

SEATS    = [west, north, east, south]

validatebasedata(SEATS)

#########
# Match #
#########

MATCH_GAMES_DFLT = 2

# TEMP: until flipforjacks() is implemented!!!
INIT_DEALER_DFLT = south

class Match(object):
    """Represents a set of games (race to 2, by default) played by two teams
    """
    def __init__(self, match_games = MATCH_GAMES_DFLT):
        self.match_games = match_games
        self.games       = []
        self.curdealer   = None
        self.curgame     = None

    def nextdealer(self):
        """
        :return: seat (new value for self.curdealer)
        """
        if self.curdealer:
            dealer_seat = SEATS.index(self.curdealer)
            self.curdealer = SEATS[(dealer_seat + 1) % 4]
        else:
            self.curdealer = self.flipforjacks()
            assert self.curdealer in SEATS

        return self.curdealer

    def flipforjacks(self):
        """
        :return: seat
        """
        return random.choice(SEATS)

    def newgame(self):
        """
        """
        self.curgame = Game(self)
        self.games.append(self.curgame)
        return self.curgame

########
# Game #
########

# TEMP: make this global for now (LATER, can be subordinate to higher-level entities, such as
# tables, tournaments, etc.)!!!
MATCH = Match()

class Game(object):
    """
    """
    def __init__(self, match = MATCH):
        self.match     = match
        self.deals     = []
        self.curdealer = None
        self.curdeal   = None

    def newdeal(self):
        """
        """
        self.curdealer = self.match.nextdealer()
        self.curdeal = Deal(self)
        self.deals.append(self.curdeal)
        return self.curdeal

    def update_score(self):
        """Update score based on completed deal (self.curdeal)
        """
        pass

########
# Deal #
########

class Card(object):
    """Represents an instance of a card that is part of a deal; the "basecard"
    is the underlying immutable card identity (e.g. rank, suit, and name) that is
    independent of deal status, trump, etc.
    """
    def __init__(self, basecard):
        self.base     = basecard
        self.is_trump = None

    def __getattr__(self, key):
        try:
            return self.base[key]
        except KeyError:
            raise AttributeError()

class Deal(object):
    """Represents a single shuffle, deal, bidding, and playing of the cards

    Note: our notion of a "deal" is also popularly called a "hand", but we are reserving that
    word to mean the holding of five dealt cards by a player during a deal
    """
    def __init__(self, game):
        self.game     = game
        self.match    = game.match
        self.dealer   = game.match.curdealer
        self.deck     = None  # [cards] -- shuffled
        self.hands    = None  # [hands] -- ordered by position (0 = first bid, 3 = dealer)
        self.bury     = None  # [cards] -- len 3 during first round bids, otherwise len 4
        self.turncard = None  # card
        self.discard  = None  # card

        self.bids     = None  # [(bidder_hand, bid), ...]
        self.contract = None  # suit -- (for now...perhaps will be a structure in the future)
        self.caller   = None  # hand
        self.plays    = None  # [(player_hand, card), ...]
        self.tricks   = None  # [(winner_hand, [cards]), ...]
        self.lead     = None  # hand

    def play(self):
        """
        :return: void
        """
        # shuffle and deal
        self.shuffle()
        self.deal()
        self.dump()

        # bidding and playing tricks
        self.bid()
        self.playtricks()

    def shuffle(self, force = False):
        """
        :return: void
        """
        if self.deck and not force:
            raise RuntimeError("Cannot shuffle if deck is already shuffled")
        self.deck = [Card(c) for c in random.sample(CARDS, k=len(CARDS))]

    def deal(self, force = False):
        """
        :return: void
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

        self.bids = []

    def bid(self):
        """
        :return: void
        """
        return
        bidder = self.hands[0]
        while len(self.bids) < 8:
            bid = bidding.bid(bidder)
            self.bids.append(bid)
            # REVISIT: None means pass for now, but LATER we may want to always pass back
            # a structure containing insight into bid decision, so we would have to check
            # for a pass within it explicitly!!!
            if bid:
                break
            bidder = bidder.next()

        if bid:
            self.caller   = bidder
            self.contract = bid
            self.plays    = []  # [(player_hand, card), ...]
            self.tricks   = []  # [(winner_hand, [cards]), ...]
            self.lead     = self.hands[0]

        return bid  # see REVISIT above on interpretation of bid

    def playtricks(self):
        """
        :return: void
        """
        return
        plays   = []            # [(player, card), ...]
        player  = self.lead
        winning = (None, None)  # (player, card)
        while len(plays) < 4:
            card = playing.play(player)
            plays.append((player, card))
            if not winning[1]:
                winning = (player, card)
            else:
                winning_card = winning[1]
                if self.cmpcard(winning_card, card) > 0:
                    winning = (player, card)
            player = player.next()

    def dump(self, what = None):
        """
        :return: void
        """
        log.debug("Deal #%d" % (len(self.game.deals)))

        if self.dealer:
            log.debug("  Dealer: %s" % (self.dealer['name']))

        if self.hands:
            log.debug("  Hands:")
            for hand in self.hands:
                log.debug("    %-5s (%d): %s" % (hand.seat['name'], hand.pos, [c.tag for c in hand.cards]))

            log.debug("  Turncard: %s" % (self.turncard.tag))
            log.debug("  Buried: %s" % ([c.tag for c in self.bury]))

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

    def next(self):
        return self.deal.hands[self.next_pos]

###########
# Testing #
###########

debug = 1
if debug > 0:
    log.setLevel(logging.DEBUG)
    log.addHandler(dbg_hand)

if __name__ == '__main__':
    g = MATCH.newgame()
    for i in range(0, 4):
        d = g.newdeal()
        d.play()
