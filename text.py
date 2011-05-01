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
    page = fetchHtml("http://www.wanfang.gov.tw/W402008web_new/opd.asp")
    soup = BeautifulSoup(page)

#'departments' is the list of departments
#'doctors' is a dictionary, doctors[dept_code] is a list of doctors and their ids
#'doctors_times' links doctors and their time
#'departments_times' links departments and their time
    table = soup.findAll('form')[0]
    opd_list = table.findAll(lambda tag: tag.name=="td" and len(tag.contents)>1 )
    departments = dict([ (opd.contents[0]["value"], opd.contents[1].lstrip()) for opd in opd_list ])
    doctors = {}
    doctors_times = {}
    departments_times = {}
    #compute the ROC time
    t = date.today()+timedelta(days=1)
    sevenday = date.today()+timedelta(days=8)
    opd_date = str(t.timetuple().tm_year-1911)+t.strftime("%m%d")
    opd_date2 = str(sevenday.timetuple().tm_year-1911)+sevenday.strftime("%m%d")
    print opd_date, opd_date2
# find all doctors

    b = departments.keys()
    for dept_code in b:
        data = {'dept_code':dept_code}
        doctor_page = fetchPOSTHtml("http://www.wanfang.gov.tw/W402008web_new/opd.asp?action=date", data)
        soup = BeautifulSoup(doctor_page)
    
        table = soup.findAll('form')[0]
        doctor_list = table.findAll("td", align="left", headers="header1")
    
        try:
            encode_big5(doctor_list[0].text)
        except UnicodeEncodeError:
            doctor_id = [doctor.text for doctor in doctor_list]
        else:
            doctor_id = [encode_big5(doctor.text) for doctor in doctor_list]
        tmp = [i.replace(ur'）','').split(ur'（') for i in doctor_id]
        tmp_dict = dict([ (i[1], i[0]) for i in tmp ])
        doctors[dept_code] = tmp_dict
    
    # for i in doctors.keys():
    #     print i, departments[i]+": "
    #     for j in doctors[i].keys():
    #         print "\t", j, doctors[i][j]
    
        # get the detail of doctor and department
        data = {'Opd_date':opd_date, 'Opd_date2':opd_date2, 'dept_code':dept_code, 'doc_code':'','Submit1':'確認送出'}
        time_page = fetchPOSTHtml("http://www.wanfang.gov.tw/W402008web_new/opdreg.asp", data)
        soup = BeautifulSoup(time_page)
        table = soup.findAll('tr', align="middle")[0].parent
        for i in table.findAll('tr', valign="center"):
            timetable=[[],[],[]]
            date_text = filter(isdigit, i.contents[1].text.split())[0]
            day_i = date(int(date_text[0:3])+1911, int(date_text[3:5]), int(date_text[5:7]))
            
            # print "Date: ", day_i.strftime("%Y-%m-%d")
            timetable[0] = map(int,filter(isdigit, i.contents[3].text.replace(")","").split("(")))
            timetable[1] = map(int,filter(isdigit, i.contents[5].text.replace(")","").split("(")))
            timetable[2] = map(int,filter(isdigit, i.contents[7].text.replace(")","").split("(")))
            # print timetable
            period_X=chr(ord('A')-1)
            for period in timetable:
                period_X = chr(ord(period_X)+1)
                if len(period)>0:
                    try: departments_times[dept_code]
                    except KeyError: departments_times[dept_code] = [day_i.strftime("%Y-%m-%d")+"-"+period_X];
                    else:   departments_times[dept_code].append(day_i.strftime("%Y-%m-%d")+"-"+period_X)    
                    
                for j in period:
                    try:
                        doctors_times[j]
                    except KeyError:
                        doctors_times[j] = [day_i.strftime("%Y-%m-%d")+"-"+period_X]
                    else:
                        doctors_times[j].append(day_i.strftime("%Y-%m-%d")+"-"+period_X)
    print doctors_times
    print "\n", departments_times
            
            