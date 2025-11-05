import datetime
from lino_welfare.projects.mathieu.settings import *


class Site(Site):
    # title = "Welfare Chatelet Demo"
    is_demo_site = True
    the_demo_date = datetime.date(2014, 5, 22)
    # ignore_dates_after = datetime.date(2019, 05, 22)
    use_java = False
    # use_silk_icons = True  # temporarily
    webdav_protocol = 'webdav'
    # beid_protocol = 'beid'
    languages = "fr nl de en"
    hidden_languages = 'nl'
    # default_ui = "lino_react.react"


SITE = Site(globals())

DEBUG = True
