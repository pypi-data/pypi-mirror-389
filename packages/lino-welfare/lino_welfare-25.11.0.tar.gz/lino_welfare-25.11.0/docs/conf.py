# -*- coding: utf-8 -*-
# fmt: off

import datetime
import lino_welfare

from atelier.sphinxconf import configure
configure(globals())

from lino.sphinxcontrib import configure
configure(globals(), 'lino_welfare.projects.gerd.settings.doctests')

project = "Lino Welfare"

copyright = '2012-{} Rumma & Ko Ltd'.format(datetime.date.today().year)
extensions += ['lino.sphinxcontrib.logo']
# autodoc_default_options = {'members': None}
html_title = "Lino Welfare"
# html_context.update(public_url='https://welfare.lino-framework.org')

from rstgen.sphinxconf import interproject

interproject.configure(
    globals(),
    django=('https://docs.djangoproject.com/en/5.2/',
            'https://docs.djangoproject.com/en/dev/_objects/'),
    sphinx=('https://www.sphinx-doc.org/en/master/', None))

extensions += ['lino.sphinxcontrib.help_texts_extractor']

extlinks.update(srcref=(lino_welfare.srcref_url, None))


help_texts_builder_targets = {
    # 'lino.': 'lino.modlib.lino_startup',
    'lino_welfare.': 'lino_welfare.modlib.welfare',
    'lino_welcht.': 'lino_welcht',
    'lino_weleup.': 'lino_weleup',
}

if html_theme == "insipid":
    html_theme_options = {
        # 'body_max_width': None,
        # 'breadcrumbs': True,
        'globaltoc_includehidden':
        False,
        'left_buttons': [
            'search-button.html',
            'home-button.html',
            'languages-button.html',
        ],
        'right_buttons': [
            'fullscreen-button.html',
            # 'repo-button.html',
            # 'facebook-button.html',
        ],
    }
    html_sidebars = {
        '**': [
            #'languages.html',
            'globaltoc.html',
            'separator.html',
            'searchbox.html',
            'indices.html',
            'links.html'
        ]
    }
