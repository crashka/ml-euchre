#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import environ
import os.path
from socket import gethostname
import logging
import logging.handlers
import random

from utils import Config

############################
# config/environment stuff #
############################

FILE_DIR      = os.path.dirname(os.path.realpath(__file__))
BASE_DIR      = os.path.realpath(os.path.join(FILE_DIR, os.pardir))
CONFIG_DIR    = 'config'
CONFIG_FILE   = 'config.yml'
CONFIG_PATH   = os.path.join(BASE_DIR, CONFIG_DIR, CONFIG_FILE)
cfg           = Config(CONFIG_PATH)

param         = cfg.config('params')
env_param     = {'EUCHRE_DEBUG': 'debug'}
param.update({v: environ[k] for k, v in env_param.items() if k in environ})

###########
# logging #
###########

# create logger (TODO: logging parameters belong in config file as well!!!)
LOGGER_NAME  = 'euchre'
LOG_DIR      = 'log'
LOG_FILE     = LOGGER_NAME + '.log'
LOG_PATH     = os.path.join(BASE_DIR, LOG_DIR, LOG_FILE)
LOG_FMTR     = logging.Formatter('%(asctime)s %(levelname)s [%(filename)s:%(lineno)s]: %(message)s')
LOG_FILE_MAX = 50000000
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

##################
# Basedata Setup #
##################

# LATER: only use configured value if debug/dev mode!!!
random.seed(param.get('random_seed'))

def validate_basedata(basedata):
    """Make sure that the embedded index for base data elements matches the position
    within the data structure

    :return: void (failed assert on validation error)
    """
    for elem in basedata:
        assert elem['idx'] == basedata.index(elem)

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

nine     = {'idx': 0, 'name': 'nine',  'tag': '9'}
ten      = {'idx': 1, 'name': 'ten',   'tag': '10'}
jack     = {'idx': 2, 'name': 'jack',  'tag': 'J'}
queen    = {'idx': 3, 'name': 'queen', 'tag': 'Q'}
king     = {'idx': 4, 'name': 'king',  'tag': 'K'}
ace      = {'idx': 5, 'name': 'ace',   'tag': 'A'}

RANKS    = [nine, ten, jack, queen, king, ace]

clubs    = {'idx': 0, 'name': 'clubs',    'tag': '\u2663'}
diamonds = {'idx': 1, 'name': 'diamonds', 'tag': '\u2666'}
hearts   = {'idx': 2, 'name': 'hearts',   'tag': '\u2665'}
spades   = {'idx': 3, 'name': 'spades',   'tag': '\u2660'}

SUITS    = [clubs, diamonds, hearts, spades]

CARDS = []
for idx in range(0, 24):
    rank = RANKS[idx // 4]
    suit = SUITS[idx % 4]
    card = {'idx'  : idx,
            'rank' : rank,
            'suit' : suit,
            'name' : "%s of %s" % (rank['name'].capitalize(),
                                   suit['name'].capitalize()),
            'tag'  : "%s%s" % (rank['tag'], suit['tag']),
            'level': rank['idx'] + 1
    }
    CARDS.append(card)

validate_basedata(RANKS)
validate_basedata(SUITS)
validate_basedata(CARDS)

###############
# Table Seats #
###############

west        = {'idx': 0, 'name': 'west',  'tag': 'W'}
north       = {'idx': 1, 'name': 'north', 'tag': 'N'}
east        = {'idx': 2, 'name': 'east',  'tag': 'E'}
south       = {'idx': 3, 'name': 'south', 'tag': 'S'}

SEATS       = [west, north, east, south]

east_west   = {'idx': 0, 'name': 'east/west',   'tag': 'E/W'}
north_south = {'idx': 1, 'name': 'north/south', 'tag': 'N/S'}

TEAMS       = [east_west, north_south]

validate_basedata(SEATS)
validate_basedata(TEAMS)
