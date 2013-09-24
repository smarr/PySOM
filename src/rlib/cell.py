#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Cell(object):

    def __init__(self, value):
        self._value = value

    def get(self):
        return self._value

    def set(self, value):
        self._value = value