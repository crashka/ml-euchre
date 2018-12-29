#!/usr/bin/env python
# -*- coding: utf-8 -*-

from core import log, TEAMS, SUITS, ALLRANKS, ace, king, queen, jack, right, left, LogicError
from utils import prettyprint as pp

########
# Card #
########

class Card(object):
    """Represents an instance of a card that is part of a deal; the "basecard"
    is the underlying immutable card identity (e.g. rank, suit, and name) that is
    independent of deal status, trump, etc.
    """
    def __init__(self, basecard, deal):
        self.base = basecard
        self.deal = deal
        # effective level and suit are based on trump suit
        self.efflevel = [self.base['level']] * 4
        self.effsuit = [self.base['suit']] * 4

        suit_idx = self.base['suit']['idx']
        opp_idx = suit_idx ^ 0x3
        if self.rank == jack:
            self.efflevel[suit_idx] = right['level']
            self.efflevel[opp_idx] = left['level']
            # counter-intuitive: this can look wrong at first glance, but is correct
            self.effsuit[opp_idx] = SUITS[opp_idx]
        elif self.rank in (queen, king):
            # REVISIT: for now, demote queen/king because jack is elevated (the gap
            # to ace and bowers accentuates strength of those cards), but not sure
            # this is best formula (could also close up gap one way or the other)--
            # would be cool to validate this against ML models at some point!!!
            self.efflevel[suit_idx] -= 1

    def __getattr__(self, key):
        try:
            return self.base[key]
        except KeyError:
            raise AttributeError()

    def __repr__(self):
        return str(self.base)

    def __str__(self):
        return self.base['tag']

    @property
    def level(self):
        if self.deal.contract:
            tru_idx = self.deal.contract['idx']
            return self.efflevel[tru_idx]
        return self.base['level']

    @property
    def suit(self):
        if self.deal.contract:
            tru_idx = self.deal.contract['idx']
            return self.effsuit[tru_idx]
        return self.base['suit']

########
# Hand #
########

# TEMP: for now, hardwire value for off-suit aces and voids, as equated with
# a trump suit card value!!!
OFF_ACE_VALUE   = queen['level']
VOID_SUIT_VALUE = queen['level']
BID_THRESHOLD   = right['level'] + left['level'] + OFF_ACE_VALUE
DEALER_VALUE    = queen['level']

