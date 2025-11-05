.. doctest docs/specs/topics/sorting.rst

.. _welfare.specs.topics.sorting:

=================
About sorting
=================

I wrote this originally when working on :ticket:`4096` to verify my theory that
the issues are caused by demo data being generated differently because sorting
has changed.  The result is negative, i.e. my theory seems wrong.

Alphabetic sorting is not as we wanted it to be when we wrote
:func:`lino_welfare.modlib.welfare.models.customize_sqlite` (which creates a
custom collation for sqlite). We wanted people like "da Vinci, David" or
"Ärgerlich, Erna" to be correctly sorted.  But this seems to not be related.


.. contents::
   :depth: 2
   :local:

.. include:: /../docs/shared/include/tested.rst

>>> from lino import startup
>>> startup('lino_welfare.projects.gerd.settings.demo')
>>> from lino.api.doctest import *

This to verify whether sorting works as expected.

>>> for o in contacts.Company.objects.all():
...    print("{o.id} {o.name}".format(o=o))
1 Belgisches Rotes Kreuz
2 Rumma & Ko OÜ
3 Bäckerei Ausdemwald
4 Bäckerei Mießen
5 Bäckerei Schmitz
6 Garage Mergelsberg
7 Donderweer BV
8 Van Achter NV
9 Hans Flott & Co
10 Bernd Brechts Bücherladen
11 Reinhards Baumschule
12 Moulin Rouge
13 Auto École Verte
88 ÖSHZ Kettenis
89 BISA
90 R-Cycle Sperrgutsortierzentrum
91 Die neue Alternative V.o.G.
92 Pro Aktiv V.o.G.
93 Werkstatt Cardijn V.o.G.
94 Behindertenstätten Eupen
95 Beschützende Werkstätte Eupen
96 Alliance Nationale des Mutualités Chrétiennes
97 Mutualité Chrétienne de Verviers - Eupen
98 Union Nationale des Mutualités Neutres
99 Mutualia - Mutualité Neutre
100 Solidaris - Mutualité socialiste et syndicale de la province de Liège
101 Apotheke Reul
102 Apotheke Schunck
103 Pharmacies Populaires de Verviers
104 Bosten-Bocken A
105 Brüll Christine
106 Brocal Catherine
107 Bourseaux Alexandre
108 Baguette Stéphanie
109 Demarteau Bernadette
110 Schmitz Marc
111 Cashback sprl
112 Money Wizard AS
115 Arbeitsamt der D.G.
121 AS Express Post
122 AS Matsalu Veevärk
123 Eesti Energia AS
124 IIZI kindlustusmaakler AS
125 Maksu- ja Tolliamet
126 Ragn-Sells AS
127 Electrabel Customer Solutions
128 Ethias s.a.
129 Niederau Eupen AG
130 Leffin Electronics
131 Oikos
132 KAP



>>> for o in contacts.Person.objects.all():
...    print("{o.id} {o.last_name}, {o.first_name}".format(o=o))
159 Adam, Albert
163 Adam, Ilja
168 Adam, Noémie
169 Adam, Odette
170 Adam, Pascale
85 Allmanns, Alicia
16 Altenberg, Hans
14 Arens, Andreas
15 Arens, Annette
17 Ausdemwald, Alfons
18 Bastiaensen, Laurent
71 Bodard, Bernard
160 Braun, Bruno
164 Braun, Jan
165 Braun, Kevin
166 Braun, Lars
167 Braun, Monique
78 Brecht, Bernd
118 Castou, Carmen
21 Chantraine, Marc
20 Charlier, Ulrike
19 Collard, Charlotte
23 Demeulenaere, Dorothée
81 Denon, Denis
22 Dericum, Daniel
25 Dobbelstein, Dorothée
24 Dobbelstein-Demeulenaere, Dorothée
150 Drosson, Dora
80 Dubois, Robin
72 Dupont, Jean
76 Eierschal, Emil
145 Einzig, Paula
29 Emonts, Daniel
51 Emonts, Erich
53 Emonts-Gast, Erna
52 Emontspool, Erwin
30 Engels, Edgar
26 Ernst, Berta
28 Evers, Eberhart
27 Evertz, Bernd
161 Evrard, Eveline
31 Faymonville, Luc
162 Freisen, Françoise
143 Frisch, Alice
144 Frisch, Bernd
149 Frisch, Clara
151 Frisch, Dennis
139 Frisch, Hubert
154 Frisch, Irma
142 Frisch, Ludwig
153 Frisch, Melba
141 Frisch, Paul
146 Frisch, Peter
148 Frisch, Philippe
140 Frogemuth, Gaby
113 Gerkens, Gerd
32 Gernegroß, Germaine
33 Groteclaes, Gregory
35 Hilgers, Henri
34 Hilgers, Hildegard
84 Huppertz, Hubert
36 Ingels, Irene
38 Jacobs, Jacqueline
37 Jansen, Jérémy
82 Jeanémart, Jérôme
39 Johnen, Johann
40 Jonas, Josef
41 Jousten, Jan
87 Jousten, Judith
42 Kaivers, Karl
114 Kasennova, Tatjana
79 Keller, Karl
120 Kimmel, Killian
77 Lahm, Lisa
43 Lambertz, Guido
44 Laschet, Laura
45 Lazarus, Line
46 Leffin, Josefine
152 Loslever, Laura
47 Malmendier, Marc
73 Martelaer, Mark
48 Meessen, Melissa
50 Meier, Marie-Louise
49 Mießen, Michael
83 Mélard, Mélanie
54 Radermacher, Alfons
55 Radermacher, Berta
56 Radermacher, Christian
57 Radermacher, Daniela
58 Radermacher, Edgard
59 Radermacher, Fritz
60 Radermacher, Guido
61 Radermacher, Hans
62 Radermacher, Hedi
63 Radermacher, Inge
64 Radermacher, Jean
74 Radermecker, Rik
86 Thelen, Theresia
75 Vandenmeulenbos, Marie-Louise
119 Waldmann, Walter
116 Waldmann, Waltraud
117 Wehnicht, Werner
147 Zweith, Petra
66 da Vinci, David
65 di Rupo, Didier
67 van Veen, Vincent
70 Ärgerlich, Erna
68 Õunapuu, Õie
69 Östges, Otto


