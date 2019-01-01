# -*- coding: utf-8 -*-

import logging

from core import log
from utils import prettyprint

#############
# Constants #
#############

NCARDS = 9
NPOS   = 8
NSEATS = 4
NSUITS = 3

###############
# Match Stats #
###############

class MatchStats(object):
    """This structure tracking team scoring across matches
    """
    def __init__(self):
        """
        """
        self.matches       = [0, 0]
        self.games         = [0, 0]
        self.tricks        = [0, 0]
        self.deals         = [0, 0]
        self.passes        = [0, 0]
        self.bids          = [0, 0]
        self.makes         = [0, 0]
        self.make_alls     = [0, 0]
        self.euchres       = [0, 0]
        self.bid_by_pos    = [[0] * NPOS,   [0] * NPOS]
        self.make_by_pos   = [[0] * NPOS,   [0] * NPOS]
        self.mkall_by_pos  = [[0] * NPOS,   [0] * NPOS]
        self.euch_by_pos   = [[0] * NPOS,   [0] * NPOS]
        self.pass_by_card  = [[0] * NCARDS, [0] * NCARDS]
        self.bid_by_card   = [[0] * NCARDS, [0] * NCARDS]
        self.make_by_card  = [[0] * NCARDS, [0] * NCARDS]
        self.mkall_by_card = [[0] * NCARDS, [0] * NCARDS]
        self.euch_by_card  = [[0] * NCARDS, [0] * NCARDS]
        self.bid_by_suit   = [[0] * NSUITS, [0] * NSUITS]
        self.make_by_suit  = [[0] * NSUITS, [0] * NSUITS]
        self.mkall_by_suit = [[0] * NSUITS, [0] * NSUITS]
        self.euch_by_suit  = [[0] * NSUITS, [0] * NSUITS]

    def update(self, match):
        """
        """
        if match.winner:
            self.matches[match.winner['idx']] += 1
        for i in range(2):
            self.games[i]       += match.games_won[i]
            self.tricks[i]      += match.teamstats[i].ntrk
            self.deals[i]       += match.teamstats[i].ndeal
            self.passes[i]      += match.teamstats[i].npass
            self.bids[i]        += match.teamstats[i].nbid
            self.makes[i]       += match.teamstats[i].nmake
            self.make_alls[i]   += match.teamstats[i].nall
            self.euchres[i]     += match.teamstats[i].neuch
            for j in range(NPOS):
                self.bid_by_pos[i][j]    += match.teamstats[i].bid_by_pos[j]
                self.make_by_pos[i][j]   += match.teamstats[i].make_by_pos[j]
                self.mkall_by_pos[i][j]  += match.teamstats[i].all_by_pos[j]
                self.euch_by_pos[i][j]   += match.teamstats[i].euch_by_pos[j]
            for j in range(NCARDS):
                self.pass_by_card[i][j]  += match.teamstats[i].pass_by_card[j]
                self.bid_by_card[i][j]   += match.teamstats[i].bid_by_card[j]
                self.make_by_card[i][j]  += match.teamstats[i].make_by_card[j]
                self.mkall_by_card[i][j] += match.teamstats[i].all_by_card[j]
                self.euch_by_card[i][j]  += match.teamstats[i].euch_by_card[j]
            for j in range(NSUITS):
                self.bid_by_suit[i][j]   += match.teamstats[i].bid_by_suit[j]
                self.make_by_suit[i][j]  += match.teamstats[i].make_by_suit[j]
                self.mkall_by_suit[i][j] += match.teamstats[i].all_by_suit[j]
                self.euch_by_suit[i][j]  += match.teamstats[i].euch_by_suit[j]

    def compute_agg(self):
        """
        """
        def pct_tref(stat, ref, prec = 2, nan = -1):
            return [round(stat[i] / ref[i] * 100.0, prec) if ref[i] else nan \
                    for i in range(2)]

        def pct_tot(stat, tot, prec = 2, nan = -1):
            nvals = len(stat[0])
            return [[round(stat[i][j] / tot[i] * 100.0, prec) if tot[i] else nan \
                     for j in range(nvals)] \
                    for i in range(2)]

        def pct_ref(stat, ref, prec = 2, nan = -1):
            nvals = len(stat[0])
            return [[round(stat[i][j] / ref[i][j] * 100.0, prec) if ref[i][j] else nan \
                     for j in range(nvals)] \
                    for i in range(2)]

        agg = self.__dict__.copy()
        agg.update({
            # overall team percentages
            'pass_pct'          : pct_tref(self.passes,       self.deals),
            'bid_pct'           : pct_tref(self.bids,         self.deals),
            'make_pct'          : pct_tref(self.makes,        self.bids),
            'mkall_pct'         : pct_tref(self.make_alls,    self.bids),
            'euchre_pct'        : pct_tref(self.euchres,      self.bids),
            # bid/result against total occurrences
            'pct_bid_by_pos'    : pct_tot(self.bid_by_pos,    self.bids),
            'pct_make_by_pos'   : pct_tot(self.make_by_pos,   self.makes),
            'pct_mkall_by_pos'  : pct_tot(self.mkall_by_pos,  self.make_alls),
            'pct_euchre_by_pos' : pct_tot(self.euch_by_pos,   self.euchres),
            # result against bids
            'make_pct_by_pos'   : pct_ref(self.make_by_pos,   self.bid_by_pos),
            'mkall_pct_by_pos'  : pct_ref(self.mkall_by_pos,  self.bid_by_pos),
            'euchre_pct_by_pos' : pct_ref(self.euch_by_pos,   self.bid_by_pos),
            # bid/result against total occurrences
            'pct_pass_by_card'  : pct_tot(self.pass_by_card,  self.passes),
            'pct_bid_by_card'   : pct_tot(self.bid_by_card,   self.bids),
            'pct_make_by_card'  : pct_tot(self.make_by_card,  self.makes),
            'pct_mkall_by_card' : pct_tot(self.mkall_by_card, self.make_alls),
            'pct_euchre_by_card': pct_tot(self.euch_by_card,  self.euchres),
            # result against bids
            'make_pct_by_card'  : pct_ref(self.make_by_card,  self.bid_by_card),
            'mkall_pct_by_card' : pct_ref(self.mkall_by_card, self.bid_by_card),
            'euchre_pct_by_card': pct_ref(self.euch_by_card,  self.bid_by_card),
            # bid/result against total occurrences
            'pct_bid_by_suit'   : pct_tot(self.bid_by_suit,   self.bids),
            'pct_make_by_suit'  : pct_tot(self.make_by_suit,  self.makes),
            'pct_mkall_by_suit' : pct_tot(self.mkall_by_suit, self.make_alls),
            'pct_euchre_by_suit': pct_tot(self.euch_by_suit,  self.euchres),
            # result against bids
            'make_pct_by_suit'  : pct_ref(self.make_by_suit,  self.bid_by_suit),
            'mkall_pct_by_suit' : pct_ref(self.mkall_by_suit, self.bid_by_suit),
            'euchre_pct_by_suit': pct_ref(self.euch_by_suit,  self.bid_by_suit),
        })
        return agg