class HandAnaly(object):
    """Analysis for a hand and specified trump suit
    """
    def __init__(self, cards, trump):
        self.cards        = cards
        self.trump        = trump

        self.suitcount    = [0, 0, 0, 0]
        self.suitcards    = [[], [], [], []]
        self.trump_score  = [None] * 2
        self.next_score   = [None] * 2
        self.green_score  = [None] * 2
        # purple is the weaker off-color suit
        self.purple_score = [None] * 2
        self.green_swap   = False  # true if green and purple scores are swapped
        self.trumps       = None
        self.aces         = 0      # only count off-aces
        self.voids        = None   # only count non-trump suits
        self.singletons   = None   # only count non-trump suits
        # for a little higher definition of trump profile, aggregate the scores for
        # the top N trump cards (though we will likely only use slots 1-3)
        self.top_trump_scores = [0] * len(cards)
        # note that hand_score should not be used as part of the bidding (or playing)
        # logic; rather, the highest hand_score "seen" thus far in the bidding round
        # is used as a rough proxy for how likely the bid would have actually gotten
        # to a hand position--this should be the only place in the program that we are
        # allowed to use a god view as part of the game strategy (LATER, we can extend
        # this idea to take into account various bidding/playing styles in determining
        # the likeliness of a bidding opportunity)
        self.hand_score   = None

        # NOTE: this does not sort bowers (as in Hand.__init__), could/should resort
        # properly in Hand.set_trump
        self.cards.sort(key=lambda c: c.sortkey)
        self.analyze_cards()

    def analyze_cards(self):
        """
        """
        tru_idx = self.trump['idx']
        nxt_idx = tru_idx ^ 0x03
        grn_idx = tru_idx ^ 0x01
        pur_idx = tru_idx ^ 0x02

        # process cards in hand
        for card in self.cards:
            suit_idx = card.suit['idx']
            is_bower = card.rank == jack
            is_ace   = card.rank == ace

            if is_bower and suit_idx == nxt_idx:
                self.suitcount[tru_idx] += 1
                self.suitcards[tru_idx].append(card)
            else:
                self.suitcount[suit_idx] += 1
                self.suitcards[suit_idx].append(card)

            # only count off-suit aces
            if suit_idx != tru_idx and is_ace:
                self.aces += 1

        # re-sort suitcards to include bower rankings (TODO: make this less ugly!!!)
        self.suitcards[tru_idx].sort(key=lambda c: c.efflevel[tru_idx])

        # count trumps/voids/singletons
        count = self.suitcount.copy()
        self.trumps = count[tru_idx]
        del count[tru_idx]  # only count off-suits
        self.voids      = len([c for c in count if c == 0])
        self.singletons = len([c for c in count if c == 1])

        # compute suit scores
        tru_cards = self.suitcards[tru_idx]
        nxt_cards = self.suitcards[nxt_idx]
        grn_cards = self.suitcards[grn_idx]
        pur_cards = self.suitcards[pur_idx]
        self.trump_score[0]  = sum(c.efflevel[tru_idx]    for c in tru_cards)
        self.trump_score[1]  = sum(c.efflevel[tru_idx]**2 for c in tru_cards)
        self.next_score[0]   = sum(c.efflevel[tru_idx]    for c in nxt_cards)
        self.next_score[1]   = sum(c.efflevel[tru_idx]**2 for c in nxt_cards)
        self.green_score[0]  = sum(c.efflevel[tru_idx]    for c in grn_cards)
        self.green_score[1]  = sum(c.efflevel[tru_idx]**2 for c in grn_cards)
        self.purple_score[0] = sum(c.efflevel[tru_idx]    for c in pur_cards)
        self.purple_score[1] = sum(c.efflevel[tru_idx]**2 for c in pur_cards)

        # aggregation for top trump card scores (idx 0 = top trump, idx 1 = second high, etc.)
        for idx in range(len(tru_cards)):
            card_idx = -1 - idx
            for idx2 in range(idx, len(self.cards)):
                self.top_trump_scores[idx2] += tru_cards[card_idx].efflevel[tru_idx]

        # REVISIT: currently swap green and purple scores based on score[0], but
        # could/should it be something else (e.g. score[1])???
        if self.purple_score[0] > self.green_score[0]:
            self.green_score[0], self.purple_score[0] = self.purple_score[0], self.green_score[0]
            self.green_score[1], self.purple_score[1] = self.purple_score[1], self.green_score[1]
            self.green_swap = True

        # TODO: hand score should take into account the turncard--penalty/reward
        # for deliverying the trump into opponent or partner hand, or included in
        # the computation for dealer hand (related to selecting discard, below)!!!
        self.hand_score = self.trump_score[0] + \
                          self.trumps + \
                          self.voids * VOID_SUIT_VALUE + \
                          self.aces * OFF_ACE_VALUE

        self.log_trace()

    @property
    def rel_suits(self):
        """Return tuple of suits relative to trump

        :return: tuple (next, green, purple)
        """
        tru_idx = self.trump['idx']
        nxt_idx = tru_idx ^ 0x03
        grn_idx = tru_idx ^ (0x02 if self.green_swap else 0x01)
        pur_idx = grn_idx ^ 0x03
        return (SUITS[nxt_idx], SUITS[grn_idx], SUITS[pur_idx])

    @property
    def card_tags(self):
        return [c.tag for c in self.cards]

    @property
    def card_tags_by_suit(self):
        return [[c.tag for c in s] for s in self.suitcards]

    def log_trace(self):
        """
        """
        log.trace("  with %s as trump:" % (self.trump['tag']))
        log.trace("    cards by suit:    %s" % (self.card_tags_by_suit))
        log.trace("    count by suit:    %s" % (self.suitcount))
        log.trace("    trump score:      %s" % (self.trump_score))
        log.trace("    next score:       %s" % (self.next_score))
        log.trace("    green score:      %s" % (self.green_score))
        log.trace("    purple score:     %s" % (self.purple_score))
        log.trace("    trumps:           %s" % (self.trumps))
        log.trace("    top trump scores: %s" % (self.top_trump_scores))
        log.trace("    aces:             %s" % (self.aces))
        log.trace("    voids:            %s" % (self.voids))
        log.trace("    singletons:       %s" % (self.singletons))
        log.trace("    hand score:       %s" % (self.hand_score))

