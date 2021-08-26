# coding=utf8
import copy
import datetime
import json
import time

import requests
from six.moves.urllib.parse import urljoin
from .utils import get_logger

log = get_logger("strack_api")

OPERATORS = {
    ">": "-gt",
    ">=": "-egt",
    "<": "-lt",
    "<=": "-elt",
    "=": "-eq",
    "==": "-eq",
    "is": "-eq",
    "!=": "-neq",
    "is not": "-neq",
    "in": "-in",
    "not in": "-not-in",
    "like": "-lk",
    "not like": "-not-lk",
    "between": "-bw",
    "not between": "-not-bw"
}


class Command(object):
    """
    command base class
    """
    cmd = None  # 命令名

    def __init__(self, server_object, module):
        """It's a Command...'"""
        self.__server = server_object
        self.__module = module
        self.__request = []

    @property
    def headers(self):
        return {'token': self.server.token, 'Content-Type': 'application/json'}

    @property
    def url(self):
        module_uri = self.module.get('code')
        if module_uri == 'base':
            module_uri = 'task'
        if self.module.get('type') == 'entity':
            module_uri = 'entity'
        if '_' in module_uri:
            new_module_uri = ''
            for i, uri_part in enumerate(module_uri.split('_')):
                if i > 0:
                    uri_part = uri_part.capitalize()
                new_module_uri += uri_part
        else:
            new_module_uri = module_uri
        module_cmd = "%s/%s" % (new_module_uri, self.cmd)
        return self.__server.cmd_to_url(module_cmd)

    @property
    def server(self):
        return self.__server

    @property
    def module(self):
        return self.__module

    @property
    def request(self):
        return self.__request

    @property
    def parameters(self):
        # 命令所需的参数(参数名, 参数类型, 是否必填, 默认值)
        # should be [{'name': '', 'type': '', 'required': True, ''defaultValue'': '')]
        return []

    def __call__(self, *args, **kwargs):
        """
        调用
        :param args:
        :param kwargs:
        :return:
        """
        self.__request = (args, kwargs)
        param_dict = self._format_params(args, kwargs)
        payload = self._setup_payload(param_dict)
        response = self._execute(payload)

        if response.status_code == 200 and response.json().get('status') in [229012, 229013]:
            self.server.refresh_token()
            response = self._execute(payload)

        return self.__handle_response(response)

    def _format_params(self, args, kwargs):
        """
        格式化参数
        :param param_dict:
        :return:
        """
        param_dict = copy.deepcopy(kwargs)
        param_dict.update({self.parameters[i].get('name'): v for i, v in enumerate(args) if v})
        return param_dict

    def _setup_payload(self, param_dict):
        """
        组装请求体
        :param param_dict:
        :return:
        """
        payload = dict()
        payload.update(param_dict)
        payload.setdefault('module', {'code': self.module.get('code', ''),
                                      'id': self.module.get('id', 0),
                                      'type': self.module.get('type', 'fixed')})
        return payload

    def _execute(self, payload):
        """
        发送请求
        :param payload:
        :return:
        """
        result = self.server.session.post(self.url, headers=self.headers, data=json.dumps(payload))
        return result

    def __handle_response(self, response):
        """
        处理response
        :param response:
        :return:
        """
        if response.status_code == 200 and response.json().get('status') == 200:
            return self._success(response)
        elif response.status_code == 200 and (
                response.json().get('status') in [216009, 202006, 214001, 223006, 223010, 231006]):
            return self._success(response)
        else:
            return self.__failed(response)

    def _success(self, response):
        """成功的结果"""
        # 成功的结果
        res = response.json()
        result = res.get("data")
        format_result = self._format_result(result)
        return format_result

    def __failed(self, response):
        """
        失败的结果
        :param response:
        :return:
        """
        if response.status_code == 500:
            error_info = u"%s: %s" % (response.status_code, response.text)
        elif response.status_code not in [200, 500]:
            error_info = u"%s: %s" % (response.status_code, response.json().get("message"))
        elif response.status_code == 200:
            error_info = u"%s: %s" % (response.json().get('status'), response.json().get("message"))
        else:
            error_info = response.json()
        log.error(error_info)
        raise RuntimeError(
            '\nURL: \n' + response.request.url + '\nPayload: \n' + response.request.body + '\n' + error_info)

    def _format_result(self, result):
        """
        格式化返回值
        :param result:
        :return:
        """
        if not result:
            return {}
        return result


