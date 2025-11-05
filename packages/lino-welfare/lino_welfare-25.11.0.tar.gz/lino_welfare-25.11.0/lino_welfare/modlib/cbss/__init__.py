# -*- coding: UTF-8 -*-
# Copyright 2012-2020 Rumma & Ko Ltd
# License: GNU Affero General Public License v3 (see file COPYING for details)
"""Adds functionality to make CBSS requests.

Technical specs see :ref:`weleup`.

.. autosummary::
   :toctree:

    mixins
    choicelists
    utils
    fixtures.cbss_demo
    fixtures.cbss
    fixtures.purposes
    fixtures.sectors

.. rubric:: Plugin configuration

"""

import os
import shutil
from pathlib import Path

from lino import ad, _

HERE = Path(__file__).parent


class Plugin(ad.Plugin):
    """The descriptor for this plugin. See
    :class:`lino.core.plugin.Plugin`.

    """
    verbose_name = _("CBSS")

    needs_plugins = ['lino_welfare.modlib.integ']

    cbss_live_requests = False
    """Whether executing requests should try to really connect to the
    CBSS.  Real requests would fail with a timeout if run from behind
    an IP address that is not registered at the :term:`CBSS`.

    """

    # ~ cbss_environment = None
    cbss_environment = 'test'
    """
    Either `None` or one of 'test', 'acpt' or 'prod'.

    Setting this to `None` means that the cbss app is "inactive" even
    if installed.

    """

    def get_requirements(self, site):
        yield 'suds-py3'
        # as long as https://github.com/cackharot/suds-py3/pull/40 is not
        # released, we must use the development version:
        # yield 'git+https://github.com/karimabdelhakim/suds-py3#egg=suds-py3'

    def get_used_libs(self, html=None):
        try:
            import suds
            version = suds.__version__
        except ImportError:
            version = self.site.not_found_msg
        yield ("suds", version, "https://pypi.org/project/suds-py3/")

    def setup_main_menu(self, site, user_type, m, ar=None):
        mg = site.plugins.integ
        m = m.add_menu(mg.app_label, mg.verbose_name)
        m = m.add_menu(self.app_label, self.verbose_name)
        m.add_action('cbss.MyIdentifyPersonRequests')
        m.add_action('cbss.MyManageAccessRequests')
        m.add_action('cbss.MyRetrieveTIGroupsRequests')

    def setup_config_menu(self, site, user_type, m, ar=None):
        m = m.add_menu(self.app_label, self.verbose_name)
        m.add_action('cbss.Sectors')
        m.add_action('cbss.Purposes')

    def setup_explorer_menu(self, site, user_type, m, ar=None):
        m = m.add_menu(self.app_label, self.verbose_name)
        m.add_action('cbss.AllIdentifyPersonRequests')
        m.add_action('cbss.AllManageAccessRequests')
        m.add_action('cbss.AllRetrieveTIGroupsRequests')

    def on_initdb(self, site, verbosity=1):
        from lino_welfare.modlib.cbss.utils import CBSS_ENVS
        environment = site.plugins.cbss.cbss_environment
        if not environment:
            return  # silently return

        if environment not in CBSS_ENVS:
            raise Exception(
                "Invalid `cbss_environment` %r: must be empty or one of %s." %
                (environment, CBSS_ENVS))

        context = dict(cbss_environment=environment)

        def make_wsdl(template, parts):
            fn = site.media_root.joinpath(*parts)
            # fn = os.path.join(settings.MEDIA_ROOT, *parts)
            if fn.exists():
                if fn.stat().st_mtime > site.kernel.lino_version:
                    site.logger.debug(
                        "NOT generating %s because it is newer than the code.",
                        fn)
                    return
            # print("20230823", fn)
            s = (HERE / 'WSDL' / template).read_text()
            # s = open(HERE / 'WSDL' / template).read()
            s = s % context
            site.makedirs_if_missing(os.path.dirname(fn))
            fn.write_text(s)
            # open(fn, 'wt').write(s)
            site.logger.debug("Generated %s for environment %r.", fn,
                              environment)

        # v1 was stopped in March 2019
        # make_wsdl('RetrieveTIGroups-v1.wsdl', RetrieveTIGroupsRequest.wsdl_parts)
        make_wsdl('RetrieveTIGroups-v2.wsdl',
                  site.models.cbss.RetrieveTIGroupsRequest.wsdl_parts)
        make_wsdl('WebServiceConnector.wsdl',
                  site.models.cbss.SSDNRequest.wsdl_parts)
        # make_wsdl('TestConnectionService.wsdl',TestConnectionRequest.wsdl_parts)

        # The following xsd files are needed, unmodified but in the same directory
        # for fn in 'RetrieveTIGroupsV3.xsd', 'rn25_Release201104.xsd', 'TestConnectionServiceV1.xsd':
        # for fn in 'RetrieveTIGroupsV5.xsd', 'rn25_Release201411.xsd':
        for fn in ['be']:
            src = HERE / 'XSD' / fn
            target = site.media_root / 'cache' / 'wsdl' / fn
            if not target.exists():
                # shutil.copy(src, target)
                # site.logger.info("Copying %s to %s.", src, target)
                shutil.copytree(src, target)
            # else:
            #     site.logger.info("Directory %s already exists.", src)
