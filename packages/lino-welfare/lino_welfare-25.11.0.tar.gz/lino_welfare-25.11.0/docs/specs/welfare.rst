.. doctest docs/specs/welfare.rst
.. _welfare.specs.welfare:

===========================================
`welfare` : the central Lino Welfare plugin
===========================================

.. currentmodule:: lino_welfare.modlib.welfare


The :mod:`lino_welfare.modlib.welfare` plugin contains PCSW-specific models and
tables that have not yet been moved into a separate module because they are
really very :term:`PCSW` specific.


.. contents:: Contents
   :local:
   :depth: 2

.. include:: /../docs/shared/include/tested.rst

>>> from lino import startup
>>> startup('lino_welfare.projects.gerd.settings.doctests')
>>> from lino.api.doctest import *


Startup handlers
================

.. function:: customize_siteconfig

    Injects application-specific fields to
    :class:`SiteConfig <lino.modlib.system.SiteConfig>`.


.. function:: customize_contacts

    Injects application-specific fields to :mod:`lino_xl.lib.contacts`.


.. function:: customize_sqlite

    Here is how we install case-insensitive sorting in sqlite3.
    Note that this caused noticeable performance degradation...

    Thanks to
    - http://efreedom.com/Question/1-3763838/Sort-Order-SQLite3-Umlauts
    - https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.create_collation
    - http://www.sqlite.org/lang_createindex.html

.. function:: my_details

  Customizes the :term:`detail layout` of countries.Places and
  countries.Countries.

  TODO: move this to a custom layout module.