>>> for o in pcsw.Client.objects.all():
...    print("{o.id} {o.last_name}, {o.first_name}".format(o=o))
17 Ausdemwald, Alfons
18 Bastiaensen, Laurent
19 Collard, Charlotte
21 Chantraine, Marc
22 Dericum, Daniel
23 Demeulenaere, Dorothée
24 Dobbelstein-Demeulenaere, Dorothée
25 Dobbelstein, Dorothée
26 Ernst, Berta
27 Evertz, Bernd
28 Evers, Eberhart
29 Emonts, Daniel
30 Engels, Edgar
31 Faymonville, Luc
32 Gernegroß, Germaine
33 Groteclaes, Gregory
34 Hilgers, Hildegard
35 Hilgers, Henri
36 Ingels, Irene
37 Jansen, Jérémy
38 Jacobs, Jacqueline
39 Johnen, Johann
40 Jonas, Josef
41 Jousten, Jan
42 Kaivers, Karl
43 Lambertz, Guido
44 Laschet, Laura
45 Lazarus, Line
46 Leffin, Josefine
47 Malmendier, Marc
48 Meessen, Melissa
50 Meier, Marie-Louise
51 Emonts, Erich
52 Emontspool, Erwin
53 Emonts-Gast, Erna
54 Radermacher, Alfons
55 Radermacher, Berta
56 Radermacher, Christian
57 Radermacher, Daniela
58 Radermacher, Edgard
59 Radermacher, Fritz
60 Radermacher, Guido
61 Radermacher, Hans
62 Radermacher, Hedi
63 Radermacher, Inge
65 di Rupo, Didier
66 da Vinci, David
67 van Veen, Vincent
68 Õunapuu, Õie
69 Östges, Otto
73 Martelaer, Mark
74 Radermecker, Rik
75 Vandenmeulenbos, Marie-Louise
76 Eierschal, Emil
77 Lahm, Lisa
78 Brecht, Bernd
79 Keller, Karl
80 Dubois, Robin
81 Denon, Denis
82 Jeanémart, Jérôme
114 Kasennova, Tatjana
141 Frisch, Paul
160 Braun, Bruno

>>> for o in pcsw.Client.objects.order_by('name'):
...    print("{o.id} {o.last_name}, {o.first_name}".format(o=o))
17 Ausdemwald, Alfons
18 Bastiaensen, Laurent
160 Braun, Bruno
78 Brecht, Bernd
21 Chantraine, Marc
19 Collard, Charlotte
23 Demeulenaere, Dorothée
81 Denon, Denis
22 Dericum, Daniel
25 Dobbelstein, Dorothée
24 Dobbelstein-Demeulenaere, Dorothée
80 Dubois, Robin
76 Eierschal, Emil
29 Emonts, Daniel
51 Emonts, Erich
53 Emonts-Gast, Erna
52 Emontspool, Erwin
30 Engels, Edgar
26 Ernst, Berta
28 Evers, Eberhart
27 Evertz, Bernd
31 Faymonville, Luc
141 Frisch, Paul
32 Gernegroß, Germaine
33 Groteclaes, Gregory
35 Hilgers, Henri
34 Hilgers, Hildegard
36 Ingels, Irene
38 Jacobs, Jacqueline
37 Jansen, Jérémy
82 Jeanémart, Jérôme
39 Johnen, Johann
40 Jonas, Josef
41 Jousten, Jan
42 Kaivers, Karl
114 Kasennova, Tatjana
79 Keller, Karl
77 Lahm, Lisa
43 Lambertz, Guido
44 Laschet, Laura
45 Lazarus, Line
46 Leffin, Josefine
47 Malmendier, Marc
73 Martelaer, Mark
48 Meessen, Melissa
50 Meier, Marie-Louise
54 Radermacher, Alfons
55 Radermacher, Berta
56 Radermacher, Christian
57 Radermacher, Daniela
58 Radermacher, Edgard
59 Radermacher, Fritz
60 Radermacher, Guido
61 Radermacher, Hans
62 Radermacher, Hedi
63 Radermacher, Inge
74 Radermecker, Rik
75 Vandenmeulenbos, Marie-Louise
66 da Vinci, David
65 di Rupo, Didier
67 van Veen, Vincent
68 Õunapuu, Õie
69 Östges, Otto


