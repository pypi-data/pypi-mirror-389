# -*- coding: UTF-8 -*-
# Copyright 2008-2022 Rumma & Ko Ltd
# License: GNU Affero General Public License v3 (see file COPYING for details)
# docs: https://welfare.lino-framework.org/specs/jobs.html

from lino import logger

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy as pgettext
from django.utils.encoding import force_str

from lino.api import dd, rt
from lino import mixins
from lino.core import constants

from lino.utils.html import E
from lino.utils.report import Report

from lino_xl.lib.cv.mixins import SectorFunction

from lino_xl.lib.coachings.utils import only_coached_on, has_contracts_filter
from lino_xl.lib.clients.choicelists import ClientEvents, ObservedEvent

from lino_welfare.modlib.isip.mixins import (ContractTypeBase)

from lino_welfare.modlib.pcsw.roles import SocialStaff, SocialUser, SocialCoordinator
from lino_welfare.modlib.integ.roles import IntegUser

from .mixins import CandidatureStates

contacts = dd.resolve_app('contacts')
isip = dd.resolve_app('isip')


class ClientHasContract(ObservedEvent):
    text = _("Art60§7 job supplyment")

    def add_filter(self, qs, pv):
        period = (pv.start_date, pv.end_date)
        flt = has_contracts_filter('jobs_contract_set_by_client', period)
        qs = qs.filter(flt).distinct()
        return qs


ClientEvents.add_item_instance(ClientHasContract("jobs", "jobs"))


class Schedules(dd.Table):
    required_roles = dd.login_required(SocialStaff)
    model = 'jobs.Schedule'
    order_by = ['name']
    detail_layout = """
    id name
    ContractsBySchedule
    """


class JobProviderDetail(contacts.CompanyDetail):
    """
    This is the same as CompanyDetail, except that we

    - add the is_social field
    - add a new tab `jobs`
    - add the UploadsByController panel

    """

    main = "general notes jobs"

    general = dd.Panel("""
    overview:30 general2:45 general3:30
    contacts.RolesByCompany:30 jobs.WorkplacesByProvider:30
    """, label=_("General"))

    general2 = """
    prefix:20 name:40
    type vat_id
    client_contact_type is_social
    url
    """

    jobs = dd.Panel("""
    JobsByProvider
    ContractsByProvider
    """,
                    label=_("Jobs"))

    notes = dd.Panel("""
    uploads.UploadsByController
    notes.NotesByCompany
    """,
                     label=_("Documents"))


class JobProviders(contacts.Companies, dd.Table):
    required_roles = dd.login_required(IntegUser)
    model = 'jobs.JobProvider'
    detail_layout = JobProviderDetail()


if dd.is_installed("art60"):

    class WorkplacesByProvider(contacts.Companies):
        required_roles = dd.login_required(IntegUser)
        master_key = "job_provider"
        label = _("Workplaces")
        column_names = "name_column:20 address_column phone * id"
        default_display_modes = {None: constants.DISPLAY_MODE_SUMMARY}

        @classmethod
        def param_defaults(self, ar, **kw):
            kw = super().param_defaults(ar, **kw)
            kw['also_obsolete'] = True
            return kw

else:
    class WorkplacesByProvider(dd.Dummy):
        pass

if dd.get_plugin_setting('jobs', 'with_employer_model'):

    class EmployerDetail(JobProviderDetail):
        general = dd.Panel("""
        overview:30 general2:45 general3:30
        contacts.RolesByCompany:30
        """, label=_("General"))

        jobs = dd.Panel("""
        art61.ContractsByProvider
        """,
                        label=_("Jobs"))

    class Employers(contacts.Companies, dd.Table):
        required_roles = dd.login_required(IntegUser)
        model = 'jobs.Employer'
        detail_layout = EmployerDetail()


class ContractTypes(dd.Table):
    """
    """
    required_roles = dd.login_required(SocialStaff)
    model = 'jobs.ContractType'
    column_names = 'name ref *'
    detail_layout = """
    id name ref overlap_group:30
    ContractsByType
    """


if dd.is_installed("art60"):

    from lino_welfare.modlib.art60.models import ConventionsByJob as ContractsByJob
    from lino_welfare.modlib.art60.models import ConventionsBySchedule as ContractsBySchedule
    from lino_welfare.modlib.art60.models import ConventionsByRegime as ContractsByRegime
    from lino_welfare.modlib.art60.models import ConventionsByProvider as ContractsByProvider
    from lino_welfare.modlib.art60.models import ContractsByType, ContractsByPolicy, ContractsByEnding, ContractsByClient

