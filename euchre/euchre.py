#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os.path
import logging
import logging.handlers
import random
import types

from core import log, RANKS, SUITS, CARDS, SEATS, TEAMS, LogicError
from hand import Card, Hand

###################
# Constants, etc. #
###################

MATCH_GAMES_DFLT = 2
GAME_POINTS_DFLT = 10

#########
# Match #
#########

class Match(object):
    """Represents a set of games (race to 2, by default) played by two teams
    """
    def __init__(self, bidding, playing, match_games = MATCH_GAMES_DFLT,
                 game_points = GAME_POINTS_DFLT):
        """
        """
        # NOTE: for now, bidding/playing are passed in as modules, but later they
        # will be Bidding and Playing (or subclass) objects, instantiated with
        # parameters from config file
        if isinstance(bidding, (list, tuple)):
            if type(playing) != type(bidding) or len(playing) != len(bidding):
                raise LogicError("playing and bidding must be same type and size")
            rep = len(bidding) // 4
            self.bidding = bidding * rep
            self.playing = playing * rep
        else:
            if not isinstance(bidding, types.ModuleType) or \
               not isinstance(playing, types.ModuleType):
                raise LogicError("playing and bidding must be modules (if scalar)")
            self.bidding = [bidding] * 4
            self.playing = [playing] * 4

        self.match_games = match_games
        self.game_points = game_points
        self.games       = []
        self.curgame     = None
        self.games_won   = [0, 0]
        self.winner      = None  # team
        self.stats       = None  # later

    def newgame(self):
        """
        :return: new Game instance
        """
        self.curgame = Game(self)
        self.games.append(self.curgame)
        log.info("===== New Game, #%d =====" % (len(self.games)))
        return self.curgame

    def update_score(self, team_games):
        """Update score based on completed game (self.curgame), called by Game.update_score
        """
        for idx in range(2):
            if team_games[idx] > 0:
                assert team_games[idx^0x01] == 0
                self.games_won[idx] += team_games[idx]
                if self.games_won[idx] >= self.match_games:
                    self.winner = TEAMS[idx]
                    log.info("%s wins match, games: %d-%d" %
                             (TEAMS[idx]['name'], self.games_won[idx], self.games_won[idx^0x01]))
                    return

        idx = 0 if self.games_won[0] > self.games_won[1] else 1
        log.info("%s leads match, games: %d-%d" %
                 (TEAMS[idx]['name'], self.games_won[idx], self.games_won[idx^0x01]))

    def update_stats(self):
        """
        """
        pass

########
# Game #
########

class Game(object):
    """
    """
    def __init__(self, match, game_points = None):
        """
        """
        self.match       = match
        self.game_points = game_points if game_points else match.game_points
        self.deals       = []
        self.curdealer   = None
        self.curdeal     = None
        self.score       = [0, 0]  # points by team
        self.winner      = None  # team
        self.stats       = None  # later

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

    def newdeal(self):
        """
        :return: new Deal instance
        """
        self.curdealer = self.nextdealer()
        self.curdeal = Deal(self)
        self.deals.append(self.curdeal)
        return self.curdeal

    def update_score(self, team_points):
        """Update score based on completed deal (self.curdeal), called by Deal.tabulate
        """
        for idx in range(2):
            if team_points[idx] > 0:
                assert team_points[idx^0x01] == 0
                self.score[idx] += team_points[idx]
                if self.score[idx] >= self.game_points:
                    self.winner = TEAMS[idx]
                    log.info("%s wins game #%d, score: %d-%d" %
                             (TEAMS[idx]['name'], len(self.match.games),
                              self.score[idx], self.score[idx^0x01]))
                    self.match.update_score([int(bool(pts)) for pts in team_points])
                    return

        idx = 0 if self.score[0] > self.score[1] else 1
        log.info("%s leads game #%d, score: %d-%d" %
                 (TEAMS[idx]['name'], len(self.match.games),
                  self.score[idx], self.score[idx^0x01]))

    def update_stats(self):
        """
        """
        pass

########
# Deal #
########

