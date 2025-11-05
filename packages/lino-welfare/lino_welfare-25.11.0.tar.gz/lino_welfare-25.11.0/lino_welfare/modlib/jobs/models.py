# -*- coding: UTF-8 -*-
# Copyright 2008-2022 Rumma & Ko Ltd
# License: GNU Affero General Public License v3 (see file COPYING for details)
# docs: https://welfare.lino-framework.org/specs/jobs.html

from lino import logger

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import force_str

from lino.api import dd, rt
from lino import mixins

from lino.utils.html import E
from lino.utils.report import Report

from lino_xl.lib.cv.mixins import SectorFunction

from lino_xl.lib.coachings.utils import only_coached_on, has_contracts_filter
from lino_xl.lib.clients.choicelists import ClientEvents, ObservedEvent

from lino_welfare.modlib.isip.mixins import ContractPartnerBase, ContractBase
from lino_welfare.modlib.isip.mixins import ContractTypeBase

from lino_welfare.modlib.pcsw.roles import SocialStaff, SocialUser, SocialCoordinator
from lino_welfare.modlib.integ.roles import IntegUser

from .mixins import JobSupplyment
from .mixins import CandidatureStates

contacts = dd.resolve_app('contacts')
isip = dd.resolve_app('isip')


class Schedule(mixins.BabelNamed):
    """List of choices for `jobs.Contract.schedule` field."""

    class Meta:
        verbose_name = _("Work Schedule")
        verbose_name_plural = _('Work Schedules')


class JobProvider(contacts.Company):

    # TODO: Rename this to `JobSupplier`?

    class Meta:
        app_label = 'jobs'
        verbose_name = _("Job provider")
        verbose_name_plural = _('Job providers')

    is_social = models.BooleanField(_("Social economy"), default=False)

    def disable_delete(self, ar=None):
        # skip the is_imported_partner test
        return super(contacts.Partner, self).disable_delete(ar)


if dd.get_plugin_setting('jobs', 'with_employer_model'):

    class Employer(contacts.Company):

        class Meta:
            app_label = 'jobs'
            verbose_name = _("Employer")
            verbose_name_plural = _('Employers')

        is_social = models.BooleanField(_("Social economy"), default=False)


class ContractType(
        ContractTypeBase,  # mixins.PrintableType,
        mixins.Referrable):
    """This is the homologue of :class:`isip.ContractType
    <lino_welfare.modlib.isip.models.ContractType>` (see there for
    general documentation).

    They are separated tables because ISIP contracts are in practice
    very different from JOBS contracts, and also their types should
    not be mixed.

    """

    preferred_foreignkey_width = 20

    templates_group = 'jobs/Contract'

    class Meta:
        verbose_name = _("Art60§7 job supplyment type")
        verbose_name_plural = _('Art60§7 job supplyment types')
        ordering = ['name']

    # ref = models.CharField(_("Reference"), max_length=20, blank=True)


