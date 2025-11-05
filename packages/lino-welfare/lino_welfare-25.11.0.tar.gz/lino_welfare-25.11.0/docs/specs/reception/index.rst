.. doctest docs/specs/reception/index.rst
.. include:: /../docs/shared/include/defs.rst
.. _welfare.specs.reception:

======================================================
:mod:`reception` : receive clients at a reception desk
======================================================

The :mod:`lino_welfare.modlib.reception` plugin adds functionality for
receiving guests by an independent reception clerk. It extends the
:mod:`lino_xl.lib.reception` plugin.


.. contents::
   :depth: 2

.. include:: /../docs/shared/include/tested.rst

>>> from lino import startup
>>> startup('lino_welfare.projects.gerd.settings.doctests')
>>> from lino.api.doctest import *
>>> translation.activate('fr')

>>> dd.plugins.reception
<lino_welfare.modlib.reception.Plugin lino_welfare.modlib.reception(needs ['lino.modlib.system', 'lino_xl.lib.cal'])>


.. _welfare.tour.reception:

Scenario
========


Imagine you are the reception clerk.
A visitor enters.

- Visitor: My name is xxx and I'd like to get social help.

    - Clerk: Can I have your id card please?
    - Search manually by name. Create manually a client record.
    - Read the id card.  If the person has a client record in our
      database, then Lino opens the the detail of this record. Otherwise
      it asks whether to create the client.


- Visitor: "My name is xxx, I have an appointment with Roger."
  (You know that Roger is one of the social agents.)

  - Open the clients table
    (:menuselection:`Reception --> Clients`) and find the client.

  - Click on "create visit" action.

  - Consult the *Waiting Visitors* table in your
    dashboard (if necessary, click on the |external-link| icon).


  - Click on "Checkin"


.. _welfare.specs.reception.AppointmentsByPartner:

AppointmentsByPartner
=====================

>>> obj = pcsw.Client.objects.get(pk=28)
>>> print(obj)
EVERS Eberhart (28)

This client has the following appointments.

>>> rt.login('romain').show(reception.AppointmentsByPartner, obj,
...     column_names="event__start_date event__start_time event__user event__summary event__state workflow_buttons",
...     language="en")  #doctest: -REPORT_UDIFF
============ ============ ================= =================== ============ =======================================================
 Start date   Start time   Managed by        Short description   State        Workflow
------------ ------------ ----------------- ------------------- ------------ -------------------------------------------------------
 15/05/2014   13:30:00     Mélanie Mélard    Souper              Took place   [Checkin] **Accepted** → [Present] [Absent] [Excused]
 22/05/2014                Mélanie Mélard    Urgent problem      Published    [Receive] [Checkout] **Waiting** → [Absent] [Excused]
 23/05/2014   09:00:00     Caroline Carnol   Auswertung 2        Suggested    [Checkin] **Accepted** → [Absent] [Excused]
 23/06/2014   09:00:00     Caroline Carnol   Auswertung 3        Suggested    [Checkin] **Accepted** → [Absent] [Excused]
 23/07/2014   09:00:00     Caroline Carnol   Auswertung 4        Suggested    [Checkin] **Accepted** → [Absent] [Excused]
 25/08/2014   09:00:00     Caroline Carnol   Auswertung 5        Suggested    [Checkin] **Accepted** → [Absent] [Excused]
 25/09/2014   09:00:00     Caroline Carnol   Auswertung 6        Suggested    [Checkin] **Accepted** → [Absent] [Excused]
 27/10/2014   09:00:00     Caroline Carnol   Auswertung 7        Suggested    [Checkin] **Accepted** → [Absent] [Excused]
 27/11/2014   09:00:00     Caroline Carnol   Auswertung 8        Suggested    [Checkin] **Accepted** → [Absent] [Excused]
 29/12/2014   09:00:00     Caroline Carnol   Auswertung 9        Suggested    [Checkin] **Accepted** → [Absent] [Excused]
 29/01/2015   09:00:00     Caroline Carnol   Auswertung 10       Suggested    [Checkin] **Accepted** → [Absent] [Excused]
