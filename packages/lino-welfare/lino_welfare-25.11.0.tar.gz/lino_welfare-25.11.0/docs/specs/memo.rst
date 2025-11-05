.. doctest docs/specs/memo.rst
.. _welfare.specs.memo:

==========================
Lino Welfare memo commands
==========================



.. contents::
   :depth: 1
   :local:

.. include:: /../docs/shared/include/tested.rst


>>> from lino import startup
>>> startup('lino_welfare.projects.gerd.settings.demo')
>>> from lino.api.doctest import *



Examples:


.. _memo.note:

note
======

Refer to a note. Usage example:

  See ``[note 1]``.

When Lino parses this, it gets converted into the following HTML:

>>> ses = rt.login('robin')
>>> print(ses.parse_memo("See [note 1]."))
See <a href="…">#1</a>.

Note that the URI of the link depends on the front end and on the user
permissions. For example, the :mod:`lino.modlib.extjs` front end will render it
like this:

>>> ses = rt.login('robin', renderer=settings.SITE.kernel.default_renderer)
>>> print(ses.parse_memo("See [note 1]."))
See <a href="…" style="text-decoration:none">#1</a>.

Referring to a non-existing note:

>>> print(ses.parse_memo("See [note 1234]."))
See [ERROR Note matching query does not exist. in '[note 1234]' at position 4-15].
