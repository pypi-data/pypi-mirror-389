.. doctest docs/specs/jobs.rst
.. _welfare.specs.jobs:

========================
`jobs` : The Jobs plugin
========================

.. currentmodule:: lino_welfare.modlib.jobs

.. doctest initialization:

    >>> from lino import startup
    >>> startup('lino_welfare.projects.gerd.settings.doctests')
    >>> from lino.api.doctest import *

    Repair database after uncomplete test run:
    >>> settings.SITE.site_config.update(hide_events_before=i2d(20140401))


The :mod:`lino_welfare.modlib.jobs` plugin provides functionality for
managing :term:`job supplyments <job supplyment>`.

This document assumes that you have read :ref:`ug.plugins.jobs`.


Jobs
====

The :class:`Job` model is used to represent a :term:`suppliable job`.

.. class:: Job

  .. attribute:: provider

    The :term:`job provider` for this job.

  .. attribute:: workplace

    The workplace for this job if the :term:`job provider` has multiple
    workplaces. See :ref:`art60_workplace`.

    This field is a dummy field it :doc:`art60 <art60>` is not installed.

>>> ses = rt.login('rolf')
>>> ses.show(jobs.Jobs, column_names="function provider sector", language="de")
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
=================== ================================ ==========================
 Berufsbezeichnung   Stellenanbieter                  Sektor
------------------- -------------------------------- --------------------------
 Kellner             BISA                             Horeca
 Kellner             R-Cycle Sperrgutsortierzentrum   Landwirtschaft & Garten
 Koch                BISA                             Seefahrt
 Koch                Pro Aktiv V.o.G.                 Unterricht
 Küchenassistent     Pro Aktiv V.o.G.                 Medizin & Paramedizin
 Küchenassistent     R-Cycle Sperrgutsortierzentrum   Reinigung
 Tellerwäscher       BISA                             Transport
 Tellerwäscher       R-Cycle Sperrgutsortierzentrum   Bauwesen & Gebäudepflege
=================== ================================ ==========================
<BLANKLINE>


Job providers
=============

The :class:`JobProvider` model is used to represent a :term:`job provider`
It is a polymorphic specialization ("MTI child") of
:class:`contacts.Company <lino_welfare.modlib.contacts.Company>`.

>>> ses.show(jobs.JobProviders)
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
================================ ============ ================ ========= ======= ==== =========
 Name                             Adresse      E-Mail-Adresse   Telefon   Handy   ID   Sprache
-------------------------------- ------------ ---------------- --------- ------- ---- ---------
 BISA                             4700 Eupen                                      89   de
 Pro Aktiv V.o.G.                 4700 Eupen                                      92   de
 R-Cycle Sperrgutsortierzentrum   4700 Eupen                                      90   de
================================ ============ ================ ========= ======= ==== =========
<BLANKLINE>


.. class:: JobProvider

  Database model used to represent a :term:`job provider`.

  .. attribute:: is_social

    Whether this is a recognized :term:`social economy project`.

.. class:: WorkplacesByProvider

  Shows the companies that act as workplaces for this job provider.

  See :ref:`art60_workplace`.


.. class:: Employer

  Database model used to represent an :term:`employer`.

  Exists only when :setting:`jobs.with_employer_model` is True.

  .. attribute:: is_social

    Whether this is a recognized :term:`social economy project`.


.. _welfare.jobs.Offers:

Job Offers
==========


>>> # settings.SITE.catch_layout_exceptions = False
>>> ses.show(jobs.Offers)  #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
======================== ================== ========================= =================== ================ ============== =============
 Name                     Stellenanbieter    Sektor                    Berufsbezeichnung   Beginn Auswahl   Ende Auswahl   Beginndatum
------------------------ ------------------ ------------------------- ------------------- ---------------- -------------- -------------
 Übersetzer DE-FR (m/w)   Pro Aktiv V.o.G.   Landwirtschaft & Garten   Kellner             22.01.14         02.05.14       01.06.14
