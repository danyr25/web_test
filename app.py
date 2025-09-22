import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import pandas as pd
import random, string
import admin_page, user_page, viewer_page
import time

#Connect spreadsheet

# Define the scope (permissions) and authenticate
sa_info = json.loads(st.secrets["GCREDS"])
sa_info["private_key"] = sa_info["private_key"].replace("\\n", "\n")
creds = Credentials.from_service_account_info(
         sa_info,
         scopes=[
                  "https://spreadsheets.google.com/feeds",
                  "https://www.googleapis.com/auth/drive"
         ]
)
client = gspread.authorize(creds)

#Open all table then convert to dataframe
user_sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1mUbmJGAEABhCqjfH7F2Jzb5JkhMSfucl2uVTiLV7Jls/edit?gid=0#gid=0').sheet1
user_table = user_sheet.get_all_values()
df_user = pd.DataFrame(user_table[1:], columns=user_table[0])

#All function goes here

def GenerateToken(length=6):          #Generate random token (for reset password)
       return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def NewUser(name, usr, password):     #Create new user
     name_check = df_user["Name"] == name
     i, j = UserCheck(usr)

     if name_check.any():
          idx = df_user.index[df_user['Name'] == name][0]
          cells_update = [
               gspread.Cell(idx+2, 2, usr),
               gspread.Cell(idx+2, 3, password),
               gspread.Cell(idx+2, 4, 'User')
          ]
          user_sheet.update_cells(cells_update)
          return 'Account Created'
     else:
          user_sheet.append_row([name, usr, password, 'User'])
          return 'Account Created'

def TokenReq(usr):                    #Create new token in database
     i, j = UserCheck(usr)

     if not i:
          return 'Invalid Username', None
     else:
          idx = df_user.index[df_user['User'] == j][0]
          token = GenerateToken()
          user_sheet.update_cell(idx+2,5,token)
          return 'Token Requested', token

def ResetPassword(usr, token, newpassword, sys_token): #Reset password verification and overwrite in database
     i, j = UserCheck(usr)

     if not i:
          return 'Username already exist'

     idx = df_user.index[df_user['User'] == j][0]
     token_data = df_user.loc[df_user['User'] == j, 'Reset Token'].iloc[0]

     if token == token_data:
          user_sheet.update_cell(idx+2,3,newpassword)
          return 'Success'
     elif token == sys_token:
          user_sheet.update_cell(idx+2,3,newpassword)
          return 'Success'
     else:
          return 'Invalid Token'

def UserCheck(usr):                 #Check if user already created
     user_check = df_user["User"] == usr
     return user_check.any(), usr

def LoginCheck(usr,password):       #Login and assign give role of account
     i, j = UserCheck(usr)

     if not i:
          return False, False, None

     pass_check = df_user.loc[df_user['User'] == j, 'Password'].iloc[0]
     role_check = df_user.loc[df_user['User'] == j, 'Role'].iloc[0]

     if pass_check == password:
          return True, True, role_check
     else:
          return True, False, None

@st.dialog("Sign Up", width='small')              #Dialog for sign up
def SignUp():
     name_su = st.selectbox(
          'Select your name',
          df_user['Name'][:245].tolist(),
          index=None,
          placeholder="Select your name or add a new one",
          accept_new_options=True
     )
     user_su = st.text_input("Username", key="new_username", placeholder="Username", autocomplete='off')
     pass_su = st.text_input("Password", type="password", key="new_password", placeholder="Password", autocomplete='off')
     repass_su = st.text_input("Confirm Password", type="password", key="new_password_confirm", placeholder="Re-enter Your Password", autocomplete='off')
     
     if repass_su != '':
          if pass_su != repass_su:
               st.error('Password doesn\'t match. Please re-check it.')

     if st.button("Sign Up", type='primary', width='stretch'):
          i, j = UserCheck(user_su)

          if name_su == None or user_su == '' or pass_su == '' or repass_su == '':
               st.warning("Please fill all fields")
          elif i:
               st.error("Username already exist")
          else:
               check_status = NewUser(name_su, user_su, pass_su)
               st.success(check_status)
               time.sleep(1)
               st.rerun()

