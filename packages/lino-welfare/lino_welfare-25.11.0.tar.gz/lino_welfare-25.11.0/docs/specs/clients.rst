.. doctest docs/specs/clients.rst

.. _welfare.clients.parameters:
.. _welfare.specs.clients:

=================
Filtering clients
=================

This document describes and tests some ways of filtering clients.

Most code is in :mod:`lino_welfare.modlib.pcsw` plugin.


.. contents::
   :depth: 2
   :local:

.. include:: /../docs/shared/include/tested.rst

>>> from lino import startup
>>> startup('lino_welfare.projects.gerd.settings.doctests')
>>> from lino.api.doctest import *

>>> ClientEvents = pcsw.ClientEvents
>>> ses = rt.login("hubert")

Quick search
============

When using quick search to find a client, Lino does not look into the
:attr:`street` field.

>>> [f.name for f in pcsw.Client.quick_search_fields]
['prefix', 'name', 'phone', 'gsm', 'national_id']


Default lists of coached clients
================================

>>> ses.show(pcsw.CoachedClients, column_names="name_column")
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE -REPORT_UDIFF
============================
 Name
----------------------------
 AUSDEMWALD Alfons (17)
 BRECHT Bernd (78)
 COLLARD Charlotte (19)
 DOBBELSTEIN Dorothée (25)
 DUBOIS Robin (80)
 EMONTS Daniel (29)
 EMONTS-GAST Erna (53)
 ENGELS Edgar (30)
 EVERS Eberhart (28)
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
============================
<BLANKLINE>

>>> ses.show(integ.Clients, column_names="name_column")
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE -REPORT_UDIFF
=========================
 Name
-------------------------
 BRECHT Bernd (78)
 COLLARD Charlotte (19)
 EMONTS Daniel (29)
 EMONTS-GAST Erna (53)
 EVERS Eberhart (28)
 HILGERS Hildegard (34)
 JACOBS Jacqueline (38)
 JEANÉMART Jérôme (82)
 JONAS Josef (40)
 LAMBERTZ Guido (43)
 MALMENDIER Marc (47)
 MEESSEN Melissa (48)
 RADERMACHER Edgard (58)
 RADERMACHER Hedi (62)
 RADERMECKER Rik (74)
 VAN VEEN Vincent (67)
 ÖSTGES Otto (69)
=========================
<BLANKLINE>





Filtering clients about their coachings
=======================================

>>> translation.activate('en')

The demo database contains 13 clients whe meet the following
conditions:

- the client_state is "Coached"
- client has more than 2 coachings
- at least one of these coachings has been ended

>>> from django.db.models import Count
>>> qs = pcsw.Client.objects.filter(client_state=pcsw.ClientStates.coached)
>>> qs = qs.annotate(coachings_count=Count('coachings_by_client'))
>>> qs = qs.filter(coachings_count__gt=2)
>>> qs = qs.filter(coachings_by_client__end_date__isnull=False)
>>> qs = qs.order_by('id')
>>> qs.count()
13
>>> [obj.pk for obj in qs]
[17, 28, 30, 34, 40, 45, 48, 56, 60, 67, 74, 80, 82]

Let's look at some of these clients more in detail.

>>> def show_coachings(pk):
...     obj = pcsw.Client.objects.get(pk=pk)
...     ses.show('coachings.CoachingsByClient', master_instance=obj, column_names="start_date end_date user primary", header_level=4)

>>> show_coachings(80)
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE +REPORT_UDIFF
Coachings of DUBOIS Robin (80) (Is active)
==========================================
============== ============ ================= =========
 Coached from   until        Coach             Primary
-------------- ------------ ----------------- ---------
 03/03/2012                  Alicia Allmanns   Yes
 08/03/2013     04/10/2013   Hubert Huppertz   No
 04/10/2013                  Mélanie Mélard    No
============== ============ ================= =========
<BLANKLINE>

We can see that Robin is currently coached by Alica and Mélanie, and
that Hubert stopped coaching him on 04.10.2013:


Same view for some other clients:

>>> show_coachings(17)
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE +REPORT_UDIFF
Coachings of AUSDEMWALD Alfons (17) (Is active)
===============================================
============== ============ ================= =========
 Coached from   until        Coach             Primary
-------------- ------------ ----------------- ---------
 03/03/2012                  Alicia Allmanns   No
 13/03/2012     08/03/2013   Hubert Huppertz   No
 08/03/2013     24/10/2013   Mélanie Mélard    No
 24/10/2013                  Caroline Carnol   Yes
============== ============ ================= =========
<BLANKLINE>


>>> show_coachings(67)
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE +REPORT_UDIFF
Coachings of VAN VEEN Vincent (67) (Is active)
==============================================
============== ============ ================= =========
 Coached from   until        Coach             Primary
