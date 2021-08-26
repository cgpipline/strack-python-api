

from pprint import pprint

from strack_api.strack import Strack

st = Strack(base_url="https://strack.cgspread.com/", login_name="strack", password="strack")

pprint(st.get_media_server([['id', 'is', 1]]))

pprint(st.get_best_media_server())

pprint(st.get_media_servers())