@st.dialog("Forgot Password", width='small')          #Dialog for forgot password
def ForgotPassword():
     user_fp = st.text_input("Username", key="fp_username", placeholder="Username", autocomplete='off')

     token_req_left, token_req_right = st.columns([2.25,1], border=False, gap='small', vertical_alignment='bottom')
     
     token_fp = token_req_left.text_input("Token", key="fp_token", placeholder="Token", autocomplete='off')
     
     if token_req_right.button("Request Token", type='secondary', width='stretch', help='Klik untuk mendapatkan token, lalu email ke tim Centro Custody HO (dany.rahman@bfi.co.id)'):
          if user_fp == '':
               st.toast("Please fill username first")
          else:
               status, st.session_state.new_token = TokenReq(user_fp)
               st.toast(status)
          
     pass_fp = st.text_input("Password", type="password", key="fp_password", placeholder="Enter your new password", autocomplete='off')
     repass_fp = st.text_input("Confirm Password", type="password", key="fp_password_confirm", placeholder="Re-enter Your Password", autocomplete='off')
     
     if repass_fp != '':
          if pass_fp != repass_fp:
               st.error('Password doesn\'t match. Please re-check it.')
     
     if st.button("Reset Password", type='primary', width='stretch'):
          if user_fp == '' or token_fp == '' or pass_fp == '' or repass_fp == '':
               st.warning("Please fill all fields")
          else:
               check_status = ResetPassword(user_fp, token_fp, pass_fp, st.session_state.new_token)
               if check_status == 'Success':
                    st.success("Password Reset Successful. Please login with your new password")
                    st.session_state.new_token = None
                    time.sleep(3)
                    st.rerun()
               else:
                    st.error(check_status)

#End of function

# ------------- Streamlit App ----------------

#Set session state
if 'role' not in st.session_state:
     st.session_state['role'] = None
     st.session_state['user_key'] = None
     st.session_state['profile_name'] = None

if 'new_token' not in st.session_state:
     st.session_state['new_token'] = None

if st.session_state['role'] == None: #Redirect to login page
     
     #Set page config & title
     st.set_page_config(page_title="[TEST SITE] OneTrack", page_icon=":fire:", layout="centered")

     st.markdown(
         """
         <style>
         body {
               background-color: #f9fafb;
         }
         .login-box {
               max-width: 360px;
               margin: 5% auto;
               padding: 2rem;
               background: white;
               border-radius: 1rem;
               box-shadow: 0px 4px 12px rgba(0,0,0,0.1);
         }
         .login-title {
               font-size: 1.5rem;
               font-weight: 700;
               margin-bottom: 1.5rem;
               text-align: left;
         }
         .stTextInput>div>div>input {
               border-radius: 0.5rem;
         }
         .stButton>button {
               background-color: #2563EB;
               color: white;
               border-radius: 0.5rem;
               padding: 0.5rem 1rem;
               font-weight: 600;
               border: none;
               width: 100%;
         }
         .stButton>button:hover {
               background-color: #1e4ed8;
         }
         .links {
               text-align: center;
               font-size: 0.9rem;
               margin-top: 1rem;
               color: #374151;
         }
         .links a {
               color: #2563EB;
               text-decoration: none;
               font-weight: 600;
         }
          .stMarkdown h1 a, .stMarkdown h2 a, .stMarkdown h3 a,
          .stMarkdown h4 a, .stMarkdown h5 a, .stMarkdown h6 a {
               display: none;
                  }
         """,
         unsafe_allow_html=True,
     )
     st.markdown(
         f"""
         <div style="text-align: center;">
             <h1>[TEST SITE]</h1>
             <h3>Login Page</h3>
         </div>
         """,
         unsafe_allow_html=True
     )
     
     #middlecol_title.title('API BFI X JNE', anchor=False)

     #leftcol_subtitle, middlecol_subtitle, rightcol_subtitle = st.columns([1,1.1,1], border=False, gap=None)

     #middlecol_subtitle.header('Login Page', anchor=False)
     
     #Login Form
     user_input_login = st.text_input("Username", key="ulogin", placeholder="Username")
     password_input_login = st.text_input("Password", type="password", key="plogin", placeholder="Password", autocomplete='off')

     underform_left, underform_right = st.columns([2.8,1], border=False, gap='small', vertical_alignment='center')

     su_container = underform_right.container(horizontal=True, border=False, horizontal_alignment='center')

     if su_container.button("Sign Up", type='secondary', width='stretch'):
          SignUp()

     forgot_container = st.container(horizontal=True, border=False, horizontal_alignment='center')

     if forgot_container.button("Forgot your password?", type='tertiary', width='stretch'):
          ForgotPassword()     #Call dialog

     notif_container = st.container(horizontal=True, border=False, horizontal_alignment='center')

     if underform_left.button("Login", type='primary', width='stretch'):
          if user_input_login == '' or password_input_login == '':
               notif_container.warning("Please fill all fields")
          else:
               i, j, k = LoginCheck(user_input_login, password_input_login)

               if not i:
                    notif_container.error("Invalid Username")
               else:
                    if not j:
                         notif_container.error("Invalid Password")
                    if i and j:
                         login_name = df_user.loc[df_user['User'] == user_input_login, 'Name'].iloc[0]
                         st.session_state['role'] = k
                         st.session_state['user_key'] = user_input_login
                         st.session_state['profile_name'] = login_name
                         notif_container.success("Login Successful as " + login_name)
                         st.rerun()

     #st.write(st.session_state)

if st.session_state['role'] == 'Admin':     #Redirect to admin page
     admin_page.show()

if st.session_state['role'] == 'User':     #Redirect to user page
     user_page.show()

if st.session_state['role'] == 'Viewer':
     viewer_page.show()
