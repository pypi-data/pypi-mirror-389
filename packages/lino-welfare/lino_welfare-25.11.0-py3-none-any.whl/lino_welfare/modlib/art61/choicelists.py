# -*- coding: UTF-8 -*-
# Copyright 2012-2022 Rumma & Ko Ltd
# License: GNU Affero General Public License v3 (see file COPYING for details)
"""
Choicelists for `lino_welfare.modlib.art61`.

Original request:

- Gestion des subsides d'un projet art 61 : 3 nouveaux champs à cocher
  "Activa", "Tutorat" et "Région wallonne". + paramètres pour pouvoir
  filtrer.  Précision: il serait bien d'avoir une ChoiceList
  "Subsidiations" (`art61.Subsidizations`) configurable. Et puis un
  champ à cocher par subsidiation et par contrat. Ce sera l'occasion
  d'implémenter :class:`lino.core.choicelists.MultiChoiceListField`.


"""

from django.db import models
from lino.api import dd, _


class Subsidization(dd.Choice):

    # def contract_field_name(self):
    #     return 'subsidize_' + self.value

    def get_contract_fields(self):
        yield "sub_{}_amount".format(self.value), dd.PriceField(
            verbose_name=self.text, blank=True, null=True)
        yield "sub_{}_start".format(self.value), models.DateField(
            verbose_name=_("From"), blank=True, null=True)
        yield "sub_{}_end".format(self.value), models.DateField(
            verbose_name=_("Until"), blank=True, null=True)


class Subsidizations(dd.ChoiceList):
    verbose_name = _("Subsidization")
    verbose_name_plural = _("Subsidizations")
    item_class = Subsidization


add = Subsidizations.add_item
add('10', _("Hiring assistance"), 'hiring')  # Aide à l'embauche
# add('10', _("Activa"), 'activa')
add('20', _("Tutorate"), 'tutorat')  # Tutorat: unique en communauté
# francaise. par Ahmed Medhoune
add('30', _("Walloon Region"), 'region')
# add('40', _("SINE"), 'sine')
# add('50', _("PTP"), 'ptp')