else:

    class ContractDetail(dd.DetailLayout):
        box1 = """
    id:8 client:25 user:15 user_asd:15 language:8
    job type company contact_person contact_role
    applies_from duration applies_until exam_policy
    regime:20 schedule:30 hourly_rate:10 refund_rate:10
    reference_person remark printed
    date_decided date_issued date_ended ending:20
    # signer1 signer2
    responsibilities
    """

        right = """
    cal.EntriesByController
    cal.TasksByController
    """

        main = """
    box1:70 right:30
    """

    class Contracts(isip.ContractBaseTable):
        # ~ debug_permissions = "20130222"

        required_roles = dd.login_required(SocialUser)
        model = 'jobs.Contract'
        column_names = 'id client client__national_id ' \
                       'applies_from date_ended job user type *'
        order_by = ['id']
        active_fields = 'job company contact_person contact_role'
        detail_layout = ContractDetail()
        insert_layout = dd.InsertLayout("""
    client
    job
    """,
                                        window_size=(60, 'auto'))

        parameters = dict(type=dd.ForeignKey(
            'jobs.ContractType',
            blank=True,
            verbose_name=_("Only contracts of type")),
                          **isip.ContractBaseTable.parameters)

        params_layout = """
    user type start_date end_date observed_event
    company ending_success ending
    """

        @classmethod
        def get_request_queryset(cls, ar):
            qs = super(Contracts, cls).get_request_queryset(ar)
            if (pv := ar.param_values) is None:
                return qs
            if pv.company:
                qs = qs.filter(company=pv.company)
            return qs

    class ContractsByClient(Contracts):
        """Shows the *Art60§7 job supplyments* for this client.
    """
        required_roles = dd.login_required((SocialUser, SocialCoordinator))
        master_key = 'client'
        auto_fit_column_widths = True
        column_names = "applies_from applies_until date_ended duration type " \
                       "job company user remark:20 *"
        no_phantom_row = False  # set back to default behaviour
        # hidden_columns = """
        # language contact_person contact_role
        # printed regime schedule hourly_rate
        # date_decided date_issued user_asd exam_policy ending date_ended
        # duration reference_person responsibilities remark
        # """

    class ContractsByProvider(Contracts):
        master_key = 'company'
        column_names = 'client job applies_from applies_until user type *'

    class ContractsByPolicy(Contracts):
        master_key = 'exam_policy'

    class ContractsByType(Contracts):
        master_key = 'type'
        column_names = "applies_from client job user *"
        order_by = ["applies_from"]

    class ContractsByEnding(Contracts):
        master_key = 'ending'

    class ContractsByJob(Contracts):
        column_names = 'client applies_from applies_until user type *'
        master_key = 'job'

    class ContractsByRegime(Contracts):
        """
    Shows Job Contracts for a given Regime.
    """
        master_key = 'regime'
        column_names = 'job applies_from applies_until user type *'

    class ContractsBySchedule(Contracts):
        master_key = 'schedule'
        column_names = 'job applies_from applies_until user type *'

    class MyContracts(Contracts):

        required_roles = dd.login_required(IntegUser)

        column_names = "applies_from client job type company applies_until date_ended ending *"
        # ~ label = _("My contracts")
        # ~ order_by = "reminder_date"
        # ~ column_names = "reminder_date client company *"
        # ~ order_by = ["applies_from"]
        # ~ filter = dict(reminder_date__isnull=False)

        @classmethod
        def param_defaults(self, ar, **kw):
            kw = super(MyContracts, self).param_defaults(ar, **kw)
            kw.update(user=ar.get_user())
            return kw

    class ContractsSearch(Contracts):
        """
    Shows the Job contracts owned by this user.
    """
        label = _("Job Contracts Search")
        group_by = ['client__group']
        column_names = 'id applies_from applies_until job client client__city client__national_id client__gender user type *'

        use_as_default_table = False

        def on_group_break(self, group):
            if group == 0:
                yield self.total_line(0)
            else:
                yield self.total_line(group)

        def total_line(self, group):
            return


