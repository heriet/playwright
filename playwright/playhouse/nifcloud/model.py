class NifcloudUser():
    def __init__(self, user_id=None, access_key=None, secret_access_key=None, regions=None):
        self.user_id = user_id
        self.access_key = access_key
        self.secret_access_key = secret_access_key
        self.regions = regions if regions else []
        self.referenced = False

    def get_playbook_vars(self, key):
        if self.referenced and self.user_id:
            var_content = "nifcloud_users['{}']['{}']".format(self.user_id, key)
            return '{{ ' + var_content + ' }}'
        else:
            return getattr(self, key)
