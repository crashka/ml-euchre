#!/usr/bin/env python
# -*- coding: utf-8 -*-

from core import log

def play(hand):
    """
    :return: Card
    """
    # TEMP: for now, just return first card (remove from hand)!!!
    return hand.cards.pop(0)
