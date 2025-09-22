import streamlit as st
from streamlit_option_menu import option_menu
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
import datetime
from zoneinfo import ZoneInfo
import uuid
import altair as alt

#Connect spreadsheet

# Define the scope (permissions) and authenticate
scope = ["https://spreadsheets.google.com/feeds",
          "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file("pengirimannasional-test-e22b468e9586.json", scopes=scope)
client = gspread.authorize(creds)

#Open all table then convert to dataframe
user_sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1mUbmJGAEABhCqjfH7F2Jzb5JkhMSfucl2uVTiLV7Jls/edit?gid=0#gid=0').sheet1
user_table = user_sheet.get_all_values()
df_user = pd.DataFrame(user_table[1:], columns=user_table[0])

data_sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/10BlL266KaE2zQ3lq_4mMlxVEA__gaDGHI0_hHdILlCo/edit?gid=0#gid=0').sheet1
data_table = data_sheet.get_all_values()
df_data = pd.DataFrame(data_table[1:], columns=data_table[0])

#Function goes here
def RefreshData():
     global df_data, data_sheet, df_user

     st.cache_data.clear()
     
     user_sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1mUbmJGAEABhCqjfH7F2Jzb5JkhMSfucl2uVTiLV7Jls/edit?gid=0#gid=0').sheet1
     user_table = user_sheet.get_all_values()
     df_user = pd.DataFrame(user_table[1:], columns=user_table[0])
     
     data_sheet = data_sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/10BlL266KaE2zQ3lq_4mMlxVEA__gaDGHI0_hHdILlCo/edit?gid=0#gid=0').sheet1
     data_table = data_sheet.get_all_values()
     df_data = pd.DataFrame(data_table[1:], columns=data_table[0])

def AddDataSingle(data_sheet, send_from, send_to, agreement_no, no_custody, send_type, awb_no, send_date, send_doc, desc):
     last_row_index = len(data_sheet.get_all_values())
     now = datetime.datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M:%S")
     user_update = st.session_state['user_key']
     send_date = send_date.strftime("%Y-%m-%d %H:%M:%S")
     
     requests = [
          {
               "range": f"A{last_row_index + 1}",
               "values": [[now]]
          },
          {
               "range": f"C{last_row_index + 1}:I{last_row_index + 1}",
               "values": [[send_from, send_to, agreement_no, no_custody, send_type, awb_no, send_date]]
          },
          {
               "range": f"P{last_row_index + 1}:S{last_row_index + 1}",
               "values": [[send_doc, desc, user_update, user_update + '_' + str(uuid.uuid4())[:8]]]
          }
     ]
     
     if last_row_index + 1 > data_sheet.row_count:
          data_sheet.add_rows(1)
          data_sheet.batch_update(requests, value_input_option="USER_ENTERED")
     else:
          data_sheet.batch_update(requests, value_input_option="USER_ENTERED")

def AddDataBatch(data_sheet, uploaded_file):
     last_row_index = len(data_sheet.get_all_values())
     last_uploaded_row_index = len(uploaded_file)
     now = datetime.datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M:%S")
     user_update = st.session_state['user_key']
     #user_name = st.session_state['profile_name']

     uploaded_file = uploaded_file.fillna('')
     uploaded_file["Tanggal Pengiriman*"] = uploaded_file["Tanggal Pengiriman*"].dt.strftime("%Y-%m-%d %H:%M:%S")
     uploaded_file["Nomor AWB*"] = uploaded_file["Nomor AWB*"].str.replace("#", "", regex=False)
     
     values_block1 = [[now] for _ in range(len(uploaded_file))]
     values_block2 = uploaded_file[["Asal Pengiriman*", "Tujuan Pengiriman*", "Nomor Kontrak*", "Nomor Custody", "Jenis Pengiriman*", "Nomor AWB*", "Tanggal Pengiriman*"]].values.tolist()
     values_block3 = uploaded_file[["Dokumen yang Dikirimkan*", "Keterangan*"]].values.tolist()
     values_block3 = [row + [user_update] + [user_update + '_' + str(uuid.uuid4())[:8]] for row in values_block3]  # add fixed username

     requests = [
          {
               "range": f"A{last_row_index + 1}:A{last_row_index + last_uploaded_row_index}",
               "values": values_block1
          },
          {
               "range": f"C{last_row_index + 1}:I{last_row_index + last_uploaded_row_index}",
               "values": values_block2
          },
          {
               "range": f"P{last_row_index + 1}:S{last_row_index + last_uploaded_row_index}",
               "values": values_block3
          }
     ]

     if last_row_index + last_uploaded_row_index > data_sheet.row_count:
          data_sheet.add_rows(last_uploaded_row_index)
          data_sheet.batch_update(requests, value_input_option="USER_ENTERED")
     else:
          data_sheet.batch_update(requests, value_input_option="USER_ENTERED")

def ViewData(df_data, search_agreement, search_awb, search_origin, search_destination, search_type, search_send_doc, search_date_range, search_jne_status):
     IsEmpty = False
     df_data = df_data[['sent_from', 'sent_to', 'agreement_no', 'no_custody', 'send_type', 'awb_no', 'send_date_opc', 'delivery_status', 'last_tracking_status', 'last_tracking_date','send_doc', 'desc','link']]
     df_data['send_date_opc'] = pd.to_datetime(df_data['send_date_opc']).dt.date
     
     if search_agreement != '':
          df_data = df_data[df_data['agreement_no'].str.contains(search_agreement, case=False, na=False)]
          if df_data.empty:
               IsEmpty = True
     if search_awb != '':
          df_data = df_data[df_data['awb_no'].str.contains(search_awb, case=False, na=False)]
          if df_data.empty:
               IsEmpty = True
     if search_origin != []:
          df_data = df_data[df_data['sent_from'].isin(search_origin)]
          if df_data.empty:
               IsEmpty = True
     if search_destination != []:
          df_data = df_data[df_data['sent_to'].isin(search_destination)]
          if df_data.empty:
               IsEmpty = True
     if search_type != []:
          df_data = df_data[df_data['send_type'].isin(search_type)]
          if df_data.empty:
               IsEmpty = True
     if search_send_doc != []:
          df_data = df_data[df_data['send_doc'].isin(search_send_doc)]
          if df_data.empty:
               IsEmpty = True
     if search_date_range != []:
          df_data = df_data[(df_data['send_date_opc'] >= search_date_range[0]) & (df_data['send_date_opc'] <= search_date_range[1])]
          if df_data.empty:
               IsEmpty = True
     if search_jne_status != []:
          df_data = df_data[df_data['delivery_status'].isin(search_jne_status)]
          if df_data.empty:
               IsEmpty = True
     
     df_data = df_data[['sent_from', 'sent_to', 'agreement_no', 'no_custody','send_type', 'awb_no', 'send_date_opc', 'last_tracking_date', 'last_tracking_status', 'send_doc', 'desc','link']]
     df_data['awb_no'] = df_data['awb_no'].apply(lambda x: f"#{x}#" if pd.notnull(x) and str(x).strip() != "" else x)
     #df_data['send_date_opc'] = pd.df_data['send_date_opc'].dt.strftime('%d/%m/%Y')
     
     df_data = df_data.rename(columns={'sent_from': 'Cabang Pengirim', 'sent_to': 'Cabang Tujuan', 'agreement_no': 'No. Kontrak', 'no_custody': 'No. Custody','send_type': 'Jenis Pengiriman', 
                                        'awb_no': 'No. AWB', 'send_date_opc': 'Tanggal Pengiriman', 'last_tracking_status': 'Status Terakhir', 'last_tracking_date': 'Tanggal Status Terakhir',
                                        'send_doc': 'Isi Paket Pengiriman', 'desc': 'Keterangan', 'link': 'Link Tracking'}
                              )     
                            
     return df_data, IsEmpty

def EditDeleteDataRow(origin_df, edited_df, origin_sheet):
     edited_df['Tanggal Pengiriman'] = edited_df['Tanggal Pengiriman'].dt.strftime("%Y-%m-%d %H:%M:%S")

     log_editdelete_input = edited_df
     editdelete_row_uid = log_editdelete_input.index.tolist()

     idx_editdelete = origin_df[origin_df['row_uid'].isin(editdelete_row_uid)].index.tolist()
     idx_editdelete = [i + 1 for i in idx_editdelete]

     if len(idx_editdelete) == 0:
          return 'Success'

     log_edit_input = edited_df[edited_df['Edit'] == True]
     edit_row_uid = log_edit_input.index.tolist()

     idx_edit = origin_df[origin_df['row_uid'].isin(edit_row_uid)].index.tolist()
     idx_edit = [i + 1 for i in idx_edit]

     log_delete_input = edited_df[edited_df['Hapus'] == True]
     delete_row_uid = log_delete_input.index.tolist()

     idx_delete = origin_df[origin_df['row_uid'].isin(delete_row_uid)].index.tolist()
     idx_delete = [i + 1 for i in idx_delete]

     now = datetime.datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M:%S")

     log_sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/10BlL266KaE2zQ3lq_4mMlxVEA__gaDGHI0_hHdILlCo/edit?gid=0#gid=0').get_worksheet(1)
     last_row_index_log = len(log_sheet.get_all_values())

     values_block1 = [[now] for _ in range(len(log_editdelete_input))]
     delete_row_uid_write = [[i] for i in editdelete_row_uid]
     values_block2 = log_editdelete_input[['Cabang Pengirim', 'Cabang Tujuan', 'No. Kontrak', 'No. Custody','Jenis Pengiriman', 'No. AWB', 'Tanggal Pengiriman','Isi Paket', 'Keterangan']].astype(str).values.tolist()
     values_block2 = [row + [st.session_state['user_key']] for row in values_block2]
     values_block3 = log_editdelete_input[['Hapus','Edit']].values.tolist()

     #WRITE LOG FIRST

     write_requests = [
          {
               'range': f'A{last_row_index_log + 1}:A{last_row_index_log + len(log_editdelete_input)}',
               'values': values_block1
          },
          {
               'range': f'B{last_row_index_log + 1}:K{last_row_index_log + len(log_editdelete_input)}',
               'values': values_block2
          },
          {
               'range': f'L{last_row_index_log + 1}:L{last_row_index_log + len(log_editdelete_input)}',
               'values': delete_row_uid_write
          },
          {
               'range': f'M{last_row_index_log + 1}:N{last_row_index_log + len(log_editdelete_input)}',
               'values': values_block3
          }
     ]

     if last_row_index_log + len(log_editdelete_input) > log_sheet.row_count:
          log_sheet.add_rows(len(log_editdelete_input))
          log_sheet.batch_update(write_requests, value_input_option="USER_ENTERED")
     else:
          log_sheet.batch_update(write_requests, value_input_option="USER_ENTERED")

     if len(idx_edit) != 0:            #Edit Function-------------------------------------------------------------------------

          values_edit_block1 = log_edit_input[['Cabang Pengirim', 'Cabang Tujuan', 'No. Kontrak', 'No. Custody','Jenis Pengiriman', 'No. AWB', 'Tanggal Pengiriman']].astype(str).values.tolist()
          values_edit_block1 = [[i] for i in values_edit_block1]
          values_edit_block2 = log_edit_input[['Isi Paket', 'Keterangan']].values.tolist()
          values_edit_block2 = [[i] for i in values_edit_block2]

          edit_requests = []

          for j, row in enumerate(idx_edit):
               edit_requests.append({
                    'range': f'B{row+1}',
                    'values': [[now]]
               })
               edit_requests.append({
                    'range': f'C{row+1}:I{row+1}',
                    'values': values_edit_block1[j]
               })
               edit_requests.append({
                    'range': f'P{row+1}',
                    'values': values_edit_block2[j]
               })

          origin_sheet.batch_update(edit_requests, value_input_option="USER_ENTERED")

     if len(idx_delete) != 0:            #Delete Function----------------------------------------------------------------------
          batch_requests_delete = []

          for r in sorted(idx_delete, reverse=True):
               batch_requests_delete.append({
                    "deleteDimension": {
                         "range": {
                              "sheetId": origin_sheet.id,
                              "dimension": "ROWS",
                              "startIndex": r,
                              "endIndex": r+1
                         }
                    }
               })

          origin_sheet.spreadsheet.batch_update({"requests": batch_requests_delete})

     return 'Success'

def ResetPassword(newpassword): #Reset password verification and overwrite in database
     idx = df_user.index[df_user['User'] == st.session_state['user_key']][0]
     user_sheet.update_cell(idx+2,3,newpassword)

@st.dialog("Ganti Password", width='small')          #Dialog for change password
def ChangePassword():
     current_password = st.text_input("Password Saat Ini", type="password", key="current_password", placeholder="Password Saat Ini", autocomplete='off')
     new_password = st.text_input("Password Baru", type="password", key="new_password", placeholder="Password Baru", autocomplete='off')
     new_password_confirm = st.text_input("Password Baru", type="password", key="new_password_confirm", placeholder="Password Baru", autocomplete='off')

     current_password_check = df_user.loc[df_user['User'] == st.session_state['user_key'], 'Password'].iloc[0]
     
     if new_password_confirm != '':
          if new_password != new_password_confirm:
               st.error('Password baru tidak sama. Mohon untuk periksa kembali.')

     if st.button("Ganti Password", type='primary', width='stretch'):
          if current_password == '' or new_password == '' or new_password_confirm == '':
               st.warning("Mohon untuk mengisi semua kolom")
          elif current_password != current_password_check:
               st.error("Password lama salah. Mohon untuk periksa kembali.")
          else:
               ResetPassword(new_password)
               st.success("Password berhasil diganti. Mohon untuk login kembali.")
               time.sleep(3)
               st.session_state['role'] = None
               st.session_state['user_key'] = None
               st.session_state['profile_name'] = None
               st.rerun()
     
@st.dialog('Konfirmasi Perubahan Data', width='large')
def ConfirmEditData(origin_df, edited_df, origin_sheet):
     st.write("This is confirmation dialog")
     
     st.dataframe(
          edited_df,
          column_config={
               "Hapus": st.column_config.CheckboxColumn(
                    "Hapus",
                    help="Centang untuk menghapus data",
                    default=False,
                    width='small',
                    pinned=True
               ),
               "Edit": st.column_config.CheckboxColumn(
                    "Edit",
                    help="Centang untuk mengedit data",
                    default=False,
                    width='small',
                    pinned=True
               ),
          },
          hide_index=True,
          column_order=['Edit', 'Hapus','Cabang Pengirim', 'Cabang Tujuan', 'No. Kontrak', 'No. Custody', 'Jenis Pengiriman', 'No. AWB', 'Tanggal Pengiriman', 'Isi Paket Pengiriman', 'Keterangan']
     )
     
     if st.button(":material/save: Simpan Perubahan", type='primary', width='stretch'):
          status = EditDeleteDataRow(origin_df, edited_df, origin_sheet)
          if status == 'Success':
               st.success("Perubahan berhasil disimpan")
               RefreshData()
               st.rerun()
          else:
               st.error("Terjadi kesalahan saat menyimpan perubahan")

#End of function
# ------------- Streamlit App ----------------

def show():

     st.markdown("""
         <style>
          header[data-testid="stHeader"] {
                    background: rgba(0,0,0,0); /* fully transparent */
               }
         </style>
     """, unsafe_allow_html=True)
     
     st.set_page_config(page_title="[TEST SITE] OneTrack", page_icon=":fire:", layout="wide", initial_sidebar_state='auto', menu_items={'Get Help': 'https://www.extremelycoolapp.com/help', 'Report a bug': "https://www.extremelycoolapp.com/bug", 'About':'TESTING'})
     #st.logo('https://www.bfi.co.id/wp-content/uploads/2021/09/bfi-logo.png')
     
     with st.sidebar:

          #img_col1, img_col2, img_col3 = st.columns([1,10,1], border=False, gap=None)

          #img_col2.image('ProfilePicture.png', use_container_width='auto', width=150)

          st.markdown(
              f"""
              <div style="text-align: center;">
                  <h3>Hello,<br>{st.session_state['profile_name']}</h3>
              </div>
              """,
              unsafe_allow_html=True
          )
          
          selected4 = option_menu(None, ["Home", "Input Data", "Edit Data", "View Data"], 
               icons=['house', 'upload', 'pencil-square', "list-task"], key='menu')

          if st.button("Ganti Password", type='secondary', width='stretch', icon=':material/manage_accounts:'):
               ChangePassword()
          
          if st.button("Logout", type='primary', width='stretch', icon=':material/logout:'):
               st.session_state['role'] = None
               st.session_state['user_key'] = None
               st.session_state['profile_name'] = None
               st.rerun()

          col_refresh1, col_refresh2 = st.columns([9,1], border=False, gap=None, vertical_alignment='center')
          
          if col_refresh2.button(":material/refresh:", type='tertiary', width='stretch', help="Refresh Data"):
               RefreshData()

          last_api_update = pd.to_datetime(df_data['track_update_at'], errors='coerce').max()
          last_api_update = last_api_update.strftime('%Y-%m-%d %H:%M:%S')

          col_refresh1.markdown(
              f"""
              <div style="text-align: center;">
                  <p>Last API Refresh:<br>{last_api_update}</p>
              </div>
              """,
              unsafe_allow_html=True
          )
     
     #st.title('This is the user page')

     if st.session_state['menu'] == 'Home' or st.session_state['menu'] == None:
          container1 = st.container(horizontal=True, border=False, horizontal_alignment='left')
          container2 = st.container(horizontal=True, border=False, horizontal_alignment='center')
          container3 = st.container(horizontal=True, border=False, horizontal_alignment='center')
          container4 = st.container(horizontal=True, border=False, horizontal_alignment='left')
          container5 = st.container(horizontal=True, border=False, horizontal_alignment='center')

          filter_col1, filter_col2 = container1.columns([1,5.5], border=False, gap='small', vertical_alignment='center')
          mat_col1, mat_col2, mat_col3 = container2.columns([1,1,1], border=False, gap='small', vertical_alignment='top')
          
          #Data is here
          branch_name = st.session_state['profile_name']

          now = pd.Timestamp.today().to_period("M")
          min_1_month = now - 1

          df_data['send_date_opc'] = pd.to_datetime(df_data['send_date_opc'])
          send_data = df_data[df_data['sent_from'] == branch_name]
          
          #Data based on agreement_no and sent_from
          send_data_ctr = send_data.groupby(send_data['send_date_opc'].dt.to_period("M")).size().reset_index(name='count')

          period_list_ctr = send_data_ctr['send_date_opc'].values.tolist()

          if now in period_list_ctr:
               now_value_ctr = send_data_ctr[send_data_ctr['send_date_opc'] == now]['count'].values[0]
          else:
               now_value_ctr = 0

          if min_1_month in period_list_ctr:
               before_value_ctr = send_data_ctr[send_data_ctr['send_date_opc'] == min_1_month]['count'].values[0]
          else:
               before_value_ctr = 0

          gap_ctr = now_value_ctr - before_value_ctr

          #Data based on awb_no and sent_from
          send_data_awb = send_data[send_data['awb_no'] != '']
          send_data_awb['send_date_opc'] = pd.to_datetime(send_data_awb['send_date_opc']).dt.to_period("M")
          send_data_awb = send_data_awb.groupby(['awb_no', 'send_date_opc']).size().reset_index(name='count')
          send_data_awb = send_data_awb.groupby('send_date_opc').size().reset_index(name='count')

          period_list_awb = send_data_awb['send_date_opc'].values.tolist()

          if now in period_list_awb:
               now_value_awb = send_data_awb[send_data_awb['send_date_opc'] == now]['count'].values[0]
          else:
               now_value_awb = 0

          if min_1_month in period_list_awb:
               before_value_awb = send_data_awb[send_data_awb['send_date_opc'] == min_1_month]['count'].values[0]
          else:
               before_value_awb = 0

          gap_awb = now_value_awb - before_value_awb

          #Data based on delivery_status and sent_from (ON PROCESS)
          send_data2 = send_data[send_data['delivery_status'] == 'ON PROCESS']
          send_data2['send_date_opc'] = pd.to_datetime(send_data2['send_date_opc']).dt.to_period("M")

          #Data based on agreement_no
          send_data_ctr2 = send_data2.groupby('send_date_opc').size().reset_index(name='count')
          period_list_ctr2 = send_data_ctr2['send_date_opc'].values.tolist()

          if now in period_list_ctr2:
               now_value_ctr2 = send_data_ctr2[send_data_ctr2['send_date_opc'] == now]['count'].values[0]
          else:
               now_value_ctr2 = 0
          
          #Data based on AWB
          send_data_awb2 = send_data2[send_data2['awb_no'] != '']
          send_data_awb2 = send_data_awb2.groupby(['awb_no', 'send_date_opc']).size().reset_index(name='count')
          send_data_awb2 = send_data_awb2.groupby('send_date_opc').size().reset_index(name='count')
          period_list_awb2 = send_data_awb2['send_date_opc'].values.tolist()
          
          if now in period_list_awb2:
               now_value_awb2 = send_data_awb2[send_data_awb2['send_date_opc'] == now]['count'].values[0]
          else:
               now_value_awb2 = 0

          #Data based on delivery_status and sent_to (ON PROCESS)
          send_data3 = df_data[df_data['sent_to'] == branch_name]
          send_data3 = send_data3[send_data['delivery_status'] == 'ON PROCESS']
          send_data3['send_date_opc'] = pd.to_datetime(send_data3['send_date_opc']).dt.to_period("M")

          #Data based on agreement_no
          send_data_ctr3 = send_data3.groupby('send_date_opc').size().reset_index(name='count')
          period_list_ctr3 = send_data_ctr3['send_date_opc'].values.tolist()

          if now in period_list_ctr3:
               now_value_ctr3 = period_list_ctr3[period_list_ctr3['send_date_opc'] == now]['count'].values[0]
          else:
               now_value_ctr3 = 0

          #Data based on AWB
          send_data_awb3 = send_data3[send_data3['awb_no'] != '']
          send_data_awb3 = send_data_awb3.groupby(['awb_no', 'send_date_opc']).size().reset_index(name='count')
          send_data_awb3 = send_data_awb3.groupby('send_date_opc').size().reset_index(name='count')
          period_list_awb3 = send_data_awb3['send_date_opc'].values.tolist()

          if now in period_list_awb3:
               now_value_awb3 = send_data_awb3[send_data_awb3['send_date_opc'] == now]['count'].values[0]
          else:
               now_value_awb3 = 0
          
          #Filter Metric
          filter_col1.markdown("**Tampilkan Sebagai:**")
          filter_awb_ctr = filter_col2.selectbox(
               "Tampilkan Berdasarkan",
               ["AWB", "Kontrak"],
               key="filter_awb_ctr",
               width=150,
               index=0,
               label_visibility='collapsed'
          )

          if filter_awb_ctr == 'Kontrak':
               now_value_metric1 = now_value_ctr
               gap_metric1 = gap_ctr
               now_value_metric2 = now_value_ctr2
               now_value_metric3 = now_value_ctr3
          else:
               now_value_metric1 = now_value_awb
               gap_metric1 = gap_awb
               now_value_metric2 = now_value_awb2
               now_value_metric3 = now_value_awb3
          
          mat_col1.metric(label="Total Pengiriman Bulan Ini", value=int(now_value_metric1), delta=int(gap_metric1), border=False)     #METRIC TOTAL PENGIRIMAN
          mat_col2.metric(label="Total Pengiriman Dalam Proses", value=int(now_value_metric2), border=False)     #METRIC PAKET ON PROCESS
          mat_col3.metric(label="Total Paket yang Akan Diterima", value=int(now_value_metric3), border=False)     #METRIC PAKET YANG AKAN DITERIMA

          container3.divider()

          min_date_line_chart = df_data['send_date_opc'].min()
          min_date_line_chart = pd.to_datetime(min_date_line_chart).date()
          
          filter_interval_line_chart = container4.selectbox(
               "Tampilkan Berdasarkan",
               ["Harian", "Bulanan"],
               key="filter_interval",
               width=150,
               index=0
          )

          filter_date_range_line_chart = container4.date_input(
               "Tanggal Pengiriman",
               key="filter_date_range",
               format="YYYY-MM-DD",
               value=[min_date_line_chart,'today'],
               min_value=min_date_line_chart,
               max_value='today',
               width=250
          )
          try:
               data_line_chart = df_data[df_data['sent_from'] == branch_name]
               data_line_chart['send_date_opc'] = pd.to_datetime(data_line_chart['send_date_opc']).dt.date

               if filter_awb_ctr == 'AWB':
                    filtered_data_line_chart = data_line_chart[data_line_chart['awb_no'] != '']
                    filtered_data_line_chart = filtered_data_line_chart[(data_line_chart['send_date_opc'] >= filter_date_range_line_chart[0]) & (data_line_chart['send_date_opc'] <= filter_date_range_line_chart[1])]
                    full_range_date = pd.date_range(start=filter_date_range_line_chart[0], end=filter_date_range_line_chart[1], freq='D')

                    if filter_interval_line_chart == 'Bulanan':
                         filtered_data_line_chart['send_date_opc'] = pd.to_datetime(filtered_data_line_chart['send_date_opc']).dt.to_period("M")
                         full_range_date = pd.date_range(start=filter_date_range_line_chart[0], end=filter_date_range_line_chart[1], freq='D').to_period("M").unique()

                    filtered_data_line_chart = filtered_data_line_chart[['send_date_opc', 'awb_no']].drop_duplicates()
                    filtered_data_line_chart = filtered_data_line_chart.groupby(['send_date_opc']).size()
                    filtered_data_line_chart = filtered_data_line_chart.reindex(full_range_date, fill_value=0)
                    filtered_data_line_chart = filtered_data_line_chart.reset_index().rename(columns={'index': 'date'})
                    filtered_data_line_chart_long = filtered_data_line_chart.melt(id_vars=['date'], value_name='count')
               
                    chart = (
                         alt.Chart(filtered_data_line_chart_long).mark_line(color="#8c8cff")
                         .mark_line(point=True)
                         .encode(
                              x="date:T",          # date on x-axis
                              y="count:Q",         # counts on y-axis
                              tooltip=["date:T", "count:Q"]
                         )
                         .properties(width="container", height=400)
                         .interactive()
                    )
          
               if filter_awb_ctr == 'Kontrak':
                    filtered_data_line_chart = data_line_chart[(data_line_chart['send_date_opc'] >= filter_date_range_line_chart[0]) & (data_line_chart['send_date_opc'] <= filter_date_range_line_chart[1])]
                    full_range_date = pd.date_range(start=filter_date_range_line_chart[0], end=filter_date_range_line_chart[1], freq='D')

                    if filter_interval_line_chart == 'Bulanan':
                         filtered_data_line_chart['send_date_opc'] = pd.to_datetime(filtered_data_line_chart['send_date_opc']).dt.to_period("M")
                         full_range_date = pd.date_range(start=filter_date_range_line_chart[0], end=filter_date_range_line_chart[1], freq='D').to_period("M").unique()

                    filtered_data_line_chart = filtered_data_line_chart[['send_date_opc', 'send_type']]
                    filtered_data_line_chart = filtered_data_line_chart.groupby(['send_date_opc', 'send_type']).size().unstack(fill_value=0)
                    filtered_data_line_chart = filtered_data_line_chart.reindex(full_range_date, fill_value=0)
                    filtered_data_line_chart = filtered_data_line_chart.reset_index().rename(columns={'index': 'date',})
                    filtered_data_line_chart_long = filtered_data_line_chart.melt(id_vars=['date'], var_name='send_type', value_name='count').rename(columns={'send_type': 'Tipe Pengiriman'})
          
                    chart = (
                         alt.Chart(filtered_data_line_chart_long)
                         .mark_line(point=True)
                         .encode(
                              x="date:T",          # date on x-axis
                              y="count:Q",         # counts on y-axis
                              color=alt.Color("Tipe Pengiriman:N", scale=alt.Scale(domain=["EKSPEDISI", "MESSENGER"], range=["#8c8cff", "#ff3131"])), # separate line per send_type
                              tooltip=["date:T", "Tipe Pengiriman:N", "count:Q"]
                         )
                         .properties(width="container", height=400)
                         .interactive()
                    )

               st.altair_chart(chart, use_container_width=True)
          
          except Exception:
               st.stop()
          
     if st.session_state['menu'] == 'Input Data':

          if 'clearcolumn' not in st.session_state:
               st.session_state['clearcolumn'] = False

          if 'uploadcount' not in st.session_state:
               st.session_state['uploadcount'] = 0

          if st.session_state['clearcolumn']:
               #st.session_state.send_from = None
               st.session_state.send_to = None
               st.session_state.agreement_no = None
               st.session_state.no_custody = None
               st.session_state.send_type = None
               st.session_state.awb_no = None
               #st.session_state.send_date = None
               st.session_state.send_doc = None
               st.session_state.desc = None
               st.session_state['clearcolumn'] = False
          
          single_input, batch_input = st.tabs(['Single Input', 'Batch Input'])

          with single_input:
          
               col1, col2 = st.columns([1,1], border=False, gap='small', vertical_alignment='center')
               col3, col4 = st.columns([1,1], border=False, gap='small', vertical_alignment='center')
               col5, col6 = st.columns([1,1], border=False, gap='small', vertical_alignment='center')
               col7, col8 = st.columns([1,1], border=False, gap='small', vertical_alignment='top')
               cont1 = st.container(horizontal=True, border=False, horizontal_alignment='center')
               container1 = st.container(horizontal=True, border=False, horizontal_alignment='center')

               branch_list = df_user['Name'][:245].tolist()
               if st.session_state['profile_name'] in branch_list:
                    branch_idx = branch_list.index(st.session_state['profile_name'])
               else:
                    branch_idx = None
               
               send_from = col1.selectbox(
                    'Cabang Pengirim*',
                    branch_list,
                    index=branch_idx,
                    placeholder="Pilih atau tambahkan cabang",
                    accept_new_options=True,
                    key = 'send_from',
               )
               send_to = col2.selectbox(
                    'Cabang Tujuan*',
                    branch_list,
                    index=None,
                    placeholder="Pilih atau tambahkan cabang",
                    accept_new_options=True,
                    key = 'send_to'
               )
               agreement_no = col3.text_input("No. Kontrak*", key="agreement_no", placeholder="No. Kontrak", autocomplete='off')
               no_custody = col4.text_input("No. Custody", key="no_custody", placeholder="No. Custody", autocomplete='off')
               send_type = col5.selectbox(
                    'Jenis Pengiriman*',
                    ['EKSPEDISI', 'MESSENGER'],
                    index=None,
                    placeholder="Pilih jenis pengiriman",
                    key = 'send_type'
               )
     
               if send_type == 'EKSPEDISI':
                    ekspedisi_flag = False
               else:
                    ekspedisi_flag = True
               
               awb_no = col6.text_input("No. AWB*", key="awb_no", placeholder="No. AWB", autocomplete='off', disabled=ekspedisi_flag, help='No. AWB wajib diisi jika jenis pengiriman adalah "EKSPEDISI"')
               send_date = col7.date_input("Tanggal Pengiriman*", key="send_date", format="YYYY-MM-DD", value='today', min_value='2025-01-01' ,max_value='today')
               send_doc = col8.selectbox(
                    'Dokumen yang Dikirim*',
                    ['ASSET', 'PPK', 'ASSET & PPK', 'BAST RELEASE', 'OTHERS'],
                    index=None,
                    placeholder="Pilih dokumen yang dikirim",
                    key = 'send_doc',
                    help = '"ASSET" mengacu pada BPKB, Invoice, SHGB, dan dokumen lainnya yang berkaitan dengan asset yang dikirimkan. Jika "OTHERS" dipilih, mohon untuk mengisi keterangan dokumen yang dikirimkan pada kolom "Keterangan" di bawah'
               )
               desc = cont1.text_area("Keterangan*", key="desc", placeholder="Keterangan", height=100)
               
               if container1.button("Submit", type='primary', width='stretch', key='submit_single'):
                    if send_type == 'Ekspedisi':
                         if send_from == '' or send_to == '' or agreement_no == '' or awb_no == '' or send_date == '' or send_doc == '' or desc == '':
                              st.error("Mohon untuk mengisi semua kolom")
                         else:
                              AddDataSingle(data_sheet, send_from, send_to, agreement_no, no_custody, send_type, awb_no, send_date, send_doc, desc)
                              st.success("Data berhasil disimpan")
                              time.sleep(1)
                              RefreshData()
                              st.session_state['clearcolumn'] = True
                              st.rerun()
                    else:
                         if send_from == '' or send_to == '' or agreement_no == '' or send_type == '' or send_date == '' or send_doc == '' or desc == '':
                              st.error("Mohon untuk mengisi semua kolom")
                         else:
                              AddDataSingle(data_sheet, send_from, send_to, agreement_no, no_custody, send_type, awb_no, send_date, send_doc, desc)
                              st.success("Data berhasil disimpan")
                              time.sleep(1)
                              RefreshData()
                              st.session_state['clearcolumn'] = True
                              st.rerun()
          with batch_input:
               
               st.session_state['uploaded_file'] = None
               
               st.write('Gunakan template di bawah ini untuk menginput data secara batch')
               
               with open("Template Report Pengiriman.xlsx", "rb") as file:
                    st.download_button(
                         label="Download Template Report",
                         data=file,
                         file_name="Template Report Pengiriman.xlsx",
                         mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                         on_click='ignore',
                         icon=':material/download:',
                         type='secondary',
                         width='stretch'
                   )
               
               #st.write('*) Pastikan template diisi dengan benar sebelum diupload agar data tersimpan dengan benar')
               st.divider()
               
               uploaded_file = st.file_uploader("Choose a file", type=['csv', 'xlsx'], accept_multiple_files=False, key=f"uploader_{st.session_state.uploadcount}")
               if uploaded_file is not None:
                    st.write('Preview '+ uploaded_file.name)
                    df = pd.read_excel(uploaded_file)
                    df = df.iloc[:, :-1]
                    st.dataframe(df.head(10))
                    
                    if st.button("Submit Data", type='primary', width='stretch', key='submit_batch'):
                         AddDataBatch(data_sheet, df)
                         st.success("Data berhasil disimpan")
                         RefreshData()
                         time.sleep(5)
                         st.session_state.uploadcount += 1
                         st.rerun()
                    
     if st.session_state['menu'] == 'Edit Data':

          button_container = st.container(horizontal=True, border=False, horizontal_alignment='left')

          df_edit_data = df_data[df_data['user_create']==st.session_state['user_key']]
          df_edit_data['send_date_opc'] = pd.to_datetime(df_edit_data['send_date_opc'], format='%Y-%m-%d %H:%M:%S')
          df_edit_data = df_edit_data[['sent_from', 'sent_to', 'agreement_no', 'no_custody', 'send_type', 'awb_no', 'send_date_opc', 'send_doc', 'desc', 'row_uid']]
          df_edit_data = df_edit_data.rename(columns={'sent_from': 'Cabang Pengirim', 'sent_to': 'Cabang Tujuan', 'agreement_no': 'No. Kontrak', 'no_custody': 'No. Custody','send_type': 'Jenis Pengiriman', 
                                                  'awb_no': 'No. AWB', 'send_date_opc': 'Tanggal Pengiriman', 'send_doc': 'Isi Paket', 'desc': 'Keterangan'}
                                        )
          df_edit_data['Hapus'] = False
          df_edit_data['Edit'] = False
          df_edit_data = df_edit_data.set_index('row_uid')

          if 'edit_data' not in st.session_state:
               st.session_state['edit_data'] = df_edit_data.copy()
          else:
               st.session_state['edit_data'] = df_edit_data.copy()

          if 'editorcount' not in st.session_state:
               st.session_state.editorcount = 0
          
          edited_data = st.data_editor(
               st.session_state['edit_data'],
               hide_index=True,
               column_order=['Edit', 'Hapus','Cabang Pengirim', 'Cabang Tujuan', 'No. Kontrak', 'No. Custody', 'Jenis Pengiriman', 'No. AWB', 'Tanggal Pengiriman', 'Isi Paket Pengiriman', 'Keterangan'],
               column_config={
                    "Hapus": st.column_config.CheckboxColumn(
                         "Hapus",
                         help="Centang untuk menghapus data",
                         default=False,
                         width='small',
                         pinned=True
                    ),
                    "Edit": st.column_config.CheckboxColumn(
                         "Edit",
                         help="Centang untuk mengedit data",
                         default=False,
                         width='small',
                         pinned=True
                    ),
                    'Jenis Pengiriman': st.column_config.SelectboxColumn(
                         "Jenis Pengiriman",
                         options=['EKSPEDISI', 'MESSENGER'],
                         required=True
                    ),
                    'Tanggal Pengiriman': st.column_config.DateColumn(
                         "Tanggal Pengiriman",
                         format="YYYY-MM-DD",
                         required=True
                    ),
                    'Isi Paket Pengiriman': st.column_config.SelectboxColumn(
                         "Isi Paket Pengiriman",
                         options=['ASSET', 'PPK', 'ASSET & PPK', 'BAST RELEASE', 'OTHERS'],
                         required=True
                    )
               },
               key=f"editor{st.session_state.editorcount}"
          )

          edited_df = edited_data[(edited_data['Hapus'] == True) | (edited_data['Edit'] == True)]
          
          if button_container.button(":material/save: Simpan Perubahan", type='primary', width='content', key='submit_edit'):
               ConfirmEditData(df_data, edited_df, data_sheet)

          if button_container.button(":material/delete: Reset Perubahan", type='secondary', width='content', key='reset_edit'):
               st.session_state.editorcount += 1
               st.rerun()
          
     if st.session_state['menu'] == 'View Data':
          
          filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([1,1,1,1], border=False, gap= 'small', vertical_alignment='center')
          filter_col5, filter_col6 = st.columns([1,1], border=False, gap= 'small', vertical_alignment='center')
          filter_col7, filter_col8 = st.columns([1,1], border=False, gap= 'medium', vertical_alignment='center')

          branch_list = df_user['Name'][:245].tolist()
          if st.session_state['profile_name'] in branch_list:
               branch_idx = st.session_state['profile_name']
          else:
               branch_idx = None
          
          search_agreement = filter_col1.text_input("No. Kontrak", key="search_agreement", placeholder="No. Kontrak", autocomplete='off')

          search_awb = filter_col2.text_input("No. AWB", key="search_awb", placeholder="No. AWB", autocomplete='off')
          
          search_origin = filter_col5.multiselect(
               'Cabang Pengirim',
               branch_list,
               key = 'search_origin',
               placeholder="Pilih cabang pengirim",
               default=branch_idx
          )

          search_destination = filter_col6.multiselect(
               'Cabang Tujuan',
               branch_list,
               key = 'search_destination',
               placeholder="Pilih cabang tujuan",
               default=None
          )

          search_type = filter_col4.pills(
               'Jenis Pengiriman',
               ['EKSPEDISI', 'MESSENGER'],
               key = 'search_type',
               selection_mode='multi',
               default=['EKSPEDISI', 'MESSENGER'],
               width='content'
          )

          search_send_doc = filter_col8.pills(
               'Isi Paket Pengiriman',
               ['ASSET', 'PPK', 'ASSET & PPK', 'BAST RELEASE', 'OTHERS'],
               key = 'search_send_doc',
               selection_mode='multi',
               default=['ASSET', 'PPK', 'ASSET & PPK', 'BAST RELEASE', 'OTHERS'],
               width='content'
          )

          search_jne_status = filter_col7.multiselect(
               'Status Pengiriman',
               ['ON PROCESS', 'DELIVERED', 'AWB NOT FOUND', 'RETURN TO SHIPPER'],
               key = 'search_jne_status',
               default=['ON PROCESS'],
               placeholder="Pilih status pengiriman"
          )
          
          today_default = datetime.date.today()
          previous_month = today_default.month - 1 if today_default.month > 1 else 12
          previous_year = today_default.year if today_default.month > 1 else today_default.year - 1
          start_default = datetime.date(previous_year, previous_month, today_default.day)
          default_range = [start_default,today_default]

          search_date_range = filter_col3.date_input("Tanggal Pengiriman", key="search_date_range", format="YYYY-MM-DD", value=default_range, min_value='2025-01-01' ,max_value='today')
          
          st.divider()

          try:
               data_view, isempty = ViewData(df_data, search_agreement, search_awb, search_origin, search_destination, search_type, search_send_doc, search_date_range, search_jne_status)

               if isempty:
                    st.warning('Data tidak ditemukan')
               else:
                    st.dataframe(
                         data_view.style.format({
                              "Tanggal Pengiriman": lambda t: t.strftime("%Y-%m-%d")
                         }),
                         hide_index=True,
                         on_select='ignore',
                         height=550,
                         width='stretch',
                         column_config={
                              "No. Kontrak": st.column_config.TextColumn(
                                   "No. Kontrak",
                                   pinned=True
                              ),
                              "No. AWB": st.column_config.TextColumn(
                                   "No. AWB",
                                   pinned=True
                              ),
                              "Link Tracking": st.column_config.LinkColumn(
                                   "Tracking",
                                   help="Klik untuk melihat tracking pengiriman",
                                   display_text=":material/open_in_new:",
                                   width='small'
                              )
                         },
                         column_order=['Cabang Pengirim','Cabang Tujuan','No. Kontrak','Jenis Pengiriman','No. AWB','Tanggal Pengiriman','Tanggal Status Terakhir','Status Terakhir','Isi Paket Pengiriman','Keterangan','Link Tracking',]
                    )

          except Exception:
               st.stop()

     #st.write(st.session_state)