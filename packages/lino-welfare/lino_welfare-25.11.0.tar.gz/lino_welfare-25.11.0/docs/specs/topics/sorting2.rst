.. doctest docs/specs/topics/sorting2.rst

.. _welfare.specs.topics.sorting2:

=================
About sorting (2)
=================


.. contents::
   :depth: 2
   :local:

.. include:: /../docs/shared/include/tested.rst

>>> from lino import startup
>>> startup('lino_welfare.projects.mathieu.settings.demo')
>>> from lino.api.doctest import *

This to verify whether sorting works as expected.

>>> for o in contacts.Company.objects.all():
...    print("{o.id} {o.name}".format(o=o))  #doctest: +REPORT_UDIFF
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
121 Pro Aktiv Unterstadt
122 Pro Aktiv Noereth
123 Pro Aktiv Nispert


>>> for o in contacts.Person.objects.all():
...    print("{o.id} {o.last_name}, {o.first_name}".format(o=o))
... #doctest: +REPORT_UDIFF
150 Adam, Albert
154 Adam, Ilja
159 Adam, Noémie
160 Adam, Odette
161 Adam, Pascale
85 Allmanns, Alicia
16 Altenberg, Hans
14 Arens, Andreas
15 Arens, Annette
17 Ausdemwald, Alfons
18 Bastiaensen, Laurent
71 Bodard, Bernard
151 Braun, Bruno
155 Braun, Jan
156 Braun, Kevin
157 Braun, Lars
158 Braun, Monique
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
141 Drosson, Dora
80 Dubois, Robin
72 Dupont, Jean
76 Eierschal, Emil
136 Einzig, Paula
29 Emonts, Daniel
51 Emonts, Erich
53 Emonts-Gast, Erna
52 Emontspool, Erwin
30 Engels, Edgar
26 Ernst, Berta
28 Evers, Eberhart
27 Evertz, Bernd
152 Evrard, Eveline
31 Faymonville, Luc
153 Freisen, Françoise
134 Frisch, Alice
135 Frisch, Bernd
140 Frisch, Clara
142 Frisch, Dennis
130 Frisch, Hubert
145 Frisch, Irma
133 Frisch, Ludwig
144 Frisch, Melba
132 Frisch, Paul
137 Frisch, Peter
139 Frisch, Philippe
131 Frogemuth, Gaby
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
143 Loslever, Laura
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
138 Zweith, Petra
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
132 Frisch, Paul
151 Braun, Bruno


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

>>> for o in cv.ObstacleType.objects.all():
...    print("{o.id} {o}".format(o=o))
1 Alcohol
2 Santé
3 Dettes
4 Problèmes familiers

>>> for o in cv.Obstacle.objects.all():
...    print("{o.id} {o.person} {o.type}".format(o=o))
1 M. Josef JONAS Alcohol
2 M. Karl KAIVERS Santé
3 M. Guido LAMBERTZ Dettes
4 Mme Line LAZARUS Problèmes familiers
5 M. Marc MALMENDIER Alcohol
6 M. Josef JONAS Santé
7 M. Karl KAIVERS Dettes
8 M. Guido LAMBERTZ Problèmes familiers
9 Mme Line LAZARUS Alcohol
10 M. Marc MALMENDIER Santé
11 M. Josef JONAS Dettes
12 M. Karl KAIVERS Problèmes familiers
13 M. Guido LAMBERTZ Alcohol
14 Mme Line LAZARUS Santé
15 M. Marc MALMENDIER Dettes
16 M. Josef JONAS Problèmes familiers
17 M. Karl KAIVERS Alcohol
18 M. Guido LAMBERTZ Santé
19 Mme Line LAZARUS Dettes
20 M. Marc MALMENDIER Problèmes familiers


>>> for o in courses.Course.objects.all():
...    print("{o.id} {o}".format(o=o))
1 Cuisine (12/05/2014)
2 Créativité (12/05/2014)
3 Notre premier bébé (12/05/2014)
4 Mathématiques (12/05/2014)
5 Français (12/05/2014)
6 Activons-nous! (12/05/2014)
7 Intervention psycho-sociale (03/11/2013)

