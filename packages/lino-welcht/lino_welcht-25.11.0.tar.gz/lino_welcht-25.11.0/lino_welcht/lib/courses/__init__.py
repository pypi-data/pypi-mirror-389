# Copyright 2014-2016 Rumma & Ko Ltd
# License: GNU Affero General Public License v3 (see file COPYING for details)
"""
The Chatelet extension of :mod:`lino_xl.lib.courses`

.. autosummary::
   :toctree:

   fixtures


"""

from lino_xl.lib.courses import Plugin
from django.utils.translation import gettext_lazy as _


class Plugin(Plugin):
    extends_models = ['Course', 'Line', 'Enrolment']
    verbose_name = _("Workshops")
    pupil_model = 'pcsw.Client'
    teacher_model = 'users.User'
    short_name = _("IO")  # "internal orientation"
