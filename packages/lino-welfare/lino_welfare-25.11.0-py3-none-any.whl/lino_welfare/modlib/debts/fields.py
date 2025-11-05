# -*- coding: UTF-8 -*-
# Copyright 2012-2023 Rumma & Ko Ltd
# License: GNU Affero General Public License v3 (see file COPYING for details)

from django.db import models

from lino.api import _


class PeriodsField(models.DecimalField):

    def __init__(self, *args, **kwargs):
        defaults = dict(
            blank=True,
            default=1,
            help_text=_("""\
For how many months the entered amount counts.
For example 1 means a monthly amount, 12 a yearly amount."""),
            #~ max_length=3,
            max_digits=3,
            decimal_places=0,
        )
        defaults.update(kwargs)
        super().__init__(*args, **defaults)
