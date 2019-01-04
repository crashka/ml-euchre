#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
