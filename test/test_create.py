# coding: utf-8
from strack_api.strack import Strack

if __name__ == '__main__':
    from pprint import pprint
    st = Strack(base_url="https://strack.cgspread.com/", login_name="strack", password="strack")
    # user_fields = st.fields('user')
    # pprint(user_fields)
    # for field_category, fields in user_fields.get('master').items():
    #     for field in fields:
    #         print(field.get('id'))
    data = {
        'login_name': 'api_user1',
        'name': 'api_user1',
        'nickname': 'api_user1',
        'email': 'api_user1@strack.com',
        'phone': '10010'
    }
    import time
    a = time.time()
    # pprint(st.create('user', data))
    b = time.time()
    print(b-a)
    #
    # data = {
    #     'name': 'maya',
    #     'code': 'maya',
    #     'engine': '',
    #     'module_id': '',
    #     'project_id': 0,
    #     'type': 'launcher',
    #     'config': ''
    # }
    #
    # st.create('action', data)

    pprint(st.create('base', {
        'project_id': 2,
        'code': 'abc',
        'name': 'dec',
        'step_id': 28,
        'entity_id': 1,
        'status_id': 1,
        'assignor': 1
    }))