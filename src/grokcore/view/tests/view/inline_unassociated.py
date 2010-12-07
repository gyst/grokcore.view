"""
Inline templates that are not associated with a view class will
provoke an error:

  >>> from grokcore.view.testing import warn
  >>> import warnings
  >>> saved_warn = warnings.warn
  >>> warnings.warn = warn

  >>> grok.testing.grok(__name__)
  From grok.testing's warn():
  ...UserWarning: Found the following unassociated template(s) when grokking
  'grokcore.view.tests.view.inline_unassociated': club. Define view classes inheriting
  from grok.View to enable the template(s)...

  >>> warnings.warn = saved_warn

"""
import grokcore.view as grok

class Mammoth(grok.Context):
    pass

club = grok.PageTemplate("""\
<html><body><h1>GROK CLUB MAMMOTH!</h1></body></html>
""")
