#!/usr/bin/env python
# -*- coding: utf-8 -*-

from playing import analyze

"""
Play Approach
    * Separate models for each position and trick
    * Separate models for calling and defending
        * Playing with partner vs. going alone
        * Defending against team vs. against loner

Play Features
    * Trick number
    * Play position (current trick, 0-3)
    * Loner position (relative position)
        * One-hot encoding (self, next seat, prev seat)
    * Caller (by team or relative position)
    * Turncard level (buried/picked-up, dealer pos, etc.)
    * Tricks won so far (by team or relative position)
    * Cards seen by suit (total)
        * Trump
        * Next
        * Green
        * Purple
    * Aces seen (total, non-trump)
    * Original hand features (from bidding)
    * Current hand features (scores)
        * Top trump (1 or more)
        * Second trump (2 or more)
        * Low trump (3 or more)
        * Top next (1 or more)
        * Low next (2 or more)
        * Top green (1 or more)
        * Low green (2 or more)
        * Top purple (1 or more)
        * Low purple (2 or more)
    * Current trick
        * Card led
            * Suit (trump, next, green/purple)
            * Level
        * Winning hand (relative position)
            * One-hot encoding (partner, next seat, prev seat)
        * Winning card
            * Suit (trump, next, green/purple)
            * Level
    * Card to play (one-hot encoded)
        * Lead (position 0)
            * Top trump
            * Second trump
            * Low trump
            * Top next
            * Low next
            * Top green
            * Low green
            * Top purple
            * Low purple
        * Play (position 1-3)
            * Follow high (to lead trick)
            * Follow highest (if choice)
            * Follow low (duck)
            * Trump high (to lead trick)
            * Trump highest (if choice)
            * Trump low
            * Throw off next
            * Throw off green
            * Throw off purple
    * Predict: tricks to win (total)

Play Learning
    * Use validated bidding model (or possibly rule-based bidding logic)
    * Lead (position 0)
        * Play scenario with each card (even if duplicate one-hot encodings)
    * Play (positions 1-3)
        * Play scenario with each legal card (even if duplicate one-hot encodings)
        * Maximum possible scenarios by trickno (tabulate actual legal runthroughs)
            * 1 - 525
            * 2 - 256
            * 3 - 81
            * 4 - 16
            * 5 - 1
"""

def play(hand, plays, winning):
    """
    * Use validated bidding model (or possibly rule-based bidding logic)
    * Lead (position 0)
        * Play scenario with each card (even if duplicate one-hot encodings)
    * Play (positions 1-3)
        * Play scenario with each legal card (even if duplicate one-hot encodings)
        * Maximum possible scenarios by trickno (tabulate actual legal runthroughs)
            * 1 - 525
            * 2 - 256
            * 3 - 81
            * 4 - 16
            * 5 - 1

    :param hand:
    :param plays: [(player, card), ...]
    :param winning: (player, card)
    :return: Card
    """
    # deal stats
    deal      = hand.deal
    trick_no  = len(deal.tricks) + 1
    play_pos  = len(plays)  # 0 = lead, etc.
    tru_idx   = deal.contract['idx']
    lead_card = plays[0][1] if plays else None

    if play_queue[play_pos] is None:
        play_queue[play_pos] = valid_plays(hand, lead_card)
    assert isinstance(play_queue[play_pos], list) and len(play_queue[play_pos]) > 0
    if play_pos < 3:
        # continue playing current card for pos
        play = play_queue[play_pos][0]
    else:
        # only one play for this card
        play = play_queue[play_pos].pop(0)
        # if done for this scenario, fix upstream positions
        if len(play_queue[play_pos]) == 0:
            play_queue[play_pos] = None
            for prev_pos in range(play_pos - 1, -1, -1):
                play_queue[prev_pos].pop(0)
                if len(play_queue[prev_pos]) > 0:
                    # have new card to play in this position
                    break
                play_queue[prev_pos] = None
            if play_queue[0] is None:
                # we are done
                play_queue = None
    # TODO: push play features onto stack, to be written with result of deal
    # (i.e. number of tricks for team) after every deal scenario; need to try
    # and smartly unwind stack for reuse (both playing positions/trick count,
    # as well as positional play features)!!!
    return play

def play_features(hand):
    """Return tuple of play features, for training and predicting

    * Trick number
    * Play position (current trick, 0-3)
    * Loner position (relative position)
        * One-hot encoding (self, next seat, prev seat)
    * Caller (by team or relative position)
    * Tricks won so far (by team or relative position)
    * Cards seen by suit (total)
        * Trump
        * Next
        * Green
        * Purple
    * Aces seen (total, non-trump)
    * Original hand features (from bidding)
    * Current hand features (scores)
        * Top trump (1 or more)
        * Second trump (2 or more)
        * Low trump (3 or more)
        * Top next (1 or more)
        * Low next (2 or more)
        * Top green (1 or more)
        * Low green (2 or more)
        * Top purple (1 or more)
        * Low purple (2 or more)
    * Current trick
        * Card led
            * Suit (trump, next, green/purple)
            * Level
        * Winning hand (relative position)
            * One-hot encoding (partner, next seat, prev seat)
        * Winning card
            * Suit (trump, next, green/purple)
            * Level
    * Card to play (one-hot encoded)
        * Lead (position 0)
            * Top trump
            * Second trump
            * Low trump
            * Top next
            * Low next
            * Top green
            * Low green
            * Top purple
            * Low purple
        * Play (position 1-3)
            * Follow high (to lead trick)
            * Follow highest (if choice)
            * Follow low (duck)
            * Trump high (to lead trick)
            * Trump highest (if choice)
            * Trump low
            * Throw off next
            * Throw off green
            * Throw off purple
    * Predict: tricks to win (total)

    :return: tuple (see above for elements)
    """
