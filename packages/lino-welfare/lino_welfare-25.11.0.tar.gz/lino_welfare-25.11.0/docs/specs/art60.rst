.. doctest docs/specs/welcht/art60.rst
.. _welfare.plugins.art60:

========================================
``art60`` : Article 60§7 job supplyments
========================================

The :mod:`lino_welfare.modlib.art60` plugin adds support for managing Art60 job
supplyments.

.. currentmodule:: lino_welfare.modlib.art60

.. contents::
   :depth: 2
   :local:

.. include:: /../docs/shared/include/tested.rst

>>> from lino import startup
>>> startup('lino_welfare.projects.mathieu.settings.demo')
>>> from lino.api.doctest import *

.. _art60_workplace:

Job providers with multiple workplaces
======================================

The demo data has one example of a :term:`job provider` with multiple
workplaces.

Any organization can become a workplace of a :term:`job provider` by setting its
field :attr:`job_provider` to that :term:`job provider`.

A same organization can't be workplace for multiple job providers.

>>> obj = jobs.JobProvider.objects.get(pk=92)
>>> obj
JobProvider #92 ('Pro Aktiv V.o.G.')

>>> ses = rt.login("robin")
>>> ses.show(jobs.WorkplacesByProvider, master_instance=obj)  #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
`[img add] <…>`__ `ⓘ <…>`__ `⏏ <…>`__ | `Pro Aktiv Nispert <…>`__, `Pro Aktiv Noereth <…>`__, `Pro Aktiv Unterstadt <…>`__

>>> ses.show(jobs.WorkplacesByProvider, master_instance=obj, nosummary=True)
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
====================== ============ =========== =====
 Nom                    Adresse      Téléphone   ID
---------------------- ------------ ----------- -----
 Pro Aktiv Nispert      4700 Eupen               123
 Pro Aktiv Noereth      4700 Eupen               122
 Pro Aktiv Unterstadt   4700 Eupen               121
====================== ============ =========== =====
<BLANKLINE>
