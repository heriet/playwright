import copy
import os

import yaml


class PlaywrightConfig:
    def __init__(self):
        self._config_path = None
        self._base_dir = None
        self._playbooks_dir = None
        self._playwright_options = None
        self._vars = None
        self._vars_files = None
        self._inspirations = None
        self._expand_vars = None

    def load_file(self, file_path):
        self._config_path = file_path
        self._base_dir = os.path.dirname(os.path.abspath(file_path))

        with open(file_path, 'r') as config_file:
            content = yaml.load(config_file)

            # TODO: validate yaml

            self._playwright_options = content['playwright_options'] if 'playwright_options' in content else {}
            self._vars = content['vars'] if 'vars' in content else {}
            self._vars_files = content['vars_files'] if 'vars_files' in content else []
            self._inspirations = content['inspirations'] if 'inspirations' in content else {}

        self._init_playbook_path()
        self._expand_vars = self._load_expand_vars()

    def _init_playbook_path(self):
        playbooks_dir = self.get_option('playbooks_dir')
        self._playbooks_dir = os.path.join(self.base_dir, playbooks_dir)

    def _load_expand_vars(self):
        expand_vars = copy.deepcopy(self._vars)

        for vars_file in self.vars_files:
            vars_file_path = os.path.join(self.playbooks_dir, vars_file)

            with open(vars_file_path, 'r') as f:
                content = yaml.load(f)
                expand_vars.update(content)

        return expand_vars

    @property
    def config_path(self):
        return self._config_path

    @property
    def base_dir(self):
        return self._base_dir

    @property
    def playbooks_dir(self):
        return self._playbooks_dir

    @property
    def playwright_options(self):
        return self._playwright_options

    @property
    def vars(self):
        return self._vars

    @property
    def vars_files(self):
        return self._vars_files

    @property
    def inspirations(self):
        return self._inspirations

    @property
    def expand_vars(self):
        return self._expand_vars

    def get_option(self, key):
        return self._playwright_options[key] if key in self._playwright_options else ''