class Offers(dd.Table):
    required_roles = dd.login_required(IntegUser)
    model = 'jobs.Offer'
    column_names = 'name provider sector function '\
                   'selection_from selection_until start_date *'
    detail_layout = """
    name provider sector function
    selection_from selection_until start_date
    remark
    ExperiencesByOffer CandidaturesByOffer
    """


class Candidatures(dd.Table):
    """
    List of :class:`Candidatures <Candidature>`.
    """
    required_roles = dd.login_required(SocialStaff)
    model = 'jobs.Candidature'
    order_by = ['date_submitted']
    column_names = 'date_submitted job:25 function person state * id'


class CandidaturesByPerson(Candidatures):
    """
    ...
    """
    required_roles = dd.login_required((SocialUser, SocialCoordinator))
    master_key = 'person'
    column_names = 'date_submitted job:25 sector function ' \
                   'art60 art61 remark state *'
    auto_fit_column_widths = True


class CandidaturesBySector(Candidatures):
    master_key = 'sector'


class CandidaturesByFunction(Candidatures):
    master_key = 'function'


class CandidaturesByJob(Candidatures):
    required_roles = dd.login_required(IntegUser)
    master_key = 'job'
    column_names = 'date_submitted person:25 state * id'

    @classmethod
    def create_instance(self, req, **kw):
        obj = super(CandidaturesByJob, self).create_instance(req, **kw)
        if obj.job is not None:
            obj.type = obj.job.type
        return obj


class SectorFunctionByOffer(dd.Table):
    """Shows the Candidatures or Experiences for this Offer.

    It is a slave report without :attr:`master_key
    <dd.Table.master_key>`, which is allowed only because it overrides
    :meth:`lino.core.dbtables..Table.get_request_queryset`.

    """
    master = "jobs.Offer"
    # abstract = True

    @classmethod
    def get_request_queryset(self, rr):
        """
        Needed because the Offer is not the direct master.
        """
        offer = rr.master_instance
        if offer is None:
            return []
        kw = {}
        # ~ qs = self.model.objects.order_by('date_submitted')
        qs = self.model.objects.order_by(self.model._meta.get_latest_by)

        if offer.function:
            qs = qs.filter(function=offer.function)
        if offer.sector:
            qs = qs.filter(sector=offer.sector)

        return qs


class CandidaturesByOffer(SectorFunctionByOffer):
    model = 'jobs.Candidature'
    label = _("Candidates")
    column_names = "date_submitted  person job state"


class ExperiencesByOffer(SectorFunctionByOffer):
    model = 'cv.Experience'
    label = _("Experiences")
    column_names = "start_date end_date person company country"


class Jobs(dd.Table):
    model = 'jobs.Job'
    required_roles = dd.login_required(IntegUser)
    # ~ order_by = ['start_date']
    column_names = 'name provider * id'

    detail_layout = """
    name provider workplace
    contract_type type id
    sector function capacity hourly_rate
    remark CandidaturesByJob
    ContractsByJob
    """
    insert_layout = """
    name provider
    contract_type type
    sector function
    # capacity hourly_rate
    """


class JobTypes(dd.Table):
    required_roles = dd.login_required(SocialStaff)
    model = 'jobs.JobType'
    order_by = ['name']
    detail_layout = """
    id name is_social
    JobsByType
    """


class JobsByProvider(Jobs):
    master_key = 'provider'
    column_names = 'name type workplace * id'


class JobsByType(Jobs):
    master_key = 'type'


