

from pprint import pprint

from strack_api.strack import Strack

st = Strack(base_url="https://strack.cgspread.com/", login_name="strack", password="strack")
pprint(st)
import time

a = time.time()
# OR 写法
pprint(st.select('user',
                 {0: ['id', 'in', [46, 47, 48]],
                  1: ['login_name', 'like', 'api%'],
                  '_logic': 'OR'},
                 ['login_name']))

# 单条件写法
pprint(st.select('user', [['id', 'in', [46, 47, 48]]]))
# AND写法
pprint(st.select('user', [['id', 'in', [46, 47, 48]], ['login_name', 'like', 'api%']]))
# AND写法2
pprint(st.select('user',
                 {0: ['id', 'in', [46, 47, 48]],
                  1: ['login_name', 'like', 'api%'],
                  '_logic': 'AND'}))
b = time.time()
print(b-a)

# pprint(st.select('project', [], ['name', 'code']))

# pprint(st.select('asset'))

# pprint(st.select('disk'))

# pprint(st.select('project_disk'))

pprint(st.select('file_type'))
pprint(st.select('base', [['created', 'between', ['2020-01-01', '2020-03-01']]]))
pprint(st.select('user', fields=['id']))