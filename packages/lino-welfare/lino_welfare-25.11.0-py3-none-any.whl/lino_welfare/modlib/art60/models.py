# -*- coding: UTF-8 -*-
# Copyright 2015-2024 Rumma & Ko Ltd
# License: GNU Affero General Public License v3 (see file COPYING for details)

from lino import logger

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from lino.api import dd, rt
from lino import mixins
from lino.core import constants
from lino.core.fields import PriceRange

from lino.modlib.uploads.mixins import UploadController
from lino_xl.lib.coachings.utils import has_contracts_filter
from lino_xl.lib.clients.choicelists import ClientEvents, ObservedEvent

from lino_welfare.modlib.integ.roles import IntegUser, IntegrationStaff

from lino_welfare.modlib.isip.mixins import (ContractPartnerBase, ContractBase)
from lino_welfare.modlib.isip.mixins import (ContractBaseTable,
                                             ContractTypeBase)
from lino_welfare.modlib.jobs.mixins import JobSupplyment
from lino_welfare.modlib.jobs.models import CandidatureStates

from lino_welfare.modlib.pcsw.roles import SocialCoordinator, SocialStaff, SocialUser


class ClientHasContract(ObservedEvent):
    text = _("Art60 job supplyment")

    def add_filter(self, qs, pv):
        period = (pv.start_date, pv.end_date)
        flt = has_contracts_filter('art60_contract_set_by_client', period)
        qs = qs.filter(flt).distinct()
        return qs


ClientEvents.add_item_instance(ClientHasContract("art60"))


class Contract(JobSupplyment, ContractBase):

    class Meta:
        verbose_name = _("Art60§7 job supplyment")
        verbose_name_plural = _('Art60§7 job supplyments')

    quick_search_fields = 'convention__job__name client__name '\
                          'client__national_id'

    type = dd.ForeignKey("jobs.ContractType",
                         verbose_name=_("Type"),
                         related_name="%(app_label)s_%(class)s_set_by_type",
                         blank=True)

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

    @classmethod
    def get_certifiable_fields(cls):
        return ('client type '
                'applies_from applies_until duration '
                'language user user_asd exam_policy '
                'date_decided date_issued ')

    @property
    def active_convention_property(self):
        if self.pk is None: return None
        return Convention.objects.filter(contract=self).first()

    @dd.virtualfield(
        dd.ForeignKey('art60.Convention', verbose_name=_("Active convention")))
    def active_convention(self, ar):
        if self.pk is None: return None
        return Convention.objects.filter(contract=self).first()

    @property
    def excerpt_type(self):  # temporary workaround.
        return rt.models.excerpts.ExcerptType()


# dd.update_field(Contract, 'user', verbose_name=_("responsible (IS)"))


class Convention(ContractPartnerBase, UploadController):

    class Meta:
        verbose_name = _("Art60§7 convention")
        verbose_name_plural = _('Art60§7 conventions')

    company = dd.ForeignKey(  # ContractPartnerBase requires a field "company"
        "jobs.JobProvider",
        related_name="%(app_label)s_%(class)s_set_by_company",
        blank=True,
        null=True)

    contract = dd.ForeignKey("art60.Contract")
    job = dd.ForeignKey("jobs.Job")
    start_date = models.DateField(blank=True,
                                  null=True,
                                  verbose_name=_("Start date"))
    regime = dd.ForeignKey('cv.Regime',
                           blank=True,
                           null=True,
                           related_name="jobs_contracts")
    schedule = dd.ForeignKey('jobs.Schedule', blank=True, null=True)
    monthly_refund = dd.PriceField(_("Monthly refund"), blank=True, null=True)
    hourly_rate = dd.PriceField(_("hourly rate"), blank=True, null=True)
    refund_rate = models.CharField(_("refund rate"),
                                   max_length=200,
                                   blank=True)

    def __str__(self):
        return "{} {}".format(dd.fds(self.start_date), self.job)

    # @dd.chooser()
    # def company_choices(cls):
    #     return rt.models.jobs.JobProvider.objects.all()

    def full_clean(self, *args, **kw):
        if self.job_id is not None:
            if self.job.provider is not None:
                self.company = self.job.provider
            if self.job.contract_type is not None:
                self.type = self.job.contract_type
            if self.hourly_rate is None:
                self.hourly_rate = self.job.hourly_rate
        if not self.start_date:
            self.start_date = settings.SITE.today()
        super().full_clean(*args, **kw)

    @classmethod
    def get_certifiable_fields(cls):
        return ('contract job company contact_person contact_role '
                'schedule regime monthly_refund hourly_rate refund_rate '
                'reference_person responsibilities '
                'start_date')

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
            if self.contract.applies_until and self.contract.applies_until > dd.today(
            ):
                n = 0
                for candi in self.contract.client.candidature_set.filter(
                        state=CandidatureStates.active):
                    candi.state = CandidatureStates.inactive
                    candi.save()
                    n += 1
                if n:
                    ar.debug(
                        str(_("(%d candidatures have been marked inactive)")) %
                        n)
                    ar.set_response(alert=_("Success"))


