# -*- coding: utf-8 -*-
from BeautifulSoup import BeautifulSoup
import os
import re
import urllib
import urllib2
import time
from datetime import date, timedelta

def fetchHtml(url):
    r = urllib2.Request(url)
    r.add_header('User-Agent', 'Mozilla 5.0')
    page = urllib2.urlopen(r)
    return page

def fetchPOSTHtml(url, data):
    r = urllib2.Request(url, urllib.urlencode(data))
    r.add_header('User-Agent', 'Mozilla 5.0')
    page = urllib2.urlopen(r)
    return page

def encode_big5(txt): return txt.encode("iso-8859-1").decode("big5")

def isdigit(str): return str.isdigit()

if __name__ == '__main__':
    id = 'AA20047115'
    dept_code = '0800'
    doct_code = '91166'
    time_shift = '2011-05-12-B'
        
    t = date.today()+timedelta(days=1)
    sevenday = t+timedelta(days=7)
    opd_date = str(t.timetuple().tm_year-1911)+t.strftime("%m%d")
    opd_date2 = str(sevenday.timetuple().tm_year-1911)+sevenday.strftime("%m%d")
    
    data = {'Opd_date':opd_date, 'Opd_date2':opd_date2, 'dept_code':dept_code, 'doc_code':'','Submit1':'確認送出'}
    page = fetchPOSTHtml("http://www.wanfang.gov.tw/W402008web_new/opdreg.asp", data)
    soup = BeautifulSoup(page)
    table = soup.findAll('tr', align="middle")[0].parent
    time = str(int(time_shift[0:4])-1911)+time_shift[5:7]+time_shift[8:10]
    shift = ord(time_shift[11:12])-64
    tr = table.findAll(lambda tag: tag.text.find(time) > -1)
    if tr == []:
        status = 1
        message = u"找不到可掛號時段."
    else:
        a = tr[0].contents[shift*2+1].findAll(attrs={'href':re.compile(doct_code)})
        if a == []:
            status = 1
            message = u"找不到可掛號時段!"
        else:
            dept_room = filter(lambda x: x.find("DeptRoom")>-1, a[0]['href'].split('&'))[0].replace("DeptRoom=",'')
            # continue to register
            reg_url = "http://www.wanfang.gov.tw/W402008web_new/OPD_WebReg.asp"
            data = {'chDate':time,'ShiftNo':shift,'DeptCode':dept_code,
                    'DeptRoom':dept_room,'DocCode':doct_code,'UserID':id}
            reg_page = fetchPOSTHtml(reg_url,data)
            soup = BeautifulSoup(reg_page)
            form = soup.findAll("form")
            if form == []:
                status = 1
                message = u"註冊錯誤"
            else:
                reg_no_tr = form[0].findAll(lambda tag: tag.name=="td" and tag.text.find(u'看診序號：')>-1)
                if reg_no_tr ==[]:
                    status = 1
                    message = form[0].contents[2]
                else:
                    status = 0
                    message = reg_no_tr[0].nextSibling.nextSibling.contents[0].text
    json_value = {'status':status, 'message':message} 
    print json_value, json_value['message']       

            
#     page = fetchHtml("http://www.wanfang.gov.tw/W402008web_new/opd.asp")
#     soup = BeautifulSoup(page)
# 
# #'departments' is the list of departments
# #'doctors' is a dictionary, doctors[dept_code] is a list of doctors and their ids
# #'doctors_times' links doctors and their time
# #'departments_times' links departments and their time
#     table = soup.findAll('form')[0]
#     opd_list = table.findAll(lambda tag: tag.name=="td" and len(tag.contents)>1 )
#     departments = dict([ (opd.contents[0]["value"], opd.contents[1].lstrip()) for opd in opd_list ])
#     doctors = {}
#     doctors_times = {}
#     departments_times = {}
#     #compute the ROC time
#     t = date.today()+timedelta(days=1)
#     sevenday = date.today()+timedelta(days=8)
#     opd_date = str(t.timetuple().tm_year-1911)+t.strftime("%m%d")
#     opd_date2 = str(sevenday.timetuple().tm_year-1911)+sevenday.strftime("%m%d")
#     print opd_date, opd_date2
# # find all doctors
# 
#     b = departments.keys()
#     for dept_code in b:
#         data = {'dept_code':dept_code}
#         doctor_page = fetchPOSTHtml("http://www.wanfang.gov.tw/W402008web_new/opd.asp?action=date", data)
#         soup = BeautifulSoup(doctor_page)
#     
#         table = soup.findAll('form')[0]
#         doctor_list = table.findAll("td", align="left", headers="header1")
#     
#         try:
#             encode_big5(doctor_list[0].text)
#         except UnicodeEncodeError:
#             doctor_id = [doctor.text for doctor in doctor_list]
#         else:
#             doctor_id = [encode_big5(doctor.text) for doctor in doctor_list]
#         tmp = [i.replace(ur'）','').split(ur'（') for i in doctor_id]
#         tmp_dict = dict([ (i[1], i[0]) for i in tmp ])
#         doctors[dept_code] = tmp_dict
#     
#     # for i in doctors.keys():
#     #     print i, departments[i]+": "
#     #     for j in doctors[i].keys():
#     #         print "\t", j, doctors[i][j]
#     
#         # get the detail of doctor and department
#         data = {'Opd_date':opd_date, 'Opd_date2':opd_date2, 'dept_code':dept_code, 'doc_code':'','Submit1':'確認送出'}
#         time_page = fetchPOSTHtml("http://www.wanfang.gov.tw/W402008web_new/opdreg.asp", data)
#         soup = BeautifulSoup(time_page)
#         table = soup.findAll('tr', align="middle")[0].parent
#         for i in table.findAll('tr', valign="center"):
#             timetable=[[],[],[]]
#             date_text = filter(isdigit, i.contents[1].text.split())[0]
#             day_i = date(int(date_text[0:3])+1911, int(date_text[3:5]), int(date_text[5:7]))
#             
#             # print "Date: ", day_i.strftime("%Y-%m-%d")
#             timetable[0] = map(int,filter(isdigit, i.contents[3].text.replace(")","").split("(")))
#             timetable[1] = map(int,filter(isdigit, i.contents[5].text.replace(")","").split("(")))
#             timetable[2] = map(int,filter(isdigit, i.contents[7].text.replace(")","").split("(")))
#             # print timetable
#             period_X=chr(ord('A')-1)
#             for period in timetable:
#                 period_X = chr(ord(period_X)+1)
#                 if len(period)>0:
#                     try: departments_times[dept_code]
#                     except KeyError: departments_times[dept_code] = [day_i.strftime("%Y-%m-%d")+"-"+period_X];
#                     else:   departments_times[dept_code].append(day_i.strftime("%Y-%m-%d")+"-"+period_X)    
#                     
#                 for j in period:
#                     try:
#                         doctors_times[j]
#                     except KeyError:
#                         doctors_times[j] = [day_i.strftime("%Y-%m-%d")+"-"+period_X]
#                     else:
#                         doctors_times[j].append(day_i.strftime("%Y-%m-%d")+"-"+period_X)
#     print doctors_times
#     print "\n", departments_times
            
            