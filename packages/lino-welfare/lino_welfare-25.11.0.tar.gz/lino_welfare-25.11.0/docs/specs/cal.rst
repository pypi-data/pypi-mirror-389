.. doctest docs/specs/cal.rst
.. _welfare.specs.cal:

==========================================
``cal`` : Calendar plugin for Lino Welfare
==========================================

The :mod:`lino_welfare.modlib.cal` plugin extends
:mod:`lino_xl.modlib.cal` for :ref:`welfare`.

.. currentmodule:: lino_welfare.modlib.cal

See also :ref:`book.specs.cal`.

.. contents::
   :local:

.. include:: /../docs/shared/include/tested.rst

>>> from lino import startup
>>> startup('lino_welfare.projects.gerd.settings.doctests')
>>> from lino.api.doctest import *

Repair database after uncomplete test run:
>>> settings.SITE.site_config.update(hide_events_before=i2d(20140401))


Calendar entry types
====================

.. class::  EventType

    Adds two fields.

    .. attribute:: invite_client

    .. attribute:: esf_field

      How to summarize entries of this type in the ESF summary.

Guests
======

.. class::  Guest

    Adds a virtual field :attr:`client`.

    .. attribute:: client

        Virtual field which returns the `partner` if it is a client.

        When clicking in :class:`WaitingVisitors
        <lino_xl.lib.reception.WaitingVisitors>` on the partner
        show the *Client's* and not the *Partner's* detail.




Lifecycle of a calendar entry
=============================

>>> rt.show(cal.EntryStates)
... #doctest: +NORMALIZE_WHITESPACE +REPORT_UDIFF
====== ============ ================ ============= ================= ======== =================== =========
 Wert   name         Text             Button text   Gäste ausfüllen   Stabil   nicht blockierend   No auto
------ ------------ ---------------- ------------- ----------------- -------- ------------------- ---------
 10     suggested    Vorschlag        ?             Ja                Nein     Nein                Nein
 20     draft        Entwurf          ☐             Ja                Nein     Nein                Nein
 40     published    Veröffentlicht   ☼             Ja                Ja       Nein                Nein
 50     took_place   Stattgefunden    ☑             Nein              Ja       Nein                Nein
 70     cancelled    Storniert        ☒             Nein              Ja       Ja                  Ja
====== ============ ================ ============= ================= ======== =================== =========
<BLANKLINE>



Not for everybody
=================

Only users with the :class:`OfficeUser
<lino.modlib.office.roles.OfficeUser>` role can see the calendar
functionality.  All users with one of the following user_types can see
each other's calendars:

>>> from lino.modlib.office.roles import OfficeUser
>>> for p in users.UserTypes.items():
...     if p.has_required_roles([OfficeUser]):
...         print(p)
... #doctest: +NORMALIZE_WHITESPACE +REPORT_UDIFF
100 (Begleiter im DSBE+DFA)
110 (Begleiter im DSBE+DFA (Verwalter))
120 (Begleiter im im  DSBE+DFA (flexibel))
130 (Administrative Kraft im DSBE+DFA)
200 (Berater Erstempfang)
300 (Schuldenberater)
400 (Sozi)
410 (Sozialarbeiter (Verwalter))
420 (Sozialarbeiter ASD (flexibel))
430 (Administrative Kraft ASD)
500 (Buchhalter)
510 (Buchhalter (Verwalter))
900 (Verwalter)
910 (Security advisor)




Events today
============

Here is what the :class:`lino_xl.lib.cal.EntriesByDay` table gives:

>>> rt.login('theresia').show(cal.EntriesByDay, language='en', header_level=1)
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE +REPORT_UDIFF
===========================
Thu 22/05/2014 (22.05.2014)
===========================
============ ======================= ============================ ================== ============= ===================== ====== =======================================
 Start time   Client                  Short description            Managed by         Assigned to   Calendar entry type   Room   Workflow