if not dd.is_installed("art60"):

    # Remains here for backward compat. Still used in weleup.

    class Contract(ContractPartnerBase, ContractBase, JobSupplyment):
        """An **Art60§7 job supplyment** is a contract bla bla...

.. attribute:: duration

    If :attr:`applies_from` and :attr:`duration` are set, then the
    default value for :attr:`applies_until` is computed assuming 26
    workdays per month:

    - duration `312` -> 12 months
    - duration `468` -> 18 months
    - duration `624` -> 24 months

    """

        class Meta:
            verbose_name = _("Art60§7 job supplyment")
            verbose_name_plural = _('Art60§7 job supplyments')

        quick_search_fields = 'job__name client__name '\
                              'company__name client__national_id'

        company = dd.ForeignKey(
            "contacts.Company",
            related_name="%(app_label)s_%(class)s_set_by_company",
            verbose_name=_("Organization"),
            blank=True,
            null=True)

        type = dd.ForeignKey(
            "jobs.ContractType",
            verbose_name=_("Type"),
            related_name="%(app_label)s_%(class)s_set_by_type",
            blank=True)

        job = dd.ForeignKey("jobs.Job")
        regime = dd.ForeignKey('cv.Regime',
                               blank=True,
                               null=True,
                               related_name="jobs_contracts")
        schedule = dd.ForeignKey('jobs.Schedule', blank=True, null=True)
        hourly_rate = dd.PriceField(_("hourly rate"), blank=True, null=True)
        refund_rate = models.CharField(_("refund rate"),
                                       max_length=200,
                                       blank=True)

        @dd.chooser()
        def company_choices(cls):
            return rt.models.jobs.JobProvider.objects.all()

        @dd.chooser(simple_values=True)
        def duration_choices(cls):
            return [312, 468, 624]

        @dd.chooser(simple_values=True)
        def refund_rate_choices(cls):
            return [
                "0%",
                "25%",
                "50%",
                "100%",
            ]

        def disabled_fields(self, ar):
            "As super, but add also job provider's company and type"
            df = super().disabled_fields(ar)
            if self.job_id is not None:
                if self.job.provider:
                    df.add('company')
                if self.job.contract_type:
                    df.add('type')
            return df

        def after_ui_save(self, ar, cw):
            super().after_ui_save(ar, cw)
            if self.job_id is not None:
                if self.applies_until and self.applies_until > dd.today():
                    n = 0
                    for candi in self.client.candidature_set.filter(
                            state=CandidatureStates.active):
                        candi.state = CandidatureStates.inactive
                        candi.save()
                        n += 1
                    if n:
                        ar.debug(
                            str(
                                _("(%d candidatures have been marked inactive)"
                                  )) % n)
                        ar.set_response(alert=_("Success"))

        def full_clean(self, *args, **kw):
            if self.job_id is not None:
                if self.job.provider is not None:
                    self.company = self.job.provider
                if self.job.contract_type is not None:
                    self.type = self.job.contract_type
                if self.hourly_rate is None:
                    self.hourly_rate = self.job.hourly_rate

            super().full_clean(*args, **kw)

        @classmethod
        def get_certifiable_fields(cls):
            return ('client job company contact_person contact_role type '
                    'applies_from applies_until duration '
                    'language schedule regime hourly_rate refund_rate '
                    'reference_person responsibilities '
                    'user user_asd exam_policy '
                    'date_decided date_issued ')


# dd.update_field(Contract, 'user', verbose_name=_("responsible (IS)"))


class Offer(SectorFunction):
    "A Job Offer"

    class Meta:
        verbose_name = _("Job Offer")
        verbose_name_plural = _('Job Offers')
        ordering = ['name']

    name = models.CharField(max_length=100, blank=True, verbose_name=_("Name"))

    provider = dd.ForeignKey(JobProvider, blank=True, null=True)

    selection_from = models.DateField(_("selection from"),
                                      blank=True,
                                      null=True)
    selection_until = models.DateField(_("selection until"),
                                       blank=True,
                                       null=True)
    start_date = models.DateField(_("start date"), blank=True, null=True)

    remark = dd.RichTextField(blank=True,
                              verbose_name=_("Remark"),
                              format='plain')

    def __str__(self):
        if self.name:
            return self.name
        return '%s @ %s' % (self.function, self.provider)


class Job(SectorFunction):
    """
    A **job** is a place where a Client can work.

    """

    preferred_foreignkey_width = 20

    class Meta:
        verbose_name = _("Job")
        verbose_name_plural = _('Jobs')
        ordering = ['name', 'provider__name']

    name = models.CharField(max_length=100, verbose_name=_("Name"))
    type = dd.ForeignKey("jobs.JobType",
                         verbose_name=_("Job Type"),
                         blank=True,
                         null=True)
    provider = dd.ForeignKey('jobs.JobProvider', blank=True, null=True)
    if dd.is_installed("art60"):
        workplace = dd.ForeignKey("contacts.Company",
            verbose_name=_("Workplace"),
            related_name="art60_workplaces",
            blank=True, null=True)
    else:
        workplace = dd.DummyField()

    contract_type = dd.ForeignKey('jobs.ContractType',
                                  verbose_name=_("Contract Type"),
                                  blank=True,
                                  null=True)
    hourly_rate = dd.PriceField(_("hourly rate"), blank=True, null=True)
    capacity = models.IntegerField(_("capacity"), default=1)
    remark = models.TextField(blank=True, verbose_name=_("Remark"))

    def __str__(self):
        if self.provider:
            return _('%(job)s at %(provider)s') % dict(
                job=self.name, provider=self.provider.name)
        return self.name

    @dd.chooser()
    def workplace_choices(cls, provider):
        return rt.models.contacts.Company.objects.filter(job_provider=provider)

    def unused_disabled_fields(self, ar):
        # disabled 20140519. must convert this to Certifiable
        if self.contract_set.filter(build_time__isnull=False).count():
            return set(('contract_type', 'provider'))
        return set()

    #~ @dd.chooser()
    #~ def provider_choices(cls):
    #~ return CourseProviders.request().queryset

    #~ @classmethod
    #~ def setup_report(model,rpt):
    #~ rpt.add_action(DirectPrintAction('candidates',_("List of candidates"),'courses/candidates.odt'))
    #~ rpt.add_action(DirectPrintAction('participants',_("List of participants"),'courses/participants.odt'))

    #~ def get_print_language(self,pm):
    #~ "Used by DirectPrintAction"
    #~ return DEFAULT_LANGUAGE

    #~ def participants(self):
    #~ u"""
    #~ Liste von :class:`CourseRequest`-Instanzen,
    #~ die in diesem Kurs eingetragen sind.
    #~ """
    #~ return ParticipantsByCourse().request(master_instance=self)

    #~ def candidates(self):
    #~ u"""
    #~ Liste von :class:`CourseRequest`-Instanzen,
    #~ die noch in keinem Kurs eingetragen sind, aber für diesen Kurs in Frage
    #~ kommen.
    #~ """
    #~ return CandidatesByCourse().request(master_instance=self)


