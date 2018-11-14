#!/usr/bin/env python
# -*- coding: utf-8 -*-

from core import log, TEAMS, SUITS, ace, jack, right, left, LogicError
from utils import prettyprint as pp

########
# Card #
########

class CAnalysis(object):
    """
    """
    def __init__(self, card):
        self.parent = card
        self.score1 = None
        self.score2 = None

class Card(object):
    """Represents an instance of a card that is part of a deal; the "basecard"
    is the underlying immutable card identity (e.g. rank, suit, and name) that is
    independent of deal status, trump, etc.
    """
    def __init__(self, basecard):
        self.base = basecard
        self.analysis = None

    def __getattr__(self, key):
        try:
            return self.base[key]
        except KeyError:
            raise AttributeError()

    def __repr__(self):
        return str(self.base)

    def __str__(self):
        return self.base['tag']

    def analyze(self, reanalyze = False):
        if self.analysis and not reanalyze:
            return self.analysis

        card_anl    = CAnalysis(self)
        suit_idx    = self.suit['idx']
        next_idx    = suit_idx ^ 0x3
        card_anl.score1 = [self.level] * 4
        card_anl.score2 = [self.level * self.level] * 4
        if self.rank == jack:
            card_anl.score1[suit_idx] = right['idx'] + 1
            card_anl.score2[suit_idx] = card_anl.score1[suit_idx] * card_anl.score1[suit_idx]
            card_anl.score1[next_idx] = left['idx'] + 1
            card_anl.score2[next_idx] = card_anl.score1[next_idx] * card_anl.score1[next_idx]
        log.debug("Analyzing card %s" % (self.tag))
        log.debug("  score1: %s" % (card_anl.score1))
        log.debug("  score2: %s" % (card_anl.score2))
        self.analysis = card_anl
        return self.analysis

########
# Hand #
########

class HAnalysis(object):
    """
    """
    def __init__(self, hand):
        self.parent        = hand
        # note: "purple" below is the weaker off-color suit
        self.count         = [0] * 4     # count by suit, independent of trump
        # the following are all lists with 4 elements, representing the
        # value given each of the possible trump suits
        self.suitcount     = [list((0, 0, 0, 0))]
        self.suitcount.append(list((0, 0, 0, 0)))
        self.suitcount.append(list((0, 0, 0, 0)))
        self.suitcount.append(list((0, 0, 0, 0)))
        self.suitcards     = [list(([], [], [], []))]
        self.suitcards.append(list(([], [], [], [])))
        self.suitcards.append(list(([], [], [], [])))
        self.suitcards.append(list(([], [], [], [])))
        self.discard       = [None] * 4  # best discard, depending on trump
        self.trump_score1  = [0] * 4
        self.trump_score2  = [0] * 4
        self.next_score1   = [0] * 4
        self.next_score2   = [0] * 4
        self.green_score1  = [0] * 4
        self.green_score2  = [0] * 4
        self.purple_score1 = [0] * 4
        self.purple_score2 = [0] * 4
        self.trumps        = [0] * 4
        self.aces          = [0] * 4     # only count off-aces
        self.voids         = [None] * 4  # only count non-trump suits
        self.singletons    = [None] * 4  # only count non-trump suits

    def logdebug(self):
        log.debug("Analyzing hand for %s"   % (self.parent.seat['name']))
        log.debug("  cards by suit: %s"     % (self.count))
        log.debug("  trump score:   %s, %s" % (self.trump_score1, self.trump_score2))
        log.debug("  next score:    %s, %s" % (self.next_score1, self.next_score2))
        log.debug("  green score:   %s, %s" % (self.green_score1, self.green_score2))
        log.debug("  purple score:  %s, %s" % (self.purple_score1, self.purple_score2))
        log.debug("  trumps:        %s"     % (self.trumps))
        log.debug("  aces:          %s"     % (self.aces))
        log.debug("  voids:         %s"     % (self.voids))
        log.debug("  singletons:    %s"     % (self.singletons))

