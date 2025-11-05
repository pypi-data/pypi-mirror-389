.. _ug.plugins.jobs:

===========================
``jobs`` : Job supplyments
===========================

This plugin is used to manage :term:`suppliable jobs <suppliable job>` offered
by the PCSW to its clients in collaboration with :term:`job providers <job
provider>` or external :term:`employers <employer>`.

The different types of job supplyments are implemented by separate plugins:

- :ref:`ug.plugins.art60`
- :ref:`ug.plugins.art61`

A :term:`job provider` is an organisation where the work will be executed. They
are not necessarily also the :term:`employer`. It may be either some public
service or a private company.

In most cases, the PSWC acts as the legal employer.  It can employ the person in
its own services (internal contracts) or put him or her at the disposal of a
third party employer (external contracts). (Adapted from `mi-is.be
<http://www.mi-is.be/en/public-social-welfare-centers/article-60-7>`__).


.. currentmodule:: lino_welfare.modlib.jobs

.. contents::
   :local:
   :depth: 1

Overview
========

.. glossary::

  suppliable job

    A position where a person exercises a specified function at a given
    :term:`job provider` or :term:`employer`.

    Database model: :class:`jobs.Job <Job>`.

  job provider

    (French *Service utilisateur*, German *Stellenabieter*)

    The legal person that supplies the job in case of an :term:`article 60 job
    supplyment` (where the PCSW acts as :term:`employer`).

    The :term:`job provider` doesn't pay the salary but is responsible for supervision.

    Database model: :class:`jobs.JobProvider <JobProvider>`.

  employer

    (French *Employeur*, German *Arbeitgeber*)

    A legal person that pays the salary.

    Database model: :class:`jobs.Employer <Employer>`.

  job supplyment

    (French *Mise à l'emploi*, German *Art-60§7-Konvention*).

    An :term:`integration contract` where the :term:`PCSW` arranges a job for a
    client, with the aim to bring this person back into the social security
    system and the employment process.

    Database model:
    :class:`jobs.Contract <Contract>` or
    :class:`art60.Contract <lino_welfare.modlib.art60.Contract>` or
    :class:`art61.Contract <lino_welfare.modlib.art61.Contract>`

  social economy project

    Organisation bénéficiant de l'agrément « Initiative d'économie sociale »
    octroyé par la Wallonie.

    Cet agrément vise à soutenir la mise en place de projets à finalité sociale
    et l'insertion socioprofessionnelle de travailleurs peu qualifiés par le
    biais d'une activité économique.
    https://economie.wallonie.be/Dvlp_Economique/Economie_sociale/AgrementES.html

    A :term:`social economy project` is marked by the checkbox
    :attr:`JobProvider.is_social` or :attr:`Employer.is_social`.
