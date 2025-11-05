.. doctest docs/specs/uploads.rst
.. _welfare.specs.uploads:

=======================
Uploads in Lino Welfare
=======================

This document describes the :mod:`lino_xl.lib.uploads` plugin as used by
:ref:`welfare`.

.. currentmodule:: lino_xl.lib.uploads

.. contents::
   :depth: 2

.. include:: /../docs/shared/include/tested.rst

>>> import lino
>>> lino.startup('lino_welfare.projects.gerd.settings.doctests')
>>> from lino.api.doctest import *

Lino Welfare uses the :mod:`lino_xl.lib.uploads` plugin together with the
:mod:`lino_xl.lib.coachings` plugin, which changes some aspects.


>>> print(cal.TasksByController.detail_layout.main)
<BLANKLINE>
    start_date due_date id workflow_buttons
    summary
    project user delegated
    owner created:20 modified:20
    description #notes.NotesByTask
<BLANKLINE>

.. A few things that should pass, otherwise don't expect the remaining
   tests to pass:

    >>> print(settings.SETTINGS_MODULE)
    lino_welfare.projects.gerd.settings.doctests
    >>> dd.today()
    datetime.date(2014, 5, 22)

    >>> dd.plugins.uploads
    <lino_xl.lib.uploads.Plugin lino_xl.lib.uploads>

.. Some of the following tests rely on the right value for the
   contenttype id of `pcsw.Client` model. If the following line
   changes, subsequent snippets need to get adapted:

    >>> contenttypes.ContentType.objects.get_for_model(pcsw.Client).id #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE -REPORT_UDIFF +SKIP
    5...

Configuring upload types
========================

This is the list of upload types:

>>> rt.login('rolf').show(uploads.UploadTypes)
==== ============================ ======== ================ ============= ========================= ====================== ============================
 ID   Bezeichnung                  Wanted   Upload-Bereich   Max. number   Ablaufwarnung (Einheit)   Ablaufwarnung (Wert)   Upload shortcut
---- ---------------------------- -------- ---------------- ------------- ------------------------- ---------------------- ----------------------------
 11   Arbeitserlaubnis             Ja       Allgemein        1             monatlich                 2
 10   Aufenthaltserlaubnis         Ja       Allgemein        1             monatlich                 2
 15   Behindertenausweis           Nein     Allgemein        -1                                      1
 16   Diplom                       Ja       Allgemein        -1                                      1
 2    Eingangsdokument             Ja       Allgemein        1             monatlich                 2                      Eingangsdokument
 12   Führerschein                 Ja       Allgemein        1             monatlich                 1
 1    Identifizierendes Dokument   Ja       Allgemein        1             monatlich                 2                      Identifizierendes Dokument
 17   Personalausweis              Nein     Allgemein        -1                                      1
 13   Vertrag                      Nein     Allgemein        -1                                      1
 14   Ärztliche Bescheinigung      Nein     Allgemein        -1                                      1
                                                             **0**                                   **14**
==== ============================ ======== ================ ============= ========================= ====================== ============================
<BLANKLINE>


Two clients and their uploads
=============================

The following newcomer has uploaded 2 identifying documents. One of
these is no longer valid, and we know it: `needed` has been unchecked.
The other is still valid but will expire in 3 days.

>>> newcomer = pcsw.Client.objects.get(pk=22)
>>> print(newcomer)
DERICUM Daniel (22)

The UploadsByProject summary shows a summary grouped by upload type.

>>> rt.show(uploads.UploadsByProject, newcomer)  #doctest: +NORMALIZE_WHITESPACE
`⏏ <…>`__ |
Identifizierendes Dokument: `14 <…>`__, `13 <…>`__
Diplom: `11 <…>`__
Personalausweis: `12 <…>`__


>>> rt.show(uploads.UploadsByProject, newcomer, nosummary=True)
============================ ============ ======= =============================== ===================
 Upload-Art                   Gültig bis   Nötig   Beschreibung                    Hochgeladen durch
---------------------------- ------------ ------- ------------------------------- -------------------
 Identifizierendes Dokument   25.05.14     Ja      Identifizierendes Dokument 14   Theresia Thelen
 Identifizierendes Dokument   22.04.14     Nein    Identifizierendes Dokument 13   Theresia Thelen
 Personalausweis              26.06.15     Nein    Personalausweis 12              Hubert Huppertz
 Diplom                       26.06.15     Nein    Diplom 11                       Hubert Huppertz
