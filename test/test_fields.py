

from pprint import pprint

from strack_api.strack import Strack

st = Strack(base_url="https://strack.cgspread.com/", login_name="strack", password="strack")

# user_fields = st.fields('base')
# pprint(user_fields)

# pprint(st.fields('action'))

# pprint(st.fields('disk'))

# print('dir_template')
# dir_template_fields = st.fields('dir_template')
#
# for i in dir_template_fields.get('master').values():
#     for j in i:
#         pprint(j.get('id'))
# print('\nfile_type')
#
# file_type_fields = st.fields('file_type')
#
# for i in file_type_fields.get('master').values():
#     for j in i:
#         pprint(j)
# #
# # print('\nfile')
# #
file_fields = st.fields('file')

for i in file_fields.get('master').values():
    for j in i:
        pprint(j.get('id'))
