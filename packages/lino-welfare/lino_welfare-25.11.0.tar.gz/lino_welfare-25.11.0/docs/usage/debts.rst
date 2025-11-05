.. _ug.plugins.debts:
.. _welfare.debts:

====================================================================
``debts`` : Debts mediation (Schuldnerberatung, Médiation de dettes)
====================================================================

.. currentmodule:: lino_welfare.modlib.debts

The :mod:`lino_welfare.modlib.debts` plugin adds functionality for doing debts
mediation. It lets social consultants create :term:`debts mediation budgets
<debts mediation budget>` for their clients.


.. glossary::

  debts mediation budget

    A document that describes the financial situation of a person or household
    at a given moment. It holds financial information like monthly incomes and
    expenses, and debts.

    Stored using the :class:`Budget` database model.

When relevant input data has been filled into the budget, Lino displays
miscellaneous reports based on the entered data. The user can print out a
document that serves as base for the consultation and discussion with debtors.


Scénarios
=========

Q: En tant que conseiller dettes je commence à remplir, avec le client, les
données d'un budget. Le client n'a pas toutes les informations nécessaires avec
lui. Comment puis-je lui imprimer une version spéciale du budget, destinée à
être utilisée pour remplir manuellement sur papier les chiffres manquants pour
les encoder la prochaine fois?

A: Activer le champ :attr:`Budget.print_empty_rows`


The actors of a budget
======================

A budget can have multiple "actors"

.. glossary::

  budget actor

    A :term:`person` that is part of the household for which the budget is being
    established, and who contributes to the budget.

When entering data for the budget, you can specify every expense or income
for each actor separately.
