# -*- coding: UTF-8 -*-
# Copyright 2013-2022 Rumma & Ko Ltd
# License: GNU Affero General Public License v3 (see file COPYING for details)

from lino import logger
import datetime

ONE_DAY = datetime.timedelta(days=1)

from django.db import models
from django.utils.translation import pgettext_lazy as pgettext

from lino.api import dd, rt, _

from lino.modlib.system.choicelists import DurationUnits
from lino_welfare.modlib.isip.mixins import (ContractPartnerBase, ContractBase)


class CandidatureStates(dd.ChoiceList):
    help_text = _("The possible states of a candidature.")
    verbose_name = _("Candidature state")
    verbose_name_plural = _("Candidature states")


add = CandidatureStates.add_item
add('10', pgettext("jobs", "Active"), 'active')
add('20', _("Probation"), 'probation')
add('25', _("Probation failed"), 'failed')
add('27', pgettext("jobs", "Working"), 'working')
add('30', pgettext("jobs", "Inactive"), 'inactive')

# 20221002: The JobSupplyment mixin no longer includes isip.ContractPartnerBase
# and isip.ContractBase


class JobSupplyment(dd.Model):

    class Meta:
        abstract = True

    duration = models.IntegerField(_("duration (days)"),
                                   blank=True,
                                   null=True,
                                   default=None)
    remark = models.TextField(_("Remark"), blank=True)

    @dd.chooser()
    def ending_choices(cls):
        return rt.models.isip.ContractEnding.objects.filter(use_in_jobs=True)

    def full_clean(self, *args, **kw):
        if self.client_id is not None:
            if self.applies_from:
                if self.client.birth_date:

                    def duration(refdate):
                        if type(refdate) != datetime.date:
                            raise Exception("%r is not a date!" % refdate)
                        delta = refdate - self.client.birth_date.as_date()
                        age = delta.days / 365
                        if age < 36:
                            return 312
                        elif age < 50:
                            return 468
                        else:
                            return 624

                    if self.duration is None:
                        if self.applies_until:
                            self.duration = duration(self.applies_until)
                        else:
                            self.duration = duration(self.applies_from)
                            self.applies_until = self.applies_from + \
                                datetime.timedelta(days=self.duration)

                if self.duration and not self.applies_until:
                    # [NOTE1]
                    self.applies_until = DurationUnits.months.add_duration(
                        self.applies_from, int(self.duration / 26)) - ONE_DAY

        super(JobSupplyment, self).full_clean(*args, **kw)


JobSupplyment.set_widget_options('duration', width=10)
