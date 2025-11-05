.. doctest docs/specs/vatless.rst
.. _welfare.specs.vatless:

=================
Incoming invoices
=================


This document is based on and extends :ref:`welfare.specs.accounting`.

.. contents::
   :depth: 1
   :local:

Code snippets in this document are tested on the
:mod:`lino_welfare.projects.gerd` demo project.

>>> from lino import startup
>>> startup('lino_welfare.projects.gerd.settings.doctests')
>>> from lino.api.doctest import *
>>> from lino.api import rt


Incoming invoices
=================

In Lino Welfare, **incoming invoices** are different from "real"
incoming invoices in that their recipient is some client of the
center, not to the center itself. The center has no direct legal
obligation, it just agrees (or not) to pay these invoices in the name
of their client.

There are two types of incoming invoices: "simple" and "collective".
The demo database has two journals with *incoming invoices*, one for
each type, referenced as "REG" (for German *Rechnungseingang*) and
SREG (*Sammelrechnungen*).

>>> REG = accounting.Journal.get_by_ref('REG')
>>> REG.voucher_type.table_class
lino_xl.lib.vatless.ui.ProjectInvoicesByJournal

>>> SREG = accounting.Journal.get_by_ref('SREG')
>>> SREG.voucher_type.table_class
lino_xl.lib.vatless.ui.InvoicesByJournal

The REG journal contains the following invoices:

>>> rt.show(REG.voucher_type.table_class, REG)
... #doctest: +NORMALIZE_WHITESPACE +REPORT_UDIFF
======================= ========== =========================== =============================== ============ ============== ================== =================
 Nr.                     Datum      Klient                      Zahlungsempfänger               Betrag       Zahlungsziel   Autor              Workflow
----------------------- ---------- --------------------------- ------------------------------- ------------ -------------- ------------------ -----------------
 1/2013                  28.12.13   EVERS Eberhart (28)         Eesti Energia AS                12,50        27.01.14       Wilfried Willems   **Registriert**
 19/2014                 07.01.14   EVERS Eberhart (28)         AS Express Post                 5,33         06.02.14       Wilfried Willems   **Registriert**
 18/2014                 12.01.14   COLLARD Charlotte (19)      Leffin Electronics              120,00       11.02.14       Wilfried Willems   **Registriert**
 17/2014                 22.01.14   EVERS Eberhart (28)         Electrabel Customer Solutions   120,00       21.02.14       Wilfried Willems   **Registriert**
 16/2014                 27.01.14   COLLARD Charlotte (19)      Ragn-Sells AS                   29,95        26.02.14       Wilfried Willems   **Registriert**
 15/2014                 06.02.14   COLLARD Charlotte (19)      IIZI kindlustusmaakler AS       12,50        08.03.14       Wilfried Willems   **Registriert**
 14/2014                 11.02.14   EMONTS Daniel (29)          Eesti Energia AS                10,00        13.03.14       Wilfried Willems   **Registriert**
 13/2014                 21.02.14   COLLARD Charlotte (19)      AS Express Post                 10,00        23.03.14       Wilfried Willems   **Registriert**
 12/2014                 26.02.14   EMONTS Daniel (29)          Leffin Electronics              5,33         28.03.14       Wilfried Willems   **Registriert**
 11/2014                 08.03.14   EMONTS Daniel (29)          Electrabel Customer Solutions   29,95        07.04.14       Wilfried Willems   **Registriert**
 10/2014                 13.03.14   DOBBELSTEIN Dorothée (25)   Ragn-Sells AS                   25,00        12.04.14       Wilfried Willems   **Registriert**
 9/2014                  23.03.14   EMONTS Daniel (29)          IIZI kindlustusmaakler AS       25,00        22.04.14       Wilfried Willems   **Registriert**
 8/2014                  28.03.14   DOBBELSTEIN Dorothée (25)   Eesti Energia AS                12,50        27.04.14       Wilfried Willems   **Registriert**
 7/2014                  07.04.14   DOBBELSTEIN Dorothée (25)   AS Express Post                 5,33         07.05.14       Wilfried Willems   **Registriert**
 6/2014                  12.04.14   AUSDEMWALD Alfons (17)      Leffin Electronics              120,00       12.05.14       Wilfried Willems   **Registriert**
 5/2014                  22.04.14   DOBBELSTEIN Dorothée (25)   Electrabel Customer Solutions   120,00       22.05.14       Wilfried Willems   **Registriert**
 4/2014                  27.04.14   AUSDEMWALD Alfons (17)      Ragn-Sells AS                   29,95        27.05.14       Wilfried Willems   **Registriert**
 3/2014                  07.05.14   AUSDEMWALD Alfons (17)      IIZI kindlustusmaakler AS       12,50        06.06.14       Wilfried Willems   **Registriert**
 2/2014                  12.05.14   EVERS Eberhart (28)         Eesti Energia AS                10,00        11.06.14       Wilfried Willems   **Registriert**
 1/2014                  22.05.14   AUSDEMWALD Alfons (17)      AS Express Post                 10,00        21.06.14       Wilfried Willems   **Registriert**
 **Total (20 Zeilen)**                                                                          **725,84**
