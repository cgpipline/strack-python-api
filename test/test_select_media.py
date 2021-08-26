
from pprint import pprint

from strack_api.strack import Strack

st = Strack(base_url="https://strack.cgspread.com/", login_name="strack", password="strack")

# get media server

media_server = st.get_best_media_server()

# upload media
media_info = st.upload(r'C:\Users\TianD\Pictures\4k\1.jpg', media_server)

# create media
pprint(st.select_media_data([['id', 'is', 1]]))
pprint(st.get_media_data([['id', 'is', 1]]))