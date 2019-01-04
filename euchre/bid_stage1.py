#!/usr/bin/env python
# -*- coding: utf-8 -*-

from core import log, SUITS, LogicError
from bidding import analyze, bid_features

###########
# Bidding #
###########

BID_VARIANTS = 16

def bid(hand):
    """
    :return: suit or None (meaning "pass")
    """
    deal     = hand.deal
    replay   = deal.replay
    bid_pos  = len(deal.bids)  # 0-7
    turnsuit = deal.turncard.suit
    turn_idx = turnsuit['idx']

    """
    Bids by replay:
    0-3:   order up turncard, bid_pos 0-3
    4-7:   call next, bid_pos 0-3
    8-11:  call green, bid_pos 0-3
    12-15: call purple, bid_pos 0-3
    """
    bid_suit = [turnsuit,
                SUITS[turn_idx ^ 0x03],  # next
                SUITS[turn_idx ^ 0x01],  # green
                SUITS[turn_idx ^ 0x02]]  # purple

    if replay < 4:
        return bid_suit[replay // 4] if bid_pos == replay & 0x03 else None
    elif replay < BID_VARIANTS:
        bid_pos -= 4
        return bid_suit[replay // 4] if bid_pos >= 0 and bid_pos == replay & 0x03 else None
    else:
        raise LogicError("Illegal value for replay (%d)" % (replay))

########
# Main #
########

import sys
import os.path
import logging
import random
import datetime as dt
import csv

import click

from core import BASE_DIR, param, dflt_hand, dbg_hand, TEAMS
from euchre import Match
import playing
import utils

mymodule  = sys.modules[__name__]
MAX_DEALS = 1000000

MODELS_DIR = 'models'
TDATA_DIR  = 'training_data'
MODEL_NAME = 'bid_stage1'

def tdata_file(run_id):
    filename  = 'tdata_' + run_id
    return os.path.join(BASE_DIR, MODELS_DIR, MODEL_NAME, TDATA_DIR, filename)

@click.command()
@click.option('--ndeals',  '-n', default=1,    type=int, help="Number of deals to run through")
@click.option('--debug',   '-d', default=0,    type=int, help="Debug level (0-2)")
@click.option('--seed',    '-s', default=None, type=int, help="Seed for random module")
def main(ndeals, debug, seed):
    """Generate training data for Stage 1 bidding model

    Currently hardwired to use the default "playing" module for playing out the hand
    (though we can make this configurable later)
    """
    ndeals = ndeals or MAX_DEALS
    debug = debug or int(param.get('debug') or 0)
    if debug > 0:
        log.setLevel(utils.TRACE if debug > 1 else logging.DEBUG)
        dflt_hand.setLevel(utils.TRACE if debug > 1 else logging.DEBUG)
    random.seed(seed)
    dsname = tdata_file(dt.datetime.now().strftime('%Y%m%d%H%M%S'))
    features = []

    match = Match(mymodule, playing, game_points=MAX_DEALS)
    for ideal in range(ndeals):
        game = match.newgame()
        for iplay in range(BID_VARIANTS):
            deal = game.replaydeal() if iplay > 0 else game.newdeal()
            deal.play()
            if deal.caller:
                caller_idx   = deal.caller.team_idx
                tricks_made  = deal.score[caller_idx]
                ml_features = (len(deal.bids) - 1,  # bidder position, 0-7 (3 and 7 are dealer)
                               int(deal.play_alone),
                               *deal.caller.bid_features(deal.contract),
                               tricks_made)
                features.append(ml_features)
                #print("ML features: %s" % (list(ml_features)))

            #print(deal.stats)

        print("Score for game #%d: %s %d, %s %d" %
              (game.gameno,
               TEAMS[0]['name'], game.score[0],
               TEAMS[1]['name'], game.score[1]))
        game.compute_stats()

    with open(dsname + '.csv', 'w', newline='') as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerows(features)

    match.compute_stats()
    matchstats_agg = Match.matchstats.compute_agg()
    for k, v in matchstats_agg.items():
        print("%20s: %s" % (k, v))
    return 0

if __name__ == '__main__':
    main()
