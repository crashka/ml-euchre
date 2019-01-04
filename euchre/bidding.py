#!/usr/bin/env python
# -*- coding: utf-8 -*-

from core import log, SUITS, ace, king, queen, jack, ten, nine, right, left

# TEMP: for now, hardwire value for off-suit aces and voids, as equated with
# a trump suit card value!!!
OFF_ACE_VALUE   = king['level']
VOID_SUIT_VALUE = queen['level']
BID_THRESHOLD   = right['level'] + left['level'] + ten['level'] + OFF_ACE_VALUE
DEALER_VALUE    = nine['level']

class BidAnalysis(object):
    """Analysis for a hand and specified trump suit

    TODO: need to transition this class into the bidding module, to keep the Hand
    class/module as unopinionated (relative to strategy) as possible!!!
    """
    def __init__(self, cards, trump, turncard, discard = None):
        self.cards        = cards
        self.trump        = trump
        self.turncard     = turncard
        self.discard      = discard   # dealer only (based on turncard)

        self.suitcount    = [0, 0, 0, 0]
        self.suitcards    = [[], [], [], []]
        self.trump_score  = None
        self.next_score   = None
        self.green_score  = None
        # purple is the weaker off-color suit
        self.purple_score = None
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
        self.trump_score  = sum(c.efflevel[tru_idx] for c in tru_cards)
        self.next_score   = sum(c.efflevel[tru_idx] for c in nxt_cards)
        self.green_score  = sum(c.efflevel[tru_idx] for c in grn_cards)
        self.purple_score = sum(c.efflevel[tru_idx] for c in pur_cards)

        # aggregation for top trump card scores (idx 0 = top trump, idx 1 = second high, etc.)
        for idx in range(len(tru_cards)):
            card_idx = -1 - idx
            for idx2 in range(idx, len(self.cards)):
                self.top_trump_scores[idx2] += tru_cards[card_idx].efflevel[tru_idx]

        # REVISIT: currently swap green and purple scores based on "score", but could
        # (or should) it be something else???
        if self.purple_score > self.green_score:
            self.green_score, self.purple_score = self.purple_score, self.green_score
            self.green_swap = True

        # NOTE: penalty/reward for deliverying the trump into opponent or partner hand is
        # included in the hand analysis below
        self.hand_score = self.trump_score + \
                          self.trumps * 2 + \
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

def analyze(hand, turncard):
    """
    """
    log.trace("Analyzing hand for %s: %s" % (hand.seat['name'], hand.card_tags))
    discard = None
    bid_analysis = [BidAnalysis(hand.cards, s, turncard) for s in SUITS]
    # penalty/reward for ordering trump into dealer hand (note, this should be
    # pushed into BidAnalysis, one way or another!)
    turn_idx = turncard.suit['idx']
    if hand.pos in (0, 2):
        penalty = turncard.efflevel[turn_idx]
        bid_analysis[turn_idx].hand_score -= penalty
    elif hand.pos == 1:
        reward = turncard.efflevel[turn_idx] // 2
        bid_analysis[turn_idx].hand_score += reward

    # fix up dealer hand based on turncard
    if hand.pos == 3:
        suit_idx = turncard.suit['idx']
        # note that the following may actually return the turncard, e.g. if it
        # would be the lowest trump (or perhaps some wacky other reason)
        discard = _bestdiscard(bid_analysis[suit_idx], turncard)
        newcards = hand.cards.copy()
        newcards.append(turncard)
        newcards.remove(discard)
        log.trace("Reanalyzing dealer hand with turncard (%s) and discard (%s)" %
                  (turncard.tag, discard.tag))
        reanalysis = BidAnalysis(newcards, turncard.suit, turncard, discard)
        bid_analysis[suit_idx] = reanalysis

    return (bid_analysis, discard)

