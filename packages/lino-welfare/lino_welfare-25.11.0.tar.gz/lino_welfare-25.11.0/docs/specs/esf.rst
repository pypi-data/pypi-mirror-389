.. doctest docs/specs/esf.rst
.. _welfare.specs.esf:

==============================
``esf`` : European Social Fund
==============================

.. currentmodule:: lino_welfare.modlib.esf

The :mod:`lino_welfare.modlib.esf` plugin helps writing yearly reports for the
`European Social Fund <http://ec.europa.eu/esf/main.jsp?catId=35&langId=en>`_
(ESF).


.. contents::
   :local:
   :depth: 2

.. include:: /../docs/shared/include/tested.rst

>>> from lino import startup
>>> startup('lino_welfare.projects.mathieu.settings.demo')
>>> from lino.api.doctest import *


Dependencies
============

This plugin needs :mod:`lino.modlib.summaries` and
:mod:`lino.modlib.weasyprint`: A client summary is a subclass of
:class:`lino.modlib.summaries.MonthlySlaveSummary`

>>> dd.plugins.esf.needs_plugins
['lino.modlib.summaries', 'lino.modlib.weasyprint']

This plugin injects
a field :attr:`has_esf
<lino_welfare.modlib.pcsw.Client.has_esf>` to every *client*
and a field :attr:`esf_field
<lino_welfare.modlib.cal.Entry.esf_field>` to every *calendar entry type*.

Client summaries
================

A **client summary** is a database entry holding statistical information for a
given year about a given client.  Client summaries are generated database
content. Every client summary can be printed as a document called "Fiche
stagiaire".

.. class:: ClientSummary

    The Django model that represents a *client summary*.

    It is a :class:`lino.modlib.summaries.MonthlySlaveSummary` and
    :class:`lino_xl.lib.excerpts.Certifiable`.


List of the data fields per *client summary*:

- `client` : a pointer to the :class:`Client
  <lino_welfare.modlib.pcsw.models.Client>`

- The observed period (`start_date` and `end_date`, usually one
  calendar year)

The remaining fields are configured in the :class:`SummaryFields` choicelist.

- Situation professionnelle à l’entrée: Bénéficiaire CPAS (ce sera
  uniquement cette appellation)

- Inoccupé(e) depuis : date field filled from «Cherche du travail
  depuis» date FSE (onglet RAE))