============================ ============ ======= =============================== ===================
<BLANKLINE>

Here is another :term:`beneficiary` with three uploads:

>>> oldclient = pcsw.Client.objects.get(pk=25)
>>> print(str(oldclient))
DOBBELSTEIN Dorothée (25)

>>> rt.show(uploads.UploadsByProject, oldclient)  #doctest: +NORMALIZE_WHITESPACE
`⏏ <…>`__ |
Aufenthaltserlaubnis: `residence_permit.pdf <…>`__ `⎙ </media/uploads/2014/05/residence_permit.pdf>`__
Arbeitserlaubnis: `work_permit.pdf <…>`__ `⎙ </media/uploads/2014/05/work_permit.pdf>`__
Führerschein: `driving_license.pdf <…>`__ `⎙ </media/uploads/2014/05/driving_license.pdf>`__


>>> rt.show(uploads.UploadsByProject, oldclient, nosummary=True)
====================== ============ ======= ============================================================================================= ===================
 Upload-Art             Gültig bis   Nötig   Beschreibung                                                                                  Hochgeladen durch
---------------------- ------------ ------- --------------------------------------------------------------------------------------------- -------------------
 Führerschein           01.06.14     Ja      `Führerschein driving_license.pdf </media/uploads/2014/05/driving_license.pdf>`__             Caroline Carnol
 Arbeitserlaubnis       30.08.14     Ja      `Arbeitserlaubnis work_permit.pdf </media/uploads/2014/05/work_permit.pdf>`__                 Alicia Allmanns
 Aufenthaltserlaubnis   18.03.15     Ja      `Aufenthaltserlaubnis residence_permit.pdf </media/uploads/2014/05/residence_permit.pdf>`__   Theresia Thelen
====================== ============ ======= ============================================================================================= ===================
<BLANKLINE>


My uploads
==========

Most users can open two tables which show "their" uploads.

>>> print(str(uploads.MyUploads.label))
Meine Upload-Dateien

>>> print(str(uploads.MyExpiringUploads.label))
Meine ablaufenden Upload-Dateien


This is the :class:`MyUploads` table for Theresia:

>>> rt.login('theresia').show(uploads.MyUploads, display_mode=DISPLAY_MODE_GRID)
==== =========================== ============================ ============ ============ ======= ============================================================================================= ======================================
 ID   Klient                      Upload-Art                   Gültig von   Gültig bis   Nötig   Beschreibung                                                                                  Datei
---- --------------------------- ---------------------------- ------------ ------------ ------- --------------------------------------------------------------------------------------------- --------------------------------------
 15   DOBBELSTEIN Dorothée (25)   Aufenthaltserlaubnis                      18.03.15     Ja      `Aufenthaltserlaubnis residence_permit.pdf </media/uploads/2014/05/residence_permit.pdf>`__   uploads/2014/05/residence_permit.pdf
 14   DERICUM Daniel (22)         Identifizierendes Dokument                25.05.14     Ja      Identifizierendes Dokument 14
 13   DERICUM Daniel (22)         Identifizierendes Dokument                22.04.14     Nein    Identifizierendes Dokument 13
==== =========================== ============================ ============ ============ ======= ============================================================================================= ======================================
<BLANKLINE>



And the same for Caroline:

>>> rt.login('caroline').show(uploads.MyUploads, display_mode=DISPLAY_MODE_GRID)
==== =========================== ============== ============ ============ ======= =================================================================================== =====================================
 ID   Klient                      Upload-Art     Gültig von   Gültig bis   Nötig   Beschreibung                                                                        Datei
---- --------------------------- -------------- ------------ ------------ ------- ----------------------------------------------------------------------------------- -------------------------------------
 17   DOBBELSTEIN Dorothée (25)   Führerschein                01.06.14     Ja      `Führerschein driving_license.pdf </media/uploads/2014/05/driving_license.pdf>`__   uploads/2014/05/driving_license.pdf
==== =========================== ============== ============ ============ ======= =================================================================================== =====================================
<BLANKLINE>



This is the :class:`MyExpiringUploads` table for :ref:`hubert`:

>>> rt.login('hubert').show(uploads.MyExpiringUploads, display_mode=DISPLAY_MODE_GRID)
======================== ============================ ============================== =================== ============ ============ =======
 Klient                   Upload-Art                   Beschreibung                   Hochgeladen durch   Gültig von   Gültig bis   Nötig
