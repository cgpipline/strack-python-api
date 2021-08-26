from pprint import pprint

from strack_api.strack import Strack

st = Strack(base_url="https://strack.cgspread.com/", login_name="strack", password="strack")

import time

a = time.time()
# OR 写法
# pprint(st.adv_select('user',
#                  {0: ['id', 'in', [46, 47, 48]],
#                   1: ['login_name', 'like', 'api%'],
#                   'logic': 'OR'},
#                  ['yuexin']))
#
# # 单条件写法
# pprint(st.adv_select('user', [['id', 'in', [46, 47, 48]]], ['yuexin']))
# # AND写法
# pprint(st.adv_select('user', [['id', 'in', [46, 47, 48]],
#                               ['login_name', 'like', 'api%']], ['yuexin']))
# # AND写法2
# pprint(st.adv_select('user',
#                  {0: ['id', 'in', [46, 47, 48]],
#                   1: ['login_name', 'like', 'api%'],
#                   'logic': 'AND'},
#                  ['yuexin']))

# pprint(st.adv_select('asset'))
b = time.time()
print(b-a)

# user = st.find('user', [['login_name', 'is', 'huiguoyu']])
# pprint(st.adv_select('base', [['executor', 'is', user.get('id')]], ['executor']))
#
# asset_module = next((module for module in st.modules if module.get('code')=='asset'))
# # pprint(asset_module)
#
# pprint(st.adv_select('base', [['executor', 'is', user.get('id')],
#                               ['entity_module_id', 'is', asset_module.get('id')]],
#                      ['entity.id']))

# pprint(st.adv_select('project', fields=['project_template.config']))

pprint(st.adv_select('shot', [], []))