.. doctest docs/specs/excerpts.rst
.. _welfare.specs.excerpts:

==========================================
Usage of database excerpts in Lino Welfare
==========================================

.. doctest init:

    >>> import lino
    >>> lino.startup('lino_welfare.projects.gerd.settings.doctests')
    >>> from lino.api.doctest import *


.. contents::
   :local:
   :depth: 2


Configuring excerpts
====================

See also :ref:`lino.admin.printing`.

Here is a more complete list of excerpt types:

>>> rt.show(excerpts.ExcerptTypes)
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE +REPORT_UDIFF
====================================== ======== =============== =========================== ===================== ============================= ================================
 Modell                                 Primär   Bescheinigend   Bezeichnung                 Druckmethode          Vorlage                       Textkörper-Vorlage
-------------------------------------- -------- --------------- --------------------------- --------------------- ----------------------------- --------------------------------
 `aids.IncomeConfirmation <…>`__        Ja       Ja              Einkommensbescheinigung                           Default.odt                   certificate.body.html
 `aids.RefundConfirmation <…>`__        Ja       Ja              Kostenübernahmeschein                             Default.odt                   certificate.body.html
 `aids.SimpleConfirmation <…>`__        Ja       Ja              Einfache Bescheinigung                            Default.odt                   certificate.body.html
 `art61.Contract <…>`__                 Ja       Ja              Art.61-Konvention                                                               contract.body.html
 `cal.Guest <…>`__                      Ja       Nein            Anwesenheitsbescheinigung                         Default.odt                   presence_certificate.body.html
 `cbss.IdentifyPersonRequest <…>`__     Ja       Ja              IdentifyPerson-Anfrage
 `cbss.ManageAccessRequest <…>`__       Ja       Ja              ManageAccess-Anfrage
 `cbss.RetrieveTIGroupsRequest <…>`__   Ja       Ja              Tx25-Anfrage
 `contacts.Partner <…>`__               Nein     Nein            Zahlungserinnerung          WeasyPdfBuildMethod   payment_reminder.weasy.html
 `contacts.Person <…>`__                Nein     Nein            Nutzungsbestimmungen        AppyPdfBuildMethod    TermsConditions.odt
 `debts.Budget <…>`__                   Ja       Ja              Finanzielle Situation
 `esf.ClientSummary <…>`__              Ja       Ja              Training report             WeasyPdfBuildMethod
 `finan.BankStatement <…>`__            Ja       Ja              Kontoauszug
 `finan.JournalEntry <…>`__             Ja       Ja              Diverse Buchung
 `finan.PaymentOrder <…>`__             Ja       Ja              Zahlungsauftrag
 `isip.Contract <…>`__                  Ja       Ja              VSE
 `jobs.Contract <…>`__                  Ja       Ja              Art.60§7-Konvention
 `pcsw.Client <…>`__                    Ja       Nein            Aktenblatt                                        file_sheet.odt
 `pcsw.Client <…>`__                    Nein     Nein            Aktionsplan                                       Default.odt                   pac.body.html
 `pcsw.Client <…>`__                    Nein     Nein            Curriculum vitae            AppyRtfBuildMethod    cv.odt
 `pcsw.Client <…>`__                    Nein     Nein            eID-Inhalt                                        eid-content.odt
====================================== ======== =============== =========================== ===================== ============================= ================================
<BLANKLINE>


Demo excerpts
=============

Here is a list of all demo excerpts.

>>> rt.show(excerpts.AllExcerpts, language="en", column_names="id excerpt_type owner project company language")
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE +REPORT_UDIFF
==== ======================== =========================================================== ============================ ================================ ==========
 ID   Excerpt Type             Controlled by                                               Client                       Recipient (Organization)         Language