>>> for o in users.User.objects.all():
...    print("{o.id} {o.username} ({o.last_name}, {o.first_name})".format(o=o))
8 nicolas (, )
6 alicia (Allmanns, Alicia)
9 caroline (Carnol, Caroline)
5 hubert (Huppertz, Hubert)
10 judith (Jousten, Judith)
13 kerstin (Kerres, Kerstin)
4 melanie (Mélard, Mélanie)
11 patrick (Paraneau, Patrick)
2 romain (Raffault, Romain)
1 rolf (Rompen, Rolf)
3 robin (Rood, Robin)
7 theresia (Thelen, Theresia)
12 wilfried (Willems, Wilfried)

>>> for o in households.Household.objects.all():
...    print("{o.id} {o.name}".format(o=o))
133 Gerkens-Kasennova
134 Huppertz-Jousten
135 Jeanémart-Thelen
136 Denon-Mélard
137 Dubois-Lahm
138 Jeanémart-Vandenmeulenbos
155 Frisch-Frogemuth
156 Frisch-Einzig
157 Frisch-Zweith
158 Frisch-Loslever
171 Adam-Evrard
172 Adam-Freisen
173 Braun-Evrard
174 Braun-Freisen



>>> for o in coachings.CoachingType.objects.all():
...    print("{o.id} {o}".format(o=o))
1 ASD
2 DSBE
3 Schuldnerberatung


>>> for o in coachings.Coaching.objects.all():
...    print("{o.id} {o}".format(o=o))
1 alicia / Ausdemwald A
2 hubert / Ausdemwald A
3 melanie / Ausdemwald A
4 caroline / Ausdemwald A
5 hubert / Collard C
6 melanie / Collard C
7 hubert / Dobbelstein-Demeulenaere D
8 melanie / Dobbelstein D
9 alicia / Evertz B
10 hubert / Evers E
11 melanie / Evers E
12 caroline / Evers E
13 hubert / Emonts D
14 melanie / Emonts D
15 hubert / Emonts D
16 melanie / Engels E
17 alicia / Engels E
18 hubert / Engels E
19 melanie / Engels E
20 caroline / Faymonville L
21 hubert / Faymonville L
22 melanie / Groteclaes G
23 hubert / Hilgers H
24 melanie / Hilgers H
25 alicia / Hilgers H
26 hubert / Jacobs J
27 melanie / Jacobs J
28 caroline / Jacobs J
29 hubert / Johnen J
30 melanie / Johnen J
31 hubert / Jonas J
32 melanie / Jonas J
33 alicia / Jonas J
34 hubert / Jonas J
35 melanie / Kaivers K
36 caroline / Kaivers K
37 hubert / Lambertz G
38 melanie / Lazarus L
39 hubert / Lazarus L
40 melanie / Lazarus L
41 alicia / Leffin J
42 hubert / Malmendier M
43 melanie / Malmendier M
44 caroline / Malmendier M
45 hubert / Meessen M
46 melanie / Meessen M
47 hubert / Meessen M
48 melanie / Meessen M
49 alicia / Emonts-Gast E
50 hubert / Emonts-Gast E
51 melanie / Radermacher A
52 caroline / Radermacher C
53 hubert / Radermacher C
54 melanie / Radermacher C
55 hubert / Radermacher E
56 melanie / Radermacher E
57 alicia / Radermacher E
58 hubert / Radermacher F
59 melanie / Radermacher G
60 caroline / Radermacher G
61 hubert / Radermacher G
62 melanie / Radermacher G
63 hubert / Radermacher H
64 melanie / Radermacher H
65 alicia / da Vinci D
66 hubert / van Veen V
67 melanie / van Veen V
68 caroline / van Veen V
69 hubert / Õunapuu Õ
70 melanie / Õunapuu Õ
71 hubert / Östges O
72 melanie / Östges O
73 alicia / Östges O
74 hubert / Radermecker R
75 melanie / Radermecker R
76 caroline / Radermecker R
77 hubert / Radermecker R
78 melanie / Brecht B
79 hubert / Brecht B
80 melanie / Keller K
81 alicia / Dubois R
82 hubert / Dubois R
83 melanie / Dubois R
84 caroline / Denon D
85 hubert / Denon D
86 melanie / Denon D
87 hubert / Jeanémart J
88 melanie / Jeanémart J
89 alicia / Jeanémart J
90 hubert / Jeanémart J

