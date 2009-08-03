import os
import warnings
import zope.component
import grokcore.component
import grokcore.view
from martian.error import GrokError
from grokcore.view.interfaces import ITemplateFileFactory, TemplateLookupError
from grokcore.view.components import PageTemplate


class InlineTemplateRegistry(object):
    def __init__(self):
        self._reg = {}
        self._unassociated = set()


    def register_inline_template(self, module_info, template_name, template):
        # verify no file template got registered with the same name
        try:
            existing_template = file_template_registry.lookup(
                module_info, template_name)
        except TemplateLookupError:
            pass
        else:
            template_dir = file_template_registry.get_template_dir(module_info)
            raise GrokError("Conflicting templates found for name '%s': "
                            "the inline template in module '%s' conflicts "
                            "with the file template in directory '%s'" %
                            (template_name, module_info.dotted_name,
                             template_dir), None)

        # register the inline template
        self._reg[(module_info.dotted_name, template_name)] = template
        self._unassociated.add((module_info.dotted_name, template_name))

    def associate(self, module_info, template_name):
        # Two views in the same module should be able to use the same inline template
        try:
            self._unassociated.remove((module_info.dotted_name, template_name))
        except KeyError:
            pass

    def lookup(self, module_info, template_name, mark_as_associated=False):
        result = self._reg.get((module_info.dotted_name, template_name))
        if result is None:
            raise TemplateLookupError("inline template '%s' in '%s' cannot be found" % (
                    template_name, module_info.dotted_name))
        if mark_as_associated:
            self.associate(module_info, template_name)
        return result
    
    def unassociated(self):
        return self._unassociated

class FileTemplateRegistry(object):
    def __init__(self):
        self._reg = {}
        self._unassociated = set()
        self._registered_directories = set()

    def register_directory(self, module_info):
        # we cannot register a templates dir for a package
        if module_info.isPackage():
            return

        template_dir = self.get_template_dir(module_info)
        # we can only register for directories
        if not os.path.isdir(template_dir):
            return

        # we don't want associated templates become unassociated again
        if template_dir in self._registered_directories:
            return
    
        for template_file in os.listdir(template_dir):
            template_path = os.path.join(template_dir, template_file)
            self._register_template_file(module_info, template_path)

        self._registered_directories.add(template_dir)
        
    def _register_template_file(self, module_info, template_path):
        template_dir, template_file = os.path.split(template_path)

        if template_file.startswith('.') or template_file.endswith('~'):
            return
        if template_file.endswith('.cache'):
            # chameleon creates '<tpl_name>.cache' files on the fly
            return

        template_name, extension = os.path.splitext(template_file)
        if (template_dir, template_name) in self._reg:
            registered_template_path = self._reg.get((template_dir, template_name)).__grok_location__
            # __grok_location__ is set by _annotateGrokInfo
            if template_path != registered_template_path:
                raise GrokError("Conflicting templates found for name '%s' "
                                "in directory '%s': multiple templates with "
                                "the same name and different extensions." %
                                (template_name, template_dir), None)
        # verify no inline template exists with the same name
        try:
            inline_template_registry.lookup(module_info, template_name)
        except TemplateLookupError:
            pass
        else:
            raise GrokError("Conflicting templates found for name '%s': "
                            "the inline template in module '%s' conflicts "
                            "with the file template in directory '%s'" %
                            (template_name, module_info.dotted_name,
                             template_dir), None)
        
        extension = extension[1:] # Get rid of the leading dot.
        template_factory = zope.component.queryUtility(
            grokcore.view.interfaces.ITemplateFileFactory,
            name=extension)

        if template_factory is None:
            # Warning when importing files. This should be
            # allowed because people may be using editors that generate
            # '.bak' files and such.
            warnings.warn("File '%s' has an unrecognized extension in "
                          "directory '%s'" %
                          (template_file, template_dir), UserWarning, 2)
            return
        template = template_factory(template_file, template_dir)
        template._annotateGrokInfo(template_name, template_path)

        self._reg[(template_dir, template_name)] = template
        self._unassociated.add(template_path)
        
    def associate(self, template_path):
        # Two views in different module should be able to use the same template
        try:
            self._unassociated.remove(template_path)
        except KeyError:
            pass

    def lookup(self, module_info, template_name, mark_as_associated=False):
        template_dir = self.get_template_dir(module_info)
        result = self._reg.get((template_dir, template_name))
        if result is None:
            raise TemplateLookupError("template '%s' in '%s' cannot be found" % (
                    template_name, template_dir))
        if mark_as_associated:
            registered_template_path = self._reg.get((template_dir, template_name)).__grok_location__
            self.associate(registered_template_path)
        return result
    
    def unassociated(self):
        return self._unassociated
        
    def get_template_dir(self, module_info):
        template_dir_name = grokcore.view.templatedir.bind().get(
            module=module_info.getModule())
        if template_dir_name is None:
            template_dir_name = module_info.name + '_templates'

        template_dir = module_info.getResourcePath(template_dir_name)
        return template_dir