class FieldsCommand(Command):
    cmd = 'fields'

    @property
    def parameters(self):
        return [{'name': 'project_id',
                 'type': 'int',
                 'required': False}
                ]


class FilterCommand(Command):
    cmd = None

    def _format_params(self, args, kwargs):
        param_dict = copy.deepcopy(kwargs)
        if 'filters' in kwargs.keys():
            filter_value = param_dict.pop('filters')
            param_dict.setdefault('filter', filter_value)
        param_dict.update({self.parameters[i].get('name'): v for i, v in enumerate(args) if v})
        # 格式化filter
        filter_param = param_dict.get('filter')
        if filter_param:
            new_filter_param = self._format_filter(filter_param)
            param_dict.update({'filter': new_filter_param})
        return param_dict

    def _format_filter(self, filter_param):

        def setup_filter_expression(filter_expression, result):
            # 如果填入的是列表
            if isinstance(filter_expression, list) and isinstance(filter_expression[0], (list, dict)):
                logic = 'AND'
                if len(filter_expression) > 1:
                    result.setdefault('_logic', logic)
                    for i, sub_expression in enumerate(filter_expression):
                        i_result = dict()
                        setup_filter_expression(sub_expression, i_result)
                        result.setdefault(i, i_result)
                elif len(filter_expression) == 1:
                    setup_filter_expression(filter_expression[0], result)
            # 如果传入的是字典
            elif isinstance(filter_expression, dict) and '_logic' in filter_expression.keys():
                logic = filter_expression.pop('_logic')
                for i, sub_expression in filter_expression.items():
                    i_result = dict()
                    setup_filter_expression(sub_expression, i_result)
                    result.setdefault(i, i_result)
                result.setdefault('_logic', logic)
            # 如果传入的是一个运算
            elif isinstance(filter_expression, list) and isinstance(filter_expression[0], str):
                field_code = filter_expression[0]
                operator = filter_expression[1]
                format_operator = OPERATORS.get(operator)
                if not format_operator:
                    error_msg = ValueError(
                        '%s is Invalid. Operators only support [%s]' % (operator, ', '.join(OPERATORS.keys())))
                    raise error_msg
                value = filter_expression[2]
                result.setdefault(field_code, [format_operator, value])
            else:
                raise ValueError('The Filter Expression is Invalid.')

        result = dict()
        setup_filter_expression(filter_param, result)
        return result


class FindCommand(FilterCommand):
    cmd = 'find'

    @property
    def parameters(self):
        return [{'name': 'filter',
                 'type': 'list',
                 'required': False},
                {'name': 'fields',
                 'type': 'list',
                 'required': False},
                {'name': 'project_id',
                 'type': 'int',
                 'required': False}
                ]

    def _format_params(self, args, kwargs):
        param = super(FindCommand, self)._format_params(args, kwargs)
        # 格式化fields
        fields_param = param.get('fields')
        if fields_param:
            new_fields_param = self._format_fields(fields_param)
            param.update({'fields': new_fields_param})
        result = {'param': param}
        return result

    def _format_fields(self, fields_param):
        if fields_param and 'id' not in fields_param:
            fields_param.append('id')
        return fields_param