---- ------------------------ ----------------------------------------------------------- ---------------------------- -------------------------------- ----------
 77   Action plan              `AUSDEMWALD Alfons (17) <…>`__                              AUSDEMWALD Alfons (17)                                        de
 76   eID sheet                `AUSDEMWALD Alfons (17) <…>`__                              AUSDEMWALD Alfons (17)                                        de
 75   File sheet               `AUSDEMWALD Alfons (17) <…>`__                              AUSDEMWALD Alfons (17)                                        de
 74   Curriculum vitae         `AUSDEMWALD Alfons (17) <…>`__                              AUSDEMWALD Alfons (17)                                        de
 73   Presence certificate     `Presence #1 (22.05.2014) <…>`__                            AUSDEMWALD Alfons (17)                                        de
 72   Payment reminder         `Belgisches Rotes Kreuz <…>`__                                                                                            de
 71   Art60§7 job supplyment   `Art60§7 job supplyment#16 (Denis DENON) <…>`__             DENON Denis (81*)            R-Cycle Sperrgutsortierzentrum   de
 70   Art60§7 job supplyment   `Art60§7 job supplyment#15 (Denis DENON) <…>`__             DENON Denis (81*)            BISA                             de
 69   Art60§7 job supplyment   `Art60§7 job supplyment#14 (Rik RADERMECKER) <…>`__         RADERMECKER Rik (74)         R-Cycle Sperrgutsortierzentrum   de
 68   Art60§7 job supplyment   `Art60§7 job supplyment#13 (Rik RADERMECKER) <…>`__         RADERMECKER Rik (74)         Pro Aktiv V.o.G.                 de
 ...
 46   ISIP                     `ISIP#25 (David DA VINCI) <…>`__                            DA VINCI David (66)                                           de
 45   ISIP                     `ISIP#24 (David DA VINCI) <…>`__                            DA VINCI David (66)                                           de
 ...
 13   Art61 job supplyment     `Art61 job supplyment#1 (Daniel EMONTS) <…>`__              EMONTS Daniel (29)                                            de
 12   Terms & conditions       `Mr Albert ADAM <…>`__                                                                                                    de
 11   Simple confirmation      `Clothes bank/22/05/2014/141/19 <…>`__                      FRISCH Paul (141)            Belgisches Rotes Kreuz           de
 10   Simple confirmation      `Clothes bank/01/06/2014/60/16 <…>`__                       RADERMACHER Guido (60)                                        de
 9    Simple confirmation      `Food bank/31/05/2014/56/13 <…>`__                          RADERMACHER Christian (56)                                    en
 8    Simple confirmation      `Heating costs/30/05/2014/53/10 <…>`__                      EMONTS-GAST Erna (53)                                         fr
 7    Simple confirmation      `Furniture/29/05/2014/47/7 <…>`__                           MALMENDIER Marc (47)                                          de
 6    Refund confirmation      `DMH/28/05/2014/43/7 <…>`__                                 LAMBERTZ Guido (43)                                           de
 5    Refund confirmation      `AMK/27/05/2014/40/1 <…>`__                                 JONAS Josef (40)                                              fr
 4    Simple confirmation      `Erstattung/25/05/2014/31/1 <…>`__                          FAYMONVILLE Luc (31*)                                         de
 3    Income confirmation      `Feste Beihilfe/24/05/2014/29/58 <…>`__                     EMONTS Daniel (29)                                            de
 2    Income confirmation      `Ausländerbeihilfe/08/08/2013/17/2 <…>`__                   AUSDEMWALD Alfons (17)                                        de
 1    Income confirmation      `EiEi/29/09/2012/17/1 <…>`__                                AUSDEMWALD Alfons (17)                                        de
==== ======================== =========================================================== ============================ ================================ ==========
<BLANKLINE>





As for the default language of an excerpt: the recipient overrides the
owner.

The above list no longer shows well how the language of an excerpt
depends on the recipient and the client.  That would need some more
excerpts.  Excerpt 88 (the only example) is in *French* because the
recipient (BISA) speaks French and although the owner (Charlotte)
speaks *German*:

>>> print(contacts.Partner.objects.get(id=97).language)
fr
>>> print(contacts.Partner.objects.get(id=19).language)
de


The default template for excerpts
==================================

.. xfile:: excerpts/Default.odt

This template should be customized locally to contain the :term:`site
operator`'s layout.


The template inserts the recipient address using this appy.pod code::

    do text
    from html(this.get_address_html(5, **{'class':"Recipient"})

This code is inserted as a command in some paragraph whose content in
the template can be anything since it will be replaced by the computed
text.

>>> obj = aids.SimpleConfirmation.objects.get(pk=19)
>>> print(obj.get_address_html(5, **{'class':"Recipient"}))
<p class="Recipient">Belgisches Rotes Kreuz<br/>Hillstraße 1<br/>4700 Eupen</p>

That paragraph should also contain another comment::

    do text if this.excerpt_type.print_recipient

There should of course be a paragraph style "Recipient" with proper
margins and spacing set.