======================== ================== ========================= =================== ================ ============== =============
<BLANKLINE>


.. _welfare.jobs.ExperiencesByOffer:

Experiences by Job Offer
------------------------

This table shows the Experiences which satisfy a given Job offer.

Example:

>>> obj = jobs.Offer.objects.get(pk=1)
>>> ses.show(jobs.ExperiencesByOffer, obj)
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
============ ========== =================== =================================== ==========
 Beginnt am   Enddatum   Klient              Organisation                        Land
------------ ---------- ------------------- ----------------------------------- ----------
 07.02.11     07.03.11   LAZARUS Line (45)   Belgisches Rotes Kreuz              Andorra
 04.04.11     04.04.13   JONAS Josef (40)    Pharmacies Populaires de Verviers   Botswana
============ ========== =================== =================================== ==========
<BLANKLINE>



.. _welfare.jobs.CandidaturesByOffer:

Candidatures by job offer
=========================

This table shows the Candidatures which satisfy a given Job offer.

Example:

>>> obj = jobs.Offer.objects.get(pk=1)
>>> ses.show(jobs.CandidaturesByOffer.create_request(obj))
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
============== ====================== ======== ====================
 Anfragedatum   Klient                 Stelle   Kandidatur-Zustand
-------------- ---------------------- -------- --------------------
 02.05.14       MALMENDIER Marc (47)            Inaktiv
 27.06.14       KAIVERS Karl (42)               Arbeitet
============== ====================== ======== ====================
<BLANKLINE>



>>> ses.show(jobs.ContractTypes)  #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
=========================== ==========
 Bezeichnung                 Referenz
--------------------------- ----------
 Sozialökonomie              art60-7a
 Sozialökonomie - majoré     art60-7b
 Stadt Eupen                 art60-7e
 mit Rückerstattung          art60-7c
 mit Rückerstattung Schule   art60-7d
=========================== ==========
<BLANKLINE>


Contracts
=========

.. class:: Contracts

  Shows all :term:`Art60 job supplyments <job supplyment>`.

.. class:: ContractsByClient

  Shows the :term:`Art60 job supplyments <job supplyment>` for this client.


.. class:: JobSupplyment

  Model mixin for :class:`jobs.Contract <lino_welfare.modlib.jobs.Contract>`
  and :class:`art61.Contract <lino_welfare.modlib.art61.Contract>`. And also
  for :class:`art60.Contract <lino_welfare.modlib.art60.Contract>`.

  .. attribute:: duration

    The duration of this job supplyment (number of working days).



Show all contracts
==================

Via :menuselection`Explorer --> DSBE --> Art.60§7-Konventionen` you
can see a list of all job supplyment contracts.

>>> show_menu_path(jobs.Contracts)
Explorer --> DSBE --> Art.60§7-Konventionen

The demo database contains 16 job supplyment contracts:

>>> ses.show(jobs.Contracts)  #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
==== ============================ =============== ============== ========== ==================================================== ========================= ===========================
 ID   Klient                       NR-Nummer       Laufzeit von   Enddatum   Stelle                                               Verantwortlicher (DSBE)   Art