class SelectCommand(FilterCommand):
    cmd = 'select'

    @property
    def parameters(self):
        return [{'name': 'filter',
                 'type': 'list',
                 'required': False},
                {'name': 'fields',
                 'type': 'list',
                 'required': False},
                {'name': 'order',
                 'type': 'dict',
                 'required': False},
                {'name': 'page',
                 'type': 'dict',
                 'required': False},
                {'name': 'project_id',
                 'type': 'int',
                 'required': False}
                ]

    def _format_params(self, args, kwargs):
        param = super(SelectCommand, self)._format_params(args, kwargs)
        # 格式化fields
        fields_param = param.get('fields')
        if fields_param:
            new_fields_param = self._format_fields(fields_param)
            param.update({'fields': new_fields_param})
        # 格式化order
        order_param = param.get('order')
        if order_param:
            new_order_param = self._format_order(order_param)
            param.update({'order': new_order_param})
        # 格式化page
        page_param = param.get('page')
        if page_param:
            new_page_param = self._format_order(page_param)
            param.update({'page': new_page_param})
        result = {'param': param}
        return result

    def _format_fields(self, fields_param):
        if fields_param and 'id' not in fields_param:
            fields_param.append('id')
        return fields_param

    def _format_order(self, order_param):
        return order_param

    def _format_page(self, page_param):
        return page_param


class CreateCommand(Command):
    cmd = 'create'

    @property
    def parameters(self):
        return [{'name': 'data',
                 'type': 'dict',
                 'required': True,
                 'defaultValue': None}
                ]

    def _format_params(self, args, kwargs):
        params = super(CreateCommand, self)._format_params(args, kwargs)
        module_fields = self.server.fields(self.module.get('code'))
        data = dict()
        for field_code, field_value in params.get('data').items():
            if '.' in field_code:
                field_list = module_fields.get('relation')
                module_code, field_code = field_code.split('.')
            else:
                field_list = module_fields.get('master')
                module_code = self.module.get('code')
            for field_type, fields in field_list.items():
                for field_info in fields:
                    if field_code == field_info.get('id'):
                        full_value = {
                            'field': field_code,
                            'field_type': field_type,
                            'value': field_value,
                            'variable_id': field_info.get('variable_id', 0)
                        }
                        data.setdefault(module_code, list()).append(full_value)
                        break
        result = {'data': data}
        return result


class UpdateCommand(FilterCommand):
    cmd = 'update'

    @property
    def parameters(self):
        return [{'name': 'filter',
                 'type': 'list',
                 'required': True,
                 'defaultValue': None},
                {'name': 'data',
                 'type': 'dict',
                 'required': True,
                 'defaultValue': None}
                ]

    def _format_params(self, args, kwargs):
        param = super(UpdateCommand, self)._format_params(args, kwargs)
        module_fields = self.server.fields(self.module.get('code'))
        data = dict()
        for field_code, field_value in param.pop('data').items():
            if '.' in field_code:
                field_list = module_fields.get('relation')
                module_code, field_code = field_code.split('.')
            else:
                field_list = module_fields.get('master')
                module_code = self.module.get('code')
            for field_type, fields in field_list.items():
                for field_info in fields:
                    if field_code == field_info.get('id'):
                        full_value = {
                            'field': field_code,
                            'field_type': field_type,
                            'value': field_value,
                            'variable_id': field_info.get('variable_id', 0)
                        }
                        data.setdefault(module_code, list()).append(full_value)
        result = {'data': data, 'param': param}
        return result


class DeleteCommand(FilterCommand):
    cmd = 'delete'

    @property
    def parameters(self):
        return [{'name': 'filter',
                 'type': (list, dict),
                 'required': True,
                 'defaultValue': None}
                ]

    def _format_params(self, args, kwargs):
        param = super(DeleteCommand, self)._format_params(args, kwargs)
        result = {'param': param}
        return result


