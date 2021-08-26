from strack_api.strack import Strack

if __name__ == '__main__':
    from pprint import pprint
    st = Strack(base_url="https://strack.cgspread.com/", login_name="strack", password="strack")
    import time
    a = time.time()
    pprint(st.delete('user', ['login_name', 'like', 'api%']))
    # pprint(st.delete('project_disk', [['project_id', 'is', 1]]))
    b = time.time()
