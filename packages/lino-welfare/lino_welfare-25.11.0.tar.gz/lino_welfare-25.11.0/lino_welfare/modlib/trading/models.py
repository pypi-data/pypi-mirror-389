# -*- coding: UTF-8 -*-
# Copyright 2014 Rumma & Ko Ltd
# License: GNU Affero General Public License v3 (see file COPYING for details)
"""
Dummy module to satisfy `lino_xl.lib.courses` dependency
on a ``trading`` app.
"""

from lino.api import dd, rt


class CreateInvoice(dd.Dummy):
    pass


class InvoiceGenerator(dd.Dummy):
    pass


class InvoiceItemsByGenerator(dd.Dummy):
    pass
