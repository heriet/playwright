import os

from future.moves.collections import OrderedDict

from jinja2 import Environment, PackageLoader

import yaml


def _represent_odict(dumper, instance):
    return dumper.represent_mapping(u'tag:yaml.org,2002:map', instance.items())


def _represent_str(dumper, instance):
    # string variable quotes double quotation
    if instance.startswith('{{') and instance.endswith('}}'):
        return dumper.represent_scalar('tag:yaml.org,2002:str', instance, style='"')
    else:
        return dumper.represent_scalar('tag:yaml.org,2002:str', instance)


yaml.add_representer(OrderedDict, _represent_odict)
yaml.add_representer(str, _represent_str)


def _dump_yaml(instance, default_flow_style=False, allow_unicode=True, width=float('inf')):
    return yaml.dump(instance, default_flow_style=default_flow_style, allow_unicode=allow_unicode, width=width)


class InspiredPlaybook():
    def __init__(self, config):
        self.config = config
        self.inspired_list = []

    def append_inspired(self, inspired):
        self.inspired_list.append(inspired)

    def render(self):
        env = Environment(loader=PackageLoader('playwright', 'templates'))
        env.filters['dump_yaml'] = _dump_yaml

        vars_groups = []
        roles_groups = []
        tasks_groups = []

        if self.config.vars:
            vars_group = yaml.dump(self.config.vars, default_flow_style=False, allow_unicode=True)
            vars_groups.append(vars_group)

        for inspired in self.inspired_list:
            vars_group = self._render_nodes(inspired.vars)
            if vars_groups:
                vars_groups.append(vars_group)

            role_group = self._render_nodes(inspired.roles)
            if role_group:
                roles_groups.append(role_group)

            task_group = self._render_nodes(inspired.tasks)
            if task_group:
                tasks_groups.append(task_group)

        template = env.get_template('default.playbook.yml.j2')
        renderd = template.render(
                vars_groups=vars_groups,
                vars_files=self.config.vars_files,
                roles_groups=roles_groups,
                tasks_groups=tasks_groups,
        )

        return renderd

    def _render_nodes(self, nodes):
        renders = [task.render() for task in nodes]
        return os.linesep.join(renders)


class Inspired():
    def __init__(self):
        self.vars = []
        self.roles = []
        self.tasks = []


class InspiredNode():
    def __init__(self):
        self.template = None
        self.content = {}

    def render(self):
        if self.template:
            return self.render_template()
        else:
            return self.render_yaml()

    def render_template(self):
        env = Environment(loader=PackageLoader('playwright', 'templates'))
        env.filters['dump_yaml'] = _dump_yaml

        template = env.get_template(self.template)
        renderd = template.render(content=self.content)
        return renderd

    def render_yaml(self):
        return yaml.dump([self.content], default_flow_style=False, allow_unicode=True)


class InspiredRole(InspiredNode):
    pass


class InspiredTask(InspiredNode):
    pass
