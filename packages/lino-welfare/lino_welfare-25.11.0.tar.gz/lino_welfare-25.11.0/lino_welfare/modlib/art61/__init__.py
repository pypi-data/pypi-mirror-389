# -*- coding: UTF-8 -*-
# Copyright 2015-2022 Rumma & Ko Ltd
# License: GNU Affero General Public License v3 (see file COPYING for details)
"""Adds functionality for managing "article 61 job
supplyments".  Technical specs see :ref:`welcht`.

"""

from lino import ad, _


class Plugin(ad.Plugin):
    verbose_name = _("Art61 job supplying")  # Mises à l'emploi art.61
    needs_plugins = ['lino_welfare.modlib.jobs', 'lino_xl.lib.cv']

    def setup_main_menu(self, site, user_type, m, ar=None):
        mg = site.plugins.integ
        m = m.add_menu(mg.app_label, mg.verbose_name)
        m.add_action('art61.MyContracts')

    def setup_config_menu(self, site, user_type, m, ar=None):
        mg = site.plugins.integ
        m = m.add_menu(mg.app_label, mg.verbose_name)
        m.add_action('art61.ContractTypes')

    def setup_explorer_menu(self, site, user_type, m, ar=None):
        mg = site.plugins.integ
        m = m.add_menu(mg.app_label, mg.verbose_name)
        m.add_action('art61.Contracts')
