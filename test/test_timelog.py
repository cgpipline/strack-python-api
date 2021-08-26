

from pprint import pprint

from strack_api.strack import Strack

st = Strack(base_url="https://strack.cgspread.com/", login_name="strack", password="strack")


pprint(st.start_timer(1, 3))

pprint(st.stop_timer(1))