============ ============ ================= =================== ============ =======================================================
<BLANKLINE>


Note that even Theresia who is a reception clerk and has no calendar
functionality can click on the dates to see their detail:

>>> rt.login('theresia').show(reception.AppointmentsByPartner, obj,
...     language="en")  #doctest: +REPORT_UDIFF
================================= ================= =======================================================
 When                              Managed by        Workflow
--------------------------------- ----------------- -------------------------------------------------------
 `Thu 15/05/2014 at 13:30 <…>`__   Mélanie Mélard    [Checkin] **Accepted** → [Present] [Absent] [Excused]
 `Thu 22/05/2014 <…>`__            Mélanie Mélard    [Receive] [Checkout] **Waiting** → [Absent] [Excused]
 `Fri 23/05/2014 at 09:00 <…>`__   Caroline Carnol   [Checkin] **Accepted** → [Absent] [Excused]
 `Mon 23/06/2014 at 09:00 <…>`__   Caroline Carnol   [Checkin] **Accepted** → [Absent] [Excused]
 `Wed 23/07/2014 at 09:00 <…>`__   Caroline Carnol   [Checkin] **Accepted** → [Absent] [Excused]
 `Mon 25/08/2014 at 09:00 <…>`__   Caroline Carnol   [Checkin] **Accepted** → [Absent] [Excused]
 `Thu 25/09/2014 at 09:00 <…>`__   Caroline Carnol   [Checkin] **Accepted** → [Absent] [Excused]
 `Mon 27/10/2014 at 09:00 <…>`__   Caroline Carnol   [Checkin] **Accepted** → [Absent] [Excused]
 `Thu 27/11/2014 at 09:00 <…>`__   Caroline Carnol   [Checkin] **Accepted** → [Absent] [Excused]
 `Mon 29/12/2014 at 09:00 <…>`__   Caroline Carnol   [Checkin] **Accepted** → [Absent] [Excused]
 `Thu 29/01/2015 at 09:00 <…>`__   Caroline Carnol   [Checkin] **Accepted** → [Absent] [Excused]
================================= ================= =======================================================
<BLANKLINE>



.. _welfare.specs.reception.AgentsByClient:

AgentsByClient
==============

The :class:`AgentsByClient
<lino_welfare.modlib.reception.models.AgentsByClient>` table shows the
users for whom a reception clerk can make an appointment with a given
client. Per user you have two possible buttons: (1) a prompt
consultation (client will wait in the lounge until the user receives
them) or (2) a scheduled appointment in the user's calendar.

Client #28 is `ClientStates.coached` and has two active coachings:

>>> obj = pcsw.Client.objects.get(pk=28)
>>> print(obj)
EVERS Eberhart (28)
>>> obj.client_state
<clients.ClientStates.coached:30>

>>> rt.login('romain').show(reception.AgentsByClient, obj, language='en')
================= =============== =======================================
 Agent             Coaching type   Actions
----------------- --------------- ---------------------------------------
 Hubert Huppertz   General         `[img hourglass] <…>`__ **Find date**
 Caroline Carnol   Integ           `[img hourglass] <…>`__ **Find date**
================= =============== =======================================
<BLANKLINE>


Client 257 is a `ClientStates.newcomer` and *not* coached. In that
case Lino shows all social agents who care for newcomers (i.e. who
have a non-zero :attr:`newcomer_quota
<lino_welfare.modlib.users.User.newcomer_quota>`).


>>> obj = pcsw.Client.objects.get(first_name="Bruno", last_name="Braun")
>>> print(obj)
BRAUN Bruno (160)
>>> obj.client_state
<clients.ClientStates.newcomer:10>

>>> reception.AgentsByClient.label
'Créer rendez-vous avec'

