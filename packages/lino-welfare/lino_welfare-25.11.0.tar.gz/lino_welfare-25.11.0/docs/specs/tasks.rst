.. doctest docs/specs/tasks.rst
.. _welfare.specs.tasks:

==============
Calendar tasks
==============

Tasks are a part of the :mod:`lino_welfare.modlib.cal` plugin.

.. contents::
   :local:

.. include:: /../docs/shared/include/tested.rst

>>> from lino import startup
>>> startup('lino_welfare.projects.mathieu.settings.demo')
>>> from lino.api.doctest import *


My tasks
========

The :guilabel:`My tasks` table (:class:`lino_xl.lib.cal.MyTasks`) is visible in
the dashboard.

This table shows tasks that are due in the next **30** days.  These edge values
may get customized locally in the :xfile:`settings.py` file. Our demo project
sets :attr:`mytasks_start_date <lino_xl.lib.cal.Plugin.mytasks_start_date>` to
*-30*, which means that users don't see tasks that are older than 30 days.

>>> print(dd.plugins.cal.mytasks_start_date)
None
>>> dd.plugins.cal.mytasks_end_date
30

For example Mélanie has one task in that table:

>>> rt.login('melanie').show(cal.MyTasks)
========== =============== ============================= ============================= =========================
 Priorité   Date de début   Description brève             Workflow                      Bénéficiaire
---------- --------------- ----------------------------- ----------------------------- -------------------------
 Normale    12/06/2014      Projet termine dans un mois   **☐ à faire** → [☑] [☒] [⚠]   RADERMACHER Edgard (58)
========== =============== ============================= ============================= =========================
<BLANKLINE>


Actually Mélanie has more than one open tasks. But they are all more than 30
days away in the future.  If she manually sets :attr:`end_date
<lino_xl.lib.cal.Tasks.end_date>` to blank then she sees them.

>>> pv = dict(end_date=None)
>>> rt.login('melanie').show(cal.MyTasks, param_values=pv, language="en")
========== ============ ============================= =========================== =========================
 Priority   Start date   Short description             Workflow                    Client
---------- ------------ ----------------------------- --------------------------- -------------------------
 Normal     12/06/2014   Projet termine dans un mois   **☐ To do** → [☑] [☒] [⚠]   RADERMACHER Edgard (58)
 Normal     01/11/2014   Projet termine dans un mois   **☐ To do** → [☑] [☒] [⚠]   AUSDEMWALD Alfons (17)
 Normal     12/12/2014   Projet termine dans un mois   **☐ To do** → [☑] [☒] [⚠]   ENGELS Edgar (30)
 Normal     02/02/2015   Projet termine dans un mois   **☐ To do** → [☑] [☒] [⚠]   RADERMACHER Guido (60)
 Normal     09/02/2015   Projet termine dans un mois   **☐ To do** → [☑] [☒] [⚠]   LAZARUS Line (45)
 Normal     28/02/2015   Projet termine dans un mois   **☐ To do** → [☑] [☒] [⚠]   ÖSTGES Otto (69)
 Normal     23/03/2015   Projet termine dans un mois   **☐ To do** → [☑] [☒] [⚠]   MEESSEN Melissa (48)
 Normal     11/04/2015   Projet termine dans un mois   **☐ To do** → [☑] [☒] [⚠]   RADERMACHER Hedi (62)
 Normal     21/04/2015   Projet termine dans un mois   **☐ To do** → [☑] [☒] [⚠]   RADERMACHER Edgard (58)
 Normal     08/05/2015   Projet termine dans un mois   **☐ To do** → [☑] [☒] [⚠]   JACOBS Jacqueline (38)
========== ============ ============================= =========================== =========================
<BLANKLINE>


Note that tasks are sorted ascending by start date.
