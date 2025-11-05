# -*- coding: UTF-8 -*-
# Copyright 2013-2021 Rumma & Ko Ltd
# License: GNU Affero General Public License v3 (see file COPYING for details)

from lino_xl.lib.cal.fixtures.demo2 import objects as lino_objects
from lino.api import rt
from lino.utils import Cycler


def walk(obj):
    if obj is None:
        pass  # ignore None values
    elif hasattr(obj, '__iter__'):
        for o in obj:
            for so in walk(o):
                yield so
    else:
        yield obj


def objects():
    ses = rt.login()
    Client = rt.models.pcsw.Client
    CLIENTS = Cycler(Client.objects.all())
    for obj in walk(lino_objects()):
        if obj.__class__.__name__ == 'Event':
            if obj.event_type.invite_client:
                obj.project = CLIENTS.pop()
        yield obj
        obj.update_guests.run_from_code(ses)