>>> for o in courses.Enrolment.objects.all():
...    print("{o.id} {o}".format(o=o))
1 Cuisine (12/05/2014) / AUSDEMWALD Alfons (17)
2 Créativité (12/05/2014) / BASTIAENSEN Laurent (18)
3 Notre premier bébé (12/05/2014) / COLLARD Charlotte (19)
4 Mathématiques (12/05/2014) / CHANTRAINE Marc (21*)
5 Français (12/05/2014) / DERICUM Daniel (22)
6 Activons-nous! (12/05/2014) / DEMEULENAERE Dorothée (23)
7 Intervention psycho-sociale (03/11/2013) / DOBBELSTEIN-DEMEULENAERE Dorothée (24*)
8 Cuisine (12/05/2014) / DOBBELSTEIN Dorothée (25)
9 Créativité (12/05/2014) / ERNST Berta (26)
10 Notre premier bébé (12/05/2014) / EVERTZ Bernd (27*)
11 Mathématiques (12/05/2014) / EVERS Eberhart (28)
12 Français (12/05/2014) / EMONTS Daniel (29)
13 Activons-nous! (12/05/2014) / ENGELS Edgar (30)
14 Intervention psycho-sociale (03/11/2013) / FAYMONVILLE Luc (31*)
15 Cuisine (12/05/2014) / GERNEGROSS Germaine (32)
16 Créativité (12/05/2014) / GROTECLAES Gregory (33)
17 Notre premier bébé (12/05/2014) / HILGERS Hildegard (34)
18 Mathématiques (12/05/2014) / HILGERS Henri (35)
19 Français (12/05/2014) / INGELS Irene (36)
20 Activons-nous! (12/05/2014) / JANSEN Jérémy (37)
21 Cuisine (12/05/2014) / JACOBS Jacqueline (38)
22 Créativité (12/05/2014) / JOHNEN Johann (39*)
23 Notre premier bébé (12/05/2014) / JONAS Josef (40)
24 Mathématiques (12/05/2014) / JOUSTEN Jan (41*)
25 Français (12/05/2014) / KAIVERS Karl (42)
26 Activons-nous! (12/05/2014) / LAMBERTZ Guido (43)
27 Cuisine (12/05/2014) / LASCHET Laura (44)
28 Créativité (12/05/2014) / LAZARUS Line (45)
29 Notre premier bébé (12/05/2014) / LEFFIN Josefine (46*)
30 Mathématiques (12/05/2014) / MALMENDIER Marc (47)
31 Français (12/05/2014) / MEESSEN Melissa (48)
32 Activons-nous! (12/05/2014) / MEIER Marie-Louise (50)
33 Cuisine (12/05/2014) / EMONTS Erich (51*)
34 Créativité (12/05/2014) / EMONTSPOOL Erwin (52)
35 Notre premier bébé (12/05/2014) / EMONTS-GAST Erna (53)
36 Mathématiques (12/05/2014) / RADERMACHER Alfons (54)
37 Français (12/05/2014) / RADERMACHER Berta (55)
38 Cuisine (12/05/2014) / RADERMACHER Christian (56)
39 Créativité (12/05/2014) / RADERMACHER Daniela (57)
40 Notre premier bébé (12/05/2014) / RADERMACHER Edgard (58)
41 Mathématiques (12/05/2014) / RADERMACHER Fritz (59*)
42 Français (12/05/2014) / RADERMACHER Guido (60)
43 Cuisine (12/05/2014) / RADERMACHER Hans (61*)
44 Créativité (12/05/2014) / RADERMACHER Hedi (62)
45 Notre premier bébé (12/05/2014) / RADERMACHER Inge (63)
46 Mathématiques (12/05/2014) / DI RUPO Didier (65)
47 Français (12/05/2014) / DA VINCI David (66)
48 Cuisine (12/05/2014) / VAN VEEN Vincent (67)
49 Créativité (12/05/2014) / ÕUNAPUU Õie (68*)
50 Notre premier bébé (12/05/2014) / ÖSTGES Otto (69)
51 Mathématiques (12/05/2014) / MARTELAER Mark (73)
52 Français (12/05/2014) / RADERMECKER Rik (74)
53 Cuisine (12/05/2014) / VANDENMEULENBOS Marie-Louise (75)
54 Créativité (12/05/2014) / EIERSCHAL Emil (76)
55 Notre premier bébé (12/05/2014) / LAHM Lisa (77)
56 Mathématiques (12/05/2014) / BRECHT Bernd (78)
57 Français (12/05/2014) / KELLER Karl (79)
58 Cuisine (12/05/2014) / DUBOIS Robin (80)
59 Créativité (12/05/2014) / DENON Denis (81*)
60 Notre premier bébé (12/05/2014) / JEANÉMART Jérôme (82)
61 Mathématiques (12/05/2014) / KASENNOVA Tatjana (114)
62 Français (12/05/2014) / AUSDEMWALD Alfons (17)
63 Cuisine (12/05/2014) / BASTIAENSEN Laurent (18)
64 Créativité (12/05/2014) / COLLARD Charlotte (19)
65 Notre premier bébé (12/05/2014) / CHANTRAINE Marc (21*)
66 Mathématiques (12/05/2014) / DERICUM Daniel (22)
67 Français (12/05/2014) / DEMEULENAERE Dorothée (23)
68 Cuisine (12/05/2014) / DOBBELSTEIN-DEMEULENAERE Dorothée (24*)
69 Créativité (12/05/2014) / DOBBELSTEIN Dorothée (25)
70 Notre premier bébé (12/05/2014) / ERNST Berta (26)
71 Mathématiques (12/05/2014) / EVERTZ Bernd (27*)
72 Français (12/05/2014) / EVERS Eberhart (28)
73 Cuisine (12/05/2014) / EMONTS Daniel (29)
74 Créativité (12/05/2014) / ENGELS Edgar (30)
75 Notre premier bébé (12/05/2014) / FAYMONVILLE Luc (31*)
76 Mathématiques (12/05/2014) / GERNEGROSS Germaine (32)
77 Français (12/05/2014) / GROTECLAES Gregory (33)
78 Cuisine (12/05/2014) / HILGERS Hildegard (34)
79 Créativité (12/05/2014) / HILGERS Henri (35)
80 Notre premier bébé (12/05/2014) / INGELS Irene (36)
81 Mathématiques (12/05/2014) / JANSEN Jérémy (37)
82 Français (12/05/2014) / JACOBS Jacqueline (38)
83 Cuisine (12/05/2014) / JOHNEN Johann (39*)
84 Créativité (12/05/2014) / JONAS Josef (40)
85 Notre premier bébé (12/05/2014) / JOUSTEN Jan (41*)
86 Mathématiques (12/05/2014) / KAIVERS Karl (42)
87 Français (12/05/2014) / LAMBERTZ Guido (43)
88 Créativité (12/05/2014) / LASCHET Laura (44)
89 Notre premier bébé (12/05/2014) / LAZARUS Line (45)
90 Mathématiques (12/05/2014) / LEFFIN Josefine (46*)
91 Français (12/05/2014) / MALMENDIER Marc (47)
92 Cuisine (12/05/2014) / MEESSEN Melissa (48)
93 Créativité (12/05/2014) / MEIER Marie-Louise (50)
94 Notre premier bébé (12/05/2014) / EMONTS Erich (51*)
95 Mathématiques (12/05/2014) / EMONTSPOOL Erwin (52)
96 Français (12/05/2014) / EMONTS-GAST Erna (53)
97 Cuisine (12/05/2014) / RADERMACHER Alfons (54)
98 Créativité (12/05/2014) / RADERMACHER Berta (55)
99 Notre premier bébé (12/05/2014) / RADERMACHER Christian (56)
100 Mathématiques (12/05/2014) / RADERMACHER Daniela (57)


