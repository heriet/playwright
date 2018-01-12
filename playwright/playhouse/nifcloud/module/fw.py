import re

from future.moves.collections import OrderedDict

from playwright.error import PlaywrightUnsupportedError
from playwright.inspired import InspiredTask

from sleety import computing
from sleety.computing.connection import ComputingConnection
from sleety.region import NifcloudRegion


class NifcloudModuleFw():

    def __init__(self, playhouse, module_config):
        self._playhouse = playhouse
        self._resources = None
        self._module_config = module_config

    def inspire_tasks(self):
        tasks = []

        self._resources = self._extract_resources()
        region_names = self._resources.keys()

        for region_name in region_names:
            fw_groups = self._resources[region_name]

            if not fw_groups:
                continue

            region = NifcloudRegion(region_name)
            endpoint = ComputingConnection.generate_endpoint(region)

            target_fw_groups = [fw_group for fw_group in fw_groups if self._is_target(fw_group)]

            for fw_group in target_fw_groups:
                task = self._generate_group_task(endpoint, fw_group)
                if task:
                    tasks.append(task)

            for fw_group in target_fw_groups:
                task = self._generate_ip_permissions_task(endpoint, fw_group)
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
        desc_fw = computing.fw.describe_fw_groups(conn, params)

        return desc_fw

    def _generate_group_task(self, endpoint, fw_group):
        user = self._playhouse.user
        access_key = user.get_playbook_vars('access_key')
        secret_access_key = user.get_playbook_vars('secret_access_key')

        tags = [
            fw_group['groupName'],
            'nifcloud_fw',
            'nifcloud_fw_group',
            'nifcloud_fw_group_{}'.format(fw_group['groupName']),
        ]

        task = InspiredTask()
        task.template = 'nifcloud/default.task.fw_group.yml.j2'
        task.content = OrderedDict((
            ('name', 'create fw {}'.format(fw_group['groupName'])),
            ('local_action', OrderedDict((
                ('module', 'nifcloud_fw'),
                ('access_key', access_key),
                ('secret_access_key', secret_access_key),
                ('endpoint', endpoint),
                ('group_name', fw_group['groupName']),
                ('availability_zone', fw_group['availabilityZone']),
                ('log_limit', fw_group['groupLogLimit']),
                ('state', 'present'),
                ('purge_ip_permissions', False),
            ))),
            ('tags', tags),
        ))

        return task

    def _generate_ip_permissions_task(self, endpoint, fw_group):
        task_ip_permissions = []
        ip_permissions = self.dict_item_as_list(fw_group, 'ipPermissions')

        if not ip_permissions:
            return None

        for ip_permission in ip_permissions:

            ip_ranges = self.dict_item_as_list(ip_permission, 'ipRanges')

            for ip_range in ip_ranges:
                task_ip_permission = OrderedDict((
                    ('ip_protocol', ip_permission['ipProtocol']),
                    ('in_out', ip_permission['inOut']),
                    ('cidr_ip', ip_range['cidrIp']),
                ))

                if 'fromPort' in ip_permission and ip_permission['fromPort']:
                    task_ip_permission['from_port'] = ip_permission['fromPort']

                if 'toPort' in ip_permission and ip_permission['toPort']:
                    task_ip_permission['to_port'] = ip_permission['toPort']

                if 'description' in ip_permission and ip_permission['description']:
                    task_ip_permission['description'] = ip_permission['description']

                task_ip_permissions.append(task_ip_permission)

            groups = self.dict_item_as_list(ip_permission, 'groups')

            for group in groups:
                task_ip_permission = OrderedDict((
                    ('ip_protocol', ip_permission['ipProtocol']),
                    ('in_out', ip_permission['inOut']),
                    ('group_name', group['groupName']),
                ))

                if 'fromPort' in ip_permission and ip_permission['fromPort']:
                    task_ip_permission['from_port'] = ip_permission['fromPort']

                if 'toPort' in ip_permission and ip_permission['toPort']:
                    task_ip_permission['to_port'] = ip_permission['toPort']

                if 'description' in ip_permission and ip_permission['description']:
                    task_ip_permission['description'] = ip_permission['description']

                task_ip_permissions.append(task_ip_permission)

        user = self._playhouse.user
        access_key = user.get_playbook_vars('access_key')
        secret_access_key = user.get_playbook_vars('secret_access_key')

        tags = [
            fw_group['groupName'],
            'nifcloud_fw',
            'nifcloud_fw_ip_permissions',
            'nifcloud_fw_ip_permissions_{}'.format(fw_group['groupName']),
        ]

        task = InspiredTask()
        task.template = 'nifcloud/default.task.fw_ip_permissions.yml.j2'
        task.content = OrderedDict((
            ('name', 'configure {} ip_permissions'.format(fw_group['groupName'])),
            ('local_action', OrderedDict((
                ('module', 'nifcloud_fw'),
                ('access_key', access_key),
                ('secret_access_key', secret_access_key),
                ('endpoint', endpoint),
                ('group_name', fw_group['groupName']),
                ('purge_ip_permissions', True),
                ('ip_permissions', task_ip_permissions),
            ))),
            ('tags', tags),
        ))

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