------------------------ ---------------------------- ------------------------------ ------------------- ------------ ------------ -------
 AUSDEMWALD Alfons (17)   Identifizierendes Dokument   Identifizierendes Dokument 3   Hubert Huppertz                  17.05.15     Ja
 AUSDEMWALD Alfons (17)   Eingangsdokument             Eingangsdokument 4             Hubert Huppertz                  17.05.15     Ja
======================== ============================ ============================== =================== ============ ============ =======
<BLANKLINE>

:ref:`theresia` does not coach anybody, so the :class:`MyExpiringUploads`
table is empty for her:

>>> rt.login('theresia').show(uploads.MyExpiringUploads, display_mode=DISPLAY_MODE_GRID)
Keine Daten anzuzeigen



Shortcut fields
===============


>>> id_document = uploads.UploadType.objects.get(shortcut=uploads.Shortcuts.id_document)
>>> rt.show(uploads.UploadsByType, id_document, display_mode=DISPLAY_MODE_GRID)
=================== ======================== ============================ ======= ============ ============ ======= ===============================
 Hochgeladen durch   Klient                   Upload-Art                   Datei   Gültig von   Gültig bis   Nötig   Beschreibung
------------------- ------------------------ ---------------------------- ------- ------------ ------------ ------- -------------------------------
 Theresia Thelen     DERICUM Daniel (22)      Identifizierendes Dokument                        25.05.14     Ja      Identifizierendes Dokument 14
 Theresia Thelen     DERICUM Daniel (22)      Identifizierendes Dokument                        22.04.14     Nein    Identifizierendes Dokument 13
 Hubert Huppertz     AUSDEMWALD Alfons (17)   Identifizierendes Dokument                        17.05.15     Ja      Identifizierendes Dokument 3
=================== ======================== ============================ ======= ============ ============ ======= ===============================
<BLANKLINE>


Let's have a closer look at the `id_document` shortcut field for
some customers.

The response to this AJAX request is in JSON, and we want to inspect
the `id_document` field using `BeautifulSoup
<https://www.crummy.com/software/BeautifulSoup/bs4/doc/>`__:

>>> uri = "pcsw/Clients/{0}".format(newcomer.pk)
>>> soup = get_json_soup('romain', uri, 'id_document')

This is an upload shortcut field whose target has more than one
row. Which means that it has two buttons.

>>> div = soup.div
>>> len(div.contents)
3

The first button NO LONGER opens a detail window on the *last* uploaded file.
This feature (was it one?)

>>> div.contents[0]  #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE +SKIP
<a href='javascript:Lino.uploads.UploadsByController.insert.run(null,{
"base_params": {...}, "data_record": { "data": {
"description": "", "disabled_fields": { "camera_stream": true, "file_size":
true, "mimetype": true }, "end_date": null, "file": "", "needed": true, "type":
"Source document", "typeHidden": 2 }, "phantom": true, "title": "Ins\u00e9rer
Fichier t\u00e9l\u00e9charg\u00e9" }, "param_values": { "coached_by": null,
"coached_byHidden": null, "end_date": null, "observed_event": "Est active",
"observed_eventHidden": "20", "start_date": null, "upload_type": null,
"upload_typeHidden": null, "user": null, "userHidden": null }, "record_id": null
})' style="vertical-align:-30%;" title="Datei von Ihrem PC zum Server
hochladen."><img alt="add" src="/static/images/mjames/add.png"/></a>

<a href='javascript:Lino.uploads.Uploads.detail.run(null,{ "base_params": {  },
"param_values": { ... }, "record_id": 14 })'
style="text-decoration:none">Letzte</a>

The second item is just the comma that separates the two buttons:

>>> div.contents[1]
', '

The second button opens the list of uploads. Here is the full HTML definition of
that button.  Until 20250306 this button pointed to UploadsByProject but now to
UploadsByController, and the text of the link changed from "Alle 2 Dateien" to
"⏏".

>>> btn = div.contents[2]
>>> btn  #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
<a href='...' style="text-decoration:none"
title="Manage the list of uploaded files."> ⏏ </a>

Already its href is quite long:

>>> btn['href']  #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
'javascript:Lino.uploads.UploadsByController.grid.run(null,{
"base_params": { "mk": 22, "mt": 59, "type": 2 }, "param_values": {
"coached_by": null, "coached_byHidden": null, "end_date": null,
"observed_event": "Est active", "observed_eventHidden": "20", "start_date":
null, "upload_type": null, "upload_typeHidden": null, "user": null,
"userHidden": null }, "record_id": 22 })'


