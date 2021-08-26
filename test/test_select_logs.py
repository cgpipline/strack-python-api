

from pprint import pprint

from strack_api.strack import Strack

st = Strack(base_url="https://strack.cgspread.com/", login_name="strack", password="strack")
pprint(st)
import time

a = time.time()

# 单条件写法
pprint(st.select('event', [['id', '>', 0]], order={'id': 'desc'}, page=[1, 10]))

b = time.time()
print(b-a)
