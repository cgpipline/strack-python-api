
from pprint import pprint

from strack_api.strack import Strack

st = Strack(base_url="https://strack.cgspread.com/", login_name="strack", password="strack")

# create media
pprint(st.get_thumbnail_path([['id', 'is', 1]], 'origin'))