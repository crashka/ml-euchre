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

ENV_ID        = "%s:%s" % (gethostname(), BASE_DIR)
env           = cfg.config('environment').get(ENV_ID) or {}
env_overrides = {'database': 'CM_DBNAME'}
env.update({k: environ[v] for k, v in env_overrides.items() if v in environ})

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