>>> for o in jobs.Job.objects.all():
...    print("{o.id} {o}".format(o=o))
5 Kellner bei BISA
1 Kellner bei R-Cycle Sperrgutsortierzentrum
2 Koch bei BISA
6 Koch bei Pro Aktiv V.o.G.
3 Küchenassistent bei Pro Aktiv V.o.G.
7 Küchenassistent bei R-Cycle Sperrgutsortierzentrum
8 Tellerwäscher bei BISA
4 Tellerwäscher bei R-Cycle Sperrgutsortierzentrum


>>> rt.show(jobs.CandidatureStates)
====== =========== =======================
 Wert   name        Text
------ ----------- -----------------------
 10     active      Aktiv
 20     probation   Probezeit
 25     failed      Probezeit ohne Erfolg
 27     working     Arbeitet
 30     inactive    Inaktiv
====== =========== =======================
<BLANKLINE>


>>> i = pcsw.Client.objects.order_by('name').__iter__()
>>> print(next(i))
AUSDEMWALD Alfons (17)
>>> print(next(i))
BASTIAENSEN Laurent (18)
>>> print(next(i))
BRAUN Bruno (160)
>>> print(next(i))
BRECHT Bernd (78)

>>> for o in cal.Calendar.objects.all():
...    print("{o.id} {o}".format(o=o))
1 Allgemein
2 alicia
3 caroline
4 hubert
5 judith
6 melanie
7 patrick
8 romain
9 rolf
10 robin
11 theresia

>>> for o in isip.Contract.objects.all():
...    print("{o.id} {o}".format(o=o))
1 VSE#1 (Alfons AUSDEMWALD)
2 VSE#2 (Alfons AUSDEMWALD)
3 VSE#3 (Dorothée DOBBELSTEIN)
4 VSE#4 (Eberhart EVERS)
5 VSE#5 (Eberhart EVERS)
6 VSE#6 (Eberhart EVERS)
7 VSE#7 (Edgar ENGELS)
8 VSE#8 (Edgar ENGELS)
9 VSE#9 (Gregory GROTECLAES)
10 VSE#10 (Jacqueline JACOBS)
11 VSE#11 (Karl KAIVERS)
12 VSE#12 (Karl KAIVERS)
13 VSE#13 (Line LAZARUS)
14 VSE#14 (Line LAZARUS)
15 VSE#15 (Melissa MEESSEN)
16 VSE#16 (Melissa MEESSEN)
17 VSE#17 (Melissa MEESSEN)
18 VSE#18 (Alfons RADERMACHER)
19 VSE#19 (Edgard RADERMACHER)
20 VSE#20 (Edgard RADERMACHER)
21 VSE#21 (Edgard RADERMACHER)
22 VSE#22 (Guido RADERMACHER)
23 VSE#23 (Guido RADERMACHER)
24 VSE#24 (David DA VINCI)
25 VSE#25 (David DA VINCI)
26 VSE#26 (David DA VINCI)
27 VSE#27 (Otto ÖSTGES)
28 VSE#28 (Otto ÖSTGES)
29 VSE#29 (Bernd BRECHT)
30 VSE#30 (Bernd BRECHT)
31 VSE#31 (Robin DUBOIS)
32 VSE#32 (Robin DUBOIS)
33 VSE#33 (Jérôme JEANÉMART)
34 VSE#34 (Jérôme JEANÉMART)

>>> for o in jobs.Contract.objects.all():
...    print("{o.id} {o}".format(o=o))
1 Art.60§7-Konvention#1 (Charlotte COLLARD)
2 Art.60§7-Konvention#2 (Bernd EVERTZ)
3 Art.60§7-Konvention#3 (Luc FAYMONVILLE)
4 Art.60§7-Konvention#4 (Luc FAYMONVILLE)
5 Art.60§7-Konvention#5 (Hildegard HILGERS)
6 Art.60§7-Konvention#6 (Guido LAMBERTZ)
7 Art.60§7-Konvention#7 (Marc MALMENDIER)
8 Art.60§7-Konvention#8 (Marc MALMENDIER)
9 Art.60§7-Konvention#9 (Christian RADERMACHER)
10 Art.60§7-Konvention#10 (Christian RADERMACHER)
11 Art.60§7-Konvention#11 (Fritz RADERMACHER)
12 Art.60§7-Konvention#12 (Vincent VAN VEEN)
13 Art.60§7-Konvention#13 (Rik RADERMECKER)
14 Art.60§7-Konvention#14 (Rik RADERMECKER)
15 Art.60§7-Konvention#15 (Denis DENON)
16 Art.60§7-Konvention#16 (Denis DENON)