class AdvQueryCommand(Command):
    cmd = 'getRelation'

    @property
    def parameters(self):
        return [{'name': 'filter',
                 'type': 'list',
                 'required': False},
                {'name': 'fields',
                 'type': 'list',
                 'required': False},
                {'name': 'order',
                 'type': 'dict',
                 'required': False},
                {'name': 'page',
                 'type': 'dict',
                 'required': False},
                {'name': 'project_id',
                 'type': 'int',
                 'required': False}
                ]

    def _format_params(self, args, kwargs):
        module_fields = self.server.fields(self.module.get('code'))

        param_dict = copy.deepcopy(kwargs)
        if 'filters' in kwargs.keys():
            filter_value = param_dict.pop('filters')
            param_dict.setdefault('filter', filter_value)
        param_dict.update({self.parameters[i].get('name'): v for i, v in enumerate(args) if v})
        # 格式化filter
        filter_param = param_dict.get('filter')
        if filter_param:
            new_filter_param = self._format_filter(filter_param, module_fields)
            param_dict.update({'filter': new_filter_param})
        # 格式化fields
        fields_param = param_dict.get('fields')
        if fields_param:
            new_fields_param = self._format_fields(fields_param)
            param_dict.update({'fields': new_fields_param})
        # 格式化order
        order_param = param_dict.get('order')
        if order_param:
            new_order_param = self._format_order(order_param, module_fields)
            param_dict.update({'order': new_order_param})
        # 格式化page
        page_param = param_dict.get('page')
        if page_param:
            new_page_param = self._format_page(page_param)
            param_dict.update({'page': new_page_param})
        result = {'param': param_dict}
        return result

    def _format_filter(self, filter_param, module_fields):

        def setup_filter_expression(level, filter_expression, result):
            # 如果填入的是列表
            if isinstance(filter_expression, list) and isinstance(filter_expression[0], (list, dict)):
                logic = 'AND'
                level += 1
                result.setdefault('logic', logic)
                for i, sub_expression in enumerate(filter_expression):
                    i_result = dict()
                    setup_filter_expression(level, sub_expression, i_result)
                    result.setdefault(i, i_result)
            # 如果传入的是字典
            elif isinstance(filter_expression, dict) and 'logic' in filter_expression.keys():
                logic = filter_expression.pop('logic')
                level += 1
                for i, sub_expression in filter_expression.items():
                    i_result = dict()
                    setup_filter_expression(level, sub_expression, i_result)
                    result.setdefault(i, i_result)
                result.setdefault('logic', logic)
            # 如果传入的是一个运算
            elif isinstance(filter_expression, list) and isinstance(filter_expression[0], str):
                field_code = filter_expression[0]
                operator = filter_expression[1]
                format_operator = OPERATORS.get(operator)
                if not format_operator:
                    error_msg = ValueError(
                        '%s is Invalid. Operators only support [%s]' % (operator, ', '.join(OPERATORS.keys())))
                    raise error_msg
                field_value = filter_expression[2]
                if '.' in field_code:
                    field_list = module_fields.get('relation')
                    module_code, field_code = field_code.split('.')
                else:
                    field_list = module_fields.get('master')
                    module_code = self.module.get('code')
                for field_type, fields in field_list.items():
                    for field_info in fields:
                        if field_code == field_info.get('id') and field_type != 'custom':
                            result.update({
                                'field': field_code,
                                'field_type': field_type,
                                'value': field_value,
                                'variable_id': field_info.get('variable_id', 0),
                                'module_code': module_code,
                                'condition': format_operator,
                                'editor': field_info.get('editor')
                            })
                            break
                        elif field_code == field_info.get('id') and field_type == 'custom':
                            result.update({
                                'field': 'id',
                                'field_type': field_type,
                                'value': field_value,
                                'variable_id': field_info.get('variable_id', 0),
                                'module_code': field_code,
                                'condition': format_operator,
                                'editor': field_info.get('editor')
                            })
                            break
                        else:
                            pass
            else:
                raise ValueError('The Filter Expression is Invalid.')

        result = dict()
        level = 0
        setup_filter_expression(level, filter_param, result)
        result.update({'number': level or 1})
        return result

    def _format_fields(self, fields_param):
        result = dict()
        for field in fields_param:
            if '.' in field:
                module_code, field_code = field.split('.')
                result.setdefault(module_code, list()).append(field_code)
            else:
                module_code = self.module.get('code')
                field_code = field
                result.setdefault(module_code, list()).append(field_code)
        for key, value in result.items():
            result.update({key: ','.join(value)})
        return result

    def _format_order(self, order_param, module_fields):
        result = list()
        for key, value in order_param.items():
            if '.' in key:
                field_list = module_fields.get('relation')
                module_code, field_code = key.split('.')
            else:
                field_list = module_fields.get('master')
                module_code = self.module.get('code')
                field_code = key
            for field_type, fields in field_list.items():
                for field_info in fields:
                    if field_code == field_info.get('id'):
                        temp = {
                            'type': value,
                            'field': field_code,
                            'module_code': module_code,
                            'field_type': field_type
                        }
                        result.append(temp)
        return result

    def _format_page(self, page_param):
        return page_param


