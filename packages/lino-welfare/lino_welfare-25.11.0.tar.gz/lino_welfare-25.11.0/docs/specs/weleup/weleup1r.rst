.. doctest docs/specs/weleup/weleup1r.rst
.. _welfare.specs.weleup1r:

================================
The weleup1r project
================================


.. contents::
   :local:
   :depth: 2


.. include:: /../docs/shared/include/tested.rst


>>> from lino import startup
>>> startup('lino_welfare.projects.weleup1r.settings')
>>> from lino.api.doctest import *

Overview
========

>>> test_client.force_login(rt.login("robin").get_user())
>>> test_client.get("/api/pcsw/Clients/132?dm=detail&fmt=json&ul=en&wt=d")  #doctest: +ELLIPSIS
<HttpResponse status_code=200, "application/json">