>>> for o in art61.Contract.objects.all():
...    print("{o.id} {o}".format(o=o))
1 Art.61-Konvention#1 (Daniel EMONTS)
2 Art.61-Konvention#2 (Josef JONAS)
3 Art.61-Konvention#3 (Josef JONAS)
4 Art.61-Konvention#4 (Erna EMONTS-GAST)
5 Art.61-Konvention#5 (Hedi RADERMACHER)
6 Art.61-Konvention#6 (Hedi RADERMACHER)
7 Art.61-Konvention#7 (Karl KELLER)

>>> for o in cv.Function.objects.all():
...    print("{o.id} {o}".format(o=o))
1 Kellner
2 Koch
3 Küchenassistent
4 Tellerwäscher


>>> for o in clients.ClientContactType.objects.all():
...    print("{o.id} {o}".format(o=o))
1 Apotheke
2 Krankenkasse
3 Rechtsanwalt
4 Gerichtsvollzieher
5 Inkasso-Unternehmen
6 Arbeitsvermittler
7 Arzt
8 Hausarzt
9 Zahnarzt
10 Kinderarzt

>>> for o in aids.AidType.objects.all():
...    print("{o.id} {o}".format(o=o))
1 Eingliederungseinkommen
2 Ausländerbeihilfe
3 Feste Beihilfe
4 Erstattung
5 Übernahmeschein
6 Übernahme von Arzt- und/oder Medikamentenkosten
7 Dringende Medizinische Hilfe
8 Möbellager
9 Heizkosten
10 Lebensmittelbank
11 Kleiderkammer

Differing results between Django 3.1.8 and 3.2.0
================================================

I simulate code used in :mod:`lino_welfare.modlib.welfare.fixtures.demo` in
order to find where the difference is hidden.

.. rubric:: No longer differing results

>>> qs = pcsw.Client.objects.filter(client_state=pcsw.ClientStates.coached)
>>> qs.ordered
True

>>> # qs = qs.order_by('name')

>>> for o in qs:
...    print("{o.id} {o.last_name}, {o.first_name}".format(o=o))
17 Ausdemwald, Alfons
19 Collard, Charlotte
25 Dobbelstein, Dorothée
28 Evers, Eberhart
29 Emonts, Daniel
30 Engels, Edgar
31 Faymonville, Luc
33 Groteclaes, Gregory
34 Hilgers, Hildegard
38 Jacobs, Jacqueline
40 Jonas, Josef
42 Kaivers, Karl
43 Lambertz, Guido
45 Lazarus, Line
47 Malmendier, Marc
48 Meessen, Melissa
53 Emonts-Gast, Erna
54 Radermacher, Alfons
56 Radermacher, Christian
58 Radermacher, Edgard
60 Radermacher, Guido
62 Radermacher, Hedi
66 da Vinci, David
67 van Veen, Vincent
69 Östges, Otto
74 Radermecker, Rik
78 Brecht, Bernd
79 Keller, Karl
80 Dubois, Robin
81 Denon, Denis
82 Jeanémart, Jérôme


>>> i = pcsw.Client.objects.all().__iter__()
>>> p = next(i)
>>> for f in cv.Function.objects.all():
...     print(p)
...     p = next(i)
AUSDEMWALD Alfons (17)
BASTIAENSEN Laurent (18)
COLLARD Charlotte (19)
CHANTRAINE Marc (21*)


>>> for o in cv.Sector.objects.all():
...    print("{o.id} {o}".format(o=o))
1  Landwirtschaft & Garten
2  Seefahrt
3  Medizin & Paramedizin
4  Bauwesen & Gebäudepflege
5  Horeca
6  Unterricht
7  Reinigung
8  Transport
9  Textil
10  Kultur
11  Informatik
12  Kosmetik
13  Verkauf
14  Verwaltung & Finanzwesen

>>> for o in pcsw.PersonGroup.objects.all():
...    print("{o.id} {o}".format(o=o))
1 Auswertung
2 Ausbildung
3 Suchen
4 Arbeit
5 Standby