class Candidature(SectorFunction):
    """A candidature is when a client applies for a known :class:`Job`.

    .. attribute:: art60
    .. attribute:: art61

        Whether an art.61 (art.60) contract can satisfy this
        candidature. Check at least one of them.

    """

    class Meta:
        verbose_name = _("Job Candidature")
        verbose_name_plural = _('Job Candidatures')
        get_latest_by = 'date_submitted'

    person = dd.ForeignKey('pcsw.Client')

    job = dd.ForeignKey("jobs.Job", blank=True, null=True)

    date_submitted = models.DateField(
        _("date submitted"),
        help_text=_("Date when the IA introduced this candidature."))

    remark = models.TextField(blank=True, null=True, verbose_name=_("Remark"))

    state = CandidatureStates.field(default='active')

    art60 = models.BooleanField(
        _("Art.60"),
        default=False,
        help_text=_(
            "Whether an art.60 contract can satisfy this candidature."))

    art61 = models.BooleanField(
        _("Art.61"),
        default=False,
        help_text=_(
            "Whether an art.61 contract can satisfy this candidature."))

    # no longer needed after 20170826
    # @classmethod
    # def setup_parameters(cls, **fields):
    #     fields = super(Candidature, cls).setup_parameters(**fields)
    #     fields.update(state=CandidatureStates.field(blank=True))
    #     fields.update(job=dd.ForeignKey(
    #         'jobs.Job', blank=True, null=True))
    #     fields.update(function=dd.ForeignKey(
    #         'cv.Function', blank=True, null=True))
    #     fields.update(person=dd.ForeignKey(
    #         'pcsw.Client', blank=True, null=True))
    #     return fields

    @classmethod
    def get_simple_parameters(cls):
        """"""
        s = list(super(Candidature, cls).get_simple_parameters())
        s += ['state', 'job', 'function', 'person']
        return s

    def __str__(self):
        return force_str(
            _('Candidature by %(person)s') %
            dict(person=self.person.get_full_name(salutation=False)))

    #~ @dd.chooser()
    #~ def contract_choices(cls,job,person):
    #~ if person and job:
    #~ return person.contract_set.filter(job=job)
    #~ return []

    #~ def clean(self,*args,**kw):
    #~ if self.contract:
    #~ if self.contract.person != self.person:
    #~ raise ValidationError(
    #~ "Cannot satisfy a Candidature with a Contract on another Person")
    #~ super(Candidature,self).clean(*args,**kw)

    def on_create(self, ar):
        self.date_submitted = settings.SITE.today()
        super(Candidature, self).on_create(ar)


class JobType(mixins.Sequenced):
    """
    The list of Job Types is used for statistical analysis.

    """

    class Meta:
        verbose_name = _("Job Type")
        verbose_name_plural = _('Job Types')

    name = models.CharField(max_length=200,
                            blank=True,
                            verbose_name=_("Designation"))

    remark = models.CharField(_("Remark"), max_length=200, blank=True)
    is_social = models.BooleanField(_("Social economy"), default=False)

    def __str__(self):
        return str(self.name)


from .ui import *