>>> rt.login('romain').show(reception.AgentsByClient, obj, language='en')
================= =============== =======================================
 Agent             Coaching type   Actions
----------------- --------------- ---------------------------------------
 Alicia Allmanns   Integ           `[img hourglass] <…>`__ **Find date**
 Caroline Carnol   General         `[img hourglass] <…>`__ **Find date**
 Hubert Huppertz   Integ           `[img hourglass] <…>`__
 Judith Jousten    General         `[img hourglass] <…>`__ **Find date**
================= =============== =======================================
<BLANKLINE>

Now let's have a closer look at the action buttons in the third column
of above table.  This column is defined by a
:func:`lino.core.fields.displayfield`.

It has up to two actions (labeled `Visit` and `Find date`)

We are going to inspect the AgentsByClient panel.

>>> soup = get_json_soup('romain', 'pcsw/Clients/28', 'reception.AgentsByClient1')

It contains a table, and we want the cell at the first data row and
third column:

>>> td = soup.table.tbody.tr.contents[2]

The first button ("Visit") is here:

>>> btn = td.contents[0]
>>> print(btn.contents)
[<img alt="hourglass" src="/static/images/mjames/hourglass.png"/>]

And yes, the `href` attribute is a JavaScript snippet:

>>> print(btn['href'])
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE +REPORT_UDIFF
javascript:Lino.pcsw.Clients.create_visit.run(null,...)

Now let's inspect the three dots (`...`).

>>> dots = btn['href'][51:-1]
>>> print(dots)  #doctest: +ELLIPSIS
{ ... }

They are a big "object" (in Python we call it a `dict`):

>>> d = AttrDict(json.loads(dots))

The object has 4 keys:

>>> sorted(d.keys())
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE -REPORT_UDIFF -SKIP
['base_params', 'field_values', 'param_values', 'record_id']

>>> d.record_id
28
>>> pprint(d.base_params)
{}

..
  >> d.base_params['mt']
  ... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE -REPORT_UDIFF +SKIP
  5...
  >> d.base_params['mk']
  28

>>> pprint(d.field_values)
{'summary': '',
 'user': 'Hubert Huppertz',
 'userHidden': 5,
 'waiting_number': ''}


**Now the second action (Find date):**

The button is here:

>>> btn = td.contents[2]
>>> print(btn.contents)
[<img alt="calendar" src="/static/images/mjames/calendar.png"/>]

And also here, the `href` attribute is a javascript snippet:

>>> print(btn['href'])
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE +REPORT_UDIFF
javascript:Lino.extensible.CalendarPanel.grid.run(null,{ "base_params": { "prj": 28, "su": 5 }, "su": 5 })


This one is shorter, so we don't need to parse it for inspecting it.
Note that `su` (subst_user) is the id of the user whose calendar is to
be displayed.  And `prj` will become the value of the `project` field
if a new event would be created.



Some tables
===========

In the following tables we remove some columns which are not relevant
here. Here we define the keyword arguments we are going to pass to the
:meth:`show <lino.core.requests.BaseRequest.show>` method:

>>> kwargs = dict(language="en")
>>> kwargs.update(column_names="client position workflow_buttons")

Social workers can see on their computer who is waiting for them in
the lounge:

>>> rt.login('alicia').show(reception.MyWaitingVisitors, **kwargs)
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE -REPORT_UDIFF
======================== ========== =======================================================
 Client                   Position   Workflow
------------------------ ---------- -------------------------------------------------------
 HILGERS Hildegard (34)   1          [Receive] [Checkout] **Waiting** → [Absent] [Excused]
 KAIVERS Karl (42)        2          [Receive] [Checkout] **Waiting** → [Absent] [Excused]
======================== ========== =======================================================
<BLANKLINE>

>>> rt.login('hubert').show(reception.MyWaitingVisitors, **kwargs)
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE -REPORT_UDIFF
==================== ========== =======================================================
 Client               Position   Workflow
