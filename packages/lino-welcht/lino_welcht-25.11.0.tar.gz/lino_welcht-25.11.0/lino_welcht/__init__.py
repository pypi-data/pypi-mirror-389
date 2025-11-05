# -*- coding: UTF-8 -*-
# Copyright 2002-2019 Rumma & Ko Ltd
# License: GNU Affero General Public License v3 (see file COPYING for details)
"""
The main package for :ref:`welcht`.

.. autosummary::
   :toctree:

   lib


.. autosummary::
   :toctree:

   settings


.. convert to prosa:
   layouts
   workflows
   migrate



"""

__version__ = '25.11.0'

# doc_trees = ['docs']
# intersphinx_urls = dict(
#     docs="https://welcht.lino-framework.org",
#     )
# intersphinx_urls = dict()
# intersphinx_urls.update(dedocs="https://de.welfare.lino-framework.org")
# intersphinx_urls.update(frdocs="https://fr.welfare.lino-framework.org")
srcref_url = 'https://github.com/lino-framework/welcht/blob/master/%s'

doc_trees = []
# welcht has no doctrees, but we want a documentation link for getlino list
intersphinx_urls = dict(docs="https://welfare.lino-framework.org")