>>> for o in contacts.Partner.objects.all():
...    print("{o.id} {o.name}".format(o=o))
1 Belgisches Rotes Kreuz
2 Rumma & Ko OÜ
3 Bäckerei Ausdemwald
4 Bäckerei Mießen
5 Bäckerei Schmitz
6 Garage Mergelsberg
7 Donderweer BV
8 Van Achter NV
9 Hans Flott & Co
10 Bernd Brechts Bücherladen
11 Reinhards Baumschule
12 Moulin Rouge
13 Auto École Verte
14 Arens Andreas
15 Arens Annette
16 Altenberg Hans
17 Ausdemwald Alfons
18 Bastiaensen Laurent
19 Collard Charlotte
20 Charlier Ulrike
21 Chantraine Marc
22 Dericum Daniel
23 Demeulenaere Dorothée
24 Dobbelstein-Demeulenaere Dorothée
25 Dobbelstein Dorothée
26 Ernst Berta
27 Evertz Bernd
28 Evers Eberhart
29 Emonts Daniel
30 Engels Edgar
31 Faymonville Luc
32 Gernegroß Germaine
33 Groteclaes Gregory
34 Hilgers Hildegard
35 Hilgers Henri
36 Ingels Irene
37 Jansen Jérémy
38 Jacobs Jacqueline
39 Johnen Johann
40 Jonas Josef
41 Jousten Jan
42 Kaivers Karl
43 Lambertz Guido
44 Laschet Laura
45 Lazarus Line
46 Leffin Josefine
47 Malmendier Marc
48 Meessen Melissa
49 Mießen Michael
50 Meier Marie-Louise
51 Emonts Erich
52 Emontspool Erwin
53 Emonts-Gast Erna
54 Radermacher Alfons
55 Radermacher Berta
56 Radermacher Christian
57 Radermacher Daniela
58 Radermacher Edgard
59 Radermacher Fritz
60 Radermacher Guido
61 Radermacher Hans
62 Radermacher Hedi
63 Radermacher Inge
64 Radermacher Jean
65 di Rupo Didier
66 da Vinci David
67 van Veen Vincent
68 Õunapuu Õie
69 Östges Otto
70 Ärgerlich Erna
71 Bodard Bernard
72 Dupont Jean
73 Martelaer Mark
74 Radermecker Rik
75 Vandenmeulenbos Marie-Louise
76 Eierschal Emil
77 Lahm Lisa
78 Brecht Bernd
79 Keller Karl
80 Dubois Robin
81 Denon Denis
82 Jeanémart Jérôme
83 Mélard Mélanie
84 Huppertz Hubert
85 Allmanns Alicia
86 Thelen Theresia
87 Jousten Judith
88 ÖSHZ Kettenis
89 BISA
90 R-Cycle Sperrgutsortierzentrum
91 Die neue Alternative V.o.G.
92 Pro Aktiv V.o.G.
93 Werkstatt Cardijn V.o.G.
94 Behindertenstätten Eupen
95 Beschützende Werkstätte Eupen
96 Alliance Nationale des Mutualités Chrétiennes
97 Mutualité Chrétienne de Verviers - Eupen
98 Union Nationale des Mutualités Neutres
99 Mutualia - Mutualité Neutre
100 Solidaris - Mutualité socialiste et syndicale de la province de Liège
101 Apotheke Reul
102 Apotheke Schunck
103 Pharmacies Populaires de Verviers
104 Bosten-Bocken A
105 Brüll Christine
106 Brocal Catherine
107 Bourseaux Alexandre
108 Baguette Stéphanie
109 Demarteau Bernadette
110 Schmitz Marc
111 Cashback sprl
112 Money Wizard AS
113 Gerkens Gerd
114 Kasennova Tatjana
115 Arbeitsamt der D.G.
116 Waldmann Waltraud
117 Wehnicht Werner
118 Castou Carmen
119 Waldmann Walter
120 Kimmel Killian
121 AS Express Post
122 AS Matsalu Veevärk
123 Eesti Energia AS
124 IIZI kindlustusmaakler AS
125 Maksu- ja Tolliamet
126 Ragn-Sells AS
127 Electrabel Customer Solutions
128 Ethias s.a.
129 Niederau Eupen AG
130 Leffin Electronics
131 Oikos
132 KAP
133 Gerkens-Kasennova
134 Huppertz-Jousten
135 Jeanémart-Thelen
136 Denon-Mélard
137 Dubois-Lahm
138 Jeanémart-Vandenmeulenbos
139 Frisch Hubert
140 Frogemuth Gaby
141 Frisch Paul
142 Frisch Ludwig
143 Frisch Alice
144 Frisch Bernd
145 Einzig Paula
146 Frisch Peter
147 Zweith Petra
148 Frisch Philippe
149 Frisch Clara
150 Drosson Dora
151 Frisch Dennis
152 Loslever Laura
153 Frisch Melba
154 Frisch Irma
155 Frisch-Frogemuth
156 Frisch-Einzig
157 Frisch-Zweith
158 Frisch-Loslever
159 Adam Albert
160 Braun Bruno
161 Evrard Eveline
162 Freisen Françoise
163 Adam Ilja
164 Braun Jan
165 Braun Kevin
166 Braun Lars
167 Braun Monique
168 Adam Noémie
169 Adam Odette
170 Adam Pascale
171 Adam-Evrard
172 Adam-Freisen
173 Braun-Evrard
174 Braun-Freisen



