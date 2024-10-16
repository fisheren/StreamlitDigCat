import streamlit_authenticator as stauth
import hashlib
import yaml
from yaml.loader import SafeLoader
import streamlit as st
from quickstart_googledrive import init_drive_client, upload_or_replace_file
import os

import random
import string

import smtplib
from email.mime.text import MIMEText
from email.header import Header


def generate_verification_code(length=6):
    # 生成随机字母和数字组合的验证码
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


def send_email(receiver_email, code):
    # 邮箱配置信息
    sender_email = "digcat.haolilab@gmail.com"  # 替换为你的邮箱
    password = "qsrpdfstixvtcvdm"  # 替换为你的邮箱密码或授权码
    smtp_server = "smtp.gmail.com"  # 替换为你的SMTP服务器地址，如Gmail的smtp.gmail.com

    # 创建邮件内容
    subject = "DigCat Verification Code"
    body = f"Your DigCat verification code is: {code}"
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['From'] = Header("Your Name", 'utf-8')  # 替换为你的名称
    msg['To'] = Header(receiver_email, 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')

    # 发送邮件
    try:
        with smtplib.SMTP(smtp_server, 587) as server:  # 587是常见的TLS端口
            server.starttls()  # 启用TLS加密
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        st.info("Email sent successfully!")
    except Exception as e:
        st.info(f"Failed to send email: {e}")


def verify_code(input_code, actual_code):
    return input_code == actual_code


def get_hashed_pw(pw_string):
    hashed_password = hashlib.sha256(pw_string.encode('utf-8')).hexdigest()
    return hashed_password


def update_passwd(authenticator, config, yaml_file = 'user.yaml'):
    #st.sidebar.write(yaml_file)
    if not 'Reset Password' in st.session_state:
        st.session_state['Reset Password'] = None
    if st.button('Reset Password'):
        st.session_state['Reset Password'] = True
    if st.session_state['Reset Password']:
        try:
            if authenticator.reset_password(st.session_state["username"]):
                with open(yaml_file, 'w') as file:
                    yaml.dump(config, file, default_flow_style=False)                
                upload_or_replace_file("user.yaml", os.path.join(os.getcwd(), "user.yaml"), 'application/x-yaml', dir_dict["user"], init_drive_client())
                st.success('Password modified successfully')
                st.session_state['Reset Password'] = False 
        except Exception as e:
            st.error(e)
        
        
def registration(authenticator, config, yaml_file = 'user.yaml', preauthori = False):
    try:
        fields = {
        'Form name': 'Register user',
        'Email': 'Email',
        'Username': 'Username (For logging in)',
        'Password': 'Password',
        'Repeat password': 'Repeat password',
        'Institute': 'Institute',  # 添加新字段
        'Register': 'Register'
        }
        email_of_registered_user, username_of_registered_user, name_of_registered_user, institute_of_registered_user = authenticator.register_user(pre_authorization=preauthori, fields=fields)
        
        if email_of_registered_user:
            with open(yaml_file, 'w') as file:
                yaml.dump(config, file, default_flow_style=False)
            upload_or_replace_file("user.yaml", os.path.join(os.getcwd(), "user.yaml"), 'application/x-yaml', dir_dict["user"], init_drive_client())
            st.success('User registered successfully')
    except Exception as e:
        st.error(e)


def forget_passwd(authenticator, config, yaml_file = 'user.yaml'):
    if "verification_code" not in st.session_state:
        st.session_state["verification_code"] = None
    if not 'Forgot Password?' in st.session_state:
        st.session_state['Forgot Password?'] = None
    if st.button('Forgot Password?'):
        st.session_state['Forgot Password?'] = True
    if not 'email_check' in st.session_state:
        st.session_state['email_check'] = None    
        
    if st.session_state['Forgot Password?']:
        st.write("Please write your email address:")
        code_email = st.text_input("email address here")
        if st.button("Send verification code"):
            st.session_state.verification_code = generate_verification_code()
            send_email(code_email, st.session_state.verification_code) 
        input_verification_code = st.text_input("Input the verification code")
        if st.button("Verify"):
            if verify_code(st.session_state.verification_code, input_verification_code):
                st.session_state['email_check'] = True
            else:
                st.error("Wrong verification code.")
                st.session_state['email_check'] = False
        if st.session_state['email_check']:
            try:
                username_of_forgotten_password, email_of_forgotten_password, new_random_password = authenticator.forgot_password()
                if username_of_forgotten_password and email_of_forgotten_password == code_email:
                    with open(yaml_file, 'w') as file:
                        yaml.dump(config, file, default_flow_style=False)
                    upload_or_replace_file("user.yaml", os.path.join(os.getcwd(), "user.yaml"), 'application/x-yaml', dir_dict["user"], init_drive_client())
                    st.markdown(f'New password is: **{new_random_password}**') 
                    st.session_state['Forgot Password?'] = False
                    st.session_state['email_check'] = False
                elif username_of_forgotten_password and email_of_forgotten_password != code_email:
                    st.error('Email does math the username')
                    st.session_state['Forgot Password?'] = False
                    st.session_state['email_check'] = False
                elif username_of_forgotten_password == False:
                    st.error('Username is not found')
                    st.session_state['Forgot Password?'] = False
                    st.session_state['email_check'] = False
            except Exception as e:
                st.error(e)
                st.session_state['Forgot Password?'] = False
                st.session_state['email_check'] = False


def login(yaml_file = 'user.yaml', preauthori = False):
    with open(yaml_file) as file:
        config = yaml.load(file, Loader=SafeLoader) 
    
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['preauthorized']
        )
    with st.sidebar:
        name, authentication_status, username = authenticator.login(fields={'Form name':'Login', 'Username':'Username', 'Password':'Password', 'Login':'Login'})
        if authentication_status:
            st.markdown('Welcome **%s %s**' % (config['credentials']['usernames'][username]['institute'], name))
            authenticator.logout(button_name = "Logout")
            update_passwd(authenticator, config, yaml_file = yaml_file)
            return authentication_status, name, username, config['credentials']['usernames'][username]['institute']
        elif authentication_status == False:
            st.sidebar.error('Username/password is incorrect')
            return None
        elif authentication_status == None:
            forget_passwd(authenticator, config, yaml_file = yaml_file)
            st.markdown("🌊 **Need a DigCat account?** Please register below.")            
            registration(authenticator, config, yaml_file = yaml_file, preauthori= preauthori)
            return None
    return None

