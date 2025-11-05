# -*- coding: UTF-8 -*-
# Copyright 2012-2021 Rumma & Ko Ltd
# License: GNU Affero General Public License v3 (see file COPYING for details)

from builtins import range
import decimal
from lino.utils import ONE_DAY

from django.conf import settings
from django.utils.translation import gettext as _

from lino.utils import Cycler
from lino.api import dd, rt

from lino_xl.lib.notes.choicelists import SpecialTypes
from lino_welfare.modlib.debts.choicelists import AccountTypes
from lino_welfare.modlib.debts.roles import DebtsUser


def n2dec(v):
    return decimal.Decimal("%.2d" % v)


def objects():

    User = rt.models.users.User
    Household = rt.models.households.Household
    Budget = rt.models.debts.Budget
    Entry = rt.models.debts.Entry
    Account = rt.models.debts.Account
    Company = rt.models.contacts.Company
    ClientStates = rt.models.pcsw.ClientStates
    Client = rt.models.pcsw.Client

    kerstin = User(username="kerstin",
                   first_name="Kerstin",
                   last_name=u"Kerres",
                   user_type='300')
    yield kerstin
    user_types = [
        p for p in rt.models.users.UserTypes.get_list_items()
        if p.has_required_roles([DebtsUser])
    ]
    USERS = Cycler(User.objects.filter(user_type__in=user_types))

    partners = list(Household.objects.all())
    # also add some coached clients so we can test get_first_meeting()
    for ben in Client.objects.filter(client_state=ClientStates.coached)[:3]:
        partners.append(ben)
    for i, hh in enumerate(partners):
        b = Budget(partner_id=hh.id, user=USERS.pop(), date=dd.today(30 - i))
        b.fill_defaults(None)
        yield b

        cal_entry = rt.models.cal.Event(start_date=b.date,
                                        start_time="9:00",
                                        user=b.user)
        yield cal_entry
        for a in b.actor_set.all():
            yield rt.models.cal.Guest(event=cal_entry, partner=a.partner)
            prj = a.client
            if prj is not None:
                note_type = SpecialTypes.first_meeting.get_object()
                yield rt.models.notes.Note(type=note_type,
                                           date=b.date,
                                           project=prj,
                                           time="9:40",
                                           user=b.user)

    INCOME_AMOUNTS = Cycler([i * 200 for i in range(8)])
    EXPENSE_AMOUNTS = Cycler([i * 5.24 for i in range(10)])
    DEBT_AMOUNTS = Cycler([(i + 1) * 300 for i in range(5)])
    DEBT_ENTRIES = Cycler([4, 8, 5, 3, 12, 5])
    PARTNERS = Cycler(Company.objects.all())

    LIABILITIES = Cycler(Account.objects.filter(type=AccountTypes.liabilities))
    EXPENSE_REMARKS = Cycler(_("Shopping"), _("Cinema"), _("Seminar"))
    # qs = rt.models.contacts.Companies.create_request().data_iterator
    # qs = qs.filter(client_contact_type__is_bailiff=True)
    BAILIFFS = Cycler(
        Company.objects.filter(client_contact_type__is_bailiff=True))

    for b in Budget.objects.all():
        seqno = 0
        for e in b.entry_set.all():
            seqno += 1
            if e.account.type == AccountTypes.incomes:
                amount = INCOME_AMOUNTS.pop()
            elif e.account.type == AccountTypes.expenses:
                amount = EXPENSE_AMOUNTS.pop()
                if e.account.ref in ('3030', '3071'):
                    e.remark = EXPENSE_REMARKS.pop()
            if e.account.required_for_household:
                e.amount = n2dec(amount)
            if e.account.required_for_person:
                for a in b.actor_set.all():
                    e.amount = n2dec(amount)
                    e.actor = a
            e.save()
        ACTORS = Cycler(None, *[a for a in b.actor_set.all()])
        for i in range(DEBT_ENTRIES.pop()):
            seqno += 1
            amount = int(DEBT_AMOUNTS.pop())
            account = LIABILITIES.pop()
            kw = dict(budget=b,
                      account=account,
                      partner=PARTNERS.pop(),
                      amount=amount,
                      actor=ACTORS.pop(),
                      seqno=seqno)
            if account.ref.startswith('71'):
                kw.update(bailiff=BAILIFFS.pop())
            if amount > 600:
                kw.update(distribute=True)
            else:
                kw.update(monthly_rate=n2dec(amount / 20))
            e = Entry(**kw)
            e.account_changed(None)  # set description
            yield e

    ses = rt.login("kerstin")
    for e in Entry.objects.filter(account__ref='3030'):
        new = e.clone_row.run_from_code(ses)
        new.remark = EXPENSE_REMARKS.pop()
        yield new

    settings.SITE.site_config.master_budget = Budget.objects.get(id=1)
    yield settings.SITE.site_config