class JobsOverviewByType(Jobs):
    """
    """
    required_roles = dd.login_required(IntegUser)
    label = _("Contracts Situation")
    column_names = "job_desc:20 working:30 probation:30 candidates:30"
    master_key = 'type'

    parameters = dict(
        date=models.DateField(blank=True, null=True, verbose_name=_("Date")),
        contract_type=dd.ForeignKey('jobs.ContractType', blank=True,
                                    null=True),
        # ~ job_type = dd.ForeignKey(JobType,blank=True,null=True),
    )

    params_panel_hidden = True

    @dd.displayfield(_("Job"))
    def job_desc(self, obj, ar):
        chunks = [ar.obj2html(obj, str(obj.function))]
        chunks.append(str(pgettext("(place)", " at ")))
        chunks.append(ar.obj2html(obj.provider))
        chunks.append(' (%d)' % obj.capacity)
        if obj.remark:
            chunks.append(' ')
            chunks.append(E.i(obj.remark))
        return E.p(*chunks)

    @dd.displayfield(pgettext("jobs", "Working"))
    def working(self, obj, ar):
        return obj._working

    @dd.displayfield(_("Candidates"))
    def candidates(self, obj, ar):
        return obj._candidates

    @dd.displayfield(_("Probation"))
    def probation(self, obj, ar):
        return obj._probation

    @classmethod
    def get_data_rows(self, ar):
        """
        """
        data_rows = self.get_request_queryset(ar)

        today = ar.param_values.date or settings.SITE.today()
        period = (today, today)

        def UL(items):
            # ~ return E.ul(*[E.li(i) for i in items])
            newitems = []
            first = True
            for i in items:
                if first:
                    first = False
                else:
                    newitems.append(E.br())
                newitems.append(i)
            return E.p(*newitems)

        for job in data_rows:
            showit = False
            working = []
            qs = job.contract_set.order_by('applies_from')
            if ar.param_values.contract_type:
                qs = qs.filter(type=ar.param_values.contract_type)
            for ct in qs:
                if ct.applies_from:
                    until = ct.date_ended or ct.applies_until
                    if not until or (ct.applies_from <= today
                                     and until >= today):
                        working.append(ct)
            if len(working) > 0:
                job._working = UL([
                    E.span(
                        # ~ ar.obj2html(ct.person,ct.person.last_name.upper()),
                        ar.obj2html(ct.person),
                        # pgettext("(place)", " at ")
                        # + unicode(ct.company.name),
                        ' bis %s' % dd.fds(ct.applies_until)) for ct in working
                ])
                showit = True
            else:
                job._working = ''

            candidates = []
            qs = job.candidature_set.order_by('date_submitted').filter(
                state=CandidatureStates.active)
            qs = only_coached_on(qs, period, 'person')
            for cand in qs:
                candidates.append(cand)
            if candidates:
                job._candidates = UL([
                    # ~ ar.obj2html(i.person,i.person.last_name.upper())
                    ar.obj2html(i.person) for i in candidates
                ])
                showit = True
            else:
                job._candidates = ''

            probation = []
            qs = job.candidature_set.order_by('date_submitted').filter(
                state=CandidatureStates.probation)
            qs = only_coached_on(qs, period, 'person')
            for cand in qs:
                probation.append(cand)
            if probation:
                job._probation = UL([
                    # ~ E.span(ar.obj2html(i.person,i.person.last_name.upper()))
                    E.span(ar.obj2html(i.person)) for i in probation
                ])
                showit = True
            else:
                job._probation = ''

            if showit:
                yield job


class JobsOverview(Report):
    """An overview of the jobs and the candidates working there or
    applying for it.

    """
    required_roles = dd.login_required(IntegUser)
    label = _("Contracts Situation")

    parameters = dict(
        today=models.DateField(blank=True, null=True, verbose_name=_("Date")),
        # ~ contract_type = dd.ForeignKey(ContractType,blank=True,null=True),
        job_type=dd.ForeignKey('jobs.JobType', blank=True, null=True),
    )
    params_panel_hidden = True

    @classmethod
    def param_defaults(self, ar, **kw):
        kw = super().param_defaults(ar, **kw)
        kw.update(today=dd.today())
        return kw

    # @classmethod
    # def create_instance(self, ar, **kw):
    #     kw.update(today=ar.param_values.today or settings.SITE.today())
    #     if ar.param_values.job_type:
    #         kw.update(jobtypes=[ar.param_values.job_type])
    #     else:
    #         kw.update(jobtypes=JobType.objects.all())
    #     return super(JobsOverview, self).create_instance(ar, **kw)

    @classmethod
    def get_story(cls, obj, ar):
        if ar.param_values.job_type:
            jobtypes = [ar.param_values.job_type]
        else:
            jobtypes = rt.models.jobs.JobType.objects.all()

        for jobtype in jobtypes:
            yield E.h2(str(jobtype))
            sar = ar.spawn(JobsOverviewByType,
                           master_instance=jobtype,
                           param_values=dict(date=ar.param_values.today))
            yield sar


@dd.receiver(dd.post_analyze)
def set_detail_layouts(sender=None, **kwargs):
    rt.models.cv.Regimes.set_detail_layout("""
    id name
    cv.ExperiencesByRegime
    jobs.ContractsByRegime
    """)
