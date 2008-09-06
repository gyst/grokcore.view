"""
  >>> grok.testing.grok(__name__)

View with an associated PageTemplate that is referred to using
``grok.template``:

  >>> manfred = Mammoth()
  >>> from zope.publisher.browser import TestRequest
  >>> request = TestRequest()
  >>> from zope import component
  >>> view = component.getMultiAdapter((manfred, request), name='food')
  >>> print view()
  <html>
  <body>
  ME GROK EAT MAMMOTH!
  </body>
  </html>

"""
import grokcore.view as grok
import os.path

grok.templatedir('templatedirectoryname')

class Mammoth(grok.Context):
    pass

class Food(grok.View):
    grok.template('food')
