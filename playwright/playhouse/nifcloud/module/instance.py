import re

from future.moves.collections import OrderedDict

from playwright.error import PlaywrightUnsupportedError
from playwright.inspired import InspiredTask

from sleety import computing
from sleety.computing.connection import ComputingConnection
from sleety.region import NifcloudRegion


class NifcloudModuleInstance():

    def __init__(self, playhouse, module_config):
        self._playhouse = playhouse
        self._resources = None
        self._module_config = module_config

    def inspire_tasks(self):
        tasks = []

        self._resources = self._extract_resources()
        region_names = self._resources.keys()

        for region_name in region_names:
            instances = self._resources[region_name]

            if not instances:
                continue

            region = NifcloudRegion(region_name)
            endpoint = ComputingConnection.generate_endpoint(region)

            target_instances = [instance for instance in instances if self._is_target(instance)]

            for instance in target_instances:
                task = self._generate_instance_task(endpoint, instance)
                if task:
                    tasks.append(task)

        return tasks

    def _extract_resources(self):
        resources = {}

        for region in self._playhouse.user.regions:
            region_resource = self._extract_resources_with_region(region)
            resources[region.name] = region_resource

        return resources

    def _extract_resources_with_region(self, region):
        config = self._module_config
        params = config['describe_params'] if 'describe_params' in config else {}

        conn = self._playhouse.create_connection(region)
        describes = computing.instance.describe_instances(conn, params)
        instances = [d['instancesSet'][0] for d in describes]

        return instances

    def _generate_instance_task(self, endpoint, instance):
        user = self._playhouse.user
        access_key = user.get_playbook_vars('access_key')
        secret_access_key = user.get_playbook_vars('secret_access_key')

        tags = [
            instance['instanceId'],
            'nifcloud',
            'nifcloud_{}'.format(instance['instanceId']),
        ]

        task = InspiredTask()
        # task.template = 'nifcloud/default.task.instance.yml.j2'
        task.content = OrderedDict((
            ('name', 'instance {}'.format(instance['instanceId'])),
            ('local_action', OrderedDict((
                ('module', 'nifcloud'),
                ('access_key', access_key),
                ('secret_access_key', secret_access_key),
                ('endpoint', endpoint),
                ('instance_id', instance['instanceId']),
                ('availability_zone', instance['placement']['availabilityZone']),
                ('ip_type', instance['ipType']),
                ('state', 'running'),
            ))),
            ('tags', tags),
        ))

        local_action = task.content['local_action']

        if instance['ipType'] == 'elastic':
            local_action['public_ip'] = instance['IpAddress']

        # TODO startup script
        # TODO network_interface

        return task

    def _is_target(self, target):
        is_include = self._is_include(target)
        is_exclude = self._is_exclude(target)

        return is_include and not is_exclude

    def _is_include(self, target):
        if 'includes' not in self._module_config:
            return True

        includes = self._module_config['includes']

        for include in includes:
            if include['key'] not in target:
                continue

            value = target[include['key']]

            if not isinstance(value, str):
                raise PlaywrightUnsupportedError('include supports only str')

            regexp = re.compile(include['regexp'])
            if re.search(regexp, value):
                return True

        return False

    def _is_exclude(self, target):
        if 'excludes' not in self._module_config:
            return False

        excludes = self._module_config['excludes']

        for exclude in excludes:
            if exclude['key'] not in target:
                continue

            value = target[exclude['key']]

            if not isinstance(value, str):
                raise PlaywrightUnsupportedError('exclude supports only str')

            regexp = re.compile(exclude['regexp'])
            if re.search(regexp, value):
                return True

        return False

    def dict_item_as_list(self, dic, key):
        if key not in dic:
            return []
        elif not dic[key]:
            return []

        return dic[key]
