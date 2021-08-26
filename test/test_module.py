

from pprint import pprint

from strack_api.strack import Strack

st = Strack(base_url="https://strack.cgspread.com/", login_name="strack", password="strack")

pprint(st.modules)


for module in st.modules:
    print('|%s |%s |' % (module.get('code'), module.get('name')))