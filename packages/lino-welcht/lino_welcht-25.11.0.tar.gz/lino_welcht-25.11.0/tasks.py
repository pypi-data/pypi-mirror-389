from atelier.invlib import setup_from_tasks

ns = setup_from_tasks(
    globals(),
    "lino_welcht",
    languages=['en', 'de', 'fr'],
    doc_trees=['docs'],
    # tolerate_sphinx_warnings=True,
    blogref_url='https://luc.lino-framework.org',
    revision_control_system='git',
    locale_dir='lino_welcht/locale')

# apidoc_exclude_pathnames:
# - lino_welfare/projects