------------ ----------------------- ---------------------------- ------------------ ------------- --------------------- ------ ---------------------------------------
                                      Absent for private reasons   Patrick Paraneau                 Absences                     [⚑] **☑ Took place** → [☐]
 08:30:00                             Versammlung                  Rolf Rompen                      External meetings            [⚑] **☼ Published** → [☑] [☒] [☐]
 09:00:00     BRECHT Bernd (78)       Évaluation 13                Hubert Huppertz                  Evaluation                   [▽] [⚑] **? Suggested** → [☼] [☑] [☒]
 09:00:00     JEANÉMART Jérôme (82)   Auswertung 2                 Hubert Huppertz                  Evaluation                   [▽] [⚑] **? Suggested** → [☼] [☑] [☒]
 13:30:00                             Petit-déjeuner               Romain Raffault                  Internal meetings            [⚑] **☒ Cancelled**
============ ======================= ============================ ================== ============= ===================== ====== =======================================
<BLANKLINE>


My calendar entries
===================

Here is the :term:`My calendar entries` view for Alicia.

>>> rt.login('alicia').show(cal.MyEntries, language='en')
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE +REPORT_UDIFF
================================= ========================= ===================== ============================ ===============================
 When                              Client                    Calendar entry type   Short description            Workflow
--------------------------------- ------------------------- --------------------- ---------------------------- -------------------------------
 `Sat 24/05/2014 at 10:20 <…>`__                             Meeting               Séminaire                    **☐ Draft** → [☼] [☒]
 `Sun 25/05/2014 <…>`__                                      Absences              Absent for private reasons   **☐ Draft** → [☼] [☒]
 `Mon 26/05/2014 <…>`__            RADERMACHER Fritz (59*)   Evaluation            Évaluation 5                 [▽] **? Suggested** → [☼] [☒]
 `Mon 26/05/2014 at 09:00 <…>`__   DA VINCI David (66)       Evaluation            Évaluation 14                [▽] **? Suggested** → [☼] [☒]
 `Thu 29/05/2014 at 08:30 <…>`__                             Meeting               Consultation                 **☐ Draft** → [☼] [☒]
 `Tue 03/06/2014 at 11:10 <…>`__                             Meeting               Réunion                      **☐ Draft** → [☼] [☒]
 `Wed 04/06/2014 <…>`__            HILGERS Hildegard (34)    Evaluation            Évaluation 6                 [▽] **? Suggested** → [☼] [☒]
 `Mon 09/06/2014 at 09:40 <…>`__                             Meeting               Petit-déjeuner               **☐ Draft** → [☼] [☒]
 `Thu 26/06/2014 at 09:00 <…>`__   DA VINCI David (66)       Evaluation            Évaluation 15                [▽] **? Suggested** → [☼] [☒]
 `Tue 26/08/2014 <…>`__            RADERMACHER Fritz (59*)   Evaluation            Évaluation 6                 [▽] **? Suggested** → [☼] [☒]
 `Thu 04/09/2014 <…>`__            HILGERS Hildegard (34)    Evaluation            Évaluation 7                 [▽] **? Suggested** → [☼] [☒]
 `Wed 10/09/2014 at 09:00 <…>`__   DA VINCI David (66)       Evaluation            Évaluation 1                 [▽] **? Suggested** → [☼] [☒]
 `Fri 10/10/2014 at 09:00 <…>`__   DA VINCI David (66)       Evaluation            Évaluation 2                 [▽] **? Suggested** → [☼] [☒]
 `Mon 10/11/2014 at 09:00 <…>`__   DA VINCI David (66)       Evaluation            Évaluation 3                 [▽] **? Suggested** → [☼] [☒]
 `Wed 26/11/2014 <…>`__            RADERMACHER Fritz (59*)   Evaluation            Évaluation 7                 [▽] **? Suggested** → [☼] [☒]
 `Wed 10/12/2014 at 09:00 <…>`__   DA VINCI David (66)       Evaluation            Évaluation 4                 [▽] **? Suggested** → [☼] [☒]
 `Mon 12/01/2015 at 09:00 <…>`__   DA VINCI David (66)       Evaluation            Évaluation 5                 [▽] **? Suggested** → [☼] [☒]
 `Thu 12/02/2015 at 09:00 <…>`__   DA VINCI David (66)       Evaluation            Évaluation 6                 [▽] **? Suggested** → [☼] [☒]
 `Thu 12/03/2015 at 09:00 <…>`__   DA VINCI David (66)       Evaluation            Évaluation 7                 [▽] **? Suggested** → [☼] [☒]
 `Mon 13/04/2015 at 09:00 <…>`__   DA VINCI David (66)       Evaluation            Évaluation 8                 [▽] **? Suggested** → [☼] [☒]
 `Wed 13/05/2015 at 09:00 <…>`__   DA VINCI David (66)       Evaluation            Évaluation 9                 [▽] **? Suggested** → [☼] [☒]
 `Mon 15/06/2015 at 09:00 <…>`__   DA VINCI David (66)       Evaluation            Évaluation 10                [▽] **? Suggested** → [☼] [☒]
