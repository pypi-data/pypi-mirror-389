.. _welfare.fr.clients:

=============
Bénéficiaires
=============

.. contents::
   :depth: 1
   :local:


Vues tabulaires
===============

- :menuselection:`Contacts --> Bénéficiaires`:
  La **liste générale des bénéficiaires** montre "tous" les bénéficiaires.

- :menuselection:`Insertion --> Bénéficiaires`:
  vue adaptée pour les agents d'insertion.

- :menuselection:`Newcomers --> Bénéficiaires`:
  vue adaptée pour les agents nouvelles demandes

- :menuselection:`Accueil --> Bénéficiaires`:
  vue adaptée pour les agents d'accueil.


.. image:: /tour/pcsw.Clients.grid.png
  :width: 90%


Vue détail d'un bénéficiaire
============================


Onglet **Personne**
-------------------

.. image:: /screenshots/pcsw.Clients.detail1.png
  :width: 90%


Onglet **Intervenants**
-----------------------

.. image:: /screenshots/pcsw.Clients.detail2.png
  :width: 90%

Onglet **Situation familiale**
------------------------------

.. image:: /screenshots/pcsw.Clients.detail3.png
  :width: 90%

Onglet **Parcours**
-------------------

.. image:: /screenshots/pcsw.Clients.detail4.png
  :width: 90%

Onglet **Compétences**
----------------------

.. image:: /screenshots/pcsw.Clients.detail5.png
  :width: 90%

Onglet **Freins**
-----------------

.. image:: /screenshots/pcsw.Clients.detail6.png
  :width: 90%

Onglet **PIISs**
----------------

.. image:: /screenshots/pcsw.Clients.detail7.png
  :width: 90%

Onglet **Orientation interne**
------------------------------

.. image:: /screenshots/pcsw.Clients.detail8.png
  :width: 90%

Onglet **Stages d'immersion**
-----------------------------

.. image:: /screenshots/pcsw.Clients.detail9.png
  :width: 90%

Onglet **Mise à l'emploi**
--------------------------

.. image:: /screenshots/pcsw.Clients.detail10.png
  :width: 90%

Onglet **Historique**
---------------------

Onglet **Calendrier**
---------------------

.. image:: /screenshots/pcsw.Clients.detail12.png
  :width: 90%

..
  Onglet **Divers**
  Onglet **Médiation de dettes**


Voir aussi
==========

Les onglets disponibles et leur contenu dépendent des permissions d'accès de
l'utilisateur.  Voir aussi les  `Spécifications techniques
<https://welfare.lino-framework.org/fr/clients.html#vue-detail-d-un-beneficiaire>`__.


Phases d'insertion
==================

Pour configurer les valeurs permises dans le champ :guilabel:`Phase d'insertion`
d'un bénéficiaire, aller dans :menuselection:`Configuration --> CPAS --> Phases
d'insertion`.

Les phases d'insertion influencent également le rapport :menuselection:`Rapports
--> Insertion --> Agents et leurs bénéficiaires`: seulement les phases avec un
:guilabel:`Nom de référence` auront leur colonne dans ce rapport.

"J'ai voulu effacer une phase que nous n'utilisons plus. Mais Lino refuse vu
que des bénéficiaires y font référence. Normal et c'est de toute façon mieux
de garder une trace de ce qui a été fait. Serait-il possible de passer une
phase d'insertion en "archive" afin qu'elle n'apparaisse plus dans la liste?"
--> On enlève le ☑ dans la colonne "Considéré actif"

Y a-t-il un moyen de les classer pour que la liste reflète l'ordre du parcours
d'insertion? --> Lors de la sélection Lino trie les phases par le :guilabel:`Nom de
référence`. Ce nom lui-même n'est pas affiché.
