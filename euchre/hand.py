#!/usr/bin/env python
# -*- coding: utf-8 -*-

from core import log, TEAMS, SUITS, ace, jack, right, left, LogicError
from utils import prettyprint as pp

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
        # analysis attributes
        self.score1 = None
        self.score2 = None

    def __getattr__(self, key):
        try:
            return self.base[key]
        except KeyError:
            raise AttributeError()

    def analyze(self, reanalyze = False):
        if self.score1 and not reanalyze:
            return

        log.debug("Analyzing card %s" % (self.tag))
        suit_idx    = self.suit['idx']
        next_idx    = suit_idx ^ 0x3
        self.score1 = [self.level] * 4
        self.score2 = [self.level * self.level] * 4
        if self.rank == jack:
            self.score1[suit_idx] = right['idx'] + 1
            self.score2[suit_idx] = self.score1[suit_idx] * self.score1[suit_idx]
            self.score1[next_idx] = left['idx'] + 1
            self.score2[next_idx] = self.score1[next_idx] * self.score1[next_idx]
        log.debug("  score1: %s" % (self.score1))
        log.debug("  score2: %s" % (self.score2))

########
# Hand #
########

class Hand(object):
    """
    """
    def __init__(self, deal, seat, pos, cards):
        self.deal          = deal
        self.seat          = seat
        self.pos           = pos
        self.cards         = cards.copy()  # do not disturb input list order
        self.next_pos      = (pos + 1) % 4
        self.partner_pos   = (pos + 2) % 4
        self.prev_pos      = (pos + 3) % 4
        self.cards.sort(key=lambda c: c.sortkey)
        # analysis fields (purple is the weaker off-color suit)
        self.count         = None  # count by suit, independent of trump
        # the following are all lists with 4 elements, representing the
        # value given each of the possible trump suits
        self.discard       = None  # best discard, depending on trump
        self.trump_score1  = None
        self.trump_score2  = None
        self.next_score1   = None
        self.next_score2   = None
        self.green_score1  = None
        self.green_score2  = None
        self.purple_score1 = None
        self.purple_score2 = None
        self.trumps        = None
        self.aces          = None  # only count off-aces
        self.voids         = None  # only count non-trump suits
        self.singletons    = None  # only count non-trump suits

    @property
    def team_idx(self):
        return self.seat['idx'] & 0x01

    def next(self):
        return self.deal.hands[self.next_pos]

    def analyze(self, reanalyze = False):
        """
        TODO: special logic for dealer (pos = 3)!!!
        """
        if self.count and not reanalyze:
            return

        self.discard       = [None] * 4
        self.count         = [0] * 4
        self.trump_score1  = [0] * 4
        self.trump_score2  = [0] * 4
        self.next_score1   = [0] * 4
        self.next_score2   = [0] * 4
        self.green_score1  = [0] * 4
        self.green_score2  = [0] * 4
        self.purple_score1 = [0] * 4
        self.purple_score2 = [0] * 4
        self.trumps        = [0] * 4
        self.aces          = [0] * 4
        self.voids         = [None] * 4
        self.singletons    = [None] * 4

        for card in self.cards:
            suit_idx = card.suit['idx']
            is_bower = card.rank == jack
            is_ace   = card.rank == ace
            self.count[suit_idx] += 1
            card.analyze()

            for trump in SUITS:
                tru_idx = trump['idx']
                nxt_idx = tru_idx ^ 0x3
                grn_idx = tru_idx ^ 0x1
                pur_idx = tru_idx ^ 0x2
                if suit_idx == tru_idx or is_bower and suit_idx == nxt_idx:
                    self.trump_score1[tru_idx]  += card.score1[tru_idx]
                    self.trump_score2[tru_idx]  += card.score2[tru_idx]
                    self.trumps[tru_idx] += 1
                elif suit_idx == nxt_idx:
                    self.next_score1[tru_idx]   += card.score1[tru_idx]
                    self.next_score2[tru_idx]   += card.score2[tru_idx]
                elif suit_idx == grn_idx:
                    self.green_score1[tru_idx]  += card.score1[tru_idx]
                    self.green_score2[tru_idx]  += card.score2[tru_idx]
                elif suit_idx == pur_idx:
                    self.purple_score1[tru_idx] += card.score1[tru_idx]
                    self.purple_score2[tru_idx] += card.score2[tru_idx]

                # only count off-suit aces
                if suit_idx != tru_idx and is_ace:
                    self.aces[tru_idx] += 1

        # final pass (aggregation)
        for trump in SUITS:
            tru_idx = trump['idx']
            count = self.count.copy()
            del count[tru_idx]  # only count off-suits
            self.voids[tru_idx]      = len([c for c in count if c == 0])
            self.singletons[tru_idx] = len([c for c in count if c == 1])

            # REVISIT: swap green and purple based on score1 (or score2???)!!!
            if self.purple_score1[tru_idx] > self.green_score1[tru_idx]:
                self.green_score1[tru_idx], self.purple_score1[tru_idx] = \
                    self.purple_score1[tru_idx], self.green_score1[tru_idx]
                self.green_score2[tru_idx], self.purple_score2[tru_idx] = \
                    self.purple_score2[tru_idx], self.green_score2[tru_idx]

        log.debug("Analyzing hand for %s" % (self.seat['name']))
        log.debug("  cards by suit: %s" % (self.count))
        log.debug("  trump score:   %s, %s" % (self.trump_score1, self.trump_score2))
        log.debug("  next score:    %s, %s" % (self.next_score1, self.next_score2))
        log.debug("  green score:   %s, %s" % (self.green_score1, self.green_score2))
        log.debug("  purple score:  %s, %s" % (self.purple_score1, self.purple_score2))
        log.debug("  trumps:        %s" % (self.trumps))
        log.debug("  aces:          %s" % (self.aces))
        log.debug("  voids:         %s" % (self.voids))
        log.debug("  singletons:    %s" % (self.singletons))

    def analysis(self, trump):
        """
        :param trump: either suit or idx
        :return: dict with analysis info
        """
        if isinstance(trump, dict):
            idx = trump['idx']
        else:
            idx = trump
            trump = SUITS[idx]
        info = {'tru_score1': self.trump_score1[idx],
                'tru_score2': self.trump_score2[idx],
                'nxt_score1': self.next_score1[idx],
                'nxt_score2': self.next_score2[idx],
                'grn_score1': self.green_score1[idx],
                'grn_score2': self.green_score2[idx],
                'pur_score1': self.purple_score1[idx],
                'pur_score2': self.purple_score2[idx],
                'trumps'    : self.trumps[idx],
                'aces'      : self.aces[idx],
                'voids'     : self.voids[idx],
                'singletons': self.singletons[idx]}
        log.debug("%s trump analysis for %s:\n%s" %
                  (trump['name'].capitalize(), [c.tag for c in self.cards],
                   pp(info, sort_keys=False, noprint=True)))

###########
# Testing #
###########

def test(*args):
    pass

if __name__ == '__main__':
    if param.get('debug'):
        log.setLevel(logging.DEBUG)
        log.addHandler(dbg_hand)

    # Usage: euchre.py [<seed> [<ndeals>}]
    prog = sys.argv.pop(0)
    test(*sys.argv)
