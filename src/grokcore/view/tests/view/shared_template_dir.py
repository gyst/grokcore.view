"""
When modules share a template directory, templates that have not been associated with any view class of a given module issue a UserWarning:

  >>> import grokcore.view as grok
  >>> from grokcore.view.testing import warn
  >>> import warnings
  >>> saved_warn = warnings.warn
  >>> warnings.warn = warn

  >>> import shared_template_fixture 

  >>> grok.testing.grok(shared_template_fixture.__name__)
  From grok.testing's warn():
  ...UserWarning: Found the following unassociated template(s) when grokking
  'grokcore.view.tests.view.shared_template_fixture.first_module': unassociated_instance.  Define view classes inheriting from
  grok.View to enable the template(s)...
  ...UserWarning: Found the following unassociated template(s) when grokking directory
  '...shared_template_fixture...templates': unassociated.  Define view classes inheriting from
  grok.View to enable the template(s)...

"""
