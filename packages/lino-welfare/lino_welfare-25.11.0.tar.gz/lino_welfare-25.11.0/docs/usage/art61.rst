.. _ug.plugins.art61:

=====================================
``art61`` :  Art 61 job supplyments
=====================================

The :mod:`lino_welfare.modlib.art61` plugin adds support for managing
:term:`article 61 job supplyments <article 61 job supplyment>`.

Technical docs in :ref:`welfare.plugins.art61`.

.. contents::
   :local:
   :depth: 1

Glossary
========

.. glossary::

  article 61 job supplyment

    (French: *Mise au travail en application de l'article 61*).

    A :term:`job supplyment` regulated by article 61.

    A project where the PCSW collaborates with a third-party employer in order
    to fulfill its duty of supplying a job for a coached client. (`www.mi-is.be
    <http://www.mi-is.be/be-fr/cpas/article-61>`__)

    An agreement between the PCSW and a private company about one of the clients
    of the PCSW.

    Represented in the database by rows of :class:`art61.Contract
    <lino_welfare.modlib.art61.Contract>`.