-------------------- ---------- -------------------------------------------------------
 EMONTS Daniel (29)   1          [Receive] [Checkout] **Waiting** → [Absent] [Excused]
 JONAS Josef (40)     2          [Receive] [Checkout] **Waiting** → [Absent] [Excused]
 LAZARUS Line (45)    3          [Receive] [Checkout] **Waiting** → [Absent] [Excused]
==================== ========== =======================================================
<BLANKLINE>

Theresia is the reception clerk. She has no visitors on her own.

>>> rt.login('theresia').show(reception.MyWaitingVisitors, **kwargs)
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE -REPORT_UDIFF
<BLANKLINE>
No data to display
<BLANKLINE>

Theresia is rather going to use the overview tables:

>>> kwargs.update(column_names="client event__user workflow_buttons")
>>> rt.login('theresia').show(reception.WaitingVisitors, **kwargs)
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE -REPORT_UDIFF
======================== ================= =======================================================
 Client                   Managed by        Workflow
------------------------ ----------------- -------------------------------------------------------
 EMONTS Daniel (29)       Hubert Huppertz   [Receive] [Checkout] **Waiting** → [Absent] [Excused]
 EVERS Eberhart (28)      Mélanie Mélard    [Receive] [Checkout] **Waiting** → [Absent] [Excused]
 HILGERS Hildegard (34)   Alicia Allmanns   [Receive] [Checkout] **Waiting** → [Absent] [Excused]
 JACOBS Jacqueline (38)   Judith Jousten    [Receive] [Checkout] **Waiting** → [Absent] [Excused]
 JONAS Josef (40)         Hubert Huppertz   [Receive] [Checkout] **Waiting** → [Absent] [Excused]
 KAIVERS Karl (42)        Alicia Allmanns   [Receive] [Checkout] **Waiting** → [Absent] [Excused]
 LAMBERTZ Guido (43)      Mélanie Mélard    [Receive] [Checkout] **Waiting** → [Absent] [Excused]
 LAZARUS Line (45)        Hubert Huppertz   [Receive] [Checkout] **Waiting** → [Absent] [Excused]
======================== ================= =======================================================
<BLANKLINE>

>>> rt.login('theresia').show(reception.BusyVisitors, **kwargs)
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE -REPORT_UDIFF
======================== ================= ==========================================
 Client                   Managed by        Workflow
------------------------ ----------------- ------------------------------------------
 BRECHT Bernd (78)        Hubert Huppertz   [Checkout] **Busy** → [Absent] [Excused]
 COLLARD Charlotte (19)   Alicia Allmanns   [Checkout] **Busy** → [Absent] [Excused]
 DUBOIS Robin (80)        Mélanie Mélard    [Checkout] **Busy** → [Absent] [Excused]
 ENGELS Edgar (30)        Judith Jousten    [Checkout] **Busy** → [Absent] [Excused]
======================== ================= ==========================================
<BLANKLINE>



>>> rt.login('theresia').show(reception.GoneVisitors, **kwargs)
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE -REPORT_UDIFF
=========================== ================= ===============================
 Client                      Managed by        Workflow
--------------------------- ----------------- -------------------------------
 MALMENDIER Marc (47)        Alicia Allmanns   **Gone** → [Absent] [Excused]
 KELLER Karl (79)            Judith Jousten    **Gone** → [Absent] [Excused]
 JEANÉMART Jérôme (82)       Mélanie Mélard    **Gone** → [Absent] [Excused]
 GROTECLAES Gregory (33)     Hubert Huppertz   **Gone** → [Absent] [Excused]
 EMONTS-GAST Erna (53)       Alicia Allmanns   **Gone** → [Absent] [Excused]
 DOBBELSTEIN Dorothée (25)   Judith Jousten    **Gone** → [Absent] [Excused]
 AUSDEMWALD Alfons (17)      Mélanie Mélard    **Gone** → [Absent] [Excused]
=========================== ================= ===============================
<BLANKLINE>





