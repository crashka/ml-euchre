#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import environ
import os.path
from socket import gethostname
import logging
import logging.handlers
import random

import utils

######################
# Config/Environment #
######################

FILE_DIR      = os.path.dirname(os.path.realpath(__file__))
BASE_DIR      = os.path.realpath(os.path.join(FILE_DIR, os.pardir))
CONFIG_DIR    = 'config'
CONFIG_FILE   = 'config.yml'
CONFIG_PATH   = os.path.join(BASE_DIR, CONFIG_DIR, CONFIG_FILE)
cfg           = utils.Config(CONFIG_PATH)

param         = cfg.config('params')
env_param     = {'EUCHREDEBUG': 'debug'}
param.update({v: environ[k] for k, v in env_param.items() if k in environ})

###########
# Logging #
###########

# create logger (TODO: logging parameters belong in config file as well!!!)
LOGGER_NAME  = 'euchre'
LOG_DIR      = 'log'
LOG_FILE     = LOGGER_NAME + '.log'
LOG_PATH     = os.path.join(BASE_DIR, LOG_DIR, LOG_FILE)
LOG_FMTR     = logging.Formatter('%(asctime)s %(levelname)s [%(filename)s:%(lineno)s]: %(message)s')
LOG_FILE_MAX = 25000000
LOG_FILE_NUM = 50

dflt_hand = logging.handlers.RotatingFileHandler(LOG_PATH, 'a', LOG_FILE_MAX, LOG_FILE_NUM)
dflt_hand.setLevel(logging.DEBUG)
dflt_hand.setFormatter(LOG_FMTR)

dbg_hand = logging.StreamHandler()
dbg_hand.setLevel(logging.DEBUG)
dbg_hand.setFormatter(LOG_FMTR)

log = logging.getLogger(LOGGER_NAME)
log.setLevel(logging.INFO)
log.addHandler(dflt_hand)

##############
# Exceptions #
##############

class LogicError(Exception):
    pass

##################
# Basedata Setup #
##################

# LATER: only use configured value if debug/dev mode!!!
#random.seed(param.get('random_seed'))

def validate_basedata(basedata, offset = 0):
    """Make sure that the embedded index for base data elements matches the position
    within the data structure

    :return: void (failed assert on validation error)
    """
    for elem in basedata:
        assert elem['idx'] == basedata.index(elem) + offset

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

Cards (rank and level)
    9  - 0-3   (1)
    10 - 4-7   (2)
    J  - 8-11  (3)
    Q  - 12-15 (4)
    K  - 16-19 (5)
    A  - 20-23 (6)

    L  - 24-27 (7)
    R  - 28-31 (8)

Suit
    card % 4

Rank
    card // 4
"""

nine     = {'idx': 0, 'name': 'nine',  'level': 1, 'tag': '9'}
ten      = {'idx': 1, 'name': 'ten',   'level': 2, 'tag': '10'}
jack     = {'idx': 2, 'name': 'jack',  'level': 3, 'tag': 'J'}
queen    = {'idx': 3, 'name': 'queen', 'level': 4, 'tag': 'Q'}
king     = {'idx': 4, 'name': 'king',  'level': 5, 'tag': 'K'}
ace      = {'idx': 5, 'name': 'ace',   'level': 6, 'tag': 'A'}

RANKS    = [nine, ten, jack, queen, king, ace]

left     = {'idx': 6, 'name': 'left',  'level': 7, 'tag': 'L'}
right    = {'idx': 7, 'name': 'right', 'level': 8, 'tag': 'R'}

BOWERS   = [left, right]
ALLRANKS = RANKS + BOWERS

clubs    = {'idx': 0, 'name': 'clubs',    'tag': '\u2663'}
diamonds = {'idx': 1, 'name': 'diamonds', 'tag': '\u2666'}
hearts   = {'idx': 2, 'name': 'hearts',   'tag': '\u2665'}
spades   = {'idx': 3, 'name': 'spades',   'tag': '\u2660'}

SUITS    = [clubs, diamonds, hearts, spades]

CARDS = []
for idx in range(0, 24):
    rank = RANKS[idx // 4]
    suit = SUITS[idx % 4]
    card = {'idx'    : idx,
            'rank'   : rank,
            'suit'   : suit,
            'name'   : "%s of %s" % (rank['name'].capitalize(),
                                     suit['name'].capitalize()),
            'tag'    : "%s%s" % (rank['tag'], suit['tag']),
            'level'  : rank['level'],
            'sortkey': suit['idx'] * len(ALLRANKS) + rank['idx'] + 1
    }
    CARDS.append(card)

validate_basedata(RANKS)
validate_basedata(BOWERS, len(RANKS))
validate_basedata(SUITS)
validate_basedata(CARDS)

###############
# Table Seats #
###############

west        = {'idx': 0, 'name': 'West',  'tag': 'W'}
north       = {'idx': 1, 'name': 'North', 'tag': 'N'}
east        = {'idx': 2, 'name': 'East',  'tag': 'E'}
south       = {'idx': 3, 'name': 'South', 'tag': 'S'}

SEATS       = [west, north, east, south]

east_west   = {'idx': 0, 'name': 'East/West',   'tag': 'E/W'}
north_south = {'idx': 1, 'name': 'North/South', 'tag': 'N/S'}

TEAMS       = [east_west, north_south]

validate_basedata(SEATS)
validate_basedata(TEAMS)
