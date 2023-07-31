##################################################################
'''
  * Tapaculo Lite에서 생성한 프로젝트가 온도 습도를 기록하는 .dat 파일을 
    읽어들여 설정 온도 범위를 벗어날 때마다 알림 메일을 전송
  * 송신에는 gmail.com 계정을 사용함
'''
# 사용자 지정 변수
temp_lower_criteria = 10 # 허용 하한 온도
temp_upper_criteria = 30 # 허용 상한 온도

update_interval_seconds = 60 # seconds, 업데이트 간격 
mailing_interval_minutes = 5 # minutes, 메일 전송 후 다음 메일 전송까지의 시간 간격

dat_file_name = './monitoring.dat'

# ;로 구분된 수신자 메일 주소 리스트
# to_address = 'id1@company.co.kr; id2@company.co.kr; id3@company.co.kr'
to_address = 'id3@company.co.kr'

# 송신 메일 계정 ID/PW
send_address = 'myID@gmail.com'
send_address_password = 'myPW' # 2단계 인증 후, 별도 비밀번호 발급 필요 : https://coding-kindergarten.tistory.com/m/204

##################################################################
import time
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

import smtplib
from email.mime.text import MIMEText

HT_title = '[Warning] High Temperature Alert: 4F Server Room'
HT_notice = '높은 온도 경고!\n'

LT_title = '[Warning] Low Temperature Alert: 4F Server Room'
LT_notice = '낮은 온도 경고!\n'

def loading_dat():
    con = sqlite3.connect(dat_file_name) # dat file 로딩
    df = pd.read_sql_query("SELECT * from radionode", con) # 온습도 시계열 테이블 전환 (https://datacarpentry.org/python-ecology-lesson/09-working-with-sql/index.html)
    df = df.sort_values(by='pointDate') # 시간순 정렬 (온습도 측정 데이터 5개를 모았다가 한번에 .dat file에 기록하는데, 이 때 시간에 따라 정렬하지 않음)
    df['pointDate'] = pd.to_datetime(df['pointDate'], unit='s') + timedelta(hours=9) # UTC → KST (https://intotw.tistory.com/m/245)
    return(df)

def mailing(title, notice, contents):
    smtp = smtplib.SMTP('smtp.gmail.com', 587) # gmail
    #smtp = smtplib.SMTP('118.128.208.148', 587) # insilico
    
    smtp.ehlo()      # say Hello
    smtp.starttls()  # TLS 사용시 필요
    smtp.login(send_address, send_address_password)
    
    msg = MIMEText(notice+contents)
    msg['Subject'] = title
    msg['To'] = to_address
    
    smtp.sendmail(send_address, msg['To'].split(';'), msg.as_string())
    smtp.quit()

while True:
    print('Running ...')
    try:
        df = loading_dat().iloc[-6:-1]
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if df['channel1'].max() > temp_upper_criteria:
            contents = '현재 서버실 온도가 {} ℃, 습도가 {} % 입니다.\n\n기준 일시 : {}\n설정 온도 : {} ℃'.format(df['channel1'].max(), df['channel2'].iloc[-1], now, temp_upper_criteria)
            mailing(HT_title, HT_notice, contents)
            time.sleep(60*mailing_interval_minutes)
            
        elif df['channel1'].min() < temp_lower_criteria:
            contents = '현재 서버실 온도가 {} ℃, 습도가 {} % 입니다.\n\n기준 일시 : {}\n설정 온도 : {} ℃'.format(df['channel1'].min(), df['channel2'].iloc[-1], now, temp_lower_criteria)
            mailing(LT_title, LT_notice, contents)
            time.sleep(60*mailing_interval_minutes)
            
        time.sleep(update_interval_seconds)
        
    except:
        time.sleep(1)