This code would call the :meth:`run` method of the ``grid`` view of the
:class:`uploads.UploadsByController` table with two positional arguments, the first
being `null` and the second being a big JavaScript object. Let's inspect this
second argument of this second button.

>>> arg = btn['href'][58:-1]
>>> print(arg)  #doctest: +ELLIPSIS
{ ... }

>>> d = AttrDict(json.loads(arg))

It has 3 keys:

>>> keys = list(d.keys())
>>> keys.sort()
>>> print(json.dumps(keys))
["base_params", "param_values", "record_id"]

>>> d.record_id
22
>>> d.base_params #doctest: +ELLIPSIS
{'mk': 22, 'mt': 59, 'type': 2}


>>> pprint(d.param_values)
... #doctest: +NORMALIZE_WHITESPACE +IGNORE_EXCEPTION_DETAIL
{'coached_by': None,
 'coached_byHidden': None,
 'end_date': None,
 'observed_event': 'Est active',
 'observed_eventHidden': '20',
 'start_date': None,
 'upload_type': None,
 'upload_typeHidden': None,
 'user': None,
 'userHidden': None}


Uploads by client
=================

:class:`UploadsByProject
<lino_welfare.modlib.uploads.UploadsByProject>` shows all the
uploads of a given client, but it has a customized
:meth:`get_slave_summary <lino.core.actors.Actor.get_slave_summary>`.

The following example is going to use client #25 as master.

>>> obj = oldclient

Here we use :func:`lino.api.doctest.get_json_soup` to inspect what the
summary view of `UploadsByProject` returns for this client.

>>> soup = get_json_soup('rolf', 'pcsw/Clients/25', 'uploads.UploadsByProject1')
>>> print(soup.get_text())
... #doctest: +NORMALIZE_WHITESPACE
Identifizierendes Dokument: Eingangsdokument: Aufenthaltserlaubnis:
residence_permit.pdf ⎙Arbeitserlaubnis: work_permit.pdf ⎙Führerschein:
driving_license.pdf ⎙Diplom:


The HTML fragment contains five links:

>>> links = soup.find_all('a')
>>> len(links)
9

The first link would run the insert action on `UploadsByProject`, with
the owner set to this client

>>> btn = links[0]
>>> print(btn.string)
None
>>> print(btn.img['src'])
/static/images/mjames/add.png

>>> print(btn)
... #doctest: +NORMALIZE_WHITESPACE +ELLIPSIS
<a href='javascript:Lino.uploads.UploadsByProject.insert.run(null,{...})'
style="vertical-align:-30%;" title="Neue(n/s) Upload-Datei
erstellen."><img alt="add" src="/static/images/mjames/add.png"/></a>


>>> print(links[2].get('href'))
... #doctest: +NORMALIZE_WHITESPACE +ELLIPSIS
javascript:Lino.uploads.UploadsByProject.detail.run(null,{ ..., "record_id": 15 })

>>> print(links[3].get('href'))
... #doctest: +NORMALIZE_WHITESPACE +ELLIPSIS
/media/uploads/2014/05/residence_permit.pdf


Now let's inspect the javascript of the first button

>>> dots = btn['href'][57:-1]
>>> print(dots)  #doctest: +ELLIPSIS
{ ... }

>>> d = AttrDict(json.loads(dots))

>>> pprint(d)
... #doctest: +NORMALIZE_WHITESPACE +REPORT_UDIFF
{'base_params': {'mk': 25, 'mt': 59, 'type_id': 1},
 'data_record': {'data': {'description': '',
                          'disabled_fields': {'camera_stream': True,
                                              'file_size': True,
                                              'mimetype': True},
                          'end_date': None,
                          'file': '',
                          'needed': True,
                          'project': 'DOBBELSTEIN Dorothée (25)',
                          'projectHidden': 25,
                          'start_date': None,
                          'type': 'Identifizierendes Dokument',
                          'typeHidden': 1},
                 'phantom': True,
                 'title': 'Upload-Datei erstellen'},
 'param_values': {'coached_by': None,
                  'coached_byHidden': None,
                  'end_date': None,
                  'observed_event': 'Ist aktiv',
                  'observed_eventHidden': '20',
                  'start_date': None,
                  'upload_type': None,
                  'upload_typeHidden': None,
                  'user': None,
                  'userHidden': None},
 'record_id': None}