================================= ========================= ===================== ============================ ===============================
<BLANKLINE>




These are for Hubert:

>>> rt.login('hubert').show(cal.MyEntries, language='en')
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE -REPORT_UDIFF
================================= ======================== =============================== ============================ ===================================
 When                              Client                   Calendar entry type             Short description            Workflow
--------------------------------- ------------------------ ------------------------------- ---------------------------- -----------------------------------
 `Thu 22/05/2014 at 09:00 <…>`__   BRECHT Bernd (78)        Evaluation                      Évaluation 13                [▽] **? Suggested** → [☼] [☑] [☒]
 `Thu 22/05/2014 at 09:00 <…>`__   JEANÉMART Jérôme (82)    Evaluation                      Auswertung 2                 [▽] **? Suggested** → [☼] [☑] [☒]
 `Sat 24/05/2014 at 11:10 <…>`__   HILGERS Hildegard (34)   Internal meetings with client   Auswertung                   **? Suggested** → [☼] [☒]
 `Mon 26/05/2014 <…>`__                                     Absences                        Absent for private reasons   **? Suggested** → [☼] [☒]
 `Fri 30/05/2014 at 09:40 <…>`__   JACOBS Jacqueline (38)   Internal meetings with client   Seminar                      **? Suggested** → [☼] [☒]
 `Wed 04/06/2014 at 13:30 <…>`__   KAIVERS Karl (42)        Internal meetings with client   Beratung                     **? Suggested** → [☼] [☒]
 `Mon 09/06/2014 at 10:20 <…>`__   LEFFIN Josefine (46*)    Internal meetings with client   Versammlung                  **? Suggested** → [☼] [☒]
 `Mon 23/06/2014 at 09:00 <…>`__   BRECHT Bernd (78)        Evaluation                      Évaluation 14                [▽] **? Suggested** → [☼] [☒]
 `Mon 23/06/2014 at 09:00 <…>`__   JEANÉMART Jérôme (82)    Evaluation                      Auswertung 3                 [▽] **? Suggested** → [☼] [☒]
 `Wed 02/07/2014 <…>`__            LAMBERTZ Guido (43)      Evaluation                      Évaluation 6                 [▽] **? Suggested** → [☼] [☒]
 ...
 `Mon 04/05/2015 <…>`__            DENON Denis (81*)        Evaluation                      Auswertung 4                 [▽] **? Suggested** → [☼] [☒]
 `Mon 04/05/2015 at 09:00 <…>`__   JEANÉMART Jérôme (82)    Evaluation                      Auswertung 13                [▽] **? Suggested** → [☼] [☒]
 `Thu 04/06/2015 at 09:00 <…>`__   JEANÉMART Jérôme (82)    Evaluation                      Auswertung 14                [▽] **? Suggested** → [☼] [☒]
 `Mon 06/07/2015 at 09:00 <…>`__   JEANÉMART Jérôme (82)    Evaluation                      Auswertung 15                [▽] **? Suggested** → [☼] [☒]
================================= ======================== =============================== ============================ ===================================
<BLANKLINE>



And these for Mélanie:

>>> rt.login('melanie').show(cal.MyEntries, language='en')
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE -REPORT_UDIFF
================================= ============================ =============================== ============================ ===============================
 When                              Client                       Calendar entry type             Short description            Workflow
--------------------------------- ---------------------------- ------------------------------- ---------------------------- -------------------------------
 `Mon 26/05/2014 at 08:30 <…>`__   INGELS Irene (36)            External meetings with client   Interview                    **? Suggested** → [☼] [☒]
 `Wed 28/05/2014 <…>`__                                         Absences                        Absent for private reasons   **? Suggested** → [☼] [☒]
 `Wed 28/05/2014 at 09:00 <…>`__   MEESSEN Melissa (48)         Evaluation                      Évaluation 5                 [▽] **? Suggested** → [☼] [☒]
 `Wed 28/05/2014 at 09:00 <…>`__   RADERMACHER Edgard (58)      Evaluation                      Évaluation 15                [▽] **? Suggested** → [☼] [☒]
 `Sat 31/05/2014 at 11:10 <…>`__   JONAS Josef (40)             External meetings with client   Première rencontre           **? Suggested** → [☼] [☒]
 `Thu 05/06/2014 at 09:40 <…>`__   LASCHET Laura (44)           External meetings with client   Evaluation                   **? Suggested** → [☼] [☒]
 `Tue 10/06/2014 at 09:00 <…>`__   ENGELS Edgar (30)            Evaluation                      Évaluation 3                 [▽] **? Suggested** → [☼] [☒]
 `Tue 10/06/2014 at 09:00 <…>`__   ÖSTGES Otto (69)             Evaluation                      Évaluation 14                [▽] **? Suggested** → [☼] [☒]
 `Tue 10/06/2014 at 09:00 <…>`__   DUBOIS Robin (80)            Evaluation                      Évaluation 3                 [▽] **? Suggested** → [☼] [☒]
 `Wed 11/06/2014 at 13:30 <…>`__   MEESSEN Melissa (48)         External meetings with client   Séminaire                    **? Suggested** → [☼] [☒]
 `Thu 12/06/2014 at 09:00 <…>`__   RADERMACHER Guido (60)       Evaluation                      Auswertung 15                [▽] **? Suggested** → [☼] [☒]
 `Thu 19/06/2014 at 09:00 <…>`__   LAZARUS Line (45)            Evaluation                      Évaluation 7                 [▽] **? Suggested** → [☼] [☒]
 `Mon 30/06/2014 at 09:00 <…>`__   MEESSEN Melissa (48)         Evaluation                      Évaluation 6                 [▽] **? Suggested** → [☼] [☒]
 `Thu 10/07/2014 at 09:00 <…>`__   ENGELS Edgar (30)            Evaluation                      Évaluation 4                 [▽] **? Suggested** → [☼] [☒]
 `Thu 10/07/2014 at 09:00 <…>`__   ÖSTGES Otto (69)             Evaluation                      Évaluation 15                [▽] **? Suggested** → [☼] [☒]
 ...
 `Thu 02/04/2015 at 09:00 <…>`__   ÖSTGES Otto (69)             Evaluation                      Évaluation 8                 [▽] **? Suggested** → [☼] [☒]
 `Tue 07/04/2015 at 09:00 <…>`__   MEESSEN Melissa (48)         Evaluation                      Évaluation 15                [▽] **? Suggested** → [☼] [☒]
 `Fri 17/04/2015 at 09:00 <…>`__   DUBOIS Robin (80)            Evaluation                      Évaluation 13                [▽] **? Suggested** → [☼] [☒]
 `Mon 20/04/2015 at 09:00 <…>`__   RADERMACHER Edgard (58)      Evaluation                      Évaluation 9                 [▽] **? Suggested** → [☼] [☒]
 `Mon 04/05/2015 at 09:00 <…>`__   RADERMACHER Guido (60)       Evaluation                      Évaluation 10                [▽] **? Suggested** → [☼] [☒]
 `Mon 04/05/2015 at 09:00 <…>`__   ÖSTGES Otto (69)             Evaluation                      Évaluation 9                 [▽] **? Suggested** → [☼] [☒]
 `Mon 18/05/2015 at 09:00 <…>`__   DUBOIS Robin (80)            Evaluation                      Évaluation 14                [▽] **? Suggested** → [☼] [☒]
 `Wed 20/05/2015 at 09:00 <…>`__   RADERMACHER Edgard (58)      Evaluation                      Évaluation 10                [▽] **? Suggested** → [☼] [☒]
 `Thu 18/06/2015 at 09:00 <…>`__   DUBOIS Robin (80)            Evaluation                      Évaluation 15                [▽] **? Suggested** → [☼] [☒]