class DealStats(object):
    """
    """
    def __init__(self, deal):
        if not deal.contract:
            raise LogicError("Contract must be set for DealStats deal")

        self.deal   = deal
        self.unseen = [[], [], [], []]
        self.seen   = [[], [], [], []]

        for c in self.deal.deck:
            self.unseen[c.suit['idx']].append(c)
        tru_idx = self.deal.contract['idx']
        for suitcards in self.unseen:
            suitcards.sort(key=lambda c: c.efflevel[tru_idx])  # slghtly more efficient than c.level

    def card_seen(self, card):
        """
        """
        suit_idx = card.suit['idx']
        self.unseen[suit_idx].remove(card)
        # not pretty, but oh well...
        self.seen[suit_idx].append(card)
        tru_idx = self.deal.contract['idx']
        self.seen[suit_idx].sort(key=lambda c: c.efflevel[tru_idx])

    @property
    def high_cards(self):
        """Return list of high cards remaining (unseen), indexed by suit number (value of
        None for a suit indicates all cards have been seen)
        """
        return [s[-1] if s else None for s in self.unseen]

class Deal(object):
    """Represents a single shuffle, deal, bidding, and playing of the cards

    Note: our notion of a "deal" is also popularly called a "hand", but we are reserving that
    word to mean the holding of five dealt cards by a player during a deal
    """
    def __init__(self, game):
        """
        """
        self.game       = game
        self.match      = game.match
        self.dealer     = game.curdealer  # note, this is a seat, not a hand!
        self.deck       = None  # [cards] -- shuffled
        self.hands      = None  # [hands] -- ordered by position (0 = first bid, 3 = dealer)
        self.bury       = None  # [cards] -- len 3 during first round bids, otherwise len 4
        self.turncard   = None  # card
        self.discard    = None  # card

        self.bids       = None  # [(bidder_hand, bid), ...]
        self.contract   = None  # suit -- (for now...perhaps will be a structure in the future)
        self.caller     = None  # hand
        self.defender   = None  # hand, only if defending alone
        self.play_alone = False
        self.dfnd_alone = False
        self.plays      = None  # [(player_hand, card), ...]
        self.tricks     = None  # [(winner_hand, [cards]), ...]
        self.score      = [0, 0]  # tricks won, by team
        self.winner     = None
        self.stats      = None
        self.replays    = 0

    def reset(self):
        """Reset all deal state other than deck, so we can replay the deal
        """
        self.hands      = None
        self.bury       = None
        self.turncard   = None
        self.discard    = None

        self.bids       = None
        self.contract   = None
        self.caller     = None
        self.defender   = None
        self.play_alone = False
        self.dfnd_alone = False
        self.plays      = None
        self.tricks     = None
        self.score      = [0, 0]
        self.winner     = None
        self.stats      = None
        self.replays    += 1

    @property
    def dealno(self):
        """Only valid for current deal within game
        """
        assert self.game.curdeal == self
        return len(self.game.deals)

    def play(self):
        """
        :return: void
        """
        if self.game.winner:
            raise RuntimeError("Cannot deal when game is already over (winner: %s)" %
                               (self.game.winner['name']))
        # shuffle and deal
        self.log_info('header')
        self.shuffle()
        self.deal()

        # bidding and playing tricks
        bid = self.bid()
        if bid:
            self.playtricks()
            self.tabulate()

        self.update_stats()

    def shuffle(self, force = False):
        """
        :return: void
        """
        if self.deck and not force:
            raise LogicError("Cannot shuffle if deck is already shuffled")
        self.deck = [Card(c, self) for c in random.sample(CARDS, k=len(CARDS))]

    def deal(self, force = False):
        """
        :return: void
        """
        if self.hands and not force:
            raise LogicError("Cannot deal when hands have been dealt")
        if not self.deck:
            raise LogicError("Deck must be shuffled in order to deal")
        if not self.dealer:
            raise LogicError("Dealer must be set in order to deal")

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
        self.log_info('hands')

        self.bids = []

    def bid(self):
        """
        :return: suit (trunp) or None (meaning passed deal)
        """
        for hand in self.hands:
            hand.analyze(self.turncard)
        dealer_hand = self.hands[3]
        if not dealer_hand.discard:
            raise RuntimeError("Dealer hand analysis must select best discard")

        log.info("Bidding for deal #%d begins" % (self.dealno))
        bidder = self.hands[0]
        while len(self.bids) < 8:
            bid = bidder.bid()
            self.bids.append(bid)
            # REVISIT: None means pass for now, but LATER we may want to always pass back
            # a structure containing insight into bid decision, so we would have to check
            # for a pass within it explicitly!!!
            if bid:
                if len(self.bids) < 4:
                    if bid != self.turncard.suit:
                        raise RuntimeError("Illegal bid, %s does not match turncard %s" %
                                           (bid['name'], self.turncard.tag))
                    self.bury.append(dealer_hand.discard)
                    log.info("  %s orders up %s" % (bidder.seat['name'], self.turncard.tag))
                elif len(self.bids) == 4:
                    if bid != self.turncard.suit:
                        raise RuntimeError("Illegal bid, %s does not match turncard %s" %
                                           (bid['name'], self.turncard.tag))
                    assert bidder == dealer_hand
                    self.bury.append(bidder.discard)
                    log.info("  %s (dealer) picks up %s" % (bidder.seat['name'], self.turncard.tag))
                else:
                    if bid == self.turncard.suit:
                        raise RuntimeError("Illegal bid, %s must be different than turncard %s" %
                                           (bid['name'], self.turncard.tag))
                    log.info("  %s calls %s" % (bidder.seat['name'], bid['name']))
                break
            elif len(self.bids) == 4:
                assert bidder == dealer_hand
                self.bury.append(self.turncard)
                log.info("  %s passes, turns down %s" % (bidder.seat['name'], self.turncard.tag))
            else:
                log.info("  %s passes" % (bidder.seat['name']))
            bidder = bidder.next

        if bid:
            self.caller   = bidder
            self.contract = bid
            self.plays    = []  # [(player_hand, card), ...]
            self.tricks   = []  # [(winner_hand, [cards]), ...]
            log.info("%s is trump, called by %s" %
                     (bid['name'].capitalize(), TEAMS[bidder.team_idx]['tag']))

            for hand in self.hands:
                hand.set_trump(self.contract)
            if len(self.bids) <= 4 and dealer_hand.discard in dealer_hand.cards:
                raise RuntimeError("Discard should not be in dealer hand")
            if len(self.bids) > 4 and self.turncard in dealer_hand.cards:
                raise RuntimeError("Turncard should not be in dealer hand")
            self.stats = DealStats(self)
            self.log_info('hands')
        else:
            log.info("Deal is passed")

        return bid  # see REVISIT above on interpretation of bid

    @property
    def is_next_call(self):
        return self.is_nextsuit and len(self.bids) == 5

    @property
    def is_reverse_next(self):
        return self.is_greensuit and len(self.bids) == 6

    @property
    def is_turnsuit(self):
        if not self.contract:
            raise LogicError("Bad call sequence, bidding not complete")
        turn_idx = self.turncard.suit['idx']
        return self.contract['idx'] == turn_idx

    @property
    def is_nextsuit(self):
        if not self.contract:
            raise LogicError("Bad call sequence, bidding not complete")
        turn_idx = self.turncard.suit['idx']
        return self.contract['idx'] == turn_idx ^ 0x03

    @property
    def is_greensuit(self):
        if not self.contract:
            raise LogicError("Bad call sequence, bidding not complete")
        turn_idx = self.turncard.suit['idx']
        return self.contract['idx'] in (turn_idx ^ 0x01, turn_idx ^ 0x02)

    def cmpcards(self, lead, winning, played):
        """
        :param lead: Card led for trick
        :param winning: Card currently winning
        :param played: Card last played
        :return: int (negative if played loses, positive if played wins)
        """
        ret = None
        trump_winning = winning.suit == self.contract
        trump_played  = played.suit == self.contract
        followed_suit = played.suit == lead.suit
        if trump_winning:
            ret = played.level - winning.level if trump_played else -played.level
        elif trump_played:
            ret = played.level
        else:
            ret = played.level - winning.level if followed_suit else -played.level
        return ret

    def playtricks(self):
        """
        :return: score [E/W tricks, N/S tricks]
        """
        player  = self.hands[0]
        while len(self.tricks) < 5:
            plays    = []            # [(player_hand, card), ...]
            cards    = []            # [cards]
            winning  = (None, None)  # (player_hand, card)
            trick_no = len(self.tricks) + 1
            log.info("Trick #%d:" % (trick_no))
            while len(plays) < 4:
                note = ''
                winning_card = winning[1]  # just for semantic readability
                card = player.play(plays, winning)
                cards.append(card)
                plays.append((player, card))
                if card:
                    self.stats.card_seen(card)
                    if not winning_card:
                        winning = (player, card)
                        note = ' (currently winning)'
                    else:
                        if self.cmpcards(cards[0], winning_card, card) > 0:
                            winning = (player, card)
                            note = ' (currently winning)'
                    if len(plays) == 1:
                        log.info("  %s leads %s%s" % (player.seat['name'], card.tag, note))
                    else:
                        log.info("  %s plays %s%s" % (player.seat['name'], card.tag, note))
                else:
                    log.info("  %s's turn is skipped" % (player.seat['name']))
                player = player.next

            winning_hand = winning[0]  # for readability (as above)
            winning_card = winning[1]
            self.plays += plays
            self.tricks.append((winning_hand, cards))
            team_idx = winning_hand.team_idx
            self.score[team_idx] += 1
            log.info("%s takes trick #%d with %s (%d-%d)" %
                     (winning_hand.seat['name'], trick_no, winning_card.tag,
                      self.score[team_idx], self.score[team_idx ^ 0x01]))
            player = winning_hand

    def tabulate(self):
        """
        :return: void
        """
        team_points  = [0, 0]
        caller_idx   = self.caller.team_idx
        defender_idx = caller_idx ^ 0x01
        tricks_made  = self.score[caller_idx]

        if tricks_made >= 3:
            self.winner = TEAMS[caller_idx]
            team_points[caller_idx] += 1
            if tricks_made == 5:
                team_points[caller_idx] += 1
            log.info("%s wins deal #%d (makes contract), tricks: %d-%d, +%d points" %
                     (TEAMS[caller_idx]['name'], self.dealno, self.score[caller_idx],
                      self.score[defender_idx], team_points[caller_idx]))
        else:
            self.winner = TEAMS[defender_idx]
            team_points[defender_idx] += 2
            log.info("%s wins deal #%d (euchre!), tricks: %d-%d, +%d points" %
                     (TEAMS[defender_idx]['name'], self.dealno, self.score[defender_idx],
                      self.score[caller_idx], team_points[defender_idx]))

        self.game.update_score(team_points)
        # notes, these are not game points, just relative to calling team for the deal
        #caller_points = team_points[caller_idx] - team_points[defender_idx]
        #log.debug("Caller (%s) points: %d" % (TEAMS[caller_idx]['name'], caller_points))

    def update_stats(self):
        """
        """
        pass

    def log_info(self, *what):
        """
        :return: void
        """
        if not what or 'header' in what:
            log.info("Deal #%d, dealer is %s" % (self.dealno, self.dealer['name']))

        if not what or 'caller' in what:
            log.info("  Caller: %s" % (self.caller.seat['name']))

        if not what or 'contract' in what:
            log.info("  Trump: %s" % (self.contract['name']))

        if not what or 'hands' in what:
            log.info("  %s hands:" % ("Bidding" if not self.contract else "Playing"))
            for hand in self.hands:
                log.info("    %-5s (%d): %s" %
                      (hand.seat['name'], hand.pos, [c.tag for c in hand.cards]))
            if not self.contract and (not self.bids or len(self.bids) < 4):
                log.info("  Turncard: %s" % (self.turncard.tag))
            log.info("  Buried: %s" % ([c.tag for c in self.bury]))

