#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os.path
import logging
import logging.handlers
import random

from core import param, log, dbg_hand, RANKS, SUITS, CARDS, SEATS, TEAMS
from hand import Card, Hand
import bidding
import playing

#########
# Match #
#########

MATCH_GAMES_DFLT = 2

class Match(object):
    """Represents a set of games (race to 2, by default) played by two teams
    """
    def __init__(self, match_games = MATCH_GAMES_DFLT):
        """
        """
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
        :return: new Game instance
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
        """
        """
        self.match     = match
        self.deals     = []
        self.curdealer = None
        self.curdeal   = None

    def newdeal(self):
        """
        :return: new Deal instance
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

class Deal(object):
    """Represents a single shuffle, deal, bidding, and playing of the cards

    Note: our notion of a "deal" is also popularly called a "hand", but we are reserving that
    word to mean the holding of five dealt cards by a player during a deal
    """
    def __init__(self, game):
        """
        """
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

    @property
    def deal_num(self):
        """Only valid for current deal within game
        """
        assert self.game.curdeal == self
        return len(self.game.deals)

    def play(self):
        """
        :return: void
        """
        # shuffle and deal
        log.debug("Deal #%d: dealer is %s" % (self.deal_num, self.dealer['name']))
        self.shuffle()
        self.deal()

        # bidding and playing tricks
        bid = self.bid()
        if bid:
            score = self.playtricks()

        self.tabulate()

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
        if param.get('debug'):
            self.dump()

        self.bids = []

    def bid(self):
        """
        :return: suit (trunp) or None (meaning passed deal)
        """
        log.debug("Bidding for deal #%d begins" % (self.deal_num))
        bidder = self.hands[0]
        while len(self.bids) < 8:
            bid = bidding.bid(bidder)
            self.bids.append(bid)
            # REVISIT: None means pass for now, but LATER we may want to always pass back
            # a structure containing insight into bid decision, so we would have to check
            # for a pass within it explicitly!!!
            if bid:
                log.debug("  %s calls %s" % (bidder.seat['name'], bid['name']))
                break
            log.debug("  %s passes" % (bidder.seat['name']))
            bidder = bidder.next()

        if bid:
            self.caller   = bidder
            self.contract = bid
            self.plays    = []  # [(player_hand, card), ...]
            self.tricks   = []  # [(winner_hand, [cards]), ...]
            log.debug("%s is trump, called by %s" %
                      (bid['name'].capitalize(), TEAMS[bidder.team_idx]['tag']))
        else:
            log.debug("Deal is passed")

        return bid  # see REVISIT above on interpretation of bid

    def cmpcards(self, lead, winning, played):
        """
        :param lead: Card led for trick
        :param winning: Card currently winning
        :param played: Card last played
        :return: int (negative if played loses, positive if played wins)
        """
        ret = None
        winning_trump = winning.suit == self.contract
        played_trump  = played.suit == self.contract
        followed_suit = played.suit == lead.suit
        if winning_trump:
            ret = played.level - winning.level if played_trump else -played.level
        elif played_trump:
            ret = played.level
        else:
            ret = played.level - winning.level if followed_suit else -played.level
        return ret

    def playtricks(self):
        """
        :return: score [E/W tricks, N/S tricks]
        """
        tricks = [0, 0]
        player  = self.hands[0]
        while len(self.tricks) < 5:
            plays   = []            # [(player_hand, card), ...]
            cards   = []            # [cards]
            winning = (None, None)  # (player_hand, card)
            while len(plays) < 4:
                note = ''
                winning_hand = winning[0]
                winning_card = winning[1]
                card = playing.play(player)
                cards.append(card)
                plays.append((player, card))
                if not winning_card:
                    winning = (player, card)
                    note = ' (currently winning)'
                else:
                    if self.cmpcards(cards[0], winning_card, card) > 0:
                        winning = (player, card)
                        note = ' (currently winning)'
                log.debug("  %s plays %s%s" % (player.seat['name'], card.tag, note))
                player = player.next()

            winning_hand = winning[0]
            winning_card = winning[1]
            self.plays += plays
            self.tricks.append((winning_hand, cards))
            log.debug("%s takes trick #%d with %s" %
                      (winning_hand.seat['name'].capitalize(), len(self.tricks), winning_card.tag))
            tricks[winning_hand.team_idx] += 1
            player = winning_hand

        log.debug("%s tricks: %d, %s tricks: %d" %
                  (TEAMS[0]['tag'], tricks[0], TEAMS[1]['tag'], tricks[1]))
        log.debug("%s wins deal" %
                  (TEAMS[0]['tag'] if tricks[0] > tricks[1] else TEAMS[1]['tag']))
        return tricks

    def tabulate(self):
        """
        :return: void
        """
        pass

    def dump(self, what = None):
        """
        :return: void
        """
        print("Deal #%d" % (self.deal_num))

        if self.dealer:
            print("  Dealer: %s" % (self.dealer['name']))

        if self.hands:
            print("  Hands:")
            for hand in self.hands:
                print("    %-5s (%d): %s" %
                      (hand.seat['name'], hand.pos, [c.tag for c in hand.cards]))
            print("  Turncard: %s" % (self.turncard.tag))
            print("  Buried: %s" % ([c.tag for c in self.bury]))

###########
# Testing #
###########

if __name__ == '__main__':
    if param.get('debug'):
        log.setLevel(logging.DEBUG)
        log.addHandler(dbg_hand)

    seed   = None
    ndeals = 1
    # Usage: euchre.py [<seed> [<ndeals>}]
    prog   = sys.argv.pop(0)
    try:
        seed   = int(sys.argv.pop(0))
        ndeals = int(sys.argv.pop(0))
    except IndexError:
        pass

    if seed:
        random.seed(seed)

    g = MATCH.newgame()
    for i in range(0, ndeals):
        d = g.newdeal()
        d.play()
