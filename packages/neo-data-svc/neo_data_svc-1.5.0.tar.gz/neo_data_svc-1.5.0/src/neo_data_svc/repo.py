import importlib
import logging
import sys

from pyspark.sql import SparkSession

from .common import *

_logger = logging.getLogger(__name__)


class M:
    _instance = None
    _config = None

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._init_instance()

        return (cls._instance, cls._instance.sql, cls._config)

    @classmethod
    def _discover_config(cls):
        if cls._config is not None:
            return cls._config

        stack = []
        frame = sys._getframe()
        for _ in range(6):
            if frame is None:
                return stack
            frame = frame.f_back

        while frame:
            mod = frame.f_globals.get('__name__', '')
            if mod and not mod.startswith('neo_data_svc'):
                stack.append(mod)
            frame = frame.f_back

        _logger.info(f"Import stack: {stack}")

        config_paths = cls._generate_config_paths(stack)
        config = {}

        for path in config_paths:
            try:
                module = importlib.import_module(path)
                cls._config = cls._parse_config(module, config)
                _logger.info(f"config from: {path}")
                return cls._config
            except ImportError as e:
                _logger.debug(f"Failed to import {path}: {e}")
                continue

        cls._config = config
        return cls._config

    @classmethod
    def _generate_config_paths(cls, stack):
        paths = []

        for module_name in stack:
            if '.' in module_name:
                root_package = module_name.split('.')[0]
                paths.extend([f"{root_package}.config.Cfg"])

        unique_paths = list(dict.fromkeys(paths))
        return unique_paths

    @classmethod
    def _parse_config(cls, module, base_config):
        config = base_config.copy()

        for attr_name in dir(module):
            value = getattr(module, attr_name)
            config[attr_name] = value
        return config

    @classmethod
    def _init_instance(cls):
        cls._discover_config()
        cls._instance = NDS_get_instance(SparkSession)

    @classmethod
    def get_config(cls):
        if cls._config is None:
            cls._discover_config()
        return cls._config

    @classmethod
    def stop_session(cls):
        if cls._instance:
            cls._instance.stop()
            cls._instance = None
            cls._config = None
