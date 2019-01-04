#!/usr/bin/env python
# -*- coding: utf-8 -*-

from core import log, TEAMS, SUITS, ALLRANKS, ace, king, queen, jack, right, left

########
# Card #
########

class Card(object):
    """Represents an instance of a card that is part of a deal/deck; the "base" card
    is the underlying immutable identity (i.e. CARDS[n]) that indicates rank, suit,
    and name, independent of deal status, trump, etc.
    """
    def __init__(self, base, deal):
        self.base = base
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
            self.efflevel[opp_idx] -= 1
        elif self.rank == ace:
            self.efflevel[opp_idx] -= 1

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

    def is_left(self):
        """Keep as method rather than property to show trump-dependent
        nature (rather inconsistsent with how we are treating level and
        suit above, I know, but this is an aesthetic thing)
        """
        return self.level == left['level']

########
# Hand #
########

class Hand(object):
    """
    Hand notifications
      * Deal hands
          * Initialize hand
      * Show turncard
          * Initial bid analysis
      * Turn to bid
          * Bid history available
          * Update bid analysis
          * Make bid
      * Contract set (general notification)
          * Make discard, if dealer
          * Initial play analysis
      * Turn to play
          * Play history available
          * Update play analysis
          * Make play
      * Deal won (general notification)
          * Update game stats/analysis (at seat level)
          * Revisit: should this really be seat/player[?]-level notifications?
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

        self.bidding       = deal.match.bidding[seat['idx']]
        self.playing       = deal.match.playing[seat['idx']]
        self.bid_analysis  = None  # managed by bidding module/class
        self.play_analysis = None  # managed by playing module/class

        # the following are set in set_trump()
        self.trump         = None  
        self.discard       = None  # dealer only

    #+-------+
    #| Teams |
    #+-------+

    @property
    def team_idx(self):
        return self.seat['idx'] & 0x01

    @property
    def next(self):
        return self.deal.hands[self.next_pos]

    @property
    def partner(self):
        return self.deal.hands[self.partner_pos]

    def is_partner(self, other):
        """
        """
        return other == self.partner

    #+-------+
    #| Cards |
    #+-------+

    @property
    def card_tags(self):
        return [c.tag for c in self.cards]

    #+---------+
    #| Bidding |
    #+---------+

    def show_turncard(self, turncard):
        """
        Note, we could get the turncard from self.deal.turncard, but better to make
        this explicit for clarity (and possible decoupling from deal)
        """
        self.bid_analysis, self.discard = self.bidding.analyze(self, turncard)
        assert self.discard or self.pos != 3

    def bid(self):
        """
        """
        return self.bidding.bid(self)

    def bid_features(self, suit):
        """Return tuple of features based on suit bid, for training and predicting
        :return: tuple (see bidding module for details)
        """
        return self.bidding.bid_features(self, suit)

    #+---------+
    #| Playing |
    #+---------+

    def set_trump(self, trump):
        """
        Note, we could get the trump suit from self.deal.contract, but better to make
        this explicit for clarity (and possible decoupling from deal)
        """
        tru_idx = trump['idx']
        self.trump = trump
        # TODO: dissociate the following from bid_analysis!!!
        self.cards = self.bid_analysis[tru_idx].cards.copy()
        self.cards.sort(key=lambda c: c.suit['idx'] * len(ALLRANKS) + c.level)
        self.play_analysis = self.playing.analyze(self, trump)

    def play(self, plays, winning):
        """
        :return: Card
        """
        card = self.playing.play(self, plays, winning)
        if card not in self.cards:
            raise LogicError("Card %s not in hand %s" % (card['tag'], self.card_tags))
        self.cards.remove(card)
        return card

    def play_features(self, suit):
        """Return tuple of features based on suit bid, for training and predicting
        :return: tuple (see bidding module for details)
        """
        return self.playing.play_features(self, suit)

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
