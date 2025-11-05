.. doctest docs/specs/checkdata.rst
.. _welfare.specs.checkdata:

==========================================
Checking for data problems in Lino Welfare
==========================================

..  doctest init:

    >>> from lino import startup
    >>> startup('lino_welfare.projects.gerd.settings.doctests')
    >>> from lino.api.doctest import *

Lino Welfare offers some functionality for managing data
problems.

See also :ref:`book.specs.checkdata`.


..  preliminary:

    >>> cal.Event.get_default_table()
    lino_xl.lib.cal.ui.Events


Data checkers available in Lino Welfare
=======================================

In the web interface you can select :menuselection:`Explorer -->
System --> Data checkers` to see a table of all available
checkers.

..
    >>> show_menu_path(checkdata.Checkers, language="en")
    Explorer --> System --> Data checkers

>>> rt.show(checkdata.Checkers, language="en")
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE +REPORT_UDIFF
======================================= ===================================================
 value                                   text
--------------------------------------- ---------------------------------------------------
 accounting.VoucherChecker               Check integrity of numbered vouchers
 addresses.AddressOwnerChecker           Check for missing or non-primary address records
 aids.ConfirmationChecker                Check for confirmations outside of granted period
 beid.SSINChecker                        Check for invalid SSINs
 cal.ConflictingEventsChecker            Check for conflicting calendar entries
 cal.EventGuestChecker                   Entries without participants
 cal.LongEntryChecker                    Too long-lasting calendar entries
 cal.ObsoleteEventTypeChecker            Obsolete generated calendar entries
 coachings.ClientCoachingsChecker        Check coachings
 countries.PlaceChecker                  Check data of geographical places
 dupable_clients.SimilarClientsChecker   Check for similar clients
 finan.FinancialVoucherItemChecker       Check for invalid account/partner combination
 isip.OverlappingContractsChecker        Check for overlapping contracts
 memo.PreviewableChecker                 Check for previewables needing update
 mixins.DupableChecker                   Check for missing phonetic words
 printing.CachedPrintableChecker         Check for missing target files
 sepa.BankAccountChecker                 Check for partner mismatches in bank accounts
 system.BleachChecker                    Find unbleached html content
 uploads.UploadChecker                   Check metadata of upload files
 uploads.UploadsFolderChecker            Find orphaned files in uploads folder
======================================= ===================================================
<BLANKLINE>



Showing all problems
====================

The demo database deliberately contains some data problems.  In the
web interface you can select :menuselection:`Explorer --> System -->
Data problem messages` to see them.  Note that messages are in the language of
the responsible user.

..
    >>> show_menu_path(checkdata.AllMessages, language="en")
    Explorer --> System --> Data problem messages


