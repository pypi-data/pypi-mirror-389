.. doctest docs/specs/addresses.rst
.. _welfare.specs.addresses:

=========================
Multiple postal addresses
=========================

How :ref:`welfare` uses :mod:`lino_xl.lib.addresses`.

.. doctest init:

    >>> from lino import startup
    >>> startup('lino_welfare.projects.gerd.settings.doctests')
    >>> from lino.api.doctest import *
    >>> from django.db.models import Q

.. contents::
   :depth: 2


These are the partners in the demo database with more than one
address:

>>> lst = [p.id for p in contacts.Partner.objects.filter(
...     addresses_by_partner__primary=False).distinct().order_by("id")]

>>> len(lst)
48
>>> print(lst)  #doctest: +NORMALIZE_WHITESPACE
[1, 3, 5, 14, 16, 17, 19, 20, 22, 23, 25, 26, 28, 29, 31, 32, 34, 35, 37, 38, 40, 41, 43, 44, 46, 47, 49, 50, 86, 87, 90, 91, 93, 94, 101, 102, 104, 105, 107, 108, 111, 112, 116, 117, 119, 120, 130, 131]

Here are the addresses of one of these partners (20):

>>> obj = contacts.Partner.objects.get(id=20)
>>> rt.show(addresses.AddressesByPartner, obj)
==================== =========== ====================== ========
 Adressenart          Bemerkung   Adresse                Primär
-------------------- ----------- ---------------------- --------
 Offizielle Adresse               Auenweg, 4700 Eupen    Ja
 Ungeprüfte Adresse               Auf dem Spitzberg 11   Nein
==================== =========== ====================== ========
<BLANKLINE>