>>> theresia = users.User.objects.get(username="theresia")
>>> for o in reception.Clients.create_request(user=theresia):
...    print("{o.id} {o}".format(o=o))  #doctest: +REPORT_UDIFF
17 AUSDEMWALD Alfons (17)
78 BRECHT Bernd (78)
19 COLLARD Charlotte (19)
25 DOBBELSTEIN Dorothée (25)
80 DUBOIS Robin (80)
29 EMONTS Daniel (29)
53 EMONTS-GAST Erna (53)
30 ENGELS Edgar (30)
28 EVERS Eberhart (28)
33 GROTECLAES Gregory (33)
34 HILGERS Hildegard (34)
38 JACOBS Jacqueline (38)
82 JEANÉMART Jérôme (82)
40 JONAS Josef (40)
42 KAIVERS Karl (42)
79 KELLER Karl (79)
43 LAMBERTZ Guido (43)
45 LAZARUS Line (45)
47 MALMENDIER Marc (47)
48 MEESSEN Melissa (48)
54 RADERMACHER Alfons (54)
56 RADERMACHER Christian (56)
58 RADERMACHER Edgard (58)
60 RADERMACHER Guido (60)
62 RADERMACHER Hedi (62)
74 RADERMECKER Rik (74)
66 DA VINCI David (66)
67 VAN VEEN Vincent (67)
69 ÖSTGES Otto (69)



.. rubric:: Still differing

Only one candidature differs:

>>> for o in jobs.Candidature.objects.all():
...    print("{o.id} {o}".format(o=o))  #doctest: +REPORT_UDIFF
1 Kandidatur von Edgar ENGELS
2 Kandidatur von Luc FAYMONVILLE
3 Kandidatur von Gregory GROTECLAES
4 Kandidatur von Hildegard HILGERS
5 Kandidatur von Jacqueline JACOBS
6 Kandidatur von Josef JONAS
7 Kandidatur von Karl KAIVERS
8 Kandidatur von Guido LAMBERTZ
9 Kandidatur von Line LAZARUS
10 Kandidatur von Marc MALMENDIER
11 Kandidatur von Melissa MEESSEN
12 Kandidatur von Erna EMONTS-GAST
13 Kandidatur von Alfons RADERMACHER
14 Kandidatur von Christian RADERMACHER
15 Kandidatur von Edgard RADERMACHER
16 Kandidatur von Guido RADERMACHER
17 Kandidatur von Hedi RADERMACHER
18 Kandidatur von David DA VINCI
19 Kandidatur von Vincent VAN VEEN
20 Kandidatur von Otto ÖSTGES
21 Kandidatur von Rik RADERMECKER
22 Kandidatur von Bernd BRECHT
23 Kandidatur von Karl KELLER
24 Kandidatur von Robin DUBOIS
25 Kandidatur von Denis DENON
26 Kandidatur von Jérôme JEANÉMART
27 Kandidatur von Alfons AUSDEMWALD
28 Kandidatur von Charlotte COLLARD
29 Kandidatur von Dorothée DOBBELSTEIN
30 Kandidatur von Eberhart EVERS
31 Kandidatur von Daniel EMONTS
32 Kandidatur von Edgar ENGELS
33 Kandidatur von Luc FAYMONVILLE
34 Kandidatur von Gregory GROTECLAES
35 Kandidatur von Hildegard HILGERS
36 Kandidatur von Jacqueline JACOBS
37 Kandidatur von Josef JONAS
38 Kandidatur von Karl KAIVERS
39 Kandidatur von Guido LAMBERTZ
40 Kandidatur von Line LAZARUS
41 Kandidatur von Marc MALMENDIER
42 Kandidatur von Melissa MEESSEN
43 Kandidatur von Erna EMONTS-GAST
44 Kandidatur von Alfons RADERMACHER
45 Kandidatur von Christian RADERMACHER
46 Kandidatur von Edgard RADERMACHER
47 Kandidatur von Guido RADERMACHER
48 Kandidatur von Hedi RADERMACHER
49 Kandidatur von David DA VINCI
50 Kandidatur von Vincent VAN VEEN
51 Kandidatur von Otto ÖSTGES
52 Kandidatur von Rik RADERMECKER
53 Kandidatur von Bernd BRECHT
54 Kandidatur von Karl KELLER
55 Kandidatur von Robin DUBOIS
56 Kandidatur von Denis DENON
57 Kandidatur von Jérôme JEANÉMART
58 Kandidatur von Alfons AUSDEMWALD
59 Kandidatur von Charlotte COLLARD
60 Kandidatur von Dorothée DOBBELSTEIN
61 Kandidatur von Eberhart EVERS
62 Kandidatur von Daniel EMONTS
63 Kandidatur von Edgar ENGELS
64 Kandidatur von Luc FAYMONVILLE
65 Kandidatur von Gregory GROTECLAES
66 Kandidatur von Hildegard HILGERS
67 Kandidatur von Jacqueline JACOBS
68 Kandidatur von Josef JONAS
69 Kandidatur von Karl KAIVERS
70 Kandidatur von Guido LAMBERTZ
71 Kandidatur von Alfons AUSDEMWALD
72 Kandidatur von Laurent BASTIAENSEN
73 Kandidatur von Bernd BRECHT
74 Kandidatur von Marc CHANTRAINE