Create a visit
==============

>>> print(py2rst(pcsw.Clients.create_visit))
Enregistrer consultation
(main) [visible for all]: **Utilisateur** (user), **Raison** (summary), **N° d'attente** (waiting_number)

>>> show_fields(pcsw.Clients.create_visit, all=True)
... #doctest: +NORMALIZE_WHITESPACE
- Utilisateur (user) :
- Raison (summary) :
- N° d'attente (waiting_number) :

>>> show_choices('romain', '/apchoices/pcsw/Clients/create_visit/user')
Alicia Allmanns
Caroline Carnol
Hubert Huppertz
Judith Jousten




Assign to me
============



Do not read
===========


When the primary key is a OneToOneField
---------------------------------------

Before :ticket:`2436`, a OneToOneField resulted in a StoreField giving
a single atomic value (the database object).


The primary key of a client is `id`:

>>> pk = pcsw.Client._meta.get_field('id')
>>> pk
<django.db.models.fields.BigAutoField: id>

>>> pk = pcsw.Client._meta.pk
>>> pk
<django.db.models.fields.related.OneToOneField: person_ptr>


>>> pk.primary_key
True

>>> ptr = pcsw.Client._meta.get_field('person_ptr')
>>> ptr
<django.db.models.fields.related.OneToOneField: person_ptr>
>>> ptr.primary_key
True

>>> ah = reception.Clients.get_handle()
>>> pprint(ah.store.grid_fields)
((virtual)DisplayStoreField 'name_column',
 (virtual)DisplayStoreField 'address_column',
 StoreField 'national_id',
 (virtual)DisplayStoreField 'workflow_buttons',
 OneToOneStoreField 'person_ptr',
 DisabledFieldsStoreField 'disabled_fields',
 DisableEditingStoreField 'disable_editing',
 RowClassStoreField 'row_class')

>>> ah.store.pk
<django.db.models.fields.related.OneToOneField: person_ptr>

>>> ah.store.pk_index
4
>>> ah.store.grid_fields[4]
OneToOneStoreField 'person_ptr'

>>> ses = rt.login("robin")
>>> ar = reception.Clients.create_request(user=ses.user)
>>> obj = pcsw.Client.objects.get(pk=17)
>>> lst = ah.store.row2list(ar, obj)
>>> #lst

>>> lst[ah.store.pk_index]
Person #17 ('M. Alfons AUSDEMWALD')


.. _welfare.specs.20150715:

Reception clerk sees "Career" tab
=================================

>>> from lino.utils.jsgen import with_user_profile

The following helped us to understand and solve ticket :ticket:`340`
(discovered :blogref:`20150714`).

>>> translation.activate('en')

The problem: A reception clerk in Eupen
(:mod:`lino_welfare.projects.gerd`) should not see the career tab of
a client because the :attr:`required_roles
<lino.core.permissions.Permittable.required_roles>` of that panel
include :class:`IntegUser
<lino_welfare.modlib.integ.roles.IntegUser>`.  But they saw it
nevertheless:

.. image:: 20150715.png

A reception clerk is not an integration agent:

>>> from lino_welfare.modlib.welfare.user_types import *
>>> isinstance(ReceptionClerk, IntegUser)
False

>>> ia_user_type = users.UserTypes.get_by_value('100')
>>> print(ia_user_type)
100 (Integration agent)

>>> rc_user_type = users.UserTypes.get_by_value('210')
>>> print(rc_user_type)
210 (Reception clerk)


We are talking about the detail layout of a client, defined by
:class:`lino_weleup.lib.pcsw.models.ClientDetail`:

>>> dtl = rt.models.pcsw.Clients.detail_layout
>>> dtl  #doctest: +ELLIPSIS
<lino_weleup.lib.pcsw.models.ClientDetail object at ...>
>>> dtl.__class__
<class 'lino_weleup.lib.pcsw.models.ClientDetail'>