>>> for o in immersion.ContractType.objects.all():
...    print("{o.id} {o}".format(o=o))
3 MISIP
1 Mise en situation interne
2 Stage d'immersion

>>> for o in immersion.Goal.objects.all():
...    print("{o.id} {o}".format(o=o))
3 Avoir une expérience de travail
2 Confirmer un projet professionel
1 Découvrir un métier
4 Démontrer des compétences

>>> for o in polls.Question.objects.all():
...    print("{o.id} {o}".format(o=o))
1 Pour commencer ma recherche d'emploi, je dois
31 1) Cherchez-vous du travail actuellement?
2 1) Avoir une farde de recherche d’emploi organisée
32 2) Avez-vous un CV à jour?
3 2) Réaliser mon curriculum vitae
33 3) Est-ce que vous vous présentez régulièrement au FOREM?
4 3) Savoir faire une lettre de motivation adaptée au poste de travail visé
34 4) Est-ce que vous consultez les petites annonces?
5 4) Respecter les modalités de candidature
35 5) Demande à l’entourage?
6 5) Me créer une boite e-mail appropriée à la recherche d’emploi
36 6) Candidature spontanée?
7 6) Créer mon compte sur le site de Forem
37 7) Antécédents judiciaires?
8 7) Mettre mon curriculum vitae sur le site du Forem
38 Temps de travail acceptés
9 8) Connaître les aides à l’embauche qui me concernent
10 9) Etre préparé à l’entretien d’embauche ou téléphonique
11 Est-ce que je sais...
12 1) Utiliser le site du Forem pour consulter les offres d’emploi
13 2) Décoder une offre d’emploi
14 3) Adapter mon curriculum vitae par rapport à une offre ou pour une candidature spontanée
15 4) Réaliser une lettre de motivation suite à une offre d’emploi
16 5) Adapter une lettre de motivation par rapport à l’offre d’emploi
17 6) Réaliser une lettre de motivation spontanée
18 7) Utiliser le fax pour envoyer mes candidatures
19 8) Utiliser ma boite e-mail pour envoyer mes candidatures
20 9) Mettre mon curriculum vitae en ligne sur des sites d’entreprise
21 10) Compléter en ligne les formulaires de candidature
22 11) M’inscrire aux agences intérim via Internet
23 12) M’inscrire auprès d’agence de recrutement via Internet
24 13) Utiliser Internet pour faire des recherches sur une entreprise
25 14) Préparer un entretien d’embauche (questions, argumentation du C.V.,…)
26 15) Utiliser Internet pour gérer ma mobilité (transport en commun ou itinéraire voiture)
27 16) Utiliser la photocopieuse (ex : copie de lettre de motivation que j’envoie par courrier)
28 17) Utiliser le téléphone pour poser ma candidature
29 18) Utiliser le téléphone pour relancer ma candidature
30 19) Trouver et imprimer les formulaires de demandes d’aides à l’embauche se trouvant sur le site de l’ONEm

>>> for o in cal.GuestRole.objects.all():
...    print("{o.id} {o}".format(o=o))
1 Collègue
2 Visiteur
3 Président
4 Greffier

>>> for o in cal.EventType.objects.all():
...    print("{o.id} {o}".format(o=o))
1 Absences
2 Jours fériés
3 Réunion
4 Interne
5 Internal meetings with client
6 Évaluation
7 Consultations avec le bénéficiaire
8 Réunions externes avec le bénéficiaire
9 Informational meetings
10 Réunions interne
11 Réunions externe
12 Privé
13 Atelier

..
  >> for o in polls.AnswerChoice.objects.all():
  ..    print("{o.id} {o}".format(o=o))

>>> for o in isip.ContractEnding.objects.all():
...    print("{o.id} {o}".format(o=o))
1 Normal
2 Alcohol
3 Santé
4 Force majeure
