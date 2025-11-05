================
Les utilisateurs
================

Types d'utilisateur
=====================

Pour qu'un utilisateur puisse se connecter, il faut que le champ
:guilabel:`Type d'utilisateur` soit rempli.


Détails techniques
==================

La liste des profils utilisateurs disponible est définie dans
:mod:`lino_welfare.modlib.welfare.user_types`.


- Le profil 420 (Agent social (flexible)) :ticket:`2362` a les mêmes
  permissions que le profil 120 (Agent d'insertion flexible) mais
  reçoit moins de notifications. Notamment il voit également les
  onglets PARCOURS – COMPÉTENCES – FREINS - STAGES D’IMMERSION -
  MÉDIATION DE DETTES.