>>> lh = dtl.get_layout_handle()
>>> print(lh)
LayoutHandle for lino_weleup.lib.pcsw.models.ClientDetail on lino_welfare.modlib.pcsw.models.Clients

Let's get the `career` panel. It is a :class:`lino.core.elems.Panel`:

>>> # career_panel = lh.main.find_by_name('career')
>>> career_panel = with_user_profile(ia_user_type, lh.main.find_by_name, 'career')
>>> career_panel
<Panel career in lino_weleup.lib.pcsw.models.ClientDetail on lino_welfare.modlib.pcsw.models.Clients>
>>> career_panel.__class__
<class 'lino.core.elems.Panel'>

To see this panel, you need to be an integration agent:

>>> career_panel.required_roles == {IntegUser}
True

Theresia is a reception clerk
(:class:`lino_welfare.modlib.welfare.user_types.ReceptionClerk`):

>>> theresia = users.User.objects.get(username="theresia")
>>> theresia.user_type.role  #doctest: +ELLIPSIS
<lino_welfare.modlib.welfare.user_types.ReceptionClerk object at ...>

And that's not the role required to view this panel:

>>> theresia.user_type.has_required_roles(career_panel.required_roles)
False

And thus this panel is not visible for her:

>>> career_panel.get_view_permission(theresia.user_type)
False

Note that the Panel objects which are not visible continue to be in
`lh.main.elements`:

>>> print(' '.join([e.name for e in lh.main.elements]))
... #doctest: +NORMALIZE_WHITESPACE
general contact coaching aids_tab work_tab_1 career languages
competences contracts history calendar accounting.MovementsByProject1 misc cbss debts

Lino filters removes them only when generating the js files, IOW
during :func:`lino.utils.jsgen.py2js`:

>>> from lino.utils.jsgen import with_user_profile
>>> from lino.utils.jsgen import py2js, declare_vars
>>> def f():
...     print(py2js(lh.main.elements))
>>> with_user_profile(theresia.user_type, f)
... #doctest: +NORMALIZE_WHITESPACE +SKIP
[ general_panel1172, contact_panel1199, coaching_panel1428, aids_tab_panel1543, work_tab_1_panel1571, contracts_panel2318, history_panel2321, calendar_panel2401, misc_panel2442 ]

.. We skip above test because it is bothersome to adapt the names whenever a
   new actor is added, and because probably it doesn't actually doesn't cover
   anything.


I can even render the :file:`lino*.js` files (at least once):

>>> class W:
...     def write(self, s):
...         if "career" in s: print(s)
>>> w = W()
>>> def f():
...     dd.plugins.extjs.renderer.write_lino_js(w)
>>> with_user_profile(theresia.user_type, f)
... #doctest: +NORMALIZE_WHITESPACE

So until now everything looks okay.

The problem was that until :blogref:`20150716`, :meth:`write_lino_js`
left the requirements of our career panel modified (loosened) after
having run.  So the following was `False` only after the first time
and `True` all subsequent times:

>>> theresia.user_type.has_required_roles(career_panel.required_roles)
False
>>> theresia.user_type.has_required_roles(career_panel.required_roles)
False


.. _welfare.specs.20200825:

Cannot select a coaching type for user
======================================

The following failed before 20200825.

>>> show_choices('romain', '/choices/users/Users/coaching_type')
<br/>
SSG
SI
Médiation de dettes


Expected guests
===============


>>> rt.show(reception.ExpectedGuests, language="en")
... #doctest: +REPORT_UDIFF
================== ================= =================== ==============
 Partner            Managed by        Short description   Workflow
------------------ ----------------- ------------------- --------------
 Mélard Mélanie     Hubert Huppertz   Évaluation 13       **Invited**
 Brecht Bernd       Hubert Huppertz   Évaluation 13       **Accepted**
 Jeanémart Jérôme   Hubert Huppertz   Auswertung 2        **Accepted**
================== ================= =================== ==============
<BLANKLINE>