---- ---------------------------- --------------- -------------- ---------- ---------------------------------------------------- ------------------------- ---------------------------
 1    COLLARD Charlotte (19)       960715 002-61   06.10.12       05.10.13   Kellner bei BISA                                     Alicia Allmanns           mit Rückerstattung Schule
 2    EVERTZ Bernd (27*)           890722 001-93   20.10.12       19.04.14   Kellner bei R-Cycle Sperrgutsortierzentrum           Alicia Allmanns           Sozialökonomie
 3    FAYMONVILLE Luc (31*)        890202 001-76   17.11.12       16.11.13   Koch bei BISA                                        Alicia Allmanns           Sozialökonomie - majoré
 4    FAYMONVILLE Luc (31*)        890202 001-76   17.11.13       17.11.14   Koch bei Pro Aktiv V.o.G.                            Hubert Huppertz           Sozialökonomie
 5    HILGERS Hildegard (34)       870325 002-29   01.12.12       30.11.14   Küchenassistent bei Pro Aktiv V.o.G.                 Alicia Allmanns           Stadt Eupen
 6    LAMBERTZ Guido (43)          810823 001-96   29.12.12       28.12.14   Küchenassistent bei R-Cycle Sperrgutsortierzentrum   Alicia Allmanns           Sozialökonomie - majoré
 7    MALMENDIER Marc (47)         791013 001-77   12.01.13       11.01.14   Tellerwäscher bei BISA                               Alicia Allmanns           Stadt Eupen
 8    MALMENDIER Marc (47)         791013 001-77   12.01.14       12.01.15   Tellerwäscher bei R-Cycle Sperrgutsortierzentrum     Mélanie Mélard            mit Rückerstattung
 9    RADERMACHER Christian (56)   761227 001-93   09.02.13       08.02.14   Kellner bei BISA                                     Alicia Allmanns           mit Rückerstattung Schule
 10   RADERMACHER Christian (56)   761227 001-93   09.02.14       09.02.15   Kellner bei R-Cycle Sperrgutsortierzentrum           Mélanie Mélard            Sozialökonomie
 11   RADERMACHER Fritz (59*)      750805 001-25   23.02.13       22.02.15   Koch bei BISA                                        Alicia Allmanns           Sozialökonomie - majoré
 12   VAN VEEN Vincent (67)        710528 001-06   23.03.13       22.03.15   Koch bei Pro Aktiv V.o.G.                            Alicia Allmanns           Sozialökonomie
 13   RADERMECKER Rik (74)         730407 001-89   06.04.13       05.04.14   Küchenassistent bei Pro Aktiv V.o.G.                 Caroline Carnol           Stadt Eupen
 14   RADERMECKER Rik (74)         730407 001-89   06.04.14       06.04.15   Küchenassistent bei R-Cycle Sperrgutsortierzentrum   Hubert Huppertz           Sozialökonomie - majoré
 15   DENON Denis (81*)            950810 001-04   04.05.13       03.05.14   Tellerwäscher bei BISA                               Alicia Allmanns           Stadt Eupen
 16   DENON Denis (81*)            950810 001-04   04.05.14       04.05.15   Tellerwäscher bei R-Cycle Sperrgutsortierzentrum     Hubert Huppertz           mit Rückerstattung
==== ============================ =============== ============== ========== ==================================================== ========================= ===========================
<BLANKLINE>



Use the filter parameters to show e.g. only contracts that were active on
2012-11-18:

>>> pv = dict(observed_event=isip.ContractEvents.active,
...     start_date=i2d(20121118), end_date=i2d(20121118))
>>> kwargs = dict()
>>> kwargs.update(param_values=pv)
>>> ses.show(jobs.Contracts, **kwargs)
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
==== ======================== =============== ============== ========== ============================================ ========================= ===========================
 ID   Klient                   NR-Nummer       Laufzeit von   Enddatum   Stelle                                       Verantwortlicher (DSBE)   Art
---- ------------------------ --------------- -------------- ---------- -------------------------------------------- ------------------------- ---------------------------
 1    COLLARD Charlotte (19)   960715 002-61   06.10.12       05.10.13   Kellner bei BISA                             Alicia Allmanns           mit Rückerstattung Schule
 2    EVERTZ Bernd (27*)       890722 001-93   20.10.12       19.04.14   Kellner bei R-Cycle Sperrgutsortierzentrum   Alicia Allmanns           Sozialökonomie
 3    FAYMONVILLE Luc (31*)    890202 001-76   17.11.12       16.11.13   Koch bei BISA                                Alicia Allmanns           Sozialökonomie - majoré
