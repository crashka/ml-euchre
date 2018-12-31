# -*- coding: utf-8 -*-

import logging

from core import log
from utils import prettyprint

#########
# Stats #
#########

class GameStats(object):
    """This structure is used for tracking stats at the game level, as well as
    rolling up stats to the match level
    """
    def __init__(self):
        """
        """
        self.npass = 0
        self.nbid  = 0
        self.nmake = 0
        self.nall  = 0
        self.neuch = 0
        self.pass_by_card = [0] * 9
        self.bid_by_card  = [0] * 9
        self.bid_by_pos   = [0] * 8
        self.bid_by_seat  = [0] * 4
        self.bid_by_suit  = [0] * 3
        self.make_by_card = [0] * 9
        self.make_by_pos  = [0] * 8
        self.make_by_seat = [0] * 4
        self.make_by_suit = [0] * 3
        self.all_by_card  = [0] * 9
        self.all_by_pos   = [0] * 8
        self.all_by_seat  = [0] * 4
        self.all_by_suit  = [0] * 3
        self.euch_by_card = [0] * 9
        self.euch_by_pos  = [0] * 8
        self.euch_by_seat = [0] * 4
        self.euch_by_suit = [0] * 3
        self.pts_by_card  = [0] * 9
        self.pts_by_pos   = [0] * 8
        self.pts_by_seat  = [0] * 4
        self.pts_by_suit  = [0] * 3
        self.tpts_by_card = [0] * 9
        self.tpts_by_pos  = [0] * 8
        self.tpts_by_seat = [0] * 4
        self.tpts_by_suit = [0] * 3

    def log_agg(self, info = None, level = logging.INFO):
        """Logs stats at the INFO level by default

        :param info: [str] identifying information to print before stats
        :return: void
        """
        stats_agg = {
            'pct_make'         : self.nmake / self.nbid * 100.0,
            'pct_all'          : self.nall  / self.nbid * 100.0,
            'pct_euch'         : self.neuch / self.nbid * 100.0,
            'pct_bid_by_card'  : [self.bid_by_card[i]  / self.nbid  * 100.0 for i in range(9)],
            'pct_bid_by_pos'   : [self.bid_by_pos[i]   / self.nbid  * 100.0 for i in range(8)],
            'pct_bid_by_seat'  : [self.bid_by_seat[i]  / self.nbid  * 100.0 for i in range(4)],
            'pct_bid_by_suit'  : [self.bid_by_suit[i]  / self.nbid  * 100.0 for i in range(3)],
            'pct_make_by_card' : [self.make_by_card[i] / self.nmake * 100.0 for i in range(9)],
            'pct_make_by_pos'  : [self.make_by_pos[i]  / self.nmake * 100.0 for i in range(8)],
            'pct_make_by_seat' : [self.make_by_seat[i] / self.nmake * 100.0 for i in range(4)],
            'pct_make_by_suit' : [self.make_by_suit[i] / self.nmake * 100.0 for i in range(3)],
            'pct_all_by_card'  : [self.all_by_card[i]  / self.nall  * 100.0 for i in range(9)],
            'pct_all_by_pos'   : [self.all_by_pos[i]   / self.nall  * 100.0 for i in range(8)],
            'pct_all_by_seat'  : [self.all_by_seat[i]  / self.nall  * 100.0 for i in range(4)],
            'pct_all_by_suit'  : [self.all_by_suit[i]  / self.nall  * 100.0 for i in range(3)],
            'pct_euch_by_card' : [self.euch_by_card[i] / self.neuch * 100.0 for i in range(9)],
            'pct_euch_by_pos'  : [self.euch_by_pos[i]  / self.neuch * 100.0 for i in range(8)],
            'pct_euch_by_seat' : [self.euch_by_seat[i] / self.neuch * 100.0 for i in range(4)],
            'pct_euch_by_suit' : [self.euch_by_suit[i] / self.neuch * 100.0 for i in range(3)],
            'make_pct_by_card' : [self.make_by_card[i] / self.bid_by_card[i] * 100.0 \
                                  if self.bid_by_card[i] else None for i in range(9)],
            'make_pct_by_pos'  : [self.make_by_pos[i]  / self.bid_by_pos[i]  * 100.0 \
                                  if self.bid_by_pos[i] else None for i in range(8)],
            'make_pct_by_seat' : [self.make_by_seat[i] / self.bid_by_seat[i] * 100.0 \
                                  if self.bid_by_seat[i] else None for i in range(4)],
            'make_pct_by_suit' : [self.make_by_suit[i] / self.bid_by_suit[i] * 100.0 \
                                  if self.bid_by_suit[i] else None for i in range(3)],
            'all_pct_by_card'  : [self.all_by_card[i]  / self.bid_by_card[i] * 100.0 \
                                  if self.bid_by_card[i] else None for i in range(9)],
            'all_pct_by_pos'   : [self.all_by_pos[i]   / self.bid_by_pos[i]  * 100.0 \
                                  if self.bid_by_pos[i] else None for i in range(8)],
            'all_pct_by_seat'  : [self.all_by_seat[i]  / self.bid_by_seat[i] * 100.0 \
                                  if self.bid_by_seat[i] else None for i in range(4)],
            'all_pct_by_suit'  : [self.all_by_suit[i]  / self.bid_by_suit[i] * 100.0 \
                                  if self.bid_by_suit[i] else None for i in range(3)],
            'euch_pct_by_card' : [self.euch_by_card[i] / self.bid_by_card[i] * 100.0 \
                                  if self.bid_by_card[i] else None for i in range(9)],
            'euch_pct_by_pos'  : [self.euch_by_pos[i]  / self.bid_by_pos[i]  * 100.0 \
                                  if self.bid_by_pos[i] else None for i in range(8)],
            'euch_pct_by_seat' : [self.euch_by_seat[i] / self.bid_by_seat[i] * 100.0 \
                                  if self.bid_by_seat[i] else None for i in range(4)],
            'euch_pct_by_suit' : [self.euch_by_suit[i] / self.bid_by_suit[i] * 100.0 \
                                  if self.bid_by_suit[i] else None for i in range(3)],
            'pts_ratio_by_card': [self.pts_by_card[i] / self.tpts_by_card[i] * 100.0 \
                                  if self.tpts_by_card[i] else None for i in range(9)],
            'pts_ratio_by_pos' : [self.pts_by_pos[i] / self.tpts_by_pos[i] * 100.0 \
                                  if self.tpts_by_pos[i] else None for i in range(8)],
            'pts_ratio_by_seat': [self.pts_by_seat[i] / self.tpts_by_seat[i] * 100.0 \
                                  if self.tpts_by_seat[i] else None for i in range(4)],
            'pts_ratio_by_suit': [self.pts_by_suit[i] / self.tpts_by_suit[i] * 100.0 \
                                  if self.tpts_by_suit[i] else None for i in range(3)]
        }
        if info:
            log.log(level, info + ':')
        log.log(level, prettyprint(stats_agg, sort_keys=False, noprint=True))
