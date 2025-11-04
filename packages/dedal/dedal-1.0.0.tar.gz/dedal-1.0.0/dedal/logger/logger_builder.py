# Dedal library - Wrapper over Spack for building multiple target
# environments: ESD, Virtual Boxes, HPC compatible kernels, etc.

#  (c) Copyright 2025 Dedal developers

#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at

#      http://www.apache.org/licenses/LICENSE-2.0

#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import os
import inspect
import weakref
import logging
import logging.config


class LoggerBuilder(object):
    """
    Class taking care of uniform Python logger initialization.
    It uses the Python native logging package.
    It's purpose is just to offer a common mechanism for initializing all modules in a package.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_file_name='logging.conf'):
        """
        Prepare Python logger based on a configuration file.
        :param: config_file_name - name of the logging configuration relative to the current package
        """
        current_folder = os.path.dirname(inspect.getfile(self.__class__))
        config_file_path = os.path.join(current_folder, config_file_name)
        logging.config.fileConfig(config_file_path, disable_existing_loggers=False)
        self._loggers = weakref.WeakValueDictionary()

    def build_logger(self, parent_module, parent_class):
        """
        Build a logger instance and return it
        """
        logger_key = f'{parent_module}.{parent_class}' if parent_class else parent_module
        self._loggers[logger_key] = logger = logging.getLogger(logger_key)
        return logger

    def set_loggers_level(self, level):
        for logger in self._loggers.values():
            logger.setLevel(level)


def get_logger(parent_module='', parent_class=None):
    """
    Function to retrieve a new Python logger instance for current module.

    :param parent_module: module name for which to create logger.
    :param parent_class: class name for which to create logger.
    """
    return LoggerBuilder().build_logger(parent_module, parent_class)
