# -*- coding: UTF-8 -*-
# Copyright 2009-2025 Rumma & Ko Ltd
# License: GNU Affero General Public License v3 (see file COPYING for details)

from lino_welfare.projects.gerd.settings import *


class Site(Site):
    languages = 'de fr en'
    is_demo_site = True
    the_demo_date = 20140522
    # ignore_dates_after = datetime.date(2019, 05, 22)
    use_java = False
    webdav_protocol = 'webdav'

    # default_ui = "lino_react.react"

    # beid_protocol = 'beid'
    # migrations_package = "lino_welfare.projects.gerd.migrations"

    def get_plugin_configs(self):
        yield super().get_plugin_configs()
        # For testing. Not recommended in prod.
        yield ('extjs', 'autorefresh_seconds', 30)
        yield ('help', 'make_help_pages', True)
        yield ('help', 'include_useless', True)
        yield ('users', 'allow_online_registration', True)

    # def get_default_language(self):
    #     return 'de'


SITE = Site(globals())

DEBUG = True
