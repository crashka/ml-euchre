#!/usr/bin/env python
# -*- coding: utf-8 -*-

from core import log, TEAMS, SUITS, ace, king, queen, jack, right, left, LogicError
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

        card_anl = CAnalysis(self)
        suit_idx = self.suit['idx']
        next_idx = suit_idx ^ 0x3
        card_anl.score1 = [self.level] * 4
        card_anl.score2 = [self.level * self.level] * 4
        if self.rank == jack:
            card_anl.score1[suit_idx] = right['level']
            card_anl.score2[suit_idx] = card_anl.score1[suit_idx] * card_anl.score1[suit_idx]
            card_anl.score1[next_idx] = left['level']
            card_anl.score2[next_idx] = card_anl.score1[next_idx] * card_anl.score1[next_idx]
        log.trace("Analyzing card %s" % (self.tag))
        log.trace("  score1: %s" % (card_anl.score1))
        log.trace("  score2: %s" % (card_anl.score2))
        self.analysis = card_anl
        return self.analysis

########
# Hand #
########

# TEMP: for now, hardwire value for off-suit aces and voids, as equated with
# a trump suit card value!!!
OFF_ACE_VALUE   = queen['level']
VOID_SUIT_VALUE = queen['level']
BID_THRESHOLD   = right['level'] + left['level'] + OFF_ACE_VALUE
DEALER_VALUE    = queen['level']

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
        # note that hand_score should not be used as part of the bidding (or playing)
        # logic; rather, the highest hand_score "seen" thus far in the bidding round
        # is used as a rough proxy for how likely the bid would have actually gotten
        # to a hand position--this should be the only place in the program that we are
        # allowed to use a god view as part of the game strategy (LATER, we can extend
        # this idea to take into account various bidding/playing styles in determining
        # the likeliness of a bidding opportunity)
        self.hand_score    = [0] * 4

    def log_debug(self):
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
        log.debug("  hand score:    %s"     % (self.hand_score))
        if self.discard[0]:
            log.debug("  discard:       %s"     % ([str(c) for c in self.discard]))

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

    def analyze(self, turncard, reanalyze = False):
        """
        """
        if self.analysis and not reanalyze:
            return self.analysis

        self.analysis = HAnalysis(self)
        hand_anl = self.analysis
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

            if self.pos == 3:
                # note that this may return the turncard, e.g. if it would be the
                # lowest trump (or perhaps some wacky other reason)
                hand_anl.discard[tru_idx] = self.bestdiscard(trump, turncard)

            count = hand_anl.suitcount[tru_idx].copy()
            del count[tru_idx]  # only count off-suits
            hand_anl.voids[tru_idx]      = len([c for c in count if c == 0])
            hand_anl.singletons[tru_idx] = len([c for c in count if c == 1])

            # re-sort suitcards to include bower rankings (TODO: make this less ugly!!!)
            hand_anl.suitcards[tru_idx][tru_idx].sort(key=lambda c: c.analysis.score1[tru_idx])

            # REVISIT: currently swap green and purple scores based on score1, but
            # should it be something else (e.g. score2)???
            if hand_anl.purple_score1[tru_idx] > hand_anl.green_score1[tru_idx]:
                hand_anl.green_score1[tru_idx], hand_anl.purple_score1[tru_idx] = \
                    hand_anl.purple_score1[tru_idx], hand_anl.green_score1[tru_idx]
                hand_anl.green_score2[tru_idx], hand_anl.purple_score2[tru_idx] = \
                    hand_anl.purple_score2[tru_idx], hand_anl.green_score2[tru_idx]

            # TODO: hand score should take into account the turn card--penalty/reward
            # for deliverying the trump into opponent or partner hand, or included in
            # the computation for dealer hand (related to selecting discard, above)!!!
            hand_anl.hand_score[tru_idx] = hand_anl.trump_score1[tru_idx] + \
                                           hand_anl.trumps[tru_idx] + \
                                           hand_anl.voids[tru_idx] * VOID_SUIT_VALUE + \
                                           hand_anl.aces[tru_idx] * OFF_ACE_VALUE

        hand_anl.log_debug()

    def bestdiscard(self, trump, turncard):
        """
        """
        hand_anl = self.analysis
        tru_idx = trump['idx']
        nxt_idx = tru_idx ^ 0x03
        suitcount = hand_anl.suitcount[tru_idx]
        suitcards = hand_anl.suitcards[tru_idx]

        # Handle all trump case (get it out of the way)
        if suitcount[tru_idx] == len(self.cards):
            discard = min(suitcards[tru_idx][0], turncard, key=lambda c: c.level)
            log.debug("Discard %s if %s trump, lowest trump" % (discard.tag, trump['tag']))
            return discard

        # Create void if possible
        if suitcount.count(1) > 0:
            mincard = None
            minlevel = 10
            for idx in range(0, len(suitcount)):
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
        minlevel = 10
        savecards = []  # attempt to preserve, only discard if no alternatives
        for idx in range(0, len(suitcards)):
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
            if suitcards[idx] and suitcards[idx][0].level < minlevel:
                mincard = suitcards[idx][0]
                minlevel = mincard.level
        assert mincard or savecards
        if not mincard:
            mincard = min(savecards, key=lambda c: c.level)
            log.debug("Have to unguard doubleton king or discard from A-K, oh well...")
        log.debug("Discard %s if %s trump, lowest card" % (mincard.tag, trump['tag']))
        return mincard

    def trumpanalysis(self, trump):
        """
        :param trump: dict
        :return: dict with analysis info
        """
        idx = trump['idx']
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
                'singletons': hand_anl.singletons[idx],
                'hand_score': hand_anl.hand_score[idx]}
        info_debug = info.copy()
        info_debug.update({'suitcards': [[c.tag for c in s] for s in hand_anl.suitcards[idx]]})
        if self.pos == 3:
            info_debug.update({'discard': hand_anl.discard[idx].tag})
        log.debug("%s trump analysis for %s:\n%s" %
                  (trump['tag'], [c.tag for c in self.cards],
                   pp(info_debug, sort_keys=False, noprint=True)))
        return info

    def bestsuit(self, exclude = None):
        """
        :return: suit (dict)
        """
        suits = SUITS.copy()
        if exclude:
            del suits[exclude['idx']]
        return max(suits, key=lambda s: self.analysis.hand_score[s['idx']])

    def biddable(self, trump, round):
        """
        TEMP TEMP TEMP: this is just a stand-in for dev purposes!!!!!!!
        :param trump: dict
        :param round: int
        :return: bool
        """
        idx = trump['idx']
        thresh = BID_THRESHOLD
        if self.pos == 3 and round == 1:
            # NOTE: this is currently not built into hand_score
            thresh -= DEALER_VALUE
        elif round == 2:
            thresh -= self.pos  # or whatever...
        return self.analysis.hand_score[idx] > thresh

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
