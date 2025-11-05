# Copyright 2014-2019 Rumma & Ko Ltd
# License: GNU Affero General Public License v3 (see file COPYING for details)
"""
Lino-Welfare extension of :mod:`lino_welfare.modlib.pcsw`
"""

from lino_welfare.modlib.pcsw import Plugin


class Plugin(Plugin):

    def setup_config_menu(config, site, user_type, m, ar=None):
        super().setup_config_menu(site, user_type, m, ar)
        m = m.add_menu(config.app_label, config.verbose_name)
        m.add_action('pcsw.UnemploymentRights')