======================= ========== =========================== =============================== ============ ============== ================== =================
<BLANKLINE>




Collective invoices
===================

The SREG journal contains the following invoices:

>>> rt.show(SREG.voucher_type.table_class, SREG)
======================= ========== ===================== ============== ============== ================== =================
 Nr.                     Datum      Zahlungsempfänger     Betrag         Zahlungsziel   Autor              Workflow
----------------------- ---------- --------------------- -------------- -------------- ------------------ -----------------
 10/2014                 02.01.14   AS Matsalu Veevärk    212,78         01.02.14       Wilfried Willems   **Registriert**
 9/2014                  17.01.14   Niederau Eupen AG     82,78          16.02.14       Wilfried Willems   **Registriert**
 8/2014                  01.02.14   Maksu- ja Tolliamet   227,78         03.03.14       Wilfried Willems   **Registriert**
 7/2014                  16.02.14   AS Matsalu Veevärk    192,78         18.03.14       Wilfried Willems   **Registriert**
 6/2014                  03.03.14   Niederau Eupen AG     322,78         02.04.14       Wilfried Willems   **Registriert**
 5/2014                  18.03.14   Maksu- ja Tolliamet   177,78         17.04.14       Wilfried Willems   **Registriert**
 4/2014                  02.04.14   AS Matsalu Veevärk    212,78         02.05.14       Wilfried Willems   **Registriert**
 3/2014                  17.04.14   Niederau Eupen AG     82,78          17.05.14       Wilfried Willems   **Registriert**
 2/2014                  02.05.14   Maksu- ja Tolliamet   227,78         01.06.14       Wilfried Willems   **Registriert**
 1/2014                  17.05.14   AS Matsalu Veevärk    192,78         16.06.14       Wilfried Willems   **Registriert**
 **Total (10 Zeilen)**                                    **1 932,80**
======================= ========== ===================== ============== ============== ================== =================
<BLANKLINE>



Incoming invoices, partners and clients
=======================================

Let's have a closer look at an incoming invoice:

>>> obj = SREG.voucher_type.model.objects.get(number=3, journal=SREG)

The partner of this invoice is Niederau:

>>> obj.partner
Partner #129 ('Niederau Eupen AG')

It is a collective invoice distributed over five clients:

>>> rt.login('wilfried').show(rt.models.vatless.ItemsByInvoice, obj)
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE +REPORT_UDIFF
=========================== =================================== =========== ============== ============
 Klient                      Haushaltsartikel                    Betrag      Beschreibung   Bearbeiten
--------------------------- ----------------------------------- ----------- -------------- ------------
 EMONTS Daniel (29)          (832/330/01) Allgemeine Beihilfen   5,33                       [🗗]
 AUSDEMWALD Alfons (17)      (832/330/01) Allgemeine Beihilfen   10,00                      [🗗]
 COLLARD Charlotte (19)      (832/330/01) Allgemeine Beihilfen   12,50                      [🗗]
 DOBBELSTEIN Dorothée (25)   (832/330/01) Allgemeine Beihilfen   25,00                      [🗗]
 EVERS Eberhart (28)         (832/330/01) Allgemeine Beihilfen   29,95                      [🗗]
 **Total (5 Zeilen)**                                            **82,78**
=========================== =================================== =========== ============== ============
<BLANKLINE>



This invoice is registered, so the :term:`ledger movements <ledger movement>`
have been created:

>>> obj.state
<accounting.VoucherStates.registered:20>
>>> rt.show(rt.models.accounting.MovementsByVoucher, obj)
=================================== =========================== =================== =========== =========== ===================== ===========
 Haushaltsartikel                    Klient                      Zahlungsempfänger   Debit       Kredit      Match                 Beglichen
----------------------------------- --------------------------- ------------------- ----------- ----------- --------------------- -----------
 (832/330/01) Allgemeine Beihilfen   EMONTS Daniel (29)                              5,33                                          Ja
 (832/330/01) Allgemeine Beihilfen   AUSDEMWALD Alfons (17)                          10,00                                         Ja
 (832/330/01) Allgemeine Beihilfen   COLLARD Charlotte (19)                          12,50                                         Ja
 (832/330/01) Allgemeine Beihilfen   DOBBELSTEIN Dorothée (25)                       25,00                                         Ja
 (832/330/01) Allgemeine Beihilfen   EVERS Eberhart (28)                             29,95                                         Ja
 (4100) Lieferanten                  EMONTS Daniel (29)          Niederau Eupen AG               5,33        `SREG 3/2014 <…>`__   Nein
 (4100) Lieferanten                  AUSDEMWALD Alfons (17)      Niederau Eupen AG               10,00       `SREG 3/2014 <…>`__   Nein
 (4100) Lieferanten                  COLLARD Charlotte (19)      Niederau Eupen AG               12,50       `SREG 3/2014 <…>`__   Nein
 (4100) Lieferanten                  DOBBELSTEIN Dorothée (25)   Niederau Eupen AG               25,00       `SREG 3/2014 <…>`__   Nein
 (4100) Lieferanten                  EVERS Eberhart (28)         Niederau Eupen AG               29,95       `SREG 3/2014 <…>`__   Nein
                                                                                     **82,78**   **82,78**
