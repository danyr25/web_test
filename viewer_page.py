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

     user_sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1mUbmJGAEABhCqjfH7F2Jzb5JkhMSfucl2uVTiLV7Jls/edit?gid=0#gid=0').sheet1
     user_table = user_sheet.get_all_values()
     df_user = pd.DataFrame(user_table[1:], columns=user_table[0])

     data_sheet = data_sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/10BlL266KaE2zQ3lq_4mMlxVEA__gaDGHI0_hHdILlCo/edit?gid=0#gid=0').sheet1
     data_table = data_sheet.get_all_values()
     df_data = pd.DataFrame(data_table[1:], columns=data_table[0])

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

@st.dialog("Ganti Password", width='small')          #Dialog for change password
def ChangePassword():
     st.write("This is change password dialog")


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

          selected4 = option_menu(None, ["Home", "View Data"], 
               icons=['house', "list-task"], key='menu')

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
          mat_col1, mat_col2 = st.columns([1,2], border=False, gap='small', vertical_alignment='center')
          container1 = mat_col1.container(horizontal=True, border=False, horizontal_alignment='center')
          container2 = mat_col1.container(horizontal=True, border=False, horizontal_alignment='center')
          container3 = mat_col1.container(horizontal=True, border=False, horizontal_alignment='center')
          container4 = mat_col1.container(horizontal=True, border=False, horizontal_alignment='center')

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
          filter_awb_ctr = container1.segmented_control(
               "Hitung Berdasarkan",
               ["AWB", "Kontrak"],
               key="filter_awb_ctr",
               width='stretch',
               selection_mode='single',
               default='AWB'
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

          container2.metric(label="Total Pengiriman Bulan Ini", value=int(now_value_metric1), delta=int(gap_metric1), border=True)     #METRIC TOTAL PENGIRIMAN
          container3.metric(label="Total Pengiriman Dalam Proses", value=int(now_value_metric2), border=True)     #METRIC PAKET ON PROCESS
          container4.metric(label="Total Paket yang Akan Diterima", value=int(now_value_metric3), border=True)     #METRIC PAKET YANG AKAN DITERIMA

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