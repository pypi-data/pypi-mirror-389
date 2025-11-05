# -*- coding: UTF-8 -*-
# Copyright 2013-2024 Rumma & Ko Ltd
# License: GNU Affero General Public License v3 (see file COPYING for details)
"""
Database models for :mod:`lino_welfare.modlib.contacts`.

Lino Welfare defines a `vat_id` field on :class:`Company` but
doesn't need :mod:`lino_xl.lib.vat`

"""

from django.core.exceptions import ValidationError
from lino.api import dd, rt, _
from lino.core.roles import Expert
# from lino_xl.lib.addresses.mixins import AddressOwner

from lino_xl.lib.contacts.models import *


class Archivable(dd.Model):

    class Meta:
        abstract = True

    is_obsolete = models.BooleanField(
        verbose_name=_("Archived"), default=False)
    # help_text="""Altfälle sind Partner, deren Stammdaten nicht mehr gepflegt
    # werden und für neue Operationen nicht benutzt werden können."""

    @classmethod
    def setup_parameters(cls, fields):
        fields.setdefault(
            'also_obsolete', models.BooleanField(
                _("With archived"), default=False,
                help_text=_("Show also archived partners.")))
        super().setup_parameters(fields)

    @classmethod
    def get_request_queryset(cls, ar):
        qs = super().get_request_queryset(ar)
        if (pv := ar.param_values) is None:
            return qs
        if not pv.also_obsolete:
            qs = qs.filter(is_obsolete=False)
        return qs

    # @classmethod
    # def get_simple_parameters(cls):
    #     for p in super().get_simple_parameters():
    #         yield p
    #     yield 'also_obsolete'

    # @classmethod
    # def add_param_filter(cls, qs, lookup_prefix='', also_obsolete=None, **kwargs):
    #     qs = super().add_param_filter(qs, **kwargs)
    #     if not also_obsolete:
    #         qs = qs.filter(**{lookup_prefix + 'is_obsolete': False})
    #     return qs

    # @classmethod
    # def get_title_tags(self, ar):
    #     for t in super().get_title_tags(ar):
    #         yield t
    #     if ar.param_values.also_obsolete:
    #         yield str(ar.actor.parameters['also_obsolete'].verbose_name)


class Partner(Partner, mixins.CreatedModified, dd.ImportedFields, Archivable):
    """Extends :class:`lino_xl.lib.contacts.models.Partner` by adding the
    following fields:

    .. attribute:: is_obsolete

        Marking a partner as archived means to stop using this partner for new
        operations. Archived partners are hidden in most views.

    .. attribute:: activity

    .. attribute:: client_contact_type

    """

    class Meta(Partner.Meta):
        abstract = dd.is_abstract_model(__name__, 'Partner')

    hidden_columns = 'created modified activity'

    # quick_search_fields = "prefix name phone gsm street"

    activity = dd.ForeignKey("pcsw.Activity", blank=True, null=True)

    # client_contact_type = dd.ForeignKey(
    #     'clients.ClientContactType', blank=True, null=True)

    # def get_overview_elems(self, ar):
    #     # In the base classes, Partner must come first because
    #     # otherwise Django won't inherit `meta.verbose_name`. OTOH we
    #     # want to get the `get_overview_elems` from AddressOwner, not
    #     # from Partner (i.e. AddressLocation).
    #     elems = super(Partner, self).get_overview_elems(ar)
    #     elems += AddressOwner.get_overview_elems(self, ar)
    #     return elems

    @classmethod
    def on_analyze(cls, site):
        super().on_analyze(site)
        cls.declare_imported_fields('''
          created modified
          name remarks region zip_code city country
          street_prefix street street_no street_box
          addr2
          language
          phone fax email url
          activity is_obsolete
          ''')

    def disabled_fields(self, ar):
        rv = super().disabled_fields(ar)
        # ~ logger.info("20120731 CpasPartner.disabled_fields()")
        # ~ raise Exception("20120731 CpasPartner.disabled_fields()")
        if settings.SITE.is_imported_partner(self):
            rv |= self._imported_fields
        return rv

    def disable_delete(self, ar=None):
        if ar is not None and settings.SITE.is_imported_partner(self):
            return _("Cannot delete companies and persons imported from TIM")
        return super().disable_delete(ar)

    def __str__(self):
        # 20150419 : print partner id only for clients because the
        # numbers become annoying when printing a debts.Budget.
        return self.get_full_name(nominative=True)


# Lino Welfare uses the `overview` field only in detail forms, and we
# don't want it to have a label "Description":
dd.update_field(Partner, 'overview', verbose_name=None)


class PartnerDetail(PartnerDetail):

    main = "general contact accounting misc"

    general = dd.Panel("""
    overview:30 general2:45 general3:20
    reception.AppointmentsByPartner
    """,
                       label=_("General"))

    general2 = """
    id language
    activity
    client_contact_type
    url
    """

    general3 = """
    email:40
    phone
    gsm
    fax
    """

    contact = dd.Panel("""
    address_box
    remarks:30 sepa.AccountsByPartner
    """,
                       label=_("Contact"))

    address_box = """
    country region city zip_code:10
    addr1
    street_prefix street:25 street_no street_box
    addr2
    """

    misc = dd.Panel("""
    is_obsolete created modified
    changes.ChangesByMaster
    """,
                    label=_("Miscellaneous"))