=================================== =========================== =================== =========== =========== ===================== ===========
<BLANKLINE>


The last five movements are *cleared* because their account is not
:attr:`clearable <lino_xl.lib.accounting.Account.clearable>`.

>>> cost_account = rt.models.accounting.Account.objects.get(ref="832/330/01")
>>> cost_account.clearable
False

The first five movements go into the suppliers account, which is
clearable:

>>> suppliers_account = rt.models.accounting.Account.objects.get(ref="4100")
>>> suppliers_account = accounting.CommonAccounts.suppliers.get_object()
>>> suppliers_account.clearable
True

The match rules table defines how to clear these movements:

>>> rt.show(accounting.MatchRulesByAccount, suppliers_account)
==========================
 Journal
--------------------------
 Ausgabeanweisungen (AAW)
==========================
<BLANKLINE>

This rule means: "Uncleared amounts in the suppliers account may be
cleared by the AAW (disbursement instructions) journal".

Since AAW is a financial journal, our story continues in :doc:`finan`.





Registering new incoming invoices
=================================

It is possible to create new invoices from the detail view of a partner.

The partner is usually some company.

>>> obj.partner
Partner #129 ('Niederau Eupen AG')

>>> rt.login('rolf').show(rt.models.vatless.VouchersByPartner, obj.partner)
`ⓘ <…>`__ `⏏ <…>`__ | Beleg erstellen in Journal `Sammelrechnungen (SREG) <…>`__, `Einkaufsrechnungen (REG) <…>`__

Our partner has 15 movements that are not yet *cleared*.

>>> rt.show(rt.models.accounting.MovementsByPartner, obj.partner)
`⏏ <…>`__ | **15 offene Bewegungen (488.34 €)**

Let's look at the detail of these movements:

>>> rt.show(rt.models.accounting.MovementsByPartner, obj.partner, nosummary=True)
========== ===================== ================================================================================================================= ============ ============== ============= ===========
 Valuta     Beleg                 Beschreibung                                                                                                      Debit        Kredit         Match         Beglichen