class GetRelationModuleCommand(Command):
    cmd = 'getRelationModuleData'

    @property
    def url(self):
        module_uri = 'module'
        module_cmd = "%s/%s" % (module_uri, self.cmd)
        return self.__server.cmd_to_url(module_cmd)

    @property
    def parameters(self):
        return [{'name': 'module_code',
                 'type': 'str',
                 'required': False}
                ]


class UploadCommand(Command):
    cmd = 'upload'

    @property
    def parameters(self):
        return [{'name': 'file_path',
                 'type': 'str',
                 'required': True},
                {'name': 'server',
                 'type': 'dict',
                 'required': True},
                {'name': 'belong_system',
                 'type': 'str',
                 'required': False,
                 'defaultValue': 'task'},
                {'name': 'size',
                 'type': 'str',
                 'required': False,
                 'defaultValue': '250x140'}
                ]

    def _execute(self, payload):
        media_server = payload.get('server')
        media_server_url = media_server.get('upload_url')
        media_server_token = media_server.get('token')
        upload_file = payload.get('file_path')
        belong_system = payload.get('belong_system')
        size = payload.get('size')
        if not upload_file:
            return None
        with open(upload_file, 'rb') as f:
            file_data = {'Filedata': f}
            result = requests.post(media_server_url,
                                   data={'token': media_server_token,
                                         'timestamp': time.mktime(datetime.datetime.now().timetuple()),
                                         'belong_system': belong_system,
                                         'size': size},
                                    files = file_data)
            return result

    def _format_result(self, result):
        return result


class GetMediaDataCommand(FilterCommand):
    cmd = 'getMediaData'

    @property
    def parameters(self):
        return [{'name': 'filter',
                 'type': 'list',
                 'required': True}
                ]

    def _format_params(self, args, kwargs):
        param_dict = super(GetMediaDataCommand, self)._format_params(args, kwargs)
        result = {'param': param_dict}
        return result

    def _format_result(self, result):
        new_result = result.get('param')
        return new_result


class GetMediaServerCommand(FilterCommand):
    cmd = 'getMediaServerItem'

    @property
    def parameters(self):
        return [{'name': 'filter',
                 'type': 'list',
                 'required': True}
                ]

    def _format_params(self, args, kwargs):
        param_dict = super(GetMediaServerCommand, self)._format_params(args, kwargs)
        result = {'param': param_dict}
        return result


class GetBestMediaServerCommand(Command):
    cmd = 'getMediaUploadServer'


