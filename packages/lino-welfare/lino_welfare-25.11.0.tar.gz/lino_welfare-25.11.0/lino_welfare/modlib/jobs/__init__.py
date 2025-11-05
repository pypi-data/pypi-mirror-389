# -*- coding: UTF-8 -*-
# Copyright 2013-2022 Rumma & Ko Ltd
# License: GNU Affero General Public License v3 (see file COPYING for details)
"""Adds functionality for managing job supply projects.

End-user docs: :ref:`ug.plugins.jobs`.
Developer docs: :doc:`/specs/jobs`.

"""

from lino import ad, _


class Plugin(ad.Plugin):
    "See :class:`lino.core.plugin.Plugin`."
    # verbose_name = _("Art.60§7")
    verbose_name = _("Job supplying")  # Mise à l'emploi
    needs_plugins = ['lino_welfare.modlib.isip']
    with_employer_model = False

    def get_quicklinks(self):
        if not self.site.is_installed('art60'):
            yield "jobs.MyContracts"

    def setup_main_menu(self, site, user_type, m, ar=None):
        if not self.site.is_installed('art60'):
            mg = site.plugins.integ
            m = m.add_menu(mg.app_label, mg.verbose_name)
            m.add_action('jobs.MyContracts')