- Ménage: combo box ("ménage sans emploi", "ménage dont au moins 1
  personne occupe un emploi")

- Enfant(s) à charge: checkbox

- Niveau diplôme: combobox (Sans diplôme - CEB - CE1D - CESI -
  CESS-CQ6-CE6P-7P - Bachelier-graduat - Master-licence -
  Enseignement secondaire complémentaire - Non reconnu – inconnu)

- Handicap reconnu: checkbox

- Autre difficulté rencontrée:	checkbox

- Date d’entrée: reprendre date de l’atelier « Séance d’information »
- Contrat de travail sous art. 60 depuis le: date field filled from `jobs.Contract`
- Date de sortie: Onglet intervenant – module intervention date « au »
- Type de sortie: Onglet intervenants – Module intervention - « Cause d’abandon »

- Acquis en fin de formation : filled from Onglet Compétence – Module
  compétences professionnelles - case « Preuve de qualification »

- Attestation de participation: combobox (Epreuve d’évaluation réussie
  sans titre spécifique - Certificat sectoriel - Titre de validation
  des compétences - Certificat de valorisation de l’acquis de
  l’expérience - Diplôme ou certificat délivré par un établissement
  scolaire - Pas d’acquis)

.. class:: Summaries

    Base class for all tables on :class:`ClientSummary`.

.. class:: AllSummaries

    Lists all ESF summaries for all clients.

.. class:: SummariesByClient

    Lists the ESF summaries for a given client.



HoursByDossier
==============

And then the module provides a way for defining a series of
"statistical numbers" which represent the activity of that client
during a given period.

For most fields this is the total duration of presences (:class:`Guest
<lino_xl.lib.cal.models.Guest>` objects) of that client.

- Information : Séance d’info. (2h FSE)

- Orientation - suivi:

  - Entretien individuel (1h FSE)
  - Evaluation formation externe et art.61 (1h FSE)

- Mobilisation : S.I.S. agréé (en fonction de la participation à un ou
  plusieurs ateliers)

- Apprentissage de base

  - Test de niveau (math, français, informatique) (3h FSE)
  - Initiation informatique (3h FSE)
  - Mobilité (3h FSE)
  - Remédiation mathématique et français (3h FSE)

- Module projet : Activons-nous (3h FSE)

- Mise en situation professionnelle Case « Heure » à ajouter au module

- Recherche d’emploi : Cyber emploi (à discuter)

- Mise à l’emploi sous contrat art.60§7 (Sélection des années – case Heure)

This distribution will probably require a choicelist with one choice
for each field.

These fields will probably not be columns of a slave table but
(dynamicaly generated) database fields in the Dossier model.

There will also be a pointer to
(one entry per `courses.Line` as it seems), but some columns are
special and require a hard-coded method.



Notes de discussion
===================

- Par bénéficiaire il peut y avoir plusieurs fiches stagiaire au cours
  du temps. En principe une fiche pour chaque stage.
- Où dans le détail du bénéficaire faut-il afficher ce panneau avec
  les "fiches stagiaire"? --> dans l'onglet "Historique"
- Idéal serait d'avoir une checkbox "Générer fiches stagiaire" par
  bénéficiaire.

- Bouton "Remplir les données"

- la fiche est un document à usage interne utilisé par Sandra pour
  encoder les données dans un fichier Excel protégé issu par X.

- Colonne "Mise en situation professionnelle" : calculer les heures
  par stage d'immersion, en fonction des dates de début et de fin et
  de l'horaire de travail.

- Colonne "Recherche d'emploi" : Somme des présences aux ateliers
  "Cyber-emploi", mais pour ces ateliers on note les heures d'arrivée
  et de départ par participation.

- Colonne "Mise à l'emploi sous contrat a60" : comme pour
  "Mise en situation professionnelle"

- Tous les "champs statistiques" représentent des heures de présences.
  Il y a deux modes d'encodage de présences des ateliers: soit avec
  soit sans les heures de d'arrivée de départ individuelles.  Par
  exemple en Insertion si la personne arrive en retard, elle aura les
  heures de présence de l'évènement (tant pis pour la statistique).


Par type d'entrée calendrier on doit configurer le champ FSE dans
lequel seront totalisés les heures.

>>> rt.show(cal.EventTypes, language="fr")
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE +REPORT_UDIFF
======================================== ======================================== =============================== ======================== ==============================
 Désignation                              Désignation (de)                         Désignation (en)                Inviter le bénéficiare   Champ FSE
---------------------------------------- ---------------------------------------- ------------------------------- ------------------------ ------------------------------
 Absences                                 Abwesenheiten                            Absences                        Non
 Atelier                                  Atelier                                  Workshop                        Non
 Consultations avec le bénéficiaire       Beratungen mit Klient                    Consultations with client       Non
 Informational meetings                   Informational meetings                   Informational meetings          Oui                      S.I.S. agréé
 Internal meetings with client            Internal meetings with client            Internal meetings with client   Oui                      Séance d’information
 Interne                                  Intern                                   Internal                        Non
 Jours fériés                             Feiertage                                Holidays                        Non
 Privé                                    Privat                                   Private                         Non
 Réunion                                  Versammlung                              Meeting                         Non
 Réunions externe                         Réunions externe                         External meetings               Non
 Réunions externes avec le bénéficiaire   Réunions externes avec le bénéficiaire   External meetings with client   Oui                      Evaluation formation externe
 Réunions interne                         Réunions interne                         Internal meetings               Non
 Évaluation                               Auswertung                               Evaluation                      Oui                      Entretien individuel
======================================== ======================================== =============================== ======================== ==============================
<BLANKLINE>

.. class:: StatisticalFields

>>> rt.show(esf.StatisticalFields, language="fr")
======= ============ =================================== =================
 value   Short name   text                                Type
------- ------------ ----------------------------------- -----------------
 10      S.Inf        Séance d’information                GuestHoursFixed
 20      E.Ind        Entretien individuel                GuestHoursFixed
 21      E.For        Evaluation formation externe        GuestHoursFixed
 30      SIS          S.I.S. agréé                        GuestHoursFixed
 40      Tst          Tests de niveau                     GuestHoursFixed
 41      Info         Initiation informatique             GuestHoursFixed
 42      Mob          Mobilité                            GuestHoursFixed
 43      Rem          Remédiation                         GuestHoursFixed
 44      AN!          Activons-nous!                      GuestHoursEvent
 50      MSP          Mise en situation professionnelle   ImmersionHours
 60      CyE          Cyber Emploi                        GuestHoursEvent
 70      60§7         Mise à l’emploi art.60§7            Art60Hours
======= ============ =================================== =================
<BLANKLINE>


.. currentmodule:: lino_welfare.modlib.esf.choicelists

Les types de champ suivants sont disponibles par défaut:

- :class:`GuestHoursFixed`
- :class:`GuestHours>`
- :class:`ImmersionHours`
- :class:`Art60Hours`

>>> # rt.show(esf.AllSummaries)

>>> dd.plugins.summaries.start_year
2012
>>> dd.plugins.summaries.end_year
2014

>>> obj = pcsw.Client.objects.get(pk=17)
>>> print(obj)
AUSDEMWALD Alfons (17)

The field :attr:`has_esf
<lino_welfare.modlib.pcsw.Client.has_esf>` must be checked:

>>> print(obj.has_esf)
True

>>> show_fields(rt.models.pcsw.Client, 'has_esf')
- ESF data (has_esf) : Whether Lino should make ESF summaries for this client.

>>> rt.show(esf.SummariesByClient, obj, language="en")
====== ======= ======= ======= ====== ====== ====== ====== ====== ====== ====== ====== ======
 Year   S.Inf   E.Ind   E.For   SIS    Tst    Info   Mob    Rem    AN!    MSP    CyE    60§7
------ ------- ------- ------- ------ ------ ------ ------ ------ ------ ------ ------ ------
 2012   0:00    3:00    0:00    0:00   0:00   0:00   0:00   0:00   0:00   0:00   0:00   0:00
 2013   0:00    11:00   0:00    0:00   0:00   0:00   0:00   0:00   0:00   0:00   0:00   0:00
 2014   2:00    11:00   0:00    0:00   0:00   0:00   0:00   0:00   0:00   0:00   0:00   0:00
====== ======= ======= ======= ====== ====== ====== ====== ====== ====== ====== ====== ======
<BLANKLINE>

Running check_summaries will have no effect since data has been
checked as part of :cmd:`pm prep`:

>>> rt.login().run(obj.check_summaries)
{'refresh': True}

The data has not changed:

>>> rt.show(esf.SummariesByClient, obj, language="en")
====== ======= ======= ======= ====== ====== ====== ====== ====== ====== ====== ====== ======
 Year   S.Inf   E.Ind   E.For   SIS    Tst    Info   Mob    Rem    AN!    MSP    CyE    60§7
------ ------- ------- ------- ------ ------ ------ ------ ------ ------ ------ ------ ------
 2012   0:00    3:00    0:00    0:00   0:00   0:00   0:00   0:00   0:00   0:00   0:00   0:00
 2013   0:00    11:00   0:00    0:00   0:00   0:00   0:00   0:00   0:00   0:00   0:00   0:00
 2014   2:00    11:00   0:00    0:00   0:00   0:00   0:00   0:00   0:00   0:00   0:00   0:00
====== ======= ======= ======= ====== ====== ====== ====== ====== ====== ====== ====== ======
<BLANKLINE>


As another example, here is the ESF summary for a client with :term:`job
supplyments <job supplyment>`:

>>> art60.Contract.objects.values_list('client', flat=True)
<QuerySet [19, 27, 33, 38, 38, 47, 53, 53, 60, 60, 66, 79, 81, 81]>

We pick one of above clients.

>>> obj = pcsw.Client.objects.get(pk=19)

>>> rt.show(esf.SummariesByClient, obj, language="en")
====== ======= ======= ======= ====== ====== ====== ====== ====== ====== ====== ====== ========
 Year   S.Inf   E.Ind   E.For   SIS    Tst    Info   Mob    Rem    AN!    MSP    CyE    60§7
------ ------- ------- ------- ------ ------ ------ ------ ------ ------ ------ ------ --------
 2012   0:00    0:00    0:00    0:00   0:00   0:00   0:00   0:00   0:00   0:00   0:00   463:36
 2013   0:00    3:00    0:00    0:00   0:00   0:00   0:00   0:00   0:00   0:00   0:00   0:00
 2014   0:00    0:00    1:00    0:00   0:00   0:00   0:00   0:00   0:00   0:00   0:00   0:00
====== ======= ======= ======= ====== ====== ====== ====== ====== ====== ====== ====== ========
<BLANKLINE>



Choicelists
===========

.. class:: ParticipationCertificates

.. class:: StatisticalField

    Base class for all statistical fields.

    .. attribute:: short_name

        Used as the verbose_name of :attr:`field`.

    .. attribute:: field_name

        The internal field name.

    .. attribute:: field

        The field descriptor (an instance of a Django Field)


.. class:: GuestCount

    Count the number of presences.

    Not used in reality.

.. class:: GuestHours

    Count the real hours of presence.

.. class:: GuestHoursEvent

    Count the event's duration for each presence.


.. class:: GuestHoursFixed

    Count a fixed time for each presence.

.. class:: ImmersionHours

.. class:: Art60Hours
