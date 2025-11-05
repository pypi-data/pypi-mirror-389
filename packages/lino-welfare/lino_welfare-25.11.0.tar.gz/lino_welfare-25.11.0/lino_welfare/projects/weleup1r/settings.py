# -*- coding: UTF-8 -*-
# Copyright 2015-2023 Rumma & Ko Ltd
# License: GNU Affero General Public License v3 (see file COPYING for details)

from lino_welfare.projects.gerd.settings.demo import *


class Site(Site):
    default_ui = 'lino_react.react'
    # title = "Noi React demo"
    master_site = SITE


SITE = Site(globals())

# from django.utils.log import DEFAULT_LOGGING
# from pprint import pprint
# pprint(DEFAULT_LOGGING)
