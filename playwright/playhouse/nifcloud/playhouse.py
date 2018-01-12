from future.moves.collections import OrderedDict

from playwright.error import PlaywrightError, PlaywrightUnsupportedError
from playwright.inspired import Inspired, InspiredRole
from playwright.playhouse.nifcloud.model import NifcloudUser
from playwright.playhouse.nifcloud.module import NifcloudModuleFw, NifcloudModuleInstance

from sleety import computing
from sleety.computing.connection import ComputingConnection
from sleety.region import NifcloudRegion


class NifcloudPlayhouse():

    def __init__(self):
        self.user = None
        self.config = None
        self.inspiration = None

        self.inspired = None

    def init(self, config, inspiration):
        self.config = config
        self.inspiration = inspiration

        self._init_user()

    def inspire(self):
        self.inspired = Inspired()

        self.inspired.roles.append(self._genelate_role_nifcloud())

        for target_module in self.inspiration['modules']:
            module_tasks = self._generate_module_tasks(target_module)
            self.inspired.tasks.extend(module_tasks)

        return self.inspired

    def _init_user(self):
        self.user = NifcloudUser()

        config_vars = self.config.expand_vars
        user_id = self.inspiration['user']

        if 'access_key' in self.inspiration and 'secret_access_key' in self.inspiration:
            self.user.access_key = self.inspiration['access_key']
            self.user.secret_access_key = self.inspiration['secret_access_key']
        elif user_id:
            if 'nifcloud_users' not in config_vars:
                raise PlaywrightError('nifcloud_users not found')

            users = config_vars['nifcloud_users']

            if user_id not in users:
                raise PlaywrightError('user not found: {}'.format(user_id))

            self.user.user_id = user_id
            self.user.access_key = users[user_id]['access_key']
            self.user.secret_access_key = users[user_id]['secret_access_key']
            self.user.referenced = True
        else:
            raise PlaywrightError('access_key and secret_access_key not found')

        self._init_user_regions()

    def _init_user_regions(self):

        self.user.regions = []

        if 'regions' in self.inspiration and self.inspiration['regions'] != 'all':
            for item in self.inspiration['regions']:
                region_name = NifcloudRegion.correct_region_name(item['name'])
                region = NifcloudRegion(region_name)
                self.user.regions.append(region)
        else:
            default_region = self.inspiration['regions'] if 'default_region' in self.inspiration else 'jp-east-1'

            region = NifcloudRegion(default_region)
            conn = self._create_connection(self.user.access_key, self.user.secret_access_key, region)
            desc_regions = computing.region.describe_regions(conn)

            for desc_region in desc_regions:
                region_name = NifcloudRegion.correct_region_name(desc_region['regionName'])
                region = NifcloudRegion(region_name)
                self.user.regions.append(region)

    def _genelate_role_nifcloud(self):
        role_nifcloud = self.inspiration['role_nifcloud'] if 'role_nifcloud' in self.inspiration else 'nifcloud'

        role = InspiredRole()
        role.content = OrderedDict((
            ('role', role_nifcloud),
            ('tags', ['role_nifcloud']),
            ('when', 'nifcloud_role_exec is defined and nifcloud_role_exec')
        ))
        return role

    def _generate_module_tasks(self, target_module):
        module_id = target_module['module']
        moduleCls = None

        # TODO mapping module
        if module_id == 'nifcloud_fw':
            moduleCls = NifcloudModuleFw
        elif module_id == 'nifcloud':
            moduleCls = NifcloudModuleInstance
        else:
            raise PlaywrightUnsupportedError('unsupported module: {}'.format(module_id))

        module = moduleCls(self, target_module)
        return module.inspire_tasks()

    def create_connection(self, region, timeout=60, request_interval=1, endpoint=None):
        access_key = self.user.access_key
        secret_access_key = self.user.secret_access_key

        return ComputingConnection(
                access_key, secret_access_key, region,
                timeout=timeout, request_interval=request_interval, endpoint=endpoint)