# Convention.set_widget_options('monthly_refund', hide_sum=True)

# dd.update_field(Convention, "company", related_model='jobs.JobProvider')


class ContractDetail(dd.DetailLayout):
    box1 = """
    id:8 client:25 user:15 user_asd:15 language:8
    type printed
    applies_from duration applies_until exam_policy
    remark
    date_decided date_issued date_ended ending:20
    # signer1 signer2
    art60.ConventionsByContract
    """

    right = """
    cal.EntriesByController
    cal.TasksByController
    """

    main = """
    box1:70 right:30
    """


class ConventionDetail(dd.DetailLayout):
    main = """
    id:8 contract job
    company contact_person contact_role
    start_date reference_person
    regime:20 schedule:30 monthly_refund #hourly_rate:10 #refund_rate:10
    responsibilities uploads.UploadsByController
    """


class RefundFilters(dd.ChoiceList):
    pass


class Contracts(ContractBaseTable):
    #~ debug_permissions = "20130222"

    required_roles = dd.login_required(SocialUser)
    model = 'art60.Contract'
    column_names = 'id client client__national_id ' \
                   'applies_from date_ended user type *'
    order_by = ['id']
    detail_layout = ContractDetail()
    insert_layout = dd.InsertLayout("""
    client
    type
    user_asd
    """,
                                    window_size=(60, 'auto'))

    parameters = PriceRange('monthly_refund',
                            _("Monthly refund"),
                            type=dd.ForeignKey(
                                'jobs.ContractType',
                                blank=True,
                                verbose_name=_("Only contracts of type")),
                            **ContractBaseTable.parameters)

    params_layout = """
    user user_asd type start_date end_date observed_event start_monthly_refund end_monthly_refund
    convention__company convention__company__type convention__job ending_success ending
    """

    @classmethod
    def get_simple_parameters(cls):
        for p in super().get_simple_parameters():
            yield p
        yield 'convention__company__type'
        yield 'convention__company'
        yield 'convention__job'

    @classmethod
    def get_request_queryset(cls, ar):
        qs = super().get_request_queryset(ar)
        if (pv := ar.param_values) is None: return qs
        if pv.company:
            qs = qs.filter(convention__company=pv.company)
        if pv.start_monthly_refund:
            qs = qs.filter(
                convention__monthly_refund__gte=pv.start_monthly_refund)
        if pv.end_monthly_refund:
            qs = qs.filter(
                Q(convention__monthly_refund__isnull=True)
                | Q(convention__monthly_refund__lte=pv.end_monthly_refund))
        return qs


class ContractsByClient(Contracts):
    required_roles = dd.login_required((SocialUser, SocialCoordinator))
    master_key = 'client'
    auto_fit_column_widths = True
    no_phantom_row = False  # override ContractBaseTable
    column_names = "applies_from applies_until date_ended duration type user active_convention:20 remark:30 *"
    # hidden_columns = """
    # language contact_person contact_role
    # printed regime schedule hourly_rate
    # date_decided date_issued user_asd exam_policy ending date_ended
    # duration reference_person responsibilities remark
    # """


class Conventions(dd.Table):
    model = "art60.Convention"
    detail_layout = ConventionDetail()
    insert_layout = """
    job
    start_date
    """


class ConventionsByContract(Conventions):
    label = _("Conventions")
    master_key = 'contract'
    column_names = 'detail_link monthly_refund *'
    order_by = ["start_date"]
    default_display_modes = {None: constants.DISPLAY_MODE_HTML}


class ConventionsByProvider(Conventions):
    master_key = 'company'
    column_names = 'start_date contract  *'
    order_by = ["start_date"]


class ContractsByPolicy(Contracts):
    master_key = 'exam_policy'


class ContractsByType(Contracts):
    master_key = 'type'
    column_names = "applies_from client user *"
    order_by = ["applies_from"]


class ContractsByEnding(Contracts):
    master_key = 'ending'


class ConventionsByJob(Conventions):
    column_names = 'start_date contract *'
    master_key = 'job'


class ConventionsByRegime(Conventions):
    """
    Shows Job Contracts for a given Regime.
    """
    master_key = 'regime'
    column_names = 'job contract start_date *'


class ConventionsBySchedule(Conventions):
    master_key = 'schedule'
    column_names = 'start_date job contract *'


class MyContracts(Contracts):

    label = _("My art60§7 contracts (IS)")
    required_roles = dd.login_required(IntegUser)
    column_names = "applies_from client type applies_until date_ended ending *"

    @classmethod
    def param_defaults(self, ar, **kw):
        kw = super().param_defaults(ar, **kw)
        kw.update(user=ar.get_user())
        return kw


class MyContractsGSS(Contracts):

    label = _("My art60§7 contracts (GSS)")
    required_roles = dd.login_required(SocialUser)
    column_names = "applies_from client type applies_until date_ended ending *"

    @classmethod
    def param_defaults(self, ar, **kw):
        kw = super().param_defaults(ar, **kw)
        kw.update(user_asd=ar.get_user())
        return kw
