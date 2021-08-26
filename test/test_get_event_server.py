from strack_api.strack import Strack

if __name__ == '__main__':
    from pprint import pprint
    st = Strack(base_url="https://strack.cgspread.com/", login_name="strack", password="strack")
    pprint(st.get_event_server().get('token'))