>>> rt.show(checkdata.AllMessages, language="en", max_width=40)
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE +REPORT_UDIFF
+------------------+------------------------------------------+------------------------------------------+---------------------------------------+
| Responsible      | Database object                          | Message text                             | Checker                               |
+==================+==========================================+==========================================+=======================================+
| Rolf Rompen      | `Christi Himmelfahrt (29.05.2014) <…>`__ | Event conflicts with 4 other events.     | cal.ConflictingEventsChecker          |
+------------------+------------------------------------------+------------------------------------------+---------------------------------------+
| Rolf Rompen      | `Pfingsten (09.06.2014) <…>`__           | Event conflicts with 3 other events.     | cal.ConflictingEventsChecker          |
+------------------+------------------------------------------+------------------------------------------+---------------------------------------+
| Romain Raffault  | `Internal meetings with client           | Event conflicts with Pfingsten           | cal.ConflictingEventsChecker          |
|                  | (09.06.2014 09:00) <…>`__                | (09.06.2014).                            |                                       |
+------------------+------------------------------------------+------------------------------------------+---------------------------------------+
| Alicia Allmanns  | `Consultation (29.05.2014 08:30) <…>`__  | Event conflicts with Christi Himmelfahrt | cal.ConflictingEventsChecker          |
|                  |                                          | (29.05.2014).                            |                                       |
+------------------+------------------------------------------+------------------------------------------+---------------------------------------+
| Alicia Allmanns  | `Petit-déjeuner (09.06.2014 09:40)       | Event conflicts with Pfingsten           | cal.ConflictingEventsChecker          |
|                  | <…>`__                                   | (09.06.2014).                            |                                       |
+------------------+------------------------------------------+------------------------------------------+---------------------------------------+
| Hubert Huppertz  | `Versammlung (09.06.2014 10:20) with     | Event conflicts with Pfingsten           | cal.ConflictingEventsChecker          |
|                  | LEFFIN Josefine (46*) <…>`__             | (09.06.2014).                            |                                       |
+------------------+------------------------------------------+------------------------------------------+---------------------------------------+
| Patrick Paraneau | `Absent for private reasons (29.05.2014) | Event conflicts with Christi Himmelfahrt | cal.ConflictingEventsChecker          |
|                  | <…>`__                                   | (29.05.2014).                            |                                       |
+------------------+------------------------------------------+------------------------------------------+---------------------------------------+
| Rolf Rompen      | `DEMEULENAERE Dorothée (23) <…>`__       | Ähnliche Klienten: DOBBELSTEIN-          | dupable_clients.SimilarClientsChecker |
|                  |                                          | DEMEULENAERE Dorothée (24*)              |                                       |
+------------------+------------------------------------------+------------------------------------------+---------------------------------------+
| Hubert Huppertz  | `DOBBELSTEIN-DEMEULENAERE Dorothée (24*) | Ähnliche Klienten: DEMEULENAERE Dorothée | dupable_clients.SimilarClientsChecker |
|                  | <…>`__                                   | (23)                                     |                                       |
+------------------+------------------------------------------+------------------------------------------+---------------------------------------+
| Mélanie Mélard   | `DOBBELSTEIN Dorothée (25) <…>`__        | Ähnliche Klienten: DOBBELSTEIN-          | dupable_clients.SimilarClientsChecker |
|                  |                                          | DEMEULENAERE Dorothée (24*)              |                                       |
+------------------+------------------------------------------+------------------------------------------+---------------------------------------+
| Caroline Carnol  | `FAYMONVILLE Luc (31*) <…>`__            | Begleitet und veraltet zugleich.         | coachings.ClientCoachingsChecker      |
+------------------+------------------------------------------+------------------------------------------+---------------------------------------+
| Caroline Carnol  | `DENON Denis (81*) <…>`__                | Begleitet und veraltet zugleich.         | coachings.ClientCoachingsChecker      |
+------------------+------------------------------------------+------------------------------------------+---------------------------------------+
<BLANKLINE>




Filtering problem messages
==========================

The user can set the table parameters e.g. to see only problems of a
given type ("checker"). The following snippet simulates the situation
of selecting the :class:`SimilarClientsChecker
<lino_welfare.modlib.dupable_clients.models.SimilarClientsChecker>`.

>>> Checkers = rt.models.checkdata.Checkers
>>> rt.show(checkdata.AllMessages, language="en",
...     param_values=dict(checker=Checkers.get_by_value(
...     'dupable_clients.SimilarClientsChecker')))
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE -REPORT_UDIFF
================= ================================================= ============================================================ =======================================
 Responsible       Database object                                   Message text                                                 Checker
----------------- ------------------------------------------------- ------------------------------------------------------------ ---------------------------------------
 Rolf Rompen       `DEMEULENAERE Dorothée (23) <…>`__                Ähnliche Klienten: DOBBELSTEIN-DEMEULENAERE Dorothée (24*)   dupable_clients.SimilarClientsChecker
 Hubert Huppertz   `DOBBELSTEIN-DEMEULENAERE Dorothée (24*) <…>`__   Ähnliche Klienten: DEMEULENAERE Dorothée (23)                dupable_clients.SimilarClientsChecker
 Mélanie Mélard    `DOBBELSTEIN Dorothée (25) <…>`__                 Ähnliche Klienten: DOBBELSTEIN-DEMEULENAERE Dorothée (24*)   dupable_clients.SimilarClientsChecker
================= ================================================= ============================================================ =======================================
<BLANKLINE>


My data problems
================

In the web interface you can select :menuselection:`Office --> Data problem
messages assigned to me` to see a list of all :term:`data problem messages <data
problem message>` assigned to you.

>>> show_menu_path(checkdata.MyMessages, language="en")
Office --> Data problem messages assigned to me

>>> print(rt.login('melanie').user.language)
fr
>>> rt.login('melanie').show(checkdata.MyMessages, language="en")
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE -REPORT_UDIFF
================ =================================== ============================================================ =======================================
 Responsible      Database object                     Message text                                                 Checker
---------------- ----------------------------------- ------------------------------------------------------------ ---------------------------------------
 Mélanie Mélard   `DOBBELSTEIN Dorothée (25) <…>`__   Ähnliche Klienten: DOBBELSTEIN-DEMEULENAERE Dorothée (24*)   dupable_clients.SimilarClientsChecker
================ =================================== ============================================================ =======================================
<BLANKLINE>
