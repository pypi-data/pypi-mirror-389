.. doctest docs/specs/welcht/isip_chatelet.rst
.. _welfare.specs.isip_chatelet:
.. _welcht.specs.isip:

=========================
ISIP contracts (Chatelet)
=========================

>>> from lino import startup
>>> startup('lino_welfare.projects.mathieu.settings.demo')
>>> from lino.api.doctest import *

>>> ses = rt.login('robin')
>>> translation.activate('en')


.. contents::
   :local:

Contracts
=========

>>> rt.show(isip.Contracts)
... #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE -REPORT_UDIFF
==== ============== ============ =========================== ================== =====================
 ID   applies from   date ended   Client                      Responsible (IS)   Contract Type
---- -------------- ------------ --------------------------- ------------------ ---------------------
 1    29/09/2012     07/08/2013   AUSDEMWALD Alfons (17)      Hubert Huppertz    VSE Ausbildung
 2    08/08/2013     01/12/2014   AUSDEMWALD Alfons (17)      Mélanie Mélard     VSE Arbeitssuche
 3    13/10/2012     21/08/2013   DOBBELSTEIN Dorothée (25)   Alicia Allmanns    VSE Lehre
 4    27/10/2012     19/02/2014   EVERS Eberhart (28)         Alicia Allmanns    VSE Vollzeitstudium
 5    20/02/2014     22/03/2014   EVERS Eberhart (28)         Caroline Carnol    VSE Sprachkurs
 6    23/03/2014     29/01/2015   EVERS Eberhart (28)         Caroline Carnol    VSE Ausbildung
 7    17/11/2012     12/03/2014   FAYMONVILLE Luc (31*)       Alicia Allmanns    VSE Arbeitssuche
 8    13/03/2014     12/04/2014   FAYMONVILLE Luc (31*)       Hubert Huppertz    VSE Lehre
 9    13/04/2014     19/02/2015   FAYMONVILLE Luc (31*)       Hubert Huppertz    VSE Vollzeitstudium
 10   01/12/2012     26/03/2014   HILGERS Hildegard (34)      Alicia Allmanns    VSE Sprachkurs
 11   27/03/2014     02/02/2015   HILGERS Hildegard (34)      Alicia Allmanns    VSE Ausbildung
 12   15/12/2012     09/04/2014   JONAS Josef (40)            Mélanie Mélard     VSE Arbeitssuche
 13   10/04/2014     10/05/2014   JONAS Josef (40)            Hubert Huppertz    VSE Lehre
 14   11/05/2014     19/03/2015   JONAS Josef (40)            Hubert Huppertz    VSE Vollzeitstudium
 15   05/01/2013     13/11/2013   LAZARUS Line (45)           Alicia Allmanns    VSE Sprachkurs
 16   14/11/2013     09/03/2015   LAZARUS Line (45)           Mélanie Mélard     VSE Ausbildung
 17   19/01/2013     18/02/2013   MEESSEN Melissa (48)        Mélanie Mélard     VSE Arbeitssuche
 18   19/02/2013     28/12/2013   MEESSEN Melissa (48)        Mélanie Mélard     VSE Lehre
 19   29/12/2013     23/04/2015   MEESSEN Melissa (48)        Mélanie Mélard     VSE Vollzeitstudium
 20   02/02/2013     11/12/2013   RADERMACHER Alfons (54)     Alicia Allmanns    VSE Sprachkurs
 21   23/02/2013     18/06/2014   RADERMACHER Fritz (59*)     Alicia Allmanns    VSE Ausbildung
 22   09/03/2013     15/01/2014   RADERMACHER Hedi (62)       Alicia Allmanns    VSE Arbeitssuche
 23   16/01/2014     11/05/2015   RADERMACHER Hedi (62)       Mélanie Mélard     VSE Lehre
 24   23/03/2013     22/04/2013   VAN VEEN Vincent (67)       Alicia Allmanns    VSE Vollzeitstudium
 25   13/04/2013     19/02/2014   BRECHT Bernd (78)           Alicia Allmanns    VSE Sprachkurs
 26   20/02/2014     15/06/2015   BRECHT Bernd (78)           Hubert Huppertz    VSE Ausbildung
 27   27/04/2013     27/05/2013   DUBOIS Robin (80)           Alicia Allmanns    VSE Arbeitssuche
 28   11/05/2013     19/03/2014   JEANÉMART Jérôme (82)       Alicia Allmanns    VSE Lehre
 29   20/03/2014     13/07/2015   JEANÉMART Jérôme (82)       Hubert Huppertz    VSE Vollzeitstudium
==== ============== ============ =========================== ================== =====================
<BLANKLINE>

This contract has a slave table
:class:`EntriesByContract<lino_welfare.modlib.isip.models.EntriesByContract>`
which contains non-ascii characters:

>>> obj = isip.Contract.objects.get(id=1)
>>> rt.show(isip.EntriesByContract, obj)
=================== ============
 Short description   Date
------------------- ------------
 Évaluation 1        29/10/2012
 Évaluation 2        29/11/2012
 Évaluation 3        31/12/2012
 Évaluation 4        31/01/2013
 Évaluation 5        28/02/2013
 Évaluation 6        28/03/2013
 Évaluation 7        29/04/2013
 Évaluation 8        29/05/2013
 Évaluation 9        01/07/2013
 Évaluation 10       01/08/2013
=================== ============
<BLANKLINE>


.. 20151005 tried to reproduce a unicode error
    >> context = obj.get_printable_context(ar)
    >> context.update(self=obj)
    >> context.update(self=obj)
    >> target = "tmp.odt"
    >> #bm = rt.models.printing.BuildMethods.appyodt
    >> #action = obj.do_print.bound_action.action
    >> #action = rt.models.excerpts.Excerpt.do_print
    >> # tplfile = bm.get_template_file(ar, action, obj)
    >> tplfile = settings.SITE.find_config_file('Default.odt', 'isip/Contract')

    >> from lino.modlib.appypod.appy_renderer import AppyRenderer
    >> r = AppyRenderer(ar, tplfile, context, target, **settings.SITE.appy_params).run()