class Hand(object):
    """
    """
    def __init__(self, deal, seat, pos, cards):
        self.deal          = deal
        self.seat          = seat
        self.pos           = pos
        self.cards         = cards.copy()  # do not disturb input list
        self.next_pos      = (pos + 1) % 4
        self.partner_pos   = (pos + 2) % 4
        self.prev_pos      = (pos + 3) % 4
        self.cards.sort(key=lambda c: c.sortkey)
        # LATER: may have multiple analyses!!!
        self.analysis      = None

    @property
    def team_idx(self):
        return self.seat['idx'] & 0x01

    def __getattr__(self, key):
        try:
            return self.analysis[key]
        except KeyError:
            raise AttributeError()

    def next(self):
        return self.deal.hands[self.next_pos]

    def analyze(self, reanalyze = False):
        """
        TODO: special logic for dealer (pos = 3)!!!
          Discard logic:
            - Hold onto trump
            - Create void if possible
                - Choose next or green, depending on opponent tendencies (later)
            - Hold onto (or create) doubletons (favor over singletons)
            - Discard next if loner call from third seat
            - Discard lowest ranked card (last resort)
        """
        if self.analysis and not reanalyze:
            return self.analysis

        hand_anl = HAnalysis(self)
        for card in self.cards:
            suit_idx = card.suit['idx']
            is_bower = card.rank == jack
            is_ace   = card.rank == ace
            hand_anl.count[suit_idx] += 1
            card_anl = card.analyze()

            for trump in SUITS:
                tru_idx = trump['idx']
                nxt_idx = tru_idx ^ 0x03
                grn_idx = tru_idx ^ 0x01
                pur_idx = tru_idx ^ 0x02
                if suit_idx == tru_idx or is_bower and suit_idx == nxt_idx:
                    hand_anl.trump_score1[tru_idx]  += card_anl.score1[tru_idx]
                    hand_anl.trump_score2[tru_idx]  += card_anl.score2[tru_idx]
                    hand_anl.trumps[tru_idx] += 1
                    hand_anl.suitcount[tru_idx][tru_idx] += 1
                    hand_anl.suitcards[tru_idx][tru_idx].append(card)
                elif suit_idx == nxt_idx:
                    hand_anl.next_score1[tru_idx]   += card_anl.score1[tru_idx]
                    hand_anl.next_score2[tru_idx]   += card_anl.score2[tru_idx]
                    hand_anl.suitcount[tru_idx][suit_idx] += 1
                    hand_anl.suitcards[tru_idx][suit_idx].append(card)
                elif suit_idx == grn_idx:
                    hand_anl.green_score1[tru_idx]  += card_anl.score1[tru_idx]
                    hand_anl.green_score2[tru_idx]  += card_anl.score2[tru_idx]
                    hand_anl.suitcount[tru_idx][suit_idx] += 1
                    hand_anl.suitcards[tru_idx][suit_idx].append(card)
                elif suit_idx == pur_idx:
                    hand_anl.purple_score1[tru_idx] += card_anl.score1[tru_idx]
                    hand_anl.purple_score2[tru_idx] += card_anl.score2[tru_idx]
                    hand_anl.suitcount[tru_idx][suit_idx] += 1
                    hand_anl.suitcards[tru_idx][suit_idx].append(card)

                # only count off-suit aces
                if suit_idx != tru_idx and is_ace:
                    hand_anl.aces[tru_idx] += 1

        # final pass (aggregation)
        for trump in SUITS:
            tru_idx = trump['idx']
            count = hand_anl.suitcount[tru_idx].copy()
            del count[tru_idx]  # only count off-suits
            hand_anl.voids[tru_idx]      = len([c for c in count if c == 0])
            hand_anl.singletons[tru_idx] = len([c for c in count if c == 1])

            # REVISIT: swap green and purple based on score1 (or score2???)!!!
            if hand_anl.purple_score1[tru_idx] > hand_anl.green_score1[tru_idx]:
                hand_anl.green_score1[tru_idx], hand_anl.purple_score1[tru_idx] = \
                    hand_anl.purple_score1[tru_idx], hand_anl.green_score1[tru_idx]
                hand_anl.green_score2[tru_idx], hand_anl.purple_score2[tru_idx] = \
                    hand_anl.purple_score2[tru_idx], hand_anl.green_score2[tru_idx]

        # overall score for hand based on the following (dependent on trump):
        #   - trump score
        #   - trumps
        #   - voids
        #   - aces

        hand_anl.logdebug()
        self.analysis = hand_anl

    def trumpanalysis(self, trump):
        """
        :param trump: either suit or idx
        :return: dict with analysis info
        """
        if isinstance(trump, dict):
            idx = trump['idx']
        else:
            idx = trump
            trump = SUITS[idx]
        hand_anl = self.analysis
        info = {'suitcount':  hand_anl.suitcount[idx],
                'suitcards':  hand_anl.suitcards[idx],
                'tru_score1': hand_anl.trump_score1[idx],
                'tru_score2': hand_anl.trump_score2[idx],
                'nxt_score1': hand_anl.next_score1[idx],
                'nxt_score2': hand_anl.next_score2[idx],
                'grn_score1': hand_anl.green_score1[idx],
                'grn_score2': hand_anl.green_score2[idx],
                'pur_score1': hand_anl.purple_score1[idx],
                'pur_score2': hand_anl.purple_score2[idx],
                'trumps'    : hand_anl.trumps[idx],
                'aces'      : hand_anl.aces[idx],
                'voids'     : hand_anl.voids[idx],
                'singletons': hand_anl.singletons[idx]}
        info_debug = info.copy()
        info_debug.update({'suitcards': [[c.tag for c in s] for s in hand_anl.suitcards[idx]]})
        log.debug("%s trump analysis for %s:\n%s" %
                  (trump['name'].capitalize(), [c.tag for c in self.cards],
                   pp(info_debug, sort_keys=False, noprint=True)))
        return info

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