>>> for o in aids.Granting.objects.all():
...    print("{o.id} {o} {o.client}".format(o=o))  #doctest: +REPORT_UDIFF
1 EiEi/29.09.12/17 AUSDEMWALD Alfons (17)
2 Ausländerbeihilfe/08.08.13/17 AUSDEMWALD Alfons (17)
3 EiEi/13.10.12/25 DOBBELSTEIN Dorothée (25)
4 Ausländerbeihilfe/27.10.12/28 EVERS Eberhart (28)
5 EiEi/20.02.14/28 EVERS Eberhart (28)
6 Ausländerbeihilfe/23.03.14/28 EVERS Eberhart (28)
7 EiEi/10.11.12/30 ENGELS Edgar (30)
8 Ausländerbeihilfe/06.03.14/30 ENGELS Edgar (30)
9 EiEi/24.11.12/33 GROTECLAES Gregory (33)
10 Ausländerbeihilfe/08.12.12/38 JACOBS Jacqueline (38)
11 EiEi/22.12.12/42 KAIVERS Karl (42)
12 Ausländerbeihilfe/31.10.13/42 KAIVERS Karl (42)
13 EiEi/05.01.13/45 LAZARUS Line (45)
14 Ausländerbeihilfe/14.11.13/45 LAZARUS Line (45)
15 EiEi/19.01.13/48 MEESSEN Melissa (48)
16 Ausländerbeihilfe/19.02.13/48 MEESSEN Melissa (48)
17 EiEi/29.12.13/48 MEESSEN Melissa (48)
18 Ausländerbeihilfe/02.02.13/54 RADERMACHER Alfons (54)
19 EiEi/16.02.13/58 RADERMACHER Edgard (58)
20 Ausländerbeihilfe/12.06.14/58 RADERMACHER Edgard (58)
21 EiEi/13.07.14/58 RADERMACHER Edgard (58)
22 Ausländerbeihilfe/02.03.13/60 RADERMACHER Guido (60)
23 EiEi/26.06.14/60 RADERMACHER Guido (60)
24 Ausländerbeihilfe/16.03.13/66 DA VINCI David (66)
25 EiEi/10.07.14/66 DA VINCI David (66)
26 Ausländerbeihilfe/10.08.14/66 DA VINCI David (66)
27 EiEi/30.03.13/69 ÖSTGES Otto (69)
28 Ausländerbeihilfe/24.07.14/69 ÖSTGES Otto (69)
29 EiEi/13.04.13/78 BRECHT Bernd (78)
30 Ausländerbeihilfe/07.08.14/78 BRECHT Bernd (78)
31 EiEi/27.04.13/80 DUBOIS Robin (80)
32 Ausländerbeihilfe/06.03.14/80 DUBOIS Robin (80)
33 EiEi/11.05.13/82 JEANÉMART Jérôme (82)
34 Ausländerbeihilfe/20.03.14/82 JEANÉMART Jérôme (82)
35 EiEi/22.05.14/17 AUSDEMWALD Alfons (17)
36 EiEi/22.05.14/19 COLLARD Charlotte (19)
37 Ausländerbeihilfe/23.05.14/25 DOBBELSTEIN Dorothée (25)
38 Ausländerbeihilfe/23.05.14/28 EVERS Eberhart (28)
39 Feste Beihilfe/24.05.14/29 EMONTS Daniel (29)
40 Feste Beihilfe/24.05.14/30 ENGELS Edgar (30)
41 Erstattung/25.05.14/31 FAYMONVILLE Luc (31*)
42 Erstattung/25.05.14/33 GROTECLAES Gregory (33)
43 Übernahmeschein/26.05.14/34 HILGERS Hildegard (34)
44 Übernahmeschein/26.05.14/38 JACOBS Jacqueline (38)
45 AMK/27.05.14/40 JONAS Josef (40)
46 AMK/27.05.14/42 KAIVERS Karl (42)
47 DMH/28.05.14/43 LAMBERTZ Guido (43)
48 DMH/28.05.14/45 LAZARUS Line (45)
49 Möbellager/29.05.14/47 MALMENDIER Marc (47)
50 Möbellager/29.05.14/48 MEESSEN Melissa (48)
51 Heizkosten/30.05.14/53 EMONTS-GAST Erna (53)
52 Heizkosten/30.05.14/54 RADERMACHER Alfons (54)
53 Lebensmittelbank/31.05.14/56 RADERMACHER Christian (56)
54 Lebensmittelbank/31.05.14/58 RADERMACHER Edgard (58)
55 Kleiderkammer/01.06.14/60 RADERMACHER Guido (60)
56 Kleiderkammer/01.06.14/62 RADERMACHER Hedi (62)
57 DMH/27.05.14/40 JONAS Josef (40)
58 DMH/27.05.14/42 KAIVERS Karl (42)
59 Kleiderkammer/22.05.14/141 FRISCH Paul (141)
