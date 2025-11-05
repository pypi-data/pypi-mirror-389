.. doctest docs/specs/finan.rst
.. _welfare.specs.finan:

==================================
Financial vouchers in Lino Welfare
==================================

.. doctest init:

    >>> import lino ; lino.startup('lino_welfare.projects.gerd.settings.doctests')
    >>> from etgen.html import E
    >>> from lino.api.doctest import *

This document describes specific aspects of *financial vouchers* in
:ref:`welfare`, as implemented by the :mod:`lino_welfare.lib.finan`
plugin.

It is based on the following other specifications:

- :ref:`cosi.specs.accounting`
- :ref:`cosi.specs.accounting`
- :ref:`specs.cosi.finan`
- :ref:`welfare.specs.accounting`


Table of contents:

.. contents::
   :depth: 1
   :local:


Disbursement orders
===================

A disbursement order is an internal confirmation that certain expenses should be
done. It is a document to be signed by some responsible person before some other
person will do the actual payments.

The demo database has a journal AAW that contains disbursement orders.
Technically it is like a :term:`payment order`, but it has no partner and no
sepa_account.

>>> AAW = accounting.Journal.get_by_ref('AAW')
>>> print(AAW)
Ausgabeanweisungen (AAW)
>>> print(AAW.voucher_type.model)
<class 'lino_xl.lib.finan.models.PaymentOrder'>
>>> print(AAW.partner)
None
>>> print(AAW.sepa_account)
None


>>> rt.show(AAW.voucher_type.table_class, AAW)
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE -REPORT_UDIFF
======================= ========== ================================ =============== ================== ================= =================
 Nr.                     Datum      Interne Referenz                 Total           Ausführungsdatum   Buchungsperiode   Workflow
----------------------- ---------- -------------------------------- --------------- ------------------ ----------------- -----------------
 1/2014                  23.03.14   Allgemeine Beihilfen             3 460,17                           2014-03           **Registriert**
 2/2014                  23.03.14   Heizkosten- u. Energiebeihilfe   3 628,62                           2014-03           **Registriert**
 3/2014                  23.03.14   Fonds Gas und Elektrizität       3 356,17                           2014-03           **Registriert**
 4/2014                  23.03.14   Eingliederungseinkommen          3 611,34                           2014-03           **Registriert**
 5/2014                  23.03.14   Sozialhilfe                      3 460,17                           2014-03           **Registriert**
 6/2014                  23.03.14   Beihilfe für Ausländer           3 628,62                           2014-03           **Registriert**
 7/2014                  23.04.14   Allgemeine Beihilfen             3 356,17                           2014-04           **Registriert**
 8/2014                  23.04.14   Heizkosten- u. Energiebeihilfe   3 611,34                           2014-04           **Registriert**
 9/2014                  23.04.14   Fonds Gas und Elektrizität       3 460,17                           2014-04           **Registriert**
 10/2014                 23.04.14   Eingliederungseinkommen          3 628,62                           2014-04           **Registriert**
 11/2014                 23.04.14   Sozialhilfe                      3 356,17                           2014-04           **Registriert**
 12/2014                 23.04.14   Beihilfe für Ausländer           3 611,34                           2014-04           **Registriert**
 13/2014                 23.05.14   Allgemeine Beihilfen             3 460,17                           2014-05           **Registriert**
 14/2014                 23.05.14   Heizkosten- u. Energiebeihilfe   3 628,62                           2014-05           **Registriert**
 15/2014                 23.05.14   Fonds Gas und Elektrizität       3 356,17                           2014-05           **Registriert**
 16/2014                 23.05.14   Eingliederungseinkommen          3 611,34                           2014-05           **Registriert**
 17/2014                 23.05.14   Sozialhilfe                      3 460,17                           2014-05           **Registriert**
 18/2014                 23.05.14   Beihilfe für Ausländer           3 628,62                           2014-05           **Registriert**
 19/2014                 13.01.14                                    350,61                             2014-01           **Registriert**
 20/2014                 13.02.14                                    483,01                             2014-02           **Registriert**
 21/2014                 13.03.14                                    585,84                             2014-03           **Registriert**
 22/2014                 13.04.14                                    553,39                             2014-04           **Registriert**
 **Total (22 Zeilen)**                                               **65 286,84**
======================= ========== ================================ =============== ================== ================= =================
<BLANKLINE>

Payment orders
==============

>>> ZKBC = accounting.Journal.get_by_ref('ZKBC')

(remaining tests are temporarily skipped after 20170525. TODO:
reactivate them and find out why the payment order is not being
generated)


The ZKBC journal contains the following payment orders:

>>> rt.show(ZKBC.voucher_type.table_class, ZKBC)  #doctest: -SKIP
====================== ========== ================== =============== ================== ================= =================
 Nr.                    Datum      Interne Referenz   Total           Ausführungsdatum   Buchungsperiode   Workflow
---------------------- ---------- ------------------ --------------- ------------------ ----------------- -----------------
 1/2014                 21.01.14                      350,61                             2014-01           **Registriert**
 2/2014                 21.02.14                      483,01                             2014-02           **Registriert**
 3/2014                 21.03.14                      585,84                             2014-03           **Registriert**
 4/2014                 21.04.14                      21 698,48                          2014-04           **Registriert**
 **Total (4 Zeilen)**                                 **23 117,94**
====================== ========== ================== =============== ================== ================= =================
<BLANKLINE>


>>> obj = ZKBC.voucher_type.model.objects.get(number=1, journal=ZKBC)  #doctest: -SKIP
>>> rt.login('wilfried').show(finan.ItemsByPaymentOrder, obj)  #doctest: -SKIP
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE +REPORT_UDIFF
===== =========================== ==================== ========== ========================== ============== ============ ==================
 Nr.   Klient                      Zahlungsempfänger    Workflow   Bankkonto                  Match          Zu zahlen    Externe Referenz
----- --------------------------- -------------------- ---------- -------------------------- -------------- ------------ ------------------
 1     EVERS Eberhart (28)         AS Express Post                 EE87 2200 2210 1206 7904   REG 19/2014    5,33
 2     AUSDEMWALD Alfons (17)      AS Matsalu Veevärk              EE73 2200 2210 4511 2758   SREG 10/2014   15,33
 3     COLLARD Charlotte (19)      AS Matsalu Veevärk              EE73 2200 2210 4511 2758   SREG 10/2014   22,50
 4     DOBBELSTEIN Dorothée (25)   AS Matsalu Veevärk              EE73 2200 2210 4511 2758   SREG 10/2014   25,00
 5     EVERS Eberhart (28)         AS Matsalu Veevärk              EE73 2200 2210 4511 2758   SREG 10/2014   29,95
 6     EMONTS Daniel (29)          AS Matsalu Veevärk              EE73 2200 2210 4511 2758   SREG 10/2014   120,00
 7     EVERS Eberhart (28)         Eesti Energia AS                EE23 2200 0011 8000 5555   REG 1/2013     12,50
 8     COLLARD Charlotte (19)      Leffin Electronics              BE38 2480 1735 7572        REG 18/2014    120,00
       **Total (8 Zeilen)**                                                                                  **350,61**
===== =========================== ==================== ========== ========================== ============== ============ ==================
<BLANKLINE>




>>> kw = dict()
>>> fields = 'count rows'
>>> obj = ZKBC.voucher_type.model.objects.get(number=1, journal=ZKBC)  #doctest: -SKIP
>>> demo_get(
...    'wilfried', 'choices/finan/ItemsByPaymentOrder/match',
...    fields, 0, mk=obj.pk, **kw)  #doctest: -SKIP
