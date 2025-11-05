.. doctest docs/specs/art61.rst
.. _welfare.plugins.art61:

======================================
``art61`` : Article 61 job supplyments
======================================

This document assumes you have read the :ref:`end-user documentation
<ug.plugins.art61>`.`

.. currentmodule:: lino_welfare.modlib.art61

.. contents::
   :depth: 2
   :local:

.. include:: /../docs/shared/include/tested.rst

>>> from lino import startup
>>> startup('lino_welfare.projects.mathieu.settings.demo')
>>> from lino.api.doctest import *

Overview
========

This plugin adds the following database models and choicelists:

- :class:`Contract` represents a :term:`article 61 job supplyment`
- :class:`ContractType`
- :class:`Activation`
- :class:`Subsidizations`


The demo database comes with different contract types and subsidization
formulas:

>>> rt.show('art61.ContractTypes')
======================== =================== ====================== ===========
 Désignation              Désignation (de)    Désignation (en)       Référence
------------------------ ------------------- ---------------------- -----------
 Mise à l'emploi art.61   Art.61-Konvention   Art61 job supplyment
======================== =================== ====================== ===========
<BLANKLINE>

>>> rt.show('art61.Subsidizations', language="fr")
======= ========= =================
 value   name      text
------- --------- -----------------
 10      hiring    Aide à l'emploi
 20      tutorat   Tutorat
 30      region    Région Wallonne
======= ========= =================
<BLANKLINE>

Subsidizations are a choicelist, i.e. cannot be edited by the end user.


Document templates
==================

.. xfile:: art61/Contract/contract.body.html

  This file is used as :attr:`body_template
  <lino.modlib.excerpts.Excerpt.body_template>` on the excerpt
  type used to print a
  :class:`lino_welfare.modlib.art61.Contract`.


The printed document
====================

>>> obj = art61.Contract.objects.filter(sub_10_amount__isnull=False).first()
>>> obj.sub_10_amount
Decimal('250.00')

>>> ar = rt.login('romain')
>>> html = ar.get_data_value(obj.printed_by, 'preview')
>>> soup = BeautifulSoup(html, 'lxml')
>>> for h in soup.find_all('h1'):
...     print(str(h))
<h1>Mise à l'emploi art.61
</h1>

>>> for h in soup.find_all('h2'):
...     print(h)
<h2>Article 1</h2>
<h2>Article 2</h2>
<h2>Article 3</h2>
<h2>Article 4 (sans tutorat)</h2>
<h2>Article 5 (activa)</h2>
<h2>Article 6 (activa)</h2>
<h2>Article 7 (sans tutorat)</h2>
<h2>Article 8</h2>
<h2>Article 9</h2>
<h2>Article 10</h2>
<h2>Article 11</h2>
<h2>Article 12</h2>
<h2>Article 13</h2>
<h2>Article 14</h2>



Class reference
===============

.. class:: Contract

    The database model used to represent an :term:`article 61 job supplyment`.

    .. method:: get_subsidizations(self)

        Yield a list of all subsidizations activated for this contract.


.. class:: ContractsByClient

    Shows the *Art61 job supplyments* for this client.


.. class:: ContractType

  This is the homologue of :class:`isip.ContractType
  <lino_welfare.modlib.isip.ContractType>` (see there for
  general documentation).


.. class:: Activation

  .. attribute:: client
  .. attribute:: amount
  .. attribute:: remark
  .. attribute:: start_date
  .. attribute:: end_date
  .. attribute:: company

      The :term:`employer` or :term:`job provider`.

.. class:: Subsidizations

  The choicelist with available subsidization formulas.
