# -*- coding: UTF-8 -*-
# Copyright 2012-2022 Rumma & Ko Ltd
# License: GNU Affero General Public License v3 (see file COPYING for details)
"""See :doc:`/specs/isip`.

"""

from lino.api import ad, _


class Plugin(ad.Plugin):
    "See :class:`lino.core.plugin.Plugin`."
    verbose_name = _("ISIP")
    needs_plugins = ['lino_welfare.modlib.integ']
