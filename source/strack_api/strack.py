# coding=utf8

import requests
from .commands import *
from six.moves.urllib.parse import urlparse, urljoin, urlunparse
from .utils import get_logger

log = get_logger("strack_api")


class Strack(object):
    """
    the main object
    """

    SPECIFIC_COMMAND_FACTORY = {
        'upload': UploadCommand,
        'create_media': CreateMediaCommand,
        'update_media': UpdateMediaCommand,
        'get_media_data': GetMediaDataCommand,
        'get_best_media_server': GetBestMediaServerCommand,
        'get_media_server': GetMediaServerCommand,
        'get_media_servers': GetMediaServerStatusCommand,
        'get_thumbnail_path': GetThumbnailCommand,
        'select_media_data': SelectMediaDataCommand,
        'start_timer': StartTimerCommand,
        'stop_timer': StopTimerCommand,
        'get_department_data': GetDepartmentDataCommand,
        'get_event_server': GetEventServerCommand,

        # TODO: 还没有完成(或修改)的方法
        'get_web_socket_server': GetWebSocketServerCommand,
        'get_email_server': GetEmailServerCommand,
        'get_options': GetOptionsCommand,
        'add_options': AddOptionsCommand,
        'add_sub_task': AddSubTaskCommand,
        'add_task_plan': AddTaskPlanCommand,
    }
    COMMON_COMMAND_FACTORY = {
        'find': FindCommand,
        'select': SelectCommand,
        'create': CreateCommand,
        'update': UpdateCommand,
        'delete': DeleteCommand,
        'fields': FieldsCommand,
        'adv_select': AdvQueryCommand
    }


    # TODO: 还没有完成(或修改)的方法
    EVENT_COMMAND_FACTORY = {
        'select': SelectLogsCommand,
        # 'create': CreateEventCommand,
        # 'find': FindEventCommand,
        # 'select': SelectEventCommand,
        # 'fields': EventFieldsCommand,
        # 'send_email': SendEmailCommand,
    }
    #
    # MEDIA_COMMAND_FACTORY = {
    #     'upload': UploadCommand,
    #     'create_media': CreateMediaCommand,
    #     'update_media': UpdateMediaCommand,
    #     'find_media_data': GetMediaDataCommand,
    #     'select_media_data': SelectMediaDataCommand,
    #     'get_best_media_server': GetBestMediaServerCommand,
    #     'get_media_server': GetMediaServerCommand,
    #     'get_media_servers': GetMediaServerStatusCommand,
    #     'get_thumbnail_path': GetThumbnailPathCommand,
    # }
    #
    # BASE_COMMAND_FACTORY = {
    #     'add_sub_task': AddSubTaskCommand,
    #     'add_task_plan': AddTaskPlanCommand,
    # }
    #
    # TIMELOG_COMMAND_FACTORY = {
    #     'start_timer': StartTimerCommand,
    #     'stop_timer': StopTimerCommand,
    # }
    #
    # OPTION_COMMAND_FACTORY = {
    #     'get_relation_module': GetRelationModuleCommand,
    #     'get_event_server': GetEventServerCommand,
    #     'get_web_socket_server': GetWebSocketServerCommand,
    #     'get_email_server': GetEmailServerCommand,
    #     'get_options': GetOptionsCommand,
    #     'add_options': AddOptionsCommand,
    # }
    #
    # ADMIN_COMMAND_FACTORY = {
    #     'create_schema': CreateSchemaCommand,
    #     'update_schema': UpdateSchemaCommand,
    #     'delete_schema': DeleteSchemaCommand,
    #     'get_schema': GetSchemaCommand,
    #     'get_all_schemas': GetAllSchemasCommand,
    #     'create_entity_module': CreateEntityModuleCommand,
    #     'get_all_table_names': GetAllTableNamesCommand,
    #     'get_table_config': GetTableConfigCommand,
    #     'update_table_config': UpdateTableConfigCommand
    # }

    def __init__(self, base_url, login_name, password, method="", server_id=0):
        """
            base_url: 服务器网址
            login_name: 登陆名
            password: 密码
        """
        if not base_url.endswith("/"):
            base_url += "/"
        self.session = requests.session()
        self.__base_url = base_url
        self.__login_name = login_name
        self.__method = method
        self.__server_id = server_id
        self._scheme, self._server, self._api_base, _, _, _ = urlparse(urljoin(base_url, 'api/'))

        self.__entity_list = []
        self.__general_doc_dict = None
        self.__logger = None
        self.__user_id = None
        self.__token = self.get_token(password)
        self.__modules = self._list_modules()

        self.__public_commands = {}  #

    @property
    def base_url(self):
        return self.__base_url

    @property
    def login_name(self):
        return self.__login_name

    @property
    def token(self):
        return self.__token

    @property
    def user_id(self):
        return self.__user_id

    @property
    def name(self):
        return "Strack"

    def cmd_to_url(self, cmd_url):
        api_path = urljoin(self._api_base, cmd_url)
        url = urlunparse((self._scheme, self._server, api_path, None, None, None))
        return url

    def set_token(self, token):
        self.__token = token

    def get_token(self, password):
        """request sign code"""
        cmd = 'login/in'
        url = self.cmd_to_url(cmd)
        auth = {
            'login_name': self.login_name,
            'password': password,
            'from': 'api',
            'method': self.__method,
            'server_id': self.__server_id

        }
        response = self.session.post(url, data=auth)
        if response.status_code == 200 and response.json().get("status") == 200:
            sign_info = response.json().get("data", {})
            self.__user_id = sign_info.get("user_id")
            return sign_info.get("token", "")
        elif response.status_code == 200:
            log_msg = "%s: %s" % (response.json().get("status"), response.json().get("message"))
            log.error(log_msg)
            raise RuntimeError(log_msg)
        else:
            log_msg = "%s: %s" % (response.status_code, response.json().get("message"))
            log.error(log_msg)
            raise RuntimeError(log_msg)

    def refresh_token(self):
        cmd = 'login/refresh'
        url = self.cmd_to_url(cmd)
        auth = {
            'token': self.token
        }
        response = self.session.post(url, data=auth)
        if response.status_code == 200 and response.json().get("status") == 200:
            sign_info = response.json().get("data", {})
            if sign_info.get("token", "") != "":
                self.set_token(sign_info.get("token", ""))
        elif response.status_code == 200:
            log_msg = "%s: %s" % (response.json().get("status"), response.json().get("message"))
            log.error(log_msg)
            raise RuntimeError(log_msg)
        else:
            log_msg = "%s: %s" % (response.status_code, response.json().get("message"))
            log.error(log_msg)
            raise RuntimeError(log_msg)

    def logout(self):
        cmd = 'login/cancel'
        url = self.cmd_to_url(cmd)
        response = self.session.post(url)
        if response.status_code == 200 and response.json().get("status") == 200:
            log_msg = response.json().get('message')
            log.info(log_msg)
            return
        elif response.status_code == 200:
            log_msg = "%s: %s" % (response.json().get("status"), response.json().get("message"))
            log.error(log_msg)
            raise RuntimeError(log_msg)
        else:
            log_msg = "%s: %s" % (response.status_code, response.json().get("message"))
            log.error(log_msg)
            raise RuntimeError(log_msg)

    def _list_modules(self):
        cmd = 'module/getModuleData'
        url = self.cmd_to_url(cmd)
        response = self.session.post(url, headers={"token": self.token})
        if response.status_code == 200 and response.json().get("status") == 200:
            data = response.json().get("data", {})
            return data.get('rows')
        elif response.status_code == 200:
            log_msg = "%s: %s" % (response.json().get("status"), response.json().get("message"))
            log.error(log_msg)
            raise RuntimeError(log_msg)
        else:
            log_msg = "%s: %s" % (response.status_code, response.json().get("message"))
            log.error(log_msg)
            raise RuntimeError(log_msg)

    @property
    def modules(self):
        """
        返回所有可以操作的模块
        Returns:

        """
        return self.__modules

    def set_up_command(self, module_code, command_name):
        if module_code in ['event', 'email']:
            module = {'code': 'event'}
            command_factory = self.EVENT_COMMAND_FACTORY
        else:
            if module_code in ['options']:
                module = {'code': 'options'}
            else:
                # check module in all modules
                for module in self.modules:
                    if module.get('code') == module_code:
                        break
                else:  # when no break triggered, go to else
                    log.error('Not module named %s.' % module_code)
                    raise RuntimeError('Not module named %s.' % module_code)

            command_factory = self.SPECIFIC_COMMAND_FACTORY \
                if command_name in self.SPECIFIC_COMMAND_FACTORY \
                else self.COMMON_COMMAND_FACTORY

        CommandClass = command_factory.get(command_name)
        return CommandClass(self, module)

    def get_relation_module(self, module_code):
        command = self.set_up_command('module', 'get_relation_module')
        return command(module_code)

    def fields(self, module_code, project_id=0):
        """

        Args:
            module_code: [string] Name of module
            project_id: [int] id_ of project

        Returns: [dict] Dicts about field name and field data type in module

        """
        command = self.set_up_command(module_code, 'fields')
        return command(project_id)

    def find(self, module_code, filters=None, fields=None, project_id=0):
        """

        Args:
            module_code: [string] Name of module
            filters: [list] List of filter conditions
            fields: [list] List of fields to return
            page:
            order:

        Returns: [dict] Dict about found item in module

        """
        command = self.set_up_command(module_code, 'find')
        return command(filters, fields, project_id)

    def select(self, module_code, filters=None, fields=None, order=None, page=None, project_id=0):
        """

        Args:
            module_code: [string] Name of module
            filters: [list] List of filter conditions
            fields: [list] List of fields to return
            order: [dict] Dict about order field
            page: [dict] Dict about pageNum and pageSize

        Returns: [list] List of dicts about found item in module

        """
        # init command object
        command = self.set_up_command(module_code, 'select')
        # execute
        return command(filters, fields, order, page, project_id)

    def adv_select(self, module_code, filters=None, fields=None, order=None, page=None, project_id=0):
        """

        Args:
            module_code: [string] Name of module
            filters: [list] List of filter conditions
            fields: [list] List of fields to return
            order: [dict] Dict about order field
            page: [dict] Dict about pageNum and pageSize

        Returns: [list] List of dicts about found item in module

        """
        # init command object
        command = self.set_up_command(module_code, 'adv_select')
        # execute
        return command(filters, fields, order, page, project_id)

    def create(self, module_code, data):
        """

        Args:
            module_code:
            data:

        Returns:

        """
        log.debug("Strack API create a object info in %s." % module_code)
        command = self.set_up_command(module_code, 'create')
        return command(data)

    def update(self, module_code, filters, data):
        log.debug("Strack API update a object info in %s." % module_code)
        command = self.set_up_command(module_code, 'update')
        return command(filters, data)

    def delete(self, module_code, filters):
        log.debug("Strack API delete a object info in %s." % module_code)
        command = self.set_up_command(module_code, 'delete')
        return command(filters)

    def upload(self, file_path, media_server, belong_system='task', size='origin'):
        command = self.set_up_command('media', 'upload')
        return command(file_path, media_server, belong_system, size)

    def create_media(self, module_code, link_id, media_data, usage_type, media_server):
        """

        :param module_code: 关联表code
        :param link_id: 关联id
        :param media_data: 已上传的媒体
        :param usage_type: thumb: 缩略图, attachment: 附件
        :param media_server: 媒体服务器
        :return:
        """
        command = self.set_up_command('media', 'create_media')
        return command(module_code, link_id, media_data, usage_type, media_server)

    def update_media(self, module_code, link_id, media_data, usage_type, media_server):
        """

        :param module_code: 关联表code
        :param link_id: 关联id
        :param media_data: 已上传的媒体
        :param usage_type: thumb: 缩略图, attachment: 附件
        :param media_server: 媒体服务器
        :return:
        """
        command = self.set_up_command('media', 'update_media')
        return command(module_code, link_id, media_data, usage_type, media_server)

    def get_media_data(self, filters):
        command = self.set_up_command('media', 'get_media_data')
        return command(filters)

    def get_best_media_server(self):
        """
        Description: 获取连接速度最快的媒体服务器

        Returns:

        """
        command = self.set_up_command('media', 'get_best_media_server')
        return command()

    def get_media_server(self, filters):
        """
        Description: 获取指定id的媒体服务器

        Args:
            server_id:

        Returns:

        """
        command = self.set_up_command('media', 'get_media_server')
        return command(filters)

    def get_media_servers(self):
        """

        Description: 获取所有的媒体服务器状态

        Returns:

        """
        command = self.set_up_command('media', 'get_media_servers')
        return command()

    def get_thumbnail_path(self, filters, size='origin'):
        command = self.set_up_command('media', 'get_thumbnail_path')
        return command(filters, size)

    def select_media_data(self, filters):
        command = self.set_up_command('media', 'select_media_data')
        return command(filters)

    def get_event_server(self):
        command = self.set_up_command('options', 'get_event_server')
        return command()

    def send_email(self, addressee_list, subject, template, content):
        command = self.set_up_command('email', 'send_email')
        return command(addressee_list, subject, template, content)

    def get_web_socket_server(self):
        command = self.set_up_command('options', 'get_web_socket_server')
        return command()

    def get_email_server(self):
        command = self.set_up_command('options', 'get_email_server')
        return command()

    def start_timer(self, base_id, user_id):
        command = self.set_up_command('timelog', 'start_timer')
        return command(base_id, user_id)

    def stop_timer(self, base_id):
        command = self.set_up_command('timelog', 'stop_timer')
        return command(base_id)

    def get_department_data(self):
        command = self.set_up_command('department', 'get_department_data')
        return command()