-------------- ------------ ----------------- ---------
 03/03/2012                  Hubert Huppertz   Yes
 08/03/2013     04/10/2013   Mélanie Mélard    No
 04/10/2013                  Caroline Carnol   No
============== ============ ================= =========
<BLANKLINE>


>>> print(dd.fds(dd.today()))
22/05/2014

When Mélanie opens her :menuselection:`Integration --> Clients` list,
then she sees the following clients:

>>> ses = rt.login('melanie')
>>> ses.show(integ.Clients, column_names="name_column", header_level=4)
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE -REPORT_UDIFF
Integration Clients (Coached, Coached by Mélanie Mélard)
========================================================
============================
 Name
----------------------------
 BRECHT Bernd (78)
 COLLARD Charlotte (19)
 DOBBELSTEIN Dorothée (25)
 DUBOIS Robin (80)
 EMONTS Daniel (29)
 ENGELS Edgar (30)
 GROTECLAES Gregory (33)
 JACOBS Jacqueline (38)
 KAIVERS Karl (42)
 KELLER Karl (79)
 LAZARUS Line (45)
 MALMENDIER Marc (47)
 MEESSEN Melissa (48)
 RADERMACHER Alfons (54)
 RADERMACHER Christian (56)
 RADERMACHER Edgard (58)
 RADERMACHER Guido (60)
 RADERMACHER Hedi (62)
 ÖSTGES Otto (69)
============================
<BLANKLINE>

Robin is there, but Alfons and Vincent aren't.

Here is a list of Mélanies clients on 2013-10-01.  Mélanie can get
this by manually filling that date into the
:attr:`lino_welfare.modlib.pcsw.Clients.end_date` parameter field.

>>> pv = dict(end_date=i2d(20131001))
>>> ses.show(integ.Clients, column_names="name_column", param_values=pv, header_level=4)
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE -REPORT_UDIFF
Integration Clients (Coached, Coached by Mélanie Mélard)
========================================================
========================
 Name
------------------------
 AUSDEMWALD Alfons (17)
 ENGELS Edgar (30)
 EVERS Eberhart (28)
 HILGERS Hildegard (34)
 LAZARUS Line (45)
 RADERMACHER Guido (60)
 VAN VEEN Vincent (67)
========================
<BLANKLINE>


Note that

- Robin is *not* included since Mélanie started coaching him only
  later.
- Vincent *is* now included since Mélanie was coaching him then.



Filtering clients about their notes
===================================


>>> ses = rt.login('robin')

Coached clients who have at least one note:

>>> pv = dict(observed_event=ClientEvents.note)
>>> ses.show(pcsw.CoachedClients, column_names="name_column", param_values=pv)
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE -REPORT_UDIFF
===========================
 Name
---------------------------
 AUSDEMWALD Alfons (17)
 COLLARD Charlotte (19)
 DOBBELSTEIN Dorothée (25)
 DUBOIS Robin (80)
 JEANÉMART Jérôme (82)
===========================
<BLANKLINE>

All clients who have at least one note:

>>> pv = dict(client_state=None, observed_event=ClientEvents.note)
>>> ses.show(pcsw.CoachedClients, column_names="name_column", param_values=pv)
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE -REPORT_UDIFF
===================================
 Name
-----------------------------------
 AUSDEMWALD Alfons (17)
 BASTIAENSEN Laurent (18)
 COLLARD Charlotte (19)
 DEMEULENAERE Dorothée (23)
 DERICUM Daniel (22)
 DOBBELSTEIN Dorothée (25)
 DUBOIS Robin (80)
 ERNST Berta (26)
 JEANÉMART Jérôme (82)
 KASENNOVA Tatjana (114)
 LAHM Lisa (77)
 VANDENMEULENBOS Marie-Louise (75)
===================================
<BLANKLINE>



Coached clients who have at least one note dated 2013-07-25 or later:

>>> pv = dict(start_date=i2d(20130725), observed_event=ClientEvents.note)
>>> ses.show(pcsw.CoachedClients, column_names="name_column", param_values=pv)
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE -REPORT_UDIFF
========================
 Name
------------------------
 AUSDEMWALD Alfons (17)
 DUBOIS Robin (80)
 JEANÉMART Jérôme (82)
========================
<BLANKLINE>

.. show the SQL when debugging:
    >>> # ar = ses.spawn(pcsw.CoachedClients, param_values=pv)
    >>> # print(ar.data_iterator.query)
    >>> # ses.show(ar, column_names="name_column")

All clients who have at least one note dated 2013-07-25 or later:

>>> pv = dict(start_date=i2d(20130725), observed_event=ClientEvents.note)
>>> pv.update(client_state=None)
>>> ses.show(pcsw.CoachedClients, column_names="name_column", param_values=pv)
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE -REPORT_UDIFF
===================================
 Name
-----------------------------------
 AUSDEMWALD Alfons (17)
 DUBOIS Robin (80)
 JEANÉMART Jérôme (82)
 KASENNOVA Tatjana (114)
 LAHM Lisa (77)
 VANDENMEULENBOS Marie-Louise (75)
===================================
<BLANKLINE>


Deleting clients
================


>>> obj = pcsw.Client.objects.get(pk=68)
>>> obj
Client #68 ('ÕUNAPUU Õie (68*)')
>>> # urlparams = dict(an='delete_selected', sr=68)
>>> urlparams = dict(an='delete_selected')
>>> pprint(get_json_dict('robin', "pcsw/Clients/68", **urlparams))
{'alert': False,
 'message': 'Row 68 is not visible here.',
 'success': False,
 'title': '<a href="javascript:Lino.pcsw.Clients.grid.run(null,{ '
          '&quot;base_params&quot;: {  }, &quot;param_values&quot;: { '
          '&quot;aged_from&quot;: null, &quot;aged_to&quot;: null, '
          '&quot;also_obsolete&quot;: false, &quot;and_coached_by&quot;: null, '
          '&quot;and_coached_byHidden&quot;: null, &quot;client_state&quot;: '
          'null, &quot;client_stateHidden&quot;: null, &quot;coached_by&quot;: '
          'null, &quot;coached_byHidden&quot;: null, &quot;end_date&quot;: '
          'null, &quot;gender&quot;: null, &quot;genderHidden&quot;: null, '
          '&quot;nationality&quot;: null, &quot;nationalityHidden&quot;: null, '
          '&quot;observed_event&quot;: null, &quot;observed_eventHidden&quot;: '
          'null, &quot;only_primary&quot;: false, &quot;start_date&quot;: null '
          '} })" style="text-decoration:none">Clients</a>'}

This fails since 20241004 because client 68 is `archived` and therefore not
visible in `pcsw.Clients` unless the user has checked the table parameter
:guilabel:`With archived`. So we need to specify them as well for testing:

>>> urlparams.update(pv=['', '', '', '', 'true', '', '', '', '', '', '', 'true'])
>>> d = get_json_dict('robin', "pcsw/Clients/68", **urlparams)
>>> print(d['message'])
You are about to delete 1 Client
(ÕUNAPUU Õie (68*))
as well as all related volatile records (2 Coachings, 1 Language knowledge, 5 Properties, 2 Phonetic words, 3 ESF Summaries, 1 Address). Are you sure?

>>> d = get_json_dict('rolf', "pcsw/Clients/68", **urlparams)
>>> print(d['message'])
Sie wollen 1 Klient löschen
(ÕUNAPUU Õie (68*))
sowie alle verknüpften unbeständigen Daten (2 Begleitungen, 1 Sprachkenntnis, 5 Eigenschaften, 2 Phonetische Wörter, 3 ESF Summaries, 1 Adresse). Sind Sie sicher?

Client 19 is not archived, so we dont need to check :guilabel:`With archived`:

>>> d = get_json_dict('robin', "pcsw/Clients/19", an='delete_selected', sr=19)
>>> print(d['message'])  #doctest: +NORMALIZE_WHITESPACE
Cannot delete Partner Collard Charlotte because 48 Movements refer to it.
(<QuerySet [Movement #143 ('AAW 1/2014.3'), Movement #144 ('AAW 1/2014.4'),
Movement #153 ('AAW 2/2014.3'), Movement #154 ('AAW 2/2014.4'), Movement #163
('AAW 3/2014.3'), Movement #164 ('AAW 3/2014.4'), Movement #173 ('AAW
4/2014.3'), Movement #174 ('AAW 4/2014.4'), Movement #183 ('AAW 5/2014.3'),
Movement #184 ('AAW 5/2014.4'), Movement #193 ('AAW 6/2014.3'), Movement #194
('AAW 6/2014.4'), Movement #203 ('AAW 7/2014.3'), Movement #204 ('AAW
7/2014.4'), Movement #213 ('AAW 8/2014.3'), Movement #214 ('AAW 8/2014.4'),
Movement #223 ('AAW 9/2014.3'), Movement #224 ('AAW 9/2014.4'), Movement #233
('AAW 10/2014.3'), Movement #234 ('AAW 10/2014.4'), '...(remaining elements
truncated)...']> via partner)


Don't read
==========

Bugfix 20200122 : preferred_width wasn't correctly set, it was 4 for all
choicelists.

>>> rt.models.pcsw.CivilStates.preferred_width
27