==== ======================== =============== ============== ========== ============================================ ========================= ===========================
<BLANKLINE>


Use the filter parameters to show e.g. only contracts that started in October
2012:

>>> pv.update(observed_event=isip.ContractEvents.started,
...     start_date=i2d(20121001), end_date=i2d(20121030))
>>> ses.show(jobs.Contracts, **kwargs)
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
==== ======================== =============== ============== ========== ============================================ ========================= ===========================
 ID   Klient                   NR-Nummer       Laufzeit von   Enddatum   Stelle                                       Verantwortlicher (DSBE)   Art
---- ------------------------ --------------- -------------- ---------- -------------------------------------------- ------------------------- ---------------------------
 1    COLLARD Charlotte (19)   960715 002-61   06.10.12       05.10.13   Kellner bei BISA                             Alicia Allmanns           mit Rückerstattung Schule
 2    EVERTZ Bernd (27*)       890722 001-93   20.10.12       19.04.14   Kellner bei R-Cycle Sperrgutsortierzentrum   Alicia Allmanns           Sozialökonomie
==== ======================== =============== ============== ========== ============================================ ========================= ===========================
<BLANKLINE>


Evaluations of a project
=========================

>>> obj = jobs.Contract.objects.get(pk=6)
>>> print(str(obj.client))
LAMBERTZ Guido (43)

>>> obj.active_period()
(datetime.date(2012, 12, 29), datetime.date(2014, 12, 28))

>>> obj.get_recurrence_set()
ExamPolicy #3 ('Alle 3 Monate')