class SaveMediaCommand(Command):

    @property
    def parameters(self):
        return [{'name': 'module',
                 'type': 'string',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': None},
                {'name': 'id',
                 'type': 'int',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': None},
                {'name': 'media_data',
                 'type': 'dict',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': None},
                {'name': 'usage_type',
                 'type': 'string',
                 'required': False,
                 'isPayload': True,
                 'defaultValue': 'thumb'},
                {'name': 'media_server',
                 'type': 'dict',
                 'required': False,
                 'isPayload': True,
                 'defaultValue': self.server.get_best_media_server()},
                ]

    def _format_params(self, args, kwargs):
        param_dict = super(SaveMediaCommand, self)._format_params(args, kwargs)
        format_param = {}
        usage_type = param_dict.get('usage_type')
        module_name = param_dict.get('module')
        module_info = list(filter(lambda x: x.get('code') == module_name, self.server.modules))[0]
        link_id = param_dict.get('id')
        media_data = param_dict.get('media_data')
        media_server = param_dict.get('media_server')
        format_param.update({'module_code': module_info.get('code'), 'link_id': link_id})
        format_param.update({'media_data': media_data})
        format_param.update({'media_server': media_server})
        format_param.update({'type': usage_type})
        return format_param

    def _setup_payload(self, param_dict):
        """
        组装请求体
        :param param_dict:
        :return:
        """
        return param_dict


class CreateMediaCommand(SaveMediaCommand):
    cmd = 'createMedia'


class UpdateMediaCommand(SaveMediaCommand):
    cmd = 'updateMedia'


class ClearMediaThumbnailCommand(Command):
    cmd = 'clearMediaThumbnail'

    @property
    def parameters(self):
        return [{'name': 'filter',
                 'type': 'list',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': None}]

    def _format_params(self, args, kwargs):
        result = super(ClearMediaThumbnailCommand, self)._format_params(param_dict)
        # 格式化filter
        filter_param = result.get('filter')
        new_filter_param = {}
        for filter_item in filter_param:
            field = filter_item[0]
            if '.' in field:
                field = field.split('.')[-1]
            operator = OPERATORS.get(filter_item[1], filter_item[1])
            values = filter_item[2]
            new_filter_param.setdefault(field, [operator, values])
        result.update({'filter': new_filter_param})
        result.pop('module')
        return result


class GetMediaServerStatusCommand(Command):
    cmd = 'getMediaServerStatus'

    def _format_result(self, result):
        return result


class DeleteMediaServerCommand(Command):
    cmd = 'deleteMediaServer'


class AddMediaServerCommand(Command):
    cmd = 'addMediaServer'


class GetThumbnailCommand(FilterCommand):
    cmd = 'getSpecifySizeThumbPath'

    @property
    def parameters(self):
        return [{'name': 'filter',
                 'type': 'list',
                 'required': True},
                {'name': 'size',
                 'type': 'string',
                 'required': False,
                 'defaultValue': 'origin'}]

    def _format_params(self, args, kwargs):
        param_dict = super(GetThumbnailCommand, self)._format_params(args, kwargs)
        result = {'param': {'filter': param_dict.get('filter')},
                  'size': param_dict.get('size')}
        return result

    def _format_result(self, result):
        # 格式化结果
        return result


class SelectMediaDataCommand(FilterCommand):
    cmd = 'selectMediaData'

    @property
    def parameters(self):
        return [{'name': 'filter',
                 'type': 'list',
                 'required': True}
                ]

    def _format_params(self, args, kwargs):
        param_dict = super(SelectMediaDataCommand, self)._format_params(args, kwargs)
        result = {'param': param_dict}
        return result

    def _format_result(self, result):
        # 格式化结果
        new_result = result.get('param')
        return new_result


class SelectLogsCommand(SelectCommand):
    cmd = 'selectLogs'


class EventCommand(Command):

    @property
    def url(self):
        module_uri = 'options'
        module_cmd = "%s/%s" % (module_uri, self.cmd)
        return self.server.cmd_to_url(module_cmd)

    def _init_payload(self, args, kwargs):
        # 初始化默认参数的值
        param_dict = copy.deepcopy(kwargs)
        param_dict.update({self.parameters[i].get('name'): v for i, v in enumerate(args)})
        param_dict, _ = self._setup_params(param_dict)
        param_dict = self._format_params(param_dict)
        # self._validate_param(param_dict)
        return param_dict, _

    def _setup_params(self, param_dict):
        # 将参数组装成需要的格式
        payload = {}
        other_params = {}
        for parameter in self.parameters:
            name = parameter.get('name')
            is_payload = parameter.get('isPayload')
            if param_dict.get(name) is None:
                value = parameter.get('defaultValue')
            else:
                value = param_dict.get(name)
            if is_payload:
                payload.setdefault(name, value)
            else:
                other_params.setdefault(name, value)
        return payload, other_params

    def _format_result(self, result):
        return result


class CreateEventCommand(EventCommand):
    cmd = 'add'

    @property
    def parameters(self):
        return [{'name': 'data',
                 'type': 'dict',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': None}
                ]

    @property
    def headers(self):
        return {'Content-Type': 'application/json'}

    def _format_params(self, args, kwargs):
        param_dict.update({'type': 'custom'})
        return param_dict

    def _execute(self, payload):
        event_server = self.server.get_event_server()
        add_request_url = event_server.get('add_url')
        data = payload.get('data')
        result = requests.post(add_request_url, headers=self.headers, data=data)
        return result


class QueryEventCommand(EventCommand):

    @property
    def parameters(self):
        return [{'name': 'filter',
                 'type': 'list',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': []},
                {'name': 'fields',
                 'type': 'list',
                 'required': False,
                 'isPayload': True,
                 'defaultValue': []},
                {'name': 'order',
                 'type': 'dict',
                 'required': False,
                 'isPayload': True,
                 'defaultValue': {}},
                {'name': 'page',
                 'type': 'dict',
                 'required': False,
                 'isPayload': True,
                 'defaultValue': {"page_number": 0,
                                  "page_size": 0}},
                {'name': 'flat',
                 'type': 'bool',
                 'required': False,
                 'isPayload': False,
                 'defaultValue': False},
                ]

    def _format_params(self, args, kwargs):
        result = super(QueryEventCommand, self)._format_params(param_dict)
        # 格式化filter
        filter_param = result.get('filter')
        new_filter_param = {}
        for filter_item in filter_param:
            field = filter_item[0]
            module = 'event_log'
            if '.' in field:
                module = field.split('.')[0]
                field = field.split('.')[-1]
            operator = OPERATORS.get(filter_item[1], filter_item[1])
            values = filter_item[2]
            if isinstance(values, list):
                values = ','.join(map(lambda x: str(x), values))
            new_filter_param.setdefault(module, dict()).setdefault(field, [operator, values])
        result.update({'filter': new_filter_param})
        # 格式化fields
        fields_param = result.get('fields')
        new_fields_param = {}
        for field_item in fields_param:
            field = field_item
            module = self.module.get('code')
            if '.' in field:
                module = field.split('.')[0]
                field = field.split('.')[-1]
                if field != '*':
                    new_fields_param.setdefault(module, list()).append(field)
                else:
                    new_fields_param.setdefault(module, list())
            else:
                new_fields_param.setdefault(module, list()).append(field)
        result.update({'fields': new_fields_param})
        # 格式化order
        order_param = result.get('order')
        new_order_param = {}
        for order_key, order_value in order_param.items():
            module = self.module.get('code')
            if '.' not in order_key:
                new_order_key = '%s.%s' % (module, order_key)
            else:
                new_order_key = order_key
            new_order_param.setdefault(new_order_key, order_value)
        result.update({'order': new_order_param})
        return result


class FindEventCommand(QueryEventCommand):
    cmd = 'find'

    @property
    def headers(self):
        return {'Content-Type': 'application/json'}

    def _execute(self, payload):
        event_server = self.server.get_event_server()
        find_request_url = event_server.get('find_url')
        result = requests.post(find_request_url, headers=self.headers, data=json.dumps(payload))
        return result


class SelectEventCommand(QueryEventCommand):
    cmd = 'select'

    @property
    def headers(self):
        return {'Content-Type': 'application/json'}

    def _execute(self, payload):
        event_server = self.server.get_event_server()
        select_request_url = event_server.get('select_url')
        result = requests.post(select_request_url, headers=self.headers, data=json.dumps(payload))
        return result


class EventFieldsCommand(EventCommand):
    cmd = 'fields'

    @property
    def headers(self):
        return {'Content-Type': 'application/json'}

    @property
    def parameters(self):
        return [{'name': 'project_id',
                 'type': 'int',
                 'required': False,
                 'isPayload': True,
                 'defaultValue': 0}
                ]

    def _execute(self, payload):
        event_server = self.server.get_event_server()
        fields_request_url = event_server.get('fields_url')
        result = requests.post(fields_request_url, headers=self.headers, data=json.dumps(payload))
        return result

    def _format_result(self, result):
        return result.get('fixed_field', {})


class SendEmailCommand(EventCommand):
    cmd = 'send'

    @property
    def parameters(self):
        return [{'name': 'addressee_list',
                 'type': 'list',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': []},
                {'name': 'subject',
                 'type': 'list',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': []},
                {'name': 'template',
                 'type': 'string',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': None},
                {'name': 'content',
                 'type': 'string,dict',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': None}
                ]

    @property
    def headers(self):
        return {'Content-Type': 'application/json'}

    def _format_params(self, args, kwargs):
        addressee_list = param_dict.get('addressee_list')
        subject = param_dict.get('subject')
        content = param_dict.get('content')
        template = param_dict.get('template')
        addressee = ','.join(addressee_list)
        format_param = {'param': {'addressee': addressee, 'subject': subject},
                        'data': {'template': template, 'content': content}}
        return format_param

    def _execute(self, payload):
        event_server = self.server.get_event_server()
        request_url = event_server.get('request_url')
        token = event_server.get('token')
        send_email_url = urljoin(request_url, 'email/%s?sign=%s' % (self.cmd, token))
        result = requests.post(send_email_url, headers=self.headers, data=json.dumps(payload))
        return result

    def _format_result(self, result):
        return result


class GetEventServerCommand(Command):
    cmd = 'getEventLogServer'

    def _format_result(self, result):
        return result


class GetWebSocketServerCommand(Command):
    cmd = 'getWebSocketServer'

    def _format_result(self, result):
        return result


class GetEmailServerCommand(Command):
    cmd = 'getEmailServer'

    def _format_result(self, result):
        return result


class GetOptionsCommand(Command):
    cmd = 'getOptions'

    @property
    def parameters(self):
        return [{'name': 'options_name',
                 'type': 'string',
                 'required': True,
                 'isPayload': True,
                 'defaultValue': ''}
                ]

    def _format_result(self, result):
        return result


class AddOptionsCommand(Command):
    cmd = 'addOptions'

    @property
    def parameters(self):
        return [{'name': 'options_name',
                 'type': 'string',
                 'required': True,
                 'defaultValue': ''},
                {'name': 'config',
                 'type': 'dict',
                 'required': True,
                 'defaultValue': []}
                ]

    def _format_result(self, result):
        return result


class GetThumbnailPathCommand(Command):
    cmd = ''


class AddSubTaskCommand(Command):
    cmd = 'addSubTask'


class AddTaskPlanCommand(Command):
    cmd = ''


class StartTimerCommand(Command):
    cmd = 'startTimer'

    @property
    def parameters(self):
        return [{'name': 'id',
                 'type': 'int',
                 'required': True},
                {'name': 'user_id',
                 'type': 'id',
                 'required': True}
                ]

    def _format_params(self, args, kwargs):
        param_dict = super(StartTimerCommand, self)._format_params(args, kwargs)
        param_dict.update({'module_code': 'base'})
        return param_dict


class StopTimerCommand(Command):
    cmd = 'stopTimer'

    @property
    def parameters(self):
        return [{'name': 'id',
                 'type': 'int',
                 'required': True}
                ]


class GetDepartmentDataCommand(Command):
    cmd = 'getDepartmentDataWithManager'


class CreateSchemaCommand(Command):
    cmd = ''


class UpdateSchemaCommand(Command):
    cmd = ''


class DeleteSchemaCommand(Command):
    cmd = ''


class GetSchemaCommand(Command):
    cmd = ''


class GetAllSchemasCommand(Command):
    cmd = ''


class CreateEntityModuleCommand(Command):
    cmd = ''


class GetAllTableNamesCommand(Command):
    cmd = ''


class GetTableConfigCommand(Command):
    cmd = ''


class UpdateTableConfigCommand(Command):
    cmd = ''