================================= ============================ =============================== ============================ ===============================
<BLANKLINE>



These are Alicia's appointments of the last two months:

>>> pv = dict(start_date=dd.today(-15), end_date=dd.today(-1))
>>> rt.login('alicia').show(cal.MyEntries, language='en',
...     param_values=pv)
================================= ======== ===================== ==================== ===============================
 When                              Client   Calendar entry type   Short description    Workflow
--------------------------------- -------- --------------------- -------------------- -------------------------------
 `Thu 08/05/2014 at 11:10 <…>`__            Meeting               Interview            **☒ Cancelled**
 `Tue 13/05/2014 at 09:40 <…>`__            Meeting               Première rencontre   **☑ Took place** → [☐]
 `Sun 18/05/2014 at 13:30 <…>`__            Meeting               Evaluation           **☼ Published** → [☑] [☒] [☐]
================================= ======== ===================== ==================== ===============================
<BLANKLINE>



Overdue appointments
====================

>>> rt.login('alicia').show(cal.MyOverdueAppointments, language='en')
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE -REPORT_UDIFF
=================================================================== =================================================== ===================== ===================================
 Calendar entry                                                      Controlled by                                       Calendar entry type   Workflow
------------------------------------------------------------------- --------------------------------------------------- --------------------- -----------------------------------
 `Évaluation 5 (02.04.2014) with LAMBERTZ Guido (43) <…>`__          `Art60§7 job supplyment#6 (Guido LAMBERTZ) <…>`__   Evaluation            [▽] **? Suggested** → [☼] [☑] [☒]
 `Évaluation 13 (24.04.2014 09:00) with DA VINCI David (66) <…>`__   `ISIP#24 (David DA VINCI) <…>`__                    Evaluation            [▽] **? Suggested** → [☼] [☑] [☒]
=================================================================== =================================================== ===================== ===================================
<BLANKLINE>


Calendars and Subscriptions
===========================

A Calendar is a set of events that can be shown or hidden in the
Calendar Panel.

In Lino Welfare, we have one Calendar per User.  Or to be more
precise:

- The :class:`User` model has a :attr:`calendar` field.

- The calendar of a calendar entry is indirectly defined by the
  Event's :attr:`user` field.

Two users can share a common calendar.  This is possible when two
colleagues really work together when receiving visitors.

A Subscription is when a given user decides that she wants to see the
calendar of another user.

Every user is, by default, subscribed to her own calendar.
For example, demo user `rolf` is automatically subscribed to the
following calendars:

>>> ses = rt.login('rolf')
>>> with translation.override('de'):
...    ses.show(cal.SubscriptionsByUser, ses.get_user()) #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
==== ========== ===========
 ID   Kalender   versteckt
---- ---------- -----------
 8    rolf       Nein
==== ========== ===========
<BLANKLINE>


Calendar entries by client
==========================

.. class:: EntriesByClient

  Shows calendar entries having either :attr:`project
  <lino_xl.lib.cal.Event.project>` or one guest pointing to this client.


This table is special in that it shows not only events directly related to the
client (i.e. :attr:`project <lino_xl.lib.cal.Event.project>`  pointing to it)
but also those where this client is among the guests.

The following snippet finds examples of clients where this is the case

