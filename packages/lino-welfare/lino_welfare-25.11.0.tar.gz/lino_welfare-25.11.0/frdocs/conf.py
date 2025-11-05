# -*- coding: utf-8 -*-
from pathlib import Path

docs = Path('../docs').resolve()
fn = docs / 'conf.py'
with open(fn, "rb") as fd:
    exec(compile(fd.read(), fn, 'exec'))

language = "fr"
html_title = "Lino pour CPAS"