>>> print(str(obj.get_recurrence_set().event_type))
Auswertung
>>> print(obj.get_recurrence_set().event_type.max_conflicting)
4
>>> [str(i.start_date) for i in obj.get_existing_auto_events()]
['2013-04-02', '2013-07-02', '2013-10-02', '2014-01-02', '2014-04-02', '2014-07-02', '2014-10-02']
>>> with ses.capture_logger('DEBUG') as out:
...     wanted, unwanted = obj.get_wanted_auto_events(ses)
>>> print(out.getvalue())  #doctest: +NORMALIZE_WHITESPACE
Generating events between 2013-03-29 and 2014-12-28 (max. 72).
Évaluation 1 wants 2013-03-29 but conflicts with <QuerySet [Event #77 ('Karfreitag (29.03.2013)')]>, moving to 2013-04-01.
Évaluation 1 wants 2013-04-01 but conflicts with <QuerySet [Event #58 ('Ostermontag (01.04.2013)')]>, moving to 2013-04-02.
Reached upper date limit 2014-12-28 for 7

>>> settings.SITE.site_config.update(hide_events_before=None)

>>> ses.show(cal.EntriesByController.create_request(obj),
... column_names="when_html summary")
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
====================== ==================
 Wann                   Kurzbeschreibung
---------------------- ------------------
 `Do. 02.10.14 <…>`__   Évaluation 7
 `Mi. 02.07.14 <…>`__   Évaluation 6
 `Mi. 02.04.14 <…>`__   Évaluation 5
 `Do. 02.01.14 <…>`__   Évaluation 4
 `Mi. 02.10.13 <…>`__   Évaluation 3
 `Di. 02.07.13 <…>`__   Évaluation 2
 `Di. 02.04.13 <…>`__   Évaluation 1
====================== ==================
<BLANKLINE>

Mélanie has two appointments on 2014-09-15:

>>> from django.db.models import Count
>>> from lino.utils import SumCollector
>>> sc = SumCollector()
>>> for e in cal.Event.objects.filter(event_type__is_appointment=True):
...     sc.collect((e.user.username, e.start_date), 1)
>>> for username_date, count in sc.items():
...     if count > 1:
...         print("{1} has {0} appointments on {2}".format(count, *username_date))
...         break
melanie has 2 appointments on 2013-10-09

>>> d = i2d(20131009)
>>> pv = dict(start_date=d, end_date=d)
>>> ses.show(cal.EntriesByDay.create_request(param_values=pv),
...     column_names="user start_date start_time summary project")
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
================= ============ ============ ================== =========================
 Verwaltet durch   Beginnt am   Beginnt um   Kurzbeschreibung   Klient
----------------- ------------ ------------ ------------------ -------------------------
 Mélanie Mélard    09.10.13     09:00:00     Évaluation 2       AUSDEMWALD Alfons (17)
 Mélanie Mélard    09.10.13     09:00:00     Évaluation 9       LAZARUS Line (45)
 Alicia Allmanns   09.10.13     09:00:00     Évaluation 8       RADERMACHER Alfons (54)
================= ============ ============ ================== =========================
<BLANKLINE>

The two appointments conflict, at least strictly speaking. This is because the
EventType of these automatically generated evaluation appointments is configured
to allow for up to 4 conflicting events:

>>> e = cal.EntriesByDay.create_request(param_values=pv).data_iterator[0]
>>> e.event_type
EventType #6 ('Auswertung')
>>> e.event_type.max_conflicting
4



After modifying :attr:`hide_events_before
<lino.modlib.system.SiteConfig.hide_events_before>` we must tidy up
and reset it in order to not disturb other test cases:

>>> settings.SITE.site_config.update(hide_events_before=i2d(20140401))


JobsOverview
============

The :class:`JobsOverview
<lino_welfare.modlib.jobs.models.JobsOverview>` report
helps integration agents to make decisions like:

    - which jobs are soon going to be free, and which candidate(s) should we
      suggest?

Example content:

>>> ses.show(jobs.JobsOverview)
----------------------------
Sozialwirtschaft = "majorés"
----------------------------
<BLANKLINE>
+------------------------------------------------------------------------------------+--------------------------------------------------+-------------------------------+--------------------------------+
| Stelle                                                                             | Arbeitet                                         | Probezeit                     | Kandidaten                     |
+====================================================================================+==================================================+===============================+================================+
| `Kellner <…>`__ bei `R-Cycle Sperrgutsortierzentrum <…>`__ (1) *Sehr harte Stelle* | `RADERMACHER Christian (56) <…>`__ bis 09.02.15  | `FAYMONVILLE Luc (31*) <…>`__ | `JEANÉMART Jérôme (82) <…>`__  |
+------------------------------------------------------------------------------------+--------------------------------------------------+-------------------------------+--------------------------------+
| `Koch <…>`__ bei `Pro Aktiv V.o.G. <…>`__ (1)                                      | `VAN VEEN Vincent (67) <…>`__ bis 22.03.15 |br|  | `EMONTS-GAST Erna (53) <…>`__ | `JACOBS Jacqueline (38) <…>`__ |
|                                                                                    | `FAYMONVILLE Luc (31*) <…>`__ bis 17.11.14       |                               |                                |
+------------------------------------------------------------------------------------+--------------------------------------------------+-------------------------------+--------------------------------+
<BLANKLINE>
------
Intern
------
<BLANKLINE>
+--------------------------------------------------------------------------------------------+------------------------------------------------+--------------------------------+------------------------------+
| Stelle                                                                                     | Arbeitet                                       | Probezeit                      | Kandidaten                   |
+============================================================================================+================================================+================================+==============================+
| `Koch <…>`__ bei `BISA <…>`__ (1)                                                          | `RADERMACHER Fritz (59*) <…>`__ bis 22.02.15   | `AUSDEMWALD Alfons (17) <…>`__ | `MEESSEN Melissa (48) <…>`__ |
+--------------------------------------------------------------------------------------------+------------------------------------------------+--------------------------------+------------------------------+
| `Küchenassistent <…>`__ bei `R-Cycle Sperrgutsortierzentrum <…>`__ (1) *Sehr harte Stelle* | `LAMBERTZ Guido (43) <…>`__ bis 28.12.14 |br|  | `BRECHT Bernd (78) <…>`__      | `JONAS Josef (40) <…>`__     |
|                                                                                            | `RADERMECKER Rik (74) <…>`__ bis 06.04.15      |                                |                              |
+--------------------------------------------------------------------------------------------+------------------------------------------------+--------------------------------+------------------------------+
<BLANKLINE>
----------------------------------------------
Extern (Öffentl. VoE mit Kostenrückerstattung)
----------------------------------------------
<BLANKLINE>
======================================================================================================== ============================================= =========================== ============================
 Stelle                                                                                                   Arbeitet                                      Probezeit                   Kandidaten
-------------------------------------------------------------------------------------------------------- --------------------------------------------- --------------------------- ----------------------------
 `Küchenassistent <…>`__ bei `Pro Aktiv V.o.G. <…>`__ (1) *No supervisor. Only for independent people.*   `HILGERS Hildegard (34) <…>`__ bis 30.11.14   `JONAS Josef (40) <…>`__
 `Tellerwäscher <…>`__ bei `BISA <…>`__ (1)                                                                                                             `KAIVERS Karl (42) <…>`__   `EMONTS Daniel (29) <…>`__
======================================================================================================== ============================================= =========================== ============================
<BLANKLINE>
------------------------------------
Extern (Privat Kostenrückerstattung)
------------------------------------
<BLANKLINE>
+----------------------------------------------------------------------+-------------------------------------------------+---------------------------+--------------------------------+
| Stelle                                                               | Arbeitet                                        | Probezeit                 | Kandidaten                     |
+======================================================================+=================================================+===========================+================================+
| `Tellerwäscher <…>`__ bei `R-Cycle Sperrgutsortierzentrum <…>`__ (1) | `MALMENDIER Marc (47) <…>`__ bis 12.01.15 |br|  | `ENGELS Edgar (30) <…>`__ | `RADERMACHER Guido (60) <…>`__ |
|                                                                      | `DENON Denis (81*) <…>`__ bis 04.05.15          |                           |                                |
+----------------------------------------------------------------------+-------------------------------------------------+---------------------------+--------------------------------+
<BLANKLINE>
--------
Sonstige
--------
<BLANKLINE>
====================================== ========== =============================== ===========================
 Stelle                                 Arbeitet   Probezeit                       Kandidaten
-------------------------------------- ---------- ------------------------------- ---------------------------
 `Kellner <…>`__ bei `BISA <…>`__ (1)              `RADERMACHER Hedi (62) <…>`__   `ENGELS Edgar (30) <…>`__
====================================== ========== =============================== ===========================
<BLANKLINE>


Printing this report caused a "NotImplementedError: <i> inside <text:p>"
traceback when one of the jobs had a remark (bug fixed on :blogref:`20130423`).

This report is printed using the ``appyodt`` method, which produces editable
target files.

>>> settings.SITE.default_build_method = "appyodt"
>>> obj = ses.spawn(jobs.JobsOverview).create_instance()
>>> rv = ses.run(obj.do_print)  #doctest: +ELLIPSIS
appy.pod render .../lino/modlib/printing/config/report/Default.odt -> .../media/webdav/userdocs/appyodt/jobs.JobsOverview.odt

>>> print(rv['success'])
True
>>> print(rv['open_url'])
... #doctest: +NORMALIZE_WHITESPACE +ELLIPSIS
webdav:///.../jobs.JobsOverview.odt

Note: the ``webdav/`` is only there when :attr:`lino.core.site.Site.use_java` is `True`.



Configuration
=============

.. setting:: jobs.with_employer_model

  Set this to True if you want to differentiate between two types of job
  providers, "services utilisateurs" and "employers".

Dependencies
============

This plugin needs the :mod:`lino_welfare.modlib.isip` plugin.