inline_template_registry = InlineTemplateRegistry()
file_template_registry = FileTemplateRegistry()

def register_inline_template(module_info, template_name, template):
    return inline_template_registry.register_inline_template(module_info, template_name, template)

def register_directory(module_info):
    return file_template_registry.register_directory(module_info)

def _clear():
    """Remove the registries (for use by tests)."""
    global inline_template_registry
    global file_template_registry
    inline_template_registry = InlineTemplateRegistry()
    file_template_registry = FileTemplateRegistry()

try:
    from zope.testing.cleanup import addCleanUp
except ImportError:
    # don't have that part of Zope
    pass
else:
    addCleanUp(_clear)
    del addCleanUp

def lookup(module_info, template_name, mark_as_associated=False):
    try:
        return file_template_registry.lookup(module_info, template_name, mark_as_associated)
    except TemplateLookupError, e:
        try:
            return inline_template_registry.lookup(module_info, template_name, mark_as_associated)
        except TemplateLookupError, e2:
            # re-raise first error again
            raise e

def check_unassociated():
    unassociated = inline_template_registry.unassociated()
    if unassociated:
        for dotted_name, template_name in unassociated:
            msg = (
                "Found the following unassociated template(s) when "
                "grokking %r: %s.  Define view classes inheriting "
                "from grok.View to enable the template(s)." % (
                dotted_name, template_name))
            warnings.warn(msg, UserWarning, 1)
    unassociated = file_template_registry.unassociated()
    if unassociated:
        msg = (
            "Found the following unassociated template(s) when "
            "grokking views: %s.  Define view classes inheriting "
            "from grok.View to enable the template(s)." % (
            ', '.join(unassociated)))
        warnings.warn(msg, UserWarning, 1)

def checkTemplates(module_info, factory, component_name,
                   has_render, has_no_render):
    factory_name = factory.__name__.lower()
    template_name = grokcore.view.template.bind().get(factory)
    if template_name is None:
        template_name = factory_name

    if factory_name != template_name:
        # grok.template is being used

        try:
            lookup(module_info, factory_name)
            raise GrokError("Multiple possible templates for %s %r. It "
                            "uses grok.template('%s'), but there is also "
                            "a template called '%s'."
                            % (component_name, factory, template_name,
                               factory_name), factory)
        except TemplateLookupError, e:
            pass
    try:
        template = lookup(module_info, template_name, mark_as_associated=True)
        if has_render(factory):
            # we do not accept render and template both for a view
            # (unless it's a form, they happen to have render.
            raise GrokError(
                "Multiple possible ways to render %s %r. "
                "It has both a 'render' method as well as "
                "an associated template." %
                (component_name, factory), factory)
        factory.template = template
        template._initFactory(factory)
    except TemplateLookupError, e:
        if has_no_render(factory):
            # we do not accept a view without any way to render it
            raise GrokError("%s %r has no associated template or "
                            "'render' method." %
                            (component_name.title(), factory), factory)


class PageTemplateFileFactory(grokcore.component.GlobalUtility):
    grokcore.component.implements(ITemplateFileFactory)
    grokcore.component.name('pt')

    def __call__(self, filename, _prefix=None):
        return PageTemplate(filename=filename, _prefix=_prefix)