>>> hb = settings.SITE.site_config.hide_events_before
>>> hb
datetime.date(2014, 4, 1)
>>> from lino.utils import mti
>>> candidates = set()
>>> for obj in cal.Guest.objects.filter(event__start_date__gt=hb):
...     if obj.partner and obj.partner_id != obj.event.project_id:
...         if mti.get_child(obj.partner, pcsw.Client):
...             candidates.add(obj.partner_id)
>>> print(sorted(candidates))
[75, 77, 80, 81, 82, 114, 141, 160]
>>> qs = cal.Event.objects.filter(start_date__gt=hb, project_id__in=candidates)
>>> print(sorted(set([e.project.id for e in qs])))
[80, 81, 82]

>>> obj = pcsw.Client.objects.get(id=80)
>>> rt.show(cal.EntriesByClient, obj, header_level=1,
...     language="en", column_names="when_text user summary project")
...     #doctest: -SKIP +ELLIPSIS +NORMALIZE_WHITESPACE +REPORT_UDIFF
===============================================================
Calendar entries of DUBOIS Robin (80) (Dates 01.04.2014 to ...)
===============================================================
================================= ================ =================== ===================
 When                              Managed by       Short description   Client
--------------------------------- ---------------- ------------------- -------------------
 `Thu 18/06/2015 at 09:00 <…>`__   Mélanie Mélard   Évaluation 15       DUBOIS Robin (80)
 `Mon 18/05/2015 at 09:00 <…>`__   Mélanie Mélard   Évaluation 14       DUBOIS Robin (80)
 `Fri 17/04/2015 at 09:00 <…>`__   Mélanie Mélard   Évaluation 13       DUBOIS Robin (80)
 `Tue 17/03/2015 at 09:00 <…>`__   Mélanie Mélard   Évaluation 12       DUBOIS Robin (80)
 `Tue 17/02/2015 at 09:00 <…>`__   Mélanie Mélard   Évaluation 11       DUBOIS Robin (80)
 `Thu 15/01/2015 at 09:00 <…>`__   Mélanie Mélard   Évaluation 10       DUBOIS Robin (80)
 `Mon 15/12/2014 at 09:00 <…>`__   Mélanie Mélard   Évaluation 9        DUBOIS Robin (80)
 `Thu 13/11/2014 at 09:00 <…>`__   Mélanie Mélard   Évaluation 8        DUBOIS Robin (80)
 `Mon 13/10/2014 at 09:00 <…>`__   Mélanie Mélard   Évaluation 7        DUBOIS Robin (80)
 `Thu 11/09/2014 at 09:00 <…>`__   Mélanie Mélard   Évaluation 6        DUBOIS Robin (80)
 `Mon 11/08/2014 at 09:00 <…>`__   Mélanie Mélard   Évaluation 5        DUBOIS Robin (80)
 `Thu 10/07/2014 at 09:00 <…>`__   Mélanie Mélard   Évaluation 4        DUBOIS Robin (80)
 `Tue 17/06/2014 at 09:00 <…>`__   Robin Rood
 `Tue 10/06/2014 at 09:00 <…>`__   Mélanie Mélard   Évaluation 3        DUBOIS Robin (80)
 `Thu 22/05/2014 <…>`__            Mélanie Mélard   Urgent problem      DUBOIS Robin (80)
 `Wed 07/05/2014 at 09:00 <…>`__   Mélanie Mélard   Évaluation 2        DUBOIS Robin (80)
 `Mon 07/04/2014 at 09:00 <…>`__   Mélanie Mélard   Évaluation 1        DUBOIS Robin (80)
================================= ================ =================== ===================
<BLANKLINE>


Hiding all events before a given date
=====================================

This database has :attr:`hide_events_before
<lino.modlib.system.SiteConfig.hide_events_before>` set to 2014-04-01.

>>> settings.SITE.site_config.hide_events_before
datetime.date(2014, 4, 1)



Events generated by a contract
==============================

>>> settings.SITE.site_config.update(hide_events_before=None)
>>> obj = isip.Contract.objects.get(id=18)
>>> rt.show(cal.EntriesByController, obj, header_level=4, language="en")
Calendar entries of ISIP#18 (Alfons RADERMACHER)
================================================
================================ =================== ================= ===== =================
 When                             Short description   Managed by        No.   Workflow
