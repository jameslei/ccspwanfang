#!/usr/bin/env python
# -*- coding: utf-8 -*-
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from BeautifulSoup import BeautifulSoup
import re
import urllib
import urllib2
import time
from datetime import date, timedelta
from google.appengine.api import urlfetch
from google.appengine.ext import db

def fetchHtml(urls):
    page = urlfetch.fetch(url = urls)
    return page.content

def fetchPOSTHtml(urls, data):
    page = urlfetch.fetch(url=urls, payload=urllib.urlencode(data), method=urlfetch.POST)
    return page.content

def encode_big5(txt): return txt.encode("iso-8859-1").decode("big5")

def isdigit(str): return str.isdigit()

## datastore ##
class Department(db.Model):
    code = db.StringProperty(required=True)
    name = db.StringProperty(required=True)

class Doctor(db.Model):
    code = db.StringProperty(required=True)
    name = db.StringProperty(required=True)
    dept_code = db.ReferenceProperty(Department)

class Department_Time(db.Model):
    dept_code = db.ReferenceProperty(Department)
    time = db.StringProperty(required=True)

class Doctor_Time(db.Model):
    doct_code = db.ReferenceProperty(Doctor)
    time = db.StringProperty(required=True)

## Handler ##

class MainHandler(webapp.RequestHandler):
    def get(self):
        self.response.out.write('Hello world!')
        
class CronHandler(webapp.RequestHandler):
    def get(self):
        db.delete(Department.all())
        db.delete(Doctor.all())
        db.delete(Department_Time.all())
        db.delete(Doctor_Time.all())
        
        page = fetchHtml("http://www.wanfang.gov.tw/W402008web_new/opd.asp")
        soup = BeautifulSoup(page)
        table = soup.findAll('form')[0]
        opd_list = table.findAll(lambda tag: tag.name=="td" and len(tag.contents)>1 )
        
        for opd in opd_list:
            department = Department(code=opd.contents[0]["value"], name=opd.contents[1].lstrip())
            department.put()
            
        departments = dict([ (opd.contents[0]["value"], opd.contents[1].lstrip()) for opd in opd_list ])
        doctors = {}
        doctors_times = {}
        departments_times = {}
        #compute the ROC time
        t = date.today()+timedelta(days=1)
        sevenday = date.today()+timedelta(days=8)
        opd_date = str(t.timetuple().tm_year-1911)+t.strftime("%m%d")
        opd_date2 = str(sevenday.timetuple().tm_year-1911)+sevenday.strftime("%m%d")
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
            
            dept = Department.gql("WHERE code= :1", dept_code)
            dept_dbmodel = dept.fetch(5)[0]
            for doc_tmp in tmp:
                doctor=Doctor(code=doc_tmp[1], name=doc_tmp[0], dept_code=dept_dbmodel)
                doctor.put()
            tmp_dict = dict([ (i[1], i[0]) for i in tmp ])
            doctors[dept_code] = tmp_dict

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
                        dept_time = Department_Time(dept_code=dept_dbmodel, time=day_i.strftime("%Y-%m-%d")+"-"+period_X)
                        dept_time.put()  
                    for j in period:
                        doct = Doctor.gql("WHERE code= '"+str(j)+"'")
                        doct_list = doct.fetch(10)
                        if len(doct_list)>0:
                            doct_dbmodel = doct_list[0]
                            doct_time = Doctor_Time(doct_code=doct_dbmodel, time=day_i.strftime("%Y-%m-%d")+"-"+period_X)
                            doct_time.put()

        
class DeptHandler(webapp.RequestHandler):
    def get(self):
        self.response.out.write('Hello world!')

def main():
    application = webapp.WSGIApplication([('/', MainHandler),
                                          ('/get_data/', CronHandler),
                                          ('/wanfang/dept',DeptHandler)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
