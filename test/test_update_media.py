
from pprint import pprint

from strack_api.strack import Strack

st = Strack(base_url="https://strack.cgspread.com/", login_name="strack", password="strack")

# get media server

media_server = st.get_best_media_server()

# upload media
media_info = st.upload(r'C:\Users\TianD\Pictures\4k\2.jpg', media_server)

# create media
pprint(st.update_media('base', 1, media_info, 'thumb', media_server))