-------------------------------- ------------------- ----------------- ----- -----------------
 `Tue 12/11/2013 (09:00) <…>`__   Évaluation 9        Alicia Allmanns   9     **? Suggested**
 `Wed 09/10/2013 (09:00) <…>`__   Évaluation 8        Alicia Allmanns   8     **? Suggested**
 `Mon 09/09/2013 (09:00) <…>`__   Évaluation 7        Alicia Allmanns   7     **? Suggested**
 `Thu 08/08/2013 (09:00) <…>`__   Évaluation 6        Alicia Allmanns   6     **? Suggested**
 `Mon 08/07/2013 (09:00) <…>`__   Évaluation 5        Alicia Allmanns   5     **? Suggested**
 `Thu 06/06/2013 (09:00) <…>`__   Évaluation 4        Alicia Allmanns   4     **? Suggested**
 `Mon 06/05/2013 (09:00) <…>`__   Évaluation 3        Alicia Allmanns   3     **? Suggested**
 `Thu 04/04/2013 (09:00) <…>`__   Évaluation 2        Alicia Allmanns   2     **? Suggested**
 `Mon 04/03/2013 (09:00) <…>`__   Évaluation 1        Alicia Allmanns   1     **? Suggested**
================================ =================== ================= ===== =================
<BLANKLINE>


After modifying :attr:`hide_events_before
<lino.modlib.system.SiteConfig.hide_events_before>` we must tidy up
and reset it in order to not disturb other test cases:

>>> settings.SITE.site_config.update(hide_events_before=i2d(20140401))

Filter list of clients when creating appointment
================================================

The "Client" field of a calendar entry in :ref:`welfare` has a
filtered choice list which shows only coached clients.  "Quand on veut
ajouter un rendez-vous dans le panneau "Rendez-vous aujourd'hui", la
liste déroulante pour le choix du bénéficiaire fait référence à la
liste de l'onglet CONTACTS --> BÉNÉFICIAIRES.  Nous souhaitons que la
liste de référence soit celle de l'onglet CPAS --> BÉNÉFICIAIRES.  En
effet, cette dernière ne reprend que les dossiers actifs (attribués
aux travailleurs sociaux)."

>>> show_choices('romain', '/choices/cal/AllEntries/project')
<br/>
AUSDEMWALD Alfons (17)
BRECHT Bernd (78)
COLLARD Charlotte (19)
DENON Denis (81*)
DOBBELSTEIN Dorothée (25)
DUBOIS Robin (80)
EMONTS Daniel (29)
EMONTS-GAST Erna (53)
ENGELS Edgar (30)
EVERS Eberhart (28)
FAYMONVILLE Luc (31*)
GROTECLAES Gregory (33)
HILGERS Hildegard (34)
JACOBS Jacqueline (38)
JEANÉMART Jérôme (82)
JONAS Josef (40)
KAIVERS Karl (42)
KELLER Karl (79)
LAMBERTZ Guido (43)
LAZARUS Line (45)
MALMENDIER Marc (47)
MEESSEN Melissa (48)
RADERMACHER Alfons (54)
RADERMACHER Christian (56)
RADERMACHER Edgard (58)
RADERMACHER Guido (60)
RADERMACHER Hedi (62)
RADERMECKER Rik (74)
DA VINCI David (66)
VAN VEEN Vincent (67)
ÖSTGES Otto (69)


.. _welfare.specs.20150717:

<ParamsPanel main ...has no variables
=====================================

This section helped us to understand and solve another problem which
occured while working on ticket :ticket:`340`.

<ParamsPanel main in ParamsLayout on cal.Subscriptions> of
LayoutHandle for ParamsLayout on cal.Subscriptions has no variables


>>> from lino.utils.jsgen import with_user_profile
>>> class W:
...     def write(self, s):
...         pass
>>> w = W()
>>> def f():
...     dd.plugins.extjs.renderer.write_lino_js(w)
>>> with_user_profile(users.UserTypes.anonymous, f)
... #doctest: +NORMALIZE_WHITESPACE