##############
# Play Stats #
##############

class PlayStats(object):
    """This structure is used for tracking stats at the game level, as well as
    rolling up stats to the match level
    """
    def __init__(self):
        """
        """
        self.ndeal = 0
        self.npass = 0
        self.nbid  = 0
        self.nmake = 0
        self.nall  = 0
        self.neuch = 0
        self.ntrk  = 0
        self.pass_by_card = [0] * NCARDS
        self.bid_by_card  = [0] * NCARDS
        self.bid_by_pos   = [0] * NPOS
        self.bid_by_seat  = [0] * NSEATS
        self.bid_by_suit  = [0] * NSUITS
        self.make_by_card = [0] * NCARDS
        self.make_by_pos  = [0] * NPOS
        self.make_by_seat = [0] * NSEATS
        self.make_by_suit = [0] * NSUITS
        self.all_by_card  = [0] * NCARDS
        self.all_by_pos   = [0] * NPOS
        self.all_by_seat  = [0] * NSEATS
        self.all_by_suit  = [0] * NSUITS
        self.euch_by_card = [0] * NCARDS
        self.euch_by_pos  = [0] * NPOS
        self.euch_by_seat = [0] * NSEATS
        self.euch_by_suit = [0] * NSUITS
        self.trks_by_card = [0] * NCARDS
        self.trks_by_pos  = [0] * NPOS
        self.trks_by_seat = [0] * NSEATS
        self.trks_by_suit = [0] * NSUITS
        self.pts_by_card  = [0] * NCARDS
        self.pts_by_pos   = [0] * NPOS
        self.pts_by_seat  = [0] * NSEATS
        self.pts_by_suit  = [0] * NSUITS
        self.tpts_by_card = [0] * NCARDS
        self.tpts_by_pos  = [0] * NPOS
        self.tpts_by_seat = [0] * NSEATS
        self.tpts_by_suit = [0] * NSUITS

    def update(self, dealstats):
        """
        :param dealstats: dict (see below for field keys)
        :return: void
        """
        self.ndeal += 1
        card = dealstats['turncard']
        pos  = dealstats['call_pos']
        if pos is None:
            self.npass += 1
            self.pass_by_card[card] += 1
            return

        seat = dealstats['call_seat']
        suit = dealstats['call_suit']
        trks = dealstats['tricks']
        pts  = dealstats['points']

        self.nbid += 1
        self.bid_by_card[card]  += 1
        self.bid_by_pos[pos]    += 1
        self.bid_by_seat[seat]  += 1
        self.bid_by_suit[suit]  += 1
        self.ntrk += trks
        self.trks_by_card[card] += trks
        self.trks_by_pos[pos]   += trks
        self.trks_by_seat[seat] += trks
        self.trks_by_suit[suit] += trks

        if pts > 0:
            self.nmake += 1
            self.make_by_card[card] += 1
            self.make_by_pos[pos]   += 1
            self.make_by_seat[seat] += 1
            self.make_by_suit[suit] += 1
            if pts > 1:
                self.nall += 1
                self.all_by_card[card] += 1
                self.all_by_pos[pos]   += 1
                self.all_by_seat[seat] += 1
                self.all_by_suit[suit] += 1
            self.pts_by_card[card]  += pts
            self.pts_by_pos[pos]    += pts
            self.pts_by_seat[seat]  += pts
            self.pts_by_suit[suit]  += pts
            self.tpts_by_card[card] += pts
            self.tpts_by_pos[pos]   += pts
            self.tpts_by_seat[seat] += pts
            self.tpts_by_suit[suit] += pts
        elif pts < 0:
            self.neuch += 1
            self.euch_by_card[card] += 1
            self.euch_by_pos[pos]   += 1
            self.euch_by_seat[seat] += 1
            self.euch_by_suit[suit] += 1
            self.tpts_by_card[card] += -pts
            self.tpts_by_pos[pos]   += -pts
            self.tpts_by_seat[seat] += -pts
            self.tpts_by_suit[suit] += -pts

    def rollup(self, other):
        """
        :param other: GameStats
        :return: void
        """
        self.ndeal += other.ndeal
        self.npass += other.npass
        self.nbid  += other.nbid
        self.nmake += other.nmake
        self.nall  += other.nall
        self.neuch += other.neuch
        self.ntrk  += other.ntrk

        for card in range(NCARDS):
            self.pass_by_card[card] += other.pass_by_card[card]
            self.bid_by_card[card]  += other.bid_by_card[card]
            self.make_by_card[card] += other.make_by_card[card]
            self.all_by_card[card]  += other.all_by_card[card]
            self.trks_by_card[card] += other.trks_by_card[card]
            self.pts_by_card[card]  += other.pts_by_card[card]
            self.tpts_by_card[card] += other.tpts_by_card[card]
            self.euch_by_card[card] += other.euch_by_card[card]

        for pos in range(NPOS):
            self.bid_by_pos[pos]    += other.bid_by_pos[pos]
            self.make_by_pos[pos]   += other.make_by_pos[pos]
            self.all_by_pos[pos]    += other.all_by_pos[pos]
            self.trks_by_pos[pos]   += other.trks_by_pos[pos]
            self.pts_by_pos[pos]    += other.pts_by_pos[pos]
            self.tpts_by_pos[pos]   += other.tpts_by_pos[pos]
            self.euch_by_pos[pos]   += other.euch_by_pos[pos]

        for seat in range(NSEATS):
            self.bid_by_seat[seat]  += other.bid_by_seat[seat]
            self.make_by_seat[seat] += other.make_by_seat[seat]
            self.all_by_seat[seat]  += other.all_by_seat[seat]
            self.trks_by_seat[seat] += other.trks_by_seat[seat]
            self.pts_by_seat[seat]  += other.pts_by_seat[seat]
            self.tpts_by_seat[seat] += other.tpts_by_seat[seat]
            self.euch_by_seat[seat] += other.euch_by_seat[seat]

        for suit in range(NSUITS):
            self.bid_by_suit[suit]  += other.bid_by_suit[suit]
            self.make_by_suit[suit] += other.make_by_suit[suit]
            self.all_by_suit[suit]  += other.all_by_suit[suit]
            self.trks_by_suit[suit] += other.trks_by_suit[suit]
            self.pts_by_suit[suit]  += other.pts_by_suit[suit]
            self.tpts_by_suit[suit] += other.tpts_by_suit[suit]
            self.euch_by_suit[suit] += other.euch_by_suit[suit]
