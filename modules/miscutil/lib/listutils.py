# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
"""List utilities."""

__revision__ = "$Id$"

def get_mean(in_list):
    """ Take a list of numbers and return its average.
        If the list contents aren't numbers, return 0. """
    def add(x,y):
        return x+y
    try:
        total = reduce(add, in_list)
        average = total*1.0/len(in_list)
    except TypeError:
        average = 0
    return average

def get_mode(in_list):
    """ Take a list and return its mode. If there are many
        modes, return the first one encountered. """
    counts_dict = {}
    counts_dict.update((x, in_list.count(x)) for x in in_list)
    mode, mode_count = 0, 0
    for item, item_count in counts_dict.iteritems():
        if item_count > mode_count:
            mode = item
            mode_count = item_count
    return mode

def get_median(in_list):
    """ Take a list of numbers and return its median value.
        If the list has an even number of elements and we can't
        average the middle two, return the smaller one. """
    new_list = sorted(in_list)
    if len(new_list) % 2:
        return new_list[len(new_list)/2]
    else:
        try:
            return (new_list[(len(new_list)-1)/2] + new_list[(len(new_list)-1)/2 + 1])/2
        except TypeError:
            return new_list[(len(new_list)-1)/2]