---------- --------------------- ----------------------------------------------------------------------------------------------------------------- ------------ -------------- ------------- -----------
 17.04.14   `SREG 3/2014 <…>`__   `(4100) Lieferanten <…>`__ | `AUSDEMWALD Alfons (17) <…>`__                                                                    10,00          SREG 3/2014   Nein
 17.04.14   `SREG 3/2014 <…>`__   `(4100) Lieferanten <…>`__ | `COLLARD Charlotte (19) <…>`__                                                                    12,50          SREG 3/2014   Nein
 17.04.14   `SREG 3/2014 <…>`__   `(4100) Lieferanten <…>`__ | `DOBBELSTEIN Dorothée (25) <…>`__                                                                 25,00          SREG 3/2014   Nein
 17.04.14   `SREG 3/2014 <…>`__   `(4100) Lieferanten <…>`__ | `EVERS Eberhart (28) <…>`__                                                                       29,95          SREG 3/2014   Nein
 17.04.14   `SREG 3/2014 <…>`__   `(4100) Lieferanten <…>`__ | `EMONTS Daniel (29) <…>`__                                                                        5,33           SREG 3/2014   Nein
 21.03.14   `ZKBC 3/2014 <…>`__   `(4300) Offene Zahlungsaufträge <…>`__ | `Niederau Eupen AG <…>`__ | `AUSDEMWALD Alfons (17) <…>`__                            25,00          SREG 6/2014   Nein
 21.03.14   `ZKBC 3/2014 <…>`__   `(4300) Offene Zahlungsaufträge <…>`__ | `Niederau Eupen AG <…>`__ | `COLLARD Charlotte (19) <…>`__                            149,95         SREG 6/2014   Nein
 21.03.14   `ZKBC 3/2014 <…>`__   `(4300) Offene Zahlungsaufträge <…>`__ | `Niederau Eupen AG <…>`__ | `DOBBELSTEIN Dorothée (25) <…>`__                         125,33         SREG 6/2014   Nein
 21.03.14   `ZKBC 3/2014 <…>`__   `(4300) Offene Zahlungsaufträge <…>`__ | `Niederau Eupen AG <…>`__ | `EVERS Eberhart (28) <…>`__                               10,00          SREG 6/2014   Nein
 21.03.14   `ZKBC 3/2014 <…>`__   `(4300) Offene Zahlungsaufträge <…>`__ | `Niederau Eupen AG <…>`__ | `EMONTS Daniel (29) <…>`__                                12,50          SREG 6/2014   Nein
 21.03.14   `ZKBC 3/2014 <…>`__   `(4450) Auszuführende Ausgabeanweisungen <…>`__ | `Niederau Eupen AG <…>`__ | `AUSDEMWALD Alfons (17) <…>`__      25,00                       SREG 6/2014   Ja
 21.03.14   `ZKBC 3/2014 <…>`__   `(4450) Auszuführende Ausgabeanweisungen <…>`__ | `Niederau Eupen AG <…>`__ | `COLLARD Charlotte (19) <…>`__      149,95                      SREG 6/2014   Ja
 21.03.14   `ZKBC 3/2014 <…>`__   `(4450) Auszuführende Ausgabeanweisungen <…>`__ | `Niederau Eupen AG <…>`__ | `DOBBELSTEIN Dorothée (25) <…>`__   125,33                      SREG 6/2014   Ja
 21.03.14   `ZKBC 3/2014 <…>`__   `(4450) Auszuführende Ausgabeanweisungen <…>`__ | `Niederau Eupen AG <…>`__ | `EVERS Eberhart (28) <…>`__         10,00                       SREG 6/2014   Ja
 21.03.14   `ZKBC 3/2014 <…>`__   `(4450) Auszuführende Ausgabeanweisungen <…>`__ | `Niederau Eupen AG <…>`__ | `EMONTS Daniel (29) <…>`__          12,50                       SREG 6/2014   Ja
 13.03.14   `AAW 21/2014 <…>`__   `(4100) Lieferanten <…>`__ | `Niederau Eupen AG <…>`__ | `AUSDEMWALD Alfons (17) <…>`__                           25,00                       SREG 6/2014   Ja
 13.03.14   `AAW 21/2014 <…>`__   `(4100) Lieferanten <…>`__ | `Niederau Eupen AG <…>`__ | `COLLARD Charlotte (19) <…>`__                           149,95                      SREG 6/2014   Ja
 13.03.14   `AAW 21/2014 <…>`__   `(4100) Lieferanten <…>`__ | `Niederau Eupen AG <…>`__ | `DOBBELSTEIN Dorothée (25) <…>`__                        125,33                      SREG 6/2014   Ja
 13.03.14   `AAW 21/2014 <…>`__   `(4100) Lieferanten <…>`__ | `Niederau Eupen AG <…>`__ | `EVERS Eberhart (28) <…>`__                              10,00                       SREG 6/2014   Ja
 13.03.14   `AAW 21/2014 <…>`__   `(4100) Lieferanten <…>`__ | `Niederau Eupen AG <…>`__ | `EMONTS Daniel (29) <…>`__                               12,50                       SREG 6/2014   Ja
 13.03.14   `AAW 21/2014 <…>`__   `(4450) Auszuführende Ausgabeanweisungen <…>`__ | `Niederau Eupen AG <…>`__ | `AUSDEMWALD Alfons (17) <…>`__                   25,00          SREG 6/2014   Ja
 13.03.14   `AAW 21/2014 <…>`__   `(4450) Auszuführende Ausgabeanweisungen <…>`__ | `Niederau Eupen AG <…>`__ | `COLLARD Charlotte (19) <…>`__                   149,95         SREG 6/2014   Ja
 13.03.14   `AAW 21/2014 <…>`__   `(4450) Auszuführende Ausgabeanweisungen <…>`__ | `Niederau Eupen AG <…>`__ | `DOBBELSTEIN Dorothée (25) <…>`__                125,33         SREG 6/2014   Ja
 13.03.14   `AAW 21/2014 <…>`__   `(4450) Auszuführende Ausgabeanweisungen <…>`__ | `Niederau Eupen AG <…>`__ | `EVERS Eberhart (28) <…>`__                      10,00          SREG 6/2014   Ja
 13.03.14   `AAW 21/2014 <…>`__   `(4450) Auszuführende Ausgabeanweisungen <…>`__ | `Niederau Eupen AG <…>`__ | `EMONTS Daniel (29) <…>`__                       12,50          SREG 6/2014   Ja
 03.03.14   `SREG 6/2014 <…>`__   `(4100) Lieferanten <…>`__ | `AUSDEMWALD Alfons (17) <…>`__                                                                    25,00          SREG 6/2014   Ja
 03.03.14   `SREG 6/2014 <…>`__   `(4100) Lieferanten <…>`__ | `COLLARD Charlotte (19) <…>`__                                                                    149,95         SREG 6/2014   Ja
 03.03.14   `SREG 6/2014 <…>`__   `(4100) Lieferanten <…>`__ | `DOBBELSTEIN Dorothée (25) <…>`__                                                                 125,33         SREG 6/2014   Ja
 03.03.14   `SREG 6/2014 <…>`__   `(4100) Lieferanten <…>`__ | `EVERS Eberhart (28) <…>`__                                                                       10,00          SREG 6/2014   Ja
 03.03.14   `SREG 6/2014 <…>`__   `(4100) Lieferanten <…>`__ | `EMONTS Daniel (29) <…>`__                                                                        12,50          SREG 6/2014   Ja
 21.02.14   `ZKBC 2/2014 <…>`__   `(4300) Offene Zahlungsaufträge <…>`__ | `Niederau Eupen AG <…>`__ | `AUSDEMWALD Alfons (17) <…>`__                            5,33           SREG 9/2014   Nein
 21.02.14   `ZKBC 2/2014 <…>`__   `(4300) Offene Zahlungsaufträge <…>`__ | `Niederau Eupen AG <…>`__ | `COLLARD Charlotte (19) <…>`__                            10,00          SREG 9/2014   Nein
 21.02.14   `ZKBC 2/2014 <…>`__   `(4300) Offene Zahlungsaufträge <…>`__ | `Niederau Eupen AG <…>`__ | `DOBBELSTEIN Dorothée (25) <…>`__                         12,50          SREG 9/2014   Nein
 21.02.14   `ZKBC 2/2014 <…>`__   `(4300) Offene Zahlungsaufträge <…>`__ | `Niederau Eupen AG <…>`__ | `EVERS Eberhart (28) <…>`__                               25,00          SREG 9/2014   Nein
 21.02.14   `ZKBC 2/2014 <…>`__   `(4300) Offene Zahlungsaufträge <…>`__ | `Niederau Eupen AG <…>`__ | `EMONTS Daniel (29) <…>`__                                29,95          SREG 9/2014   Nein
 21.02.14   `ZKBC 2/2014 <…>`__   `(4450) Auszuführende Ausgabeanweisungen <…>`__ | `Niederau Eupen AG <…>`__ | `AUSDEMWALD Alfons (17) <…>`__      5,33                        SREG 9/2014   Ja
 21.02.14   `ZKBC 2/2014 <…>`__   `(4450) Auszuführende Ausgabeanweisungen <…>`__ | `Niederau Eupen AG <…>`__ | `COLLARD Charlotte (19) <…>`__      10,00                       SREG 9/2014   Ja
 21.02.14   `ZKBC 2/2014 <…>`__   `(4450) Auszuführende Ausgabeanweisungen <…>`__ | `Niederau Eupen AG <…>`__ | `DOBBELSTEIN Dorothée (25) <…>`__   12,50                       SREG 9/2014   Ja
 21.02.14   `ZKBC 2/2014 <…>`__   `(4450) Auszuführende Ausgabeanweisungen <…>`__ | `Niederau Eupen AG <…>`__ | `EVERS Eberhart (28) <…>`__         25,00                       SREG 9/2014   Ja
 21.02.14   `ZKBC 2/2014 <…>`__   `(4450) Auszuführende Ausgabeanweisungen <…>`__ | `Niederau Eupen AG <…>`__ | `EMONTS Daniel (29) <…>`__          29,95                       SREG 9/2014   Ja
 13.02.14   `AAW 20/2014 <…>`__   `(4100) Lieferanten <…>`__ | `Niederau Eupen AG <…>`__ | `AUSDEMWALD Alfons (17) <…>`__                           5,33                        SREG 9/2014   Ja
 13.02.14   `AAW 20/2014 <…>`__   `(4100) Lieferanten <…>`__ | `Niederau Eupen AG <…>`__ | `COLLARD Charlotte (19) <…>`__                           10,00                       SREG 9/2014   Ja
 13.02.14   `AAW 20/2014 <…>`__   `(4100) Lieferanten <…>`__ | `Niederau Eupen AG <…>`__ | `DOBBELSTEIN Dorothée (25) <…>`__                        12,50                       SREG 9/2014   Ja
 13.02.14   `AAW 20/2014 <…>`__   `(4100) Lieferanten <…>`__ | `Niederau Eupen AG <…>`__ | `EVERS Eberhart (28) <…>`__                              25,00                       SREG 9/2014   Ja
 13.02.14   `AAW 20/2014 <…>`__   `(4100) Lieferanten <…>`__ | `Niederau Eupen AG <…>`__ | `EMONTS Daniel (29) <…>`__                               29,95                       SREG 9/2014   Ja
 13.02.14   `AAW 20/2014 <…>`__   `(4450) Auszuführende Ausgabeanweisungen <…>`__ | `Niederau Eupen AG <…>`__ | `AUSDEMWALD Alfons (17) <…>`__                   5,33           SREG 9/2014   Ja
 13.02.14   `AAW 20/2014 <…>`__   `(4450) Auszuführende Ausgabeanweisungen <…>`__ | `Niederau Eupen AG <…>`__ | `COLLARD Charlotte (19) <…>`__                   10,00          SREG 9/2014   Ja
 13.02.14   `AAW 20/2014 <…>`__   `(4450) Auszuführende Ausgabeanweisungen <…>`__ | `Niederau Eupen AG <…>`__ | `DOBBELSTEIN Dorothée (25) <…>`__                12,50          SREG 9/2014   Ja
 13.02.14   `AAW 20/2014 <…>`__   `(4450) Auszuführende Ausgabeanweisungen <…>`__ | `Niederau Eupen AG <…>`__ | `EVERS Eberhart (28) <…>`__                      25,00          SREG 9/2014   Ja
 13.02.14   `AAW 20/2014 <…>`__   `(4450) Auszuführende Ausgabeanweisungen <…>`__ | `Niederau Eupen AG <…>`__ | `EMONTS Daniel (29) <…>`__                       29,95          SREG 9/2014   Ja
 17.01.14   `SREG 9/2014 <…>`__   `(4100) Lieferanten <…>`__ | `AUSDEMWALD Alfons (17) <…>`__                                                                    5,33           SREG 9/2014   Ja
 17.01.14   `SREG 9/2014 <…>`__   `(4100) Lieferanten <…>`__ | `COLLARD Charlotte (19) <…>`__                                                                    10,00          SREG 9/2014   Ja
 17.01.14   `SREG 9/2014 <…>`__   `(4100) Lieferanten <…>`__ | `DOBBELSTEIN Dorothée (25) <…>`__                                                                 12,50          SREG 9/2014   Ja
 17.01.14   `SREG 9/2014 <…>`__   `(4100) Lieferanten <…>`__ | `EVERS Eberhart (28) <…>`__                                                                       25,00          SREG 9/2014   Ja
 17.01.14   `SREG 9/2014 <…>`__   `(4100) Lieferanten <…>`__ | `EMONTS Daniel (29) <…>`__                                                                        29,95          SREG 9/2014   Ja
                                  **Saldo -488.34 (55 Bewegungen)**                                                                                 **811,12**   **1 299,46**
