from inspect import isclass
from pkgutil import iter_modules
from pathlib import Path
from importlib import import_module
import logging

from plugins.base_plugin import BasePlugin

LOG = logging.getLogger(__name__)


class PluginLoader:
    def __init__(self):
        self.plugins = []
        attribute_cache = {}

        # iterate through the modules in the current package
        package_dir = Path(__file__).resolve().parent
        LOG.info(f"Searching for plugins in {package_dir} ")

        for (_, module_name, _) in iter_modules([str(package_dir)]):
            # import the module and iterate through its attributes
            module = import_module(f"plugins.{module_name}")

            for attribute_name in dir(module):
                attribute = getattr(module, attribute_name)

                if isclass(attribute) and self.is_subclassn(attribute, BasePlugin):
                    attribute_cache[attribute_name] = module

        LOG.info("Dynamically importing plugins:")
        for class_name in attribute_cache.keys():
            attribute = getattr(attribute_cache[class_name], class_name)
            LOG.info(f"Loading plugin: {attribute}")
            plugin = attribute()
            self.plugins.append(plugin)
            globals()[class_name] = attribute
        LOG.info("Dynamic import completed!")

    def is_subclassn(self, c1, c2):
        return c1 != c2 and issubclass(c1, c2)