def _bestdiscard(analysis, turncard):
    """
    """
    trump = turncard.suit
    tru_idx = trump['idx']
    nxt_idx = tru_idx ^ 0x03
    suitcount = analysis.suitcount
    suitcards = analysis.suitcards

    def all_trump_case():
        """Handle all trump case (get it out of the way)
        """
        if suitcount[tru_idx] == len(analysis.cards):
            discard = min(suitcards[tru_idx][0], turncard, key=lambda c: c.level)
            log.debug("Discard %s if %s trump, lowest trump" % (discard.tag, trump['tag']))
            return discard

    def create_void():
        """Create void if possible
        """
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
                log.debug("Discard %s if %s trump, voiding suit" % (mincard.tag, trump['tag']))
                return mincard

    def create_doubleton():
        """Create doubletons, if possible (favor over creating singletons)
        """
        if suitcount.count(3) > 0:
            idx = suitcount.index(3)
            # REVISIT: perhaps only do if high card in suit is actually viable (like
            # queen or higher)!!!
            if idx != tru_idx:
                # note that first element is the loweest (cards sorted ascending)
                discard = suitcards[idx][0]
                log.debug("Discard %s if %s trump, creating doubleton" % (discard.tag, trump['tag']))
                return discard

    def discard_from_next():
        """Discard next if loner call from third seat (REVISIT: not sure it makes sense
        to extend this to the general, non-voiding, non-third-seat-loner case!!!)
        """
        if suitcount[nxt_idx] == 2:
            # don't unguard doubleton king or break up A-K
            if king not in (c.rank for c in suitcards[nxt_idx]):
                discard = suitcards[nxt_idx][0]
                log.debug("Discard %s if %s trump, reducing next" % (discard.tag, trump['tag']))
                return discard

    def discard_lowest():
        """Discard lowest card, any suit (last resort)

        Note: always returns value, can be last in ruleset
        """
        mincard = None
        minlevel = ace['level']
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
            if suitcards[idx]:
                if suitcards[idx][0].level < minlevel:
                    mincard = suitcards[idx][0]
                    minlevel = mincard.level
                elif suitcards[idx][0].level == minlevel:
                    # may need to stow an ace, if only outstanding card
                    savecards.append(suitcards[idx][0])
        assert mincard or savecards
        if not mincard:
            mincard = min(savecards, key=lambda c: c.level)
            log.debug("Have to unguard doubleton king or discard from A/A-K, oh well...")
        log.debug("Discard %s if %s trump, lowest card" % (mincard.tag, trump['tag']))
        return mincard

    # for now, we only have a single ruleset (later, can conditionally choose rules)
    discard_logic = [all_trump_case,
                     create_void,
                     create_doubleton,
                     discard_from_next,
                     discard_lowest]

    def apply(ruleset):
        """TODO: move to core (currently replicated across modules)!!!
        """
        res = None
        for rule in ruleset:
            res = rule()
            if res:
                break
        if not res:
            raise LogicError("Ruleset did not produce valid result")
        return res

    return apply(discard_logic)


def bid(hand):
    """
    :return: suit or None (meaning "pass")
    """
    deal = hand.deal
    bid_pos = len(deal.bids)  # 0-7
    turnsuit = deal.turncard.suit

    if bid_pos < 4:
        return turnsuit if _biddable(hand, turnsuit, bid_pos) else None
    else:
        suit = _bestsuit(hand, turnsuit)
        return suit if _biddable(hand, suit, bid_pos) else None

def _bestsuit(hand, exclude = None):
    """
    :param hand: Hand
    :param exclude: dict (SUITS[i])
    :return: suit (dict)
    """
    suits = SUITS.copy()
    if exclude:
        del suits[exclude['idx']]
    # TODO: add tie-breaker in the case of equal scores!!!
    return max(suits, key=lambda s: hand.bid_analysis[s['idx']].hand_score)

def _biddable(hand, trump, bid_pos):
    """
    TEMP TEMP TEMP: this is just a stand-in for dev purposes!!!!!!!
    :param hand: Hand
    :param trump: dict (SUITS[i])
    :param bid_pos: int
    :return: bool
    """
    idx = trump['idx']
    thresh = BID_THRESHOLD
    if bid_pos == 3:
        # NOTE: this is currently not built into hand_score
        thresh -= DEALER_VALUE
    elif bid_pos > 3:
        thresh -= bid_pos % 4  # or whatever...
    log.debug("  Hand score: %d (with %s as trump), threshold: %d" %
              (hand.bid_analysis[idx].hand_score, trump['tag'], thresh))
    return hand.bid_analysis[idx].hand_score > thresh

def bid_features(hand, suit):
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
    analysis = hand.bid_analysis[suit_idx]

    if analysis.turncard.is_left():
        turn_level = right['level']
        turn_suit  = analysis.turncard.base['suit']
    else:
        turn_level = analysis.turncard.level
        turn_suit  = analysis.turncard.suit
    one_hot_rel_suits = tuple(int(turn_suit == s) for s in analysis.rel_suits)
    top_trump_scores = tuple(analysis.top_trump_scores[:3])
    return (turn_level,
            *one_hot_rel_suits,
            *top_trump_scores,
            analysis.trump_score,
            analysis.next_score,
            analysis.green_score,
            analysis.purple_score,
            analysis.suitcount[suit_idx],
            analysis.voids,
            analysis.aces)