###########
# Testing #
###########

import click
import bidding
import playing

from core import param, dflt_hand, dbg_hand
import utils

# TEMP: make this global for now (LATER, can be subordinate to higher-level entities, such as
# tables, tournaments, etc.)!!!
MATCH = Match(bidding, playing)

@click.command()
@click.option('--seed',   '-s', default=None, type=int, help="Seed for random module")
@click.option('--ndeals', '-n', default=None, type=int, help="Number of deals")
@click.option('--debug',  '-d', default=0, help="Debug level")
def test(seed, ndeals, debug):
    """Play a single game, print out ML features
    """
    debug = debug or int(param.get('debug') or 0)
    if debug > 0:
        log.setLevel(utils.TRACE if debug > 1 else logging.DEBUG)
        dflt_hand.setLevel(utils.TRACE if debug > 1 else logging.DEBUG)
        #dbg_hand.setLevel(utils.TRACE if debug > 1 else logging.DEBUG)
        #log.addHandler(dbg_hand)

    if seed:
        random.seed(seed)

    g = MATCH.newgame()
    for i in range(ndeals or 1000):
        d = g.newdeal()
        d.play()
        if not d.winner:
            print("Deal passed")
            continue

        caller_idx   = d.caller.team_idx
        tricks_made  = d.score[caller_idx]
        ml_features = (len(d.bids) - 1,  # bidder position, 0-7 (3 and 7 are dealer)
                       int(d.play_alone),
                       *d.caller.features(d.contract),
                       tricks_made)
        print("ML features: %s" % (list(ml_features)))

        if g.winner:
            idx = g.winner['idx']
            print("%s wins game #%d, score: %d-%d" %
                  (g.winner['name'], len(MATCH.games), g.score[idx], g.score[idx^0x01]))
            break

    if not g.winner:
        print("Score for game #%d: %s %d, %s %d" %
              (len(MATCH.games), TEAMS[0]['name'], g.score[0], TEAMS[1]['name'], g.score[1]))

    return 0

if __name__ == '__main__':
    test()
