.. _welfare.de.clients:

=====================
Klienten verwalten
=====================

Eine Tabellenansicht der :term:`Klienten <Begünstigter>` sieht ungefähr so aus:

.. image:: /tour/pcsw.Clients.grid.png
  :width: 90%

Beachte die Farben: **Begleitete** Klienten sind **weiß** dargestellt,
**Neuanträge** sind **grün** und **ehemalige Klienten** sind **gelb**.

Für Klienten gibt es mehrere **Tabellenansichten**, die sich durch
Kolonnenanordnung und Filterparameter unterscheiden:

..
  actors_overview:: pcsw.Clients integ.Clients reception.Clients
                     newcomers.NewClients debts.Clients

- :menuselection:`Kontakte --> Klienten`:
  allgemeine Liste, die jeder Benutzer sehen darf.

- :menuselection:`DSBE --> Klienten`:
  spezielle Liste für die Kollegen im DSBE.
  Zeigt immer nur **begleitete** Klienten.
  Hier kann man keine neuen Klienten anlegen.

- :menuselection:`Neuanträge --> Klienten`:
  spezielle Liste für die Zuweisung von Neuanträgen.

- :menuselection:`Empfang --> Klienten`:
  Liste für den Empfangsschalter.

- :menuselection:`Schuldnerberatung --> Klienten`:
  spezielle Liste für die Kollegen der Schuldnerberatung.


Detail-Ansicht
==============

Das :term:`Detail-Fenster <detail window>` eines Klienten ist für alle
Klientenansichten das Gleiche. *Was* im Detail-Fenster angezeigt wird (bzw. was
nicht), das hängt jedoch von den Zugriffsrechten des Benutzers ab.

.. image:: /tour/pcsw.Clients.detail.png
  :width: 90%

Hier drei interessante Felder:

- :attr:`lino_welfare.modlib.pcsw.Client.unemployed_since`
- :attr:`lino_welfare.modlib.pcsw.Client.seeking_since`
- :attr:`lino_welfare.modlib.pcsw.Client.unavailable_until`

Technisches
===========

Technische Details in Englisch unter :mod:`lino_welfare.modlib.pcsw`