class Person(Partner, Person):
    """Represents a physical person.

    """

    class Meta(Person.Meta):
        verbose_name = _("Person")  # :doc:`/tickets/14`
        verbose_name_plural = _("Persons")  # :doc:`/tickets/14`
        # ~ ordering = ['last_name','first_name']
        abstract = dd.is_abstract_model(__name__, 'Person')

    # @classmethod
    # def get_request_queryset(cls, *args, **kwargs):
    #     qs = super().get_request_queryset(*args, **kwargs)
    #     return qs.select_related('country', 'city')

    def get_print_language(self):
        "Used by DirectPrintAction"
        return self.language

    @classmethod
    def on_analyze(cls, site):
        super().on_analyze(site)
        cls.declare_imported_fields(
            '''name first_name middle_name last_name title
            birth_date gender''')

    @classmethod
    def choice_text_to_dict(cls, text, ar):
        """
        In Welfare we don't want Lino to automatically create persons
        from learning comboboxes.
        """
        if ar.get_user().has_required_roles([Expert]):
            return super().choice_text_to_dict(text, ar)
        msg = _("Cannot create new {obj} from '{text}'").format(
            obj=cls._meta.verbose_name, text=text)
        msg += " ({})".format(_("You are not an expert"))
        raise ValidationError(msg)


# dd.update_field(Person, 'first_name', blank=False)
dd.update_field(Person, 'last_name', blank=False)


class PersonDetail(PersonDetail):

    main = "general contact accounting misc"

    general = dd.Panel("""
    overview:30 general2:45 general3:30
    contacts.RolesByPerson:20  \
    """, label=_("General"))

    general2 = """
    title first_name:15 middle_name:15
    last_name
    gender:10 birth_date age:10
    id language
    """

    general3 = """
    email:40
    phone
    gsm
    fax
    """

    contact = dd.Panel("""
    households.MembersByPerson:20 households.SiblingsByPerson:60
    humanlinks.LinksByHuman
    remarks:30 sepa.AccountsByPartner
    """, label=_("Contact"))

    address_box = """
    country region city zip_code:10
    addr1
    street_prefix street:25 street_no street_box
    addr2
    """

    misc = dd.Panel("""
    activity url client_contact_type is_obsolete
    created modified
    reception.AppointmentsByPartner
    """, label=_("Miscellaneous"))


class Persons(Persons):

    detail_layout = PersonDetail()

    params_panel_hidden = True

    params_layout = """
    gender also_obsolete
    """

    # @classmethod
    # def get_request_queryset(self, ar):
    #     qs = super().get_request_queryset(ar)
    #     if not ar.param_values.also_obsolete:
    #         qs = qs.filter(is_obsolete=False)
    #     return qs

    # @classmethod
    # def get_title_tags(self, ar):
    #     for t in super().get_title_tags(ar):
    #         yield t
    #     if ar.param_values.also_obsolete:
    #         yield str(self.parameters['also_obsolete'].verbose_name)


class Company(Partner, Company):

    class Meta(Company.Meta):
        # verbose_name = _("Organisation")
        # verbose_name_plural = _("Organisations")
        abstract = dd.is_abstract_model(__name__, 'Company')

    vat_id = models.CharField(_("VAT id"), max_length=200, blank=True)

    if dd.is_installed("art60"):
        job_provider = dd.ForeignKey('jobs.JobProvider', blank=True, null=True)
    else:
        job_provider = dd.DummyField()

    @classmethod
    def on_analyze(cls, site):
        # ~ if cls.model is None:
        # ~ raise Exception("%r.model is None" % cls)
        super().on_analyze(site)
        cls.declare_imported_fields(
            '''name vat_id prefix phone fax email activity''')


class CompanyDetail(CompanyDetail):

    main = "general contact notes accounting misc"

    general = dd.Panel("""
    overview:30 general2:45 general3:30
    contacts.RolesByCompany
    """, label=_("General"))

    general2 = """
    prefix:20 name:40
    type vat_id
    url
    client_contact_type job_provider
    """

    general3 = """
    email:40
    phone
    gsm
    fax
    """

    contact = dd.Panel("""
    #address_box addresses.AddressesByPartner
    remarks:30 sepa.AccountsByPartner
    """, label=_("Contact"))

    address_box = """
    country region city zip_code:10
    addr1
    street_prefix street:25 street_no street_box
    addr2
    """

    notes = "notes.NotesByCompany"

    misc = dd.Panel("""
    id language activity is_obsolete
    created modified
    reception.AppointmentsByPartner
    """, label=_("Miscellaneous"))


# class Companies(Companies):
#     detail_layout = CompanyDetail()

# Partners.set_detail_layout(PartnerDetail())
# Companies.set_detail_layout(CompanyDetail())

# @dd.receiver(dd.post_analyze)
# def my_details(sender, **kw):
#     contacts = sender.models.contacts
#     contacts.Partners.set_detail_layout(contacts.PartnerDetail())
#     contacts.Companies.set_detail_layout(contacts.CompanyDetail())

Partners.detail_layout = "contacts.PartnerDetail"
