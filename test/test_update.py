# coding: utf-8
from pprint import pprint

from strack_api.strack import Strack

st = Strack(base_url="https://strack.cgspread.com/", login_name="strack", password="strack")
import time

a = time.time()

data = {
    'phone': '10086'
}
pprint(st.update('user', [['login_name', 'like', 'api%']], data))

b = time.time()
pprint(b - a)