========== ===================== ================================================================================================================= ============ ============== ============= ===========
<BLANKLINE>


The first two movements are invoices that have been admitted for payment (i.e. a
disbursement instruction (AAW) has been registered), but the payment has not yet
been executed.

Let's look at one of these movements via its client.

>>> client = rt.models.pcsw.Client.objects.get(pk=29)
>>> print(client)
EMONTS Daniel (29)

Our client has lots of other open transactions:

>>> rt.show(accounting.MovementsByProject, client)
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE +REPORT_UDIFF
========== ===================== ============================================================================================================== =============== =============== ====================== ===========
 Valuta     Beleg                 Beschreibung                                                                                                   Debit           Kredit          Match                  Beglichen
---------- --------------------- -------------------------------------------------------------------------------------------------------------- --------------- --------------- ---------------------- -----------
 23.05.14   `AAW 13/2014 <…>`__   `(832/330/01) Allgemeine Beihilfen <…>`__ / Allgemeine Beihilfen / `Emonts Daniel <…>`__                       648,91                          `AAW 13:5 <…>`__       Nein
 23.05.14   `AAW 13/2014 <…>`__   `(4450) Auszuführende Ausgabeanweisungen <…>`__ / Allgemeine Beihilfen / `Emonts Daniel <…>`__                                 648,91          `AAW 13:5 <…>`__       Nein
 23.05.14   `AAW 14/2014 <…>`__   `(832/330/03) Heizkosten- u. Energiebeihilfe <…>`__ / Heizkosten- u. Energiebeihilfe / `Emonts Daniel <…>`__   817,36                          `AAW 14:5 <…>`__       Nein
 23.05.14   `AAW 14/2014 <…>`__   `(4450) Auszuführende Ausgabeanweisungen <…>`__ / Heizkosten- u. Energiebeihilfe / `Emonts Daniel <…>`__                       817,36          `AAW 14:5 <…>`__       Nein
 23.05.14   `AAW 15/2014 <…>`__   `(832/330/03F) Fonds Gas und Elektrizität <…>`__ / Fonds Gas und Elektrizität / `Emonts Daniel <…>`__          544,91                          `AAW 15:5 <…>`__       Nein
 23.05.14   `AAW 15/2014 <…>`__   `(4450) Auszuführende Ausgabeanweisungen <…>`__ / Fonds Gas und Elektrizität / `Emonts Daniel <…>`__                           544,91          `AAW 15:5 <…>`__       Nein
 23.05.14   `AAW 16/2014 <…>`__   `(832/3331/01) Eingliederungseinkommen <…>`__ / Eingliederungseinkommen / `Emonts Daniel <…>`__                800,08                          `AAW 16:5 <…>`__       Nein
 23.05.14   `AAW 16/2014 <…>`__   `(4450) Auszuführende Ausgabeanweisungen <…>`__ / Eingliederungseinkommen / `Emonts Daniel <…>`__                              800,08          `AAW 16:5 <…>`__       Nein
 23.05.14   `AAW 17/2014 <…>`__   `(832/334/27) Sozialhilfe <…>`__ / Sozialhilfe / `Emonts Daniel <…>`__                                         648,91                          `AAW 17:5 <…>`__       Nein
 23.05.14   `AAW 17/2014 <…>`__   `(4450) Auszuführende Ausgabeanweisungen <…>`__ / Sozialhilfe / `Emonts Daniel <…>`__                                          648,91          `AAW 17:5 <…>`__       Nein
 23.05.14   `AAW 18/2014 <…>`__   `(832/3343/21) Beihilfe für Ausländer <…>`__ / Beihilfe für Ausländer / `Emonts Daniel <…>`__                  817,36                          `AAW 18:5 <…>`__       Nein
 23.05.14   `AAW 18/2014 <…>`__   `(4450) Auszuführende Ausgabeanweisungen <…>`__ / Beihilfe für Ausländer / `Emonts Daniel <…>`__                               817,36          `AAW 18:5 <…>`__       Nein
 17.05.14   `SREG 1/2014 <…>`__   `(4100) Lieferanten <…>`__ / `AS Matsalu Veevärk <…>`__                                                                        29,95           `SREG 1/2014 <…>`__    Nein
 02.05.14   `SREG 2/2014 <…>`__   `(4100) Lieferanten <…>`__ / `Maksu- ja Tolliamet <…>`__                                                                       120,00          `SREG 2/2014 <…>`__    Nein
 23.04.14   `AAW 7/2014 <…>`__    `(832/330/01) Allgemeine Beihilfen <…>`__ / Allgemeine Beihilfen / `Emonts Daniel <…>`__                       544,91                          `AAW 7:5 <…>`__        Nein
 23.04.14   `AAW 7/2014 <…>`__    `(4450) Auszuführende Ausgabeanweisungen <…>`__ / Allgemeine Beihilfen / `Emonts Daniel <…>`__                                 544,91          `AAW 7:5 <…>`__        Nein
 23.04.14   `AAW 8/2014 <…>`__    `(832/330/03) Heizkosten- u. Energiebeihilfe <…>`__ / Heizkosten- u. Energiebeihilfe / `Emonts Daniel <…>`__   800,08                          `AAW 8:5 <…>`__        Nein
 23.04.14   `AAW 8/2014 <…>`__    `(4450) Auszuführende Ausgabeanweisungen <…>`__ / Heizkosten- u. Energiebeihilfe / `Emonts Daniel <…>`__                       800,08          `AAW 8:5 <…>`__        Nein
 23.04.14   `AAW 9/2014 <…>`__    `(832/330/03F) Fonds Gas und Elektrizität <…>`__ / Fonds Gas und Elektrizität / `Emonts Daniel <…>`__          648,91                          `AAW 9:5 <…>`__        Nein
 23.04.14   `AAW 9/2014 <…>`__    `(4450) Auszuführende Ausgabeanweisungen <…>`__ / Fonds Gas und Elektrizität / `Emonts Daniel <…>`__                           648,91          `AAW 9:5 <…>`__        Nein
 23.04.14   `AAW 10/2014 <…>`__   `(832/3331/01) Eingliederungseinkommen <…>`__ / Eingliederungseinkommen / `Emonts Daniel <…>`__                817,36                          `AAW 10:5 <…>`__       Nein
 23.04.14   `AAW 10/2014 <…>`__   `(4450) Auszuführende Ausgabeanweisungen <…>`__ / Eingliederungseinkommen / `Emonts Daniel <…>`__                              817,36          `AAW 10:5 <…>`__       Nein
 23.04.14   `AAW 11/2014 <…>`__   `(832/334/27) Sozialhilfe <…>`__ / Sozialhilfe / `Emonts Daniel <…>`__                                         544,91                          `AAW 11:5 <…>`__       Nein
 23.04.14   `AAW 11/2014 <…>`__   `(4450) Auszuführende Ausgabeanweisungen <…>`__ / Sozialhilfe / `Emonts Daniel <…>`__                                          544,91          `AAW 11:5 <…>`__       Nein
 23.04.14   `AAW 12/2014 <…>`__   `(832/3343/21) Beihilfe für Ausländer <…>`__ / Beihilfe für Ausländer / `Emonts Daniel <…>`__                  800,08                          `AAW 12:5 <…>`__       Nein
 23.04.14   `AAW 12/2014 <…>`__   `(4450) Auszuführende Ausgabeanweisungen <…>`__ / Beihilfe für Ausländer / `Emonts Daniel <…>`__                               800,08          `AAW 12:5 <…>`__       Nein
 21.04.14   `ZKBC 4/2014 <…>`__   `(4300) Offene Zahlungsaufträge <…>`__ / `Emonts Daniel <…>`__                                                                 648,91          `AAW 1:5 <…>`__        Nein
 21.04.14   `ZKBC 4/2014 <…>`__   `(4300) Offene Zahlungsaufträge <…>`__ / `Emonts Daniel <…>`__                                                                 817,36          `AAW 2:5 <…>`__        Nein
 21.04.14   `ZKBC 4/2014 <…>`__   `(4300) Offene Zahlungsaufträge <…>`__ / `Emonts Daniel <…>`__                                                                 544,91          `AAW 3:5 <…>`__        Nein
 21.04.14   `ZKBC 4/2014 <…>`__   `(4300) Offene Zahlungsaufträge <…>`__ / `Emonts Daniel <…>`__                                                                 800,08          `AAW 4:5 <…>`__        Nein
 21.04.14   `ZKBC 4/2014 <…>`__   `(4300) Offene Zahlungsaufträge <…>`__ / `Emonts Daniel <…>`__                                                                 648,91          `AAW 5:5 <…>`__        Nein
 21.04.14   `ZKBC 4/2014 <…>`__   `(4300) Offene Zahlungsaufträge <…>`__ / `Emonts Daniel <…>`__                                                                 817,36          `AAW 6:5 <…>`__        Nein
 21.04.14   `ZKBC 4/2014 <…>`__   `(4300) Offene Zahlungsaufträge <…>`__ / `AS Matsalu Veevärk <…>`__                                                            15,33           `SREG 4/2014 <…>`__    Nein
 21.04.14   `ZKBC 4/2014 <…>`__   `(4300) Offene Zahlungsaufträge <…>`__ / `IIZI kindlustusmaakler AS <…>`__                                                     25,00           `REG 9/2014 <…>`__     Nein
 21.04.14   `ZKBC 4/2014 <…>`__   `(4300) Offene Zahlungsaufträge <…>`__ / `Maksu- ja Tolliamet <…>`__                                                           10,00           `SREG 5/2014 <…>`__    Nein
 17.04.14   `SREG 3/2014 <…>`__   `(4100) Lieferanten <…>`__ / `Niederau Eupen AG <…>`__                                                                         5,33            `SREG 3/2014 <…>`__    Nein
 23.03.14   `AAW 1/2014 <…>`__    `(832/330/01) Allgemeine Beihilfen <…>`__ / Allgemeine Beihilfen / `Emonts Daniel <…>`__                       648,91                          `AAW 1:5 <…>`__        Nein
 23.03.14   `AAW 2/2014 <…>`__    `(832/330/03) Heizkosten- u. Energiebeihilfe <…>`__ / Heizkosten- u. Energiebeihilfe / `Emonts Daniel <…>`__   817,36                          `AAW 2:5 <…>`__        Nein
 23.03.14   `AAW 3/2014 <…>`__    `(832/330/03F) Fonds Gas und Elektrizität <…>`__ / Fonds Gas und Elektrizität / `Emonts Daniel <…>`__          544,91                          `AAW 3:5 <…>`__        Nein
 23.03.14   `AAW 4/2014 <…>`__    `(832/3331/01) Eingliederungseinkommen <…>`__ / Eingliederungseinkommen / `Emonts Daniel <…>`__                800,08                          `AAW 4:5 <…>`__        Nein
 23.03.14   `AAW 5/2014 <…>`__    `(832/334/27) Sozialhilfe <…>`__ / Sozialhilfe / `Emonts Daniel <…>`__                                         648,91                          `AAW 5:5 <…>`__        Nein
 23.03.14   `AAW 6/2014 <…>`__    `(832/3343/21) Beihilfe für Ausländer <…>`__ / Beihilfe für Ausländer / `Emonts Daniel <…>`__                  817,36                          `AAW 6:5 <…>`__        Nein
 21.03.14   `ZKBC 3/2014 <…>`__   `(4300) Offene Zahlungsaufträge <…>`__ / `AS Matsalu Veevärk <…>`__                                                            25,00           `SREG 7/2014 <…>`__    Nein
 21.03.14   `ZKBC 3/2014 <…>`__   `(4300) Offene Zahlungsaufträge <…>`__ / `Electrabel Customer Solutions <…>`__                                                 29,95           `REG 11/2014 <…>`__    Nein
 21.03.14   `ZKBC 3/2014 <…>`__   `(4300) Offene Zahlungsaufträge <…>`__ / `Niederau Eupen AG <…>`__                                                             12,50           `SREG 6/2014 <…>`__    Nein
 21.03.14   `ZKBC 3/2014 <…>`__   `(4300) Offene Zahlungsaufträge <…>`__ / `Leffin Electronics <…>`__                                                            5,33            `REG 12/2014 <…>`__    Nein
 21.02.14   `ZKBC 2/2014 <…>`__   `(4300) Offene Zahlungsaufträge <…>`__ / `Eesti Energia AS <…>`__                                                              10,00           `REG 14/2014 <…>`__    Nein
 21.02.14   `ZKBC 2/2014 <…>`__   `(4300) Offene Zahlungsaufträge <…>`__ / `Maksu- ja Tolliamet <…>`__                                                           54,95           `SREG 8/2014 <…>`__    Nein
 21.02.14   `ZKBC 2/2014 <…>`__   `(4300) Offene Zahlungsaufträge <…>`__ / `Niederau Eupen AG <…>`__                                                             29,95           `SREG 9/2014 <…>`__    Nein
 21.01.14   `ZKBC 1/2014 <…>`__   `(4300) Offene Zahlungsaufträge <…>`__ / `AS Matsalu Veevärk <…>`__                                                            120,00          `SREG 10/2014 <…>`__   Nein
                                  **Saldo -493.29 (50 Bewegungen)**                                                                              **12 711,31**   **13 204,60**
========== ===================== ============================================================================================================== =============== =============== ====================== ===========
<BLANKLINE>




.. _welfare.specs.r20160105:


Some choices requests
=====================

>>> obj = vatless.AccountInvoice.objects.get(pk=1)
>>> obj
AccountInvoice #1 ('REG 1/2014')

>>> kwargs = dict()
>>> fields = 'count rows'
>>> mt = contenttypes.ContentType.objects.get_for_model(vatless.AccountInvoice).pk
>>> demo_get(
...    'wilfried', 'choices/vatless/ItemsByProjectInvoice/account',
...    fields, 22, mt=mt, mk=1, **kwargs)
