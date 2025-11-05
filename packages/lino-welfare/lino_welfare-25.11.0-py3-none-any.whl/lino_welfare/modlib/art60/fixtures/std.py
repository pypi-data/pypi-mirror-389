# -*- coding: UTF-8 -*-
# Copyright 2015-2022 Rumma & Ko Ltd
# License: GNU Affero General Public License v3 (see file COPYING for details)
"""Adds a default contract type for art60.

"""

from lino.api import dd, rt


def objects():

    #     CT = rt.models.jobs.ContractType
    #     yield CT(**dd.str2kw('name', rt.models.art60.Contract._meta.verbose_name))

    ContentType = rt.models.contenttypes.ContentType
    ExcerptType = rt.models.excerpts.ExcerptType
    Contract = rt.models.art60.Contract

    yield ExcerptType(
        build_method='appypdf',
        template='Default.odt',
        # body_template='contract.body.html',
        # certifying=True,
        primary=True,
        content_type=ContentType.objects.get_for_model(Contract),
        **dd.str2kw('name', Contract._meta.verbose_name))