class Hand(object):
    """
    """
    def __init__(self, deal, seat, pos, cards):
        self.deal          = deal
        self.seat          = seat
        self.pos           = pos
        self.next_pos      = (pos + 1) % 4
        self.partner_pos   = (pos + 2) % 4
        self.prev_pos      = (pos + 3) % 4
        self.cards         = cards.copy()  # do not disturb input list
        self.cards.sort(key=lambda c: c.sortkey)
        self.trump         = None  # set in set_trump()
        self.suitcards     = None  # dependent on trump
        self.bidding       = deal.match.bidding[seat['idx']]
        self.playing       = deal.match.playing[seat['idx']]

        # note that analysis (and best dealer discard) is based on turncard
        self.turncard      = None  # basis for special dealer analysis
        self.analysis      = None  # list (HandAnaly per trump suit)
        self.discard       = None  # dealer only
        self.strategy      = []    # list of string tags for playing phase

    @property
    def team_idx(self):
        return self.seat['idx'] & 0x01

    @property
    def card_tags(self):
        return [c.tag for c in self.cards]

    @property
    def card_tags_by_suit(self):
        return [[c.tag for c in s] for s in self.suitcards]

    def is_partner(self, other):
        return other == self.partner

    @property
    def next(self):
        return self.deal.hands[self.next_pos]

    @property
    def partner(self):
        return self.deal.hands[self.partner_pos]

    def features(self, suit):
        """Return tuple of features based on suit bid, for training and predicting

        * Level of turncard (1-8)
        * Relative suit of turncard (in relation to trump)
           * One-hot encoding for next, green, or purple (all zeros if turncard picked up)
        * Trump (turncard or called) suit strength (various measures, start with sum of levels 1-8)
           * Top 1, 2, and 3 trump cards (three aggregate values)
           * Note: include turncard and exclude discard, if dealer (which implies that model
             will be tied to discard algorithm)
        * Trump/next/green/purple suit scores (instead of just trump strength?)
        * Number of trump (with turncard/discard, if dealer)
        * Number of voids (or suits)
        * Number of off-aces

        :return: tuple (see above for elements)
        """
        suit_idx = suit['idx']
        hand_anl = self.analysis[suit_idx]
        turnsuit = self.turncard.suit
        one_hot_rel_suits = tuple(int(turnsuit == s) for s in hand_anl.rel_suits)
        top_trump_scores = tuple(hand_anl.top_trump_scores[:3])
        return (self.turncard.level,
                *one_hot_rel_suits,
                *top_trump_scores,
                hand_anl.trump_score[0],
                hand_anl.next_score[0],
                hand_anl.green_score[0],
                hand_anl.purple_score[0],
                hand_anl.suitcount[suit_idx],
                hand_anl.voids,
                hand_anl.aces)

    def analyze(self, turncard, reanalyze = False):
        """
        """
        if not self.analysis or reanalyze:
            log.trace("%snalyzing hand for %s: %s" %
                      ("Rea" if reanalyze else "A", self.seat['name'], self.card_tags))
            self.turncard = turncard  # not currently used for non-dealer
            self.analysis = [HandAnaly(self.cards, s) for s in SUITS]
            if self.pos in (0, 2):
                # penalty for ordering trump into dealer hand (note, this should be
                # pushed into HandAnaly, one way or another!)
                turn_idx = turncard.suit['idx']
                penalty = turncard.efflevel[turn_idx] // 2
                self.analysis[turn_idx].hand_score -= penalty

            # fix up dealer hand based on turncard
            if self.pos == 3:
                newcards = self.cards.copy()
                newcards.append(turncard)
                # note that the following may actually return the turncard, e.g. if it
                # would be the lowest trump (or perhaps some wacky other reason)
                discard = self.bestdiscard(turncard)
                newcards.remove(discard)
                log.trace("Reanalyzing dealer hand with turncard (%s) and discard (%s)" %
                          (turncard.tag, discard.tag))
                reanalysis = HandAnaly(newcards, turncard.suit)
                self.discard = discard
                self.analysis[turncard.suit['idx']] = reanalysis

    def bestdiscard(self, turncard):
        """
        """
        trump = turncard.suit
        tru_idx = trump['idx']
        nxt_idx = tru_idx ^ 0x03
        hand_anl = self.analysis[tru_idx]
        suitcount = hand_anl.suitcount
        suitcards = hand_anl.suitcards

        # Handle all trump case (get it out of the way)
        if suitcount[tru_idx] == len(self.cards):
            discard = min(suitcards[tru_idx][0], turncard, key=lambda c: c.level)
            log.trace("Discard %s if %s trump, lowest trump" % (discard.tag, trump['tag']))
            return discard

        # Create void if possible
        if suitcount.count(1) > 0:
            mincard = None
            minlevel = 10
            for idx in range(len(suitcount)):
                if idx == tru_idx or suitcount[idx] != 1:
                    continue
                # for now, we just pick the first card found at the lowest level
                # LATER: favor voiding next or green, depending on opponent tendencies
                # (always void next if loner called from pos = 2)!!!
                if suitcards[idx][0].level < minlevel and suitcards[idx][0].rank != ace:
                    mincard = suitcards[idx][0]
                    minlevel = mincard.level
            if mincard:
                log.trace("Discard %s if %s trump, voiding suit" % (mincard.tag, trump['tag']))
                return mincard

        # Create doubletons, if possible (favor over creating singletons)
        if suitcount.count(3) > 0:
            idx = suitcount.index(3)
            # REVISIT: perhaps only do if high card in suit is actually viable (like
            # queen or higher)!!!
            if idx != tru_idx:
                # note that first element is the loweest (cards sorted ascending)
                discard = suitcards[idx][0]
                log.trace("Discard %s if %s trump, creating doubleton" % (discard.tag, trump['tag']))
                return discard

        # Discard next if loner call from third seat (REVISIT: not sure it makes sense
        # to extend this to the general, non-voiding, non-third-seat-loner case!!!)
        if suitcount[nxt_idx] == 2:
            # don't unguard doubleton king or break up A-K
            if king not in (c.rank for c in suitcards[nxt_idx]):
                discard = suitcards[nxt_idx][0]
                log.trace("Discard %s if %s trump, reducing next" % (discard.tag, trump['tag']))
                return discard

        # Discard lowest card, any suit (last resort)
        mincard = None
        minlevel = 10
        savecards = []  # attempt to preserve, only discard if no alternatives
        for idx in range(len(suitcards)):
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
            log.trace("Have to unguard doubleton king or discard from A-K, oh well...")
        log.trace("Discard %s if %s trump, lowest card" % (mincard.tag, trump['tag']))
        return mincard

    def bid(self):
        """
        """
        return self.bidding.bid(self)

    def play(self, plays, winning):
        """
        """
        return self.playing.play(self, plays, winning)

    def set_trump(self, trump):
        """
        Note, we could get the trump suit from self.deal.contract, but better to make
        this explicit for clarity (and possible decoupling from deal)
        """
        self.trump = trump
        tru_idx = self.trump['idx']
        self.cards = self.analysis[tru_idx].cards.copy()
        self.suitcards = self.analysis[tru_idx].suitcards.copy()
        self.cards.sort(key=lambda c: c.suit['idx'] * len(ALLRANKS) + c.level)

    def play_card(self, card):
        """
        :param card: Card (must be in hand)
        :return: card (for convenience, chaining, etc.)
        """
        suit_idx = card.suit['idx']
        self.cards.remove(card)
        self.suitcards[suit_idx].remove(card)
        return card

    @property
    def has_bower(self):
        """
        :return: true if one or more bowers in hand
        """
        tru_cards = self.trump_cards
        return tru_cards and tru_cards[-1].level >= left['level']

    @property
    def has_off_ace(self):
        """
        :return: true if one or more off aces in hand
        """
        return len(self.off_aces) > 0

    @property
    def trump_cards(self):
        """
        :return: list of cards
        """
        tru_idx = self.trump['idx']
        return self.suitcards[tru_idx]

    @property
    def green_suitcards(self):
        """
        :return: tuple (two lists of cards)
        """
        tru_idx = self.trump['idx']
        grn_cards = self.suitcards[tru_idx ^ 0x01]
        pur_cards = self.suitcards[tru_idx ^ 0x02]
        return (grn_cards, pur_cards) if len(grn_cards) >= len(pur_cards) \
            else (pur_cards, grn_cards)

    @property
    def off_aces(self):
        """
        :return: list
        """
        return [scs[-1] for scs in self.suitcards
                if scs and scs[-1].rank == ace and scs[-1].suit != self.trump]

    def bestsuit(self, exclude = None):
        """
        :return: suit (dict)
        """
        suits = SUITS.copy()
        if exclude:
            del suits[exclude['idx']]
        # TODO: add tie-breaker in the case of equal scores!!!
        return max(suits, key=lambda s: self.analysis[s['idx']].hand_score)

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
        log.debug("  Hand score: %d (with %s as trump), threshold: %d" %
                  (self.analysis[idx].hand_score, trump['tag'], thresh))
        return self.analysis[idx].hand_score > thresh

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
