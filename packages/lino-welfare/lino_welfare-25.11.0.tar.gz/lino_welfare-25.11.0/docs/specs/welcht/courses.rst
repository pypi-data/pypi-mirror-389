.. doctest docs/specs/welcht/courses.rst
.. _welfare.specs.courses2:

=======================
``courses`` : Workshops
=======================

This is about *internal* courses (:mod:`lino_welcht.lib.courses`), not to mixed
up with :mod:`lino_welcht.lib.xcourses`.


.. contents::
    :local:
    :depth: 1

.. include:: /../docs/shared/include/tested.rst

>>> from lino import startup
>>> startup('lino_welfare.projects.mathieu.settings.demo')
>>> from lino.api.doctest import *

>>> dd.plugins.courses
<lino_welcht.lib.courses.Plugin lino_welcht.lib.courses>

>>> dd.plugins.courses.extends_models
['Course', 'Line', 'Enrolment']

We call them "workshops":


>>> def show_labels():
...     print(dd.plugins.courses.verbose_name)
...     print(courses.Course._meta.verbose_name)
...     print(courses.Enrolment._meta.verbose_name)
...     print(courses.Enrolment._meta.get_field("pupil").verbose_name)

>>> with translation.override('en'):
...     show_labels()
Workshops
Workshop
Enrolment
Participant

>>> with translation.override('fr'):
...     show_labels()
Ateliers
Atelier
Inscription
Participant

The "teacher" (person responsible for a workshop) must be a :term:`site user`
(not just any person). And the "pupils" of a workshop must be clients (not just
any persons):

>>> dd.get_plugin_setting('courses', 'teacher_model')
<class 'lino_welfare.modlib.users.models.User'>

>>> dd.get_plugin_setting('courses', 'pupil_model')
<class 'lino_welfare.modlib.pcsw.models.Client'>


>>> rt.show(rt.models.courses.Activities)
=============== ============= ============================= ============= ======= ===============
 Date de début   Désignation   Série d'ateliers              Instructeur   Local   Workflow
--------------- ------------- ----------------------------- ------------- ------- ---------------
 12/05/2014                    Cuisine                                             **Brouillon**
 12/05/2014                    Créativité                                          **Brouillon**
 12/05/2014                    Notre premier bébé                                  **Brouillon**
 12/05/2014                    Mathématiques                                       **Brouillon**
 12/05/2014                    Français                                            **Brouillon**
 12/05/2014                    Activons-nous!                                      **Brouillon**
 03/11/2013                    Intervention psycho-sociale                         **Brouillon**
=============== ============= ============================= ============= ======= ===============
<BLANKLINE>


>>> print(rt.models.courses.Activities.params_layout.main)
... #doctest: +NORMALIZE_WHITESPACE +REPORT_UDIFF
topic line user teacher state
    room can_enroll:10 start_date end_date show_exposed

>>> demo_get('robin', 'choices/courses/Activities/topic', 'count rows', 0)
>>> demo_get('robin', 'choices/courses/Activities/teacher', 'count rows', 5)
>>> demo_get('robin', 'choices/courses/Activities/user', 'count rows', 12)

Yes, the demo database has no topics defined:

>>> rt.show(rt.models.courses.Topics)
No data to display


>>> course = courses.Course.objects.get(pk=1)
>>> print(course)
Kitchen (12/05/2014)

>>> # rt.show(rt.models.cal.EntriesByController, course)
>>> ar = cal.EntriesByController.create_request(course)
>>> ar.show()
================================ =================== ================= ===== =================
 When                             Short description   Managed by        No.   Workflow
-------------------------------- ------------------- ----------------- ----- -----------------
 `Mon 16/06/2014 (08:00) <…>`__   5                   Hubert Huppertz   5     **? Suggested**
 `Mon 02/06/2014 (08:00) <…>`__   4                   Hubert Huppertz   4     **? Suggested**
 `Mon 26/05/2014 (08:00) <…>`__   3                   Hubert Huppertz   3     **? Suggested**
 `Mon 19/05/2014 (08:00) <…>`__   2                   Hubert Huppertz   2     **? Suggested**
 `Mon 12/05/2014 (08:00) <…>`__   1                   Hubert Huppertz   1     **? Suggested**
================================ =================== ================= ===== =================
<BLANKLINE>


>>> event = ar[4]
>>> print(event)
 1 (12.05.2014 08:00)

>>> cal.GuestsByEvent.create_request(event).show()
=================================== ========= ============= ========
 Partner                             Role      Workflow      Remark
----------------------------------- --------- ------------- --------
 Bastiaensen Laurent                 Visitor   **Invited**
 Dobbelstein Dorothée                Visitor   **Invited**
 Dobbelstein-Demeulenaere Dorothée   Visitor   **Invited**
 Emonts Erich                        Visitor   **Invited**
 Gernegroß Germaine                  Visitor   **Invited**
 Jacobs Jacqueline                   Visitor   **Invited**
 Johnen Johann                       Visitor   **Invited**
 Laschet Laura                       Visitor   **Invited**
 Meessen Melissa                     Visitor   **Invited**
 Radermacher Christian               Visitor   **Invited**
 Vandenmeulenbos Marie-Louise        Visitor   **Invited**
=================================== ========= ============= ========
<BLANKLINE>



>>> with translation.override('fr'):
...   show_fields(rt.models.courses.Course, 'start_date end_date')
... #doctest: +NORMALIZE_WHITESPACE
- Date de début (start_date) : La date de début de la première rencontre à générer.
- Date de fin (end_date) : La date de fin de la première rencontre à générer.
  Laisser vide si les rencontres durent moins d'une journée.


Don't read on
=============

Verify that users can create new courses:

>>> url = '/api/courses/MyActivities?an=insert'
>>> response = test_client.get(url, REMOTE_USER='romain')
>>> response.status_code
200
