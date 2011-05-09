#!/usr/bin/env python
# -*- coding: utf-8 -*-
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from BeautifulSoup import BeautifulSoup
import re
import urllib
import urllib2
import Cookie
import time
import logging
from datetime import date, timedelta
from google.appengine.api import urlfetch
from google.appengine.ext import db
from django.utils import simplejson
from django.core import serializers

## datastore ##
class Department(db.Model):
    code = db.StringProperty(required=True)
    name = db.StringProperty(required=True)

class Doctor(db.Model):
    code = db.StringProperty(required=True)
    name = db.StringProperty(required=True)
    dept_code = db.StringProperty(required=True)

class Department_Time(db.Model):
    dept_code = db.StringProperty(required=True)
    time = db.StringProperty(required=True)

class Doctor_Time(db.Model):
    doct_code = db.StringProperty(required=True)
    time = db.StringProperty(required=True)

class URLOpener:
  def __init__(self):
      self.cookie = Cookie.SimpleCookie()

  def open(self, url, data = None):
      if data is None:
          method = urlfetch.GET
      else:
          method = urlfetch.POST

      while url is not None:
          response = urlfetch.fetch(url=url,
                          payload=data,
                          method=method,
                          headers=self._getHeaders(self.cookie),
                          allow_truncated=False,
                          follow_redirects=False,
                          deadline=10
                          )
          data = None # Next request will be a get, so no need to send the data again. 
          method = urlfetch.GET
          self.cookie.load(response.headers.get('set-cookie', '')) # Load the cookies from the response
          url = response.headers.get('location')

      return response

  def _getHeaders(self, cookie):
      headers = {
                 'Host' : 'www.google.com',
                 'User-Agent' : 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2 (.NET CLR 3.5.30729)',
                 'Cookie' : self._makeCookieHeader(cookie)
                  }
      return headers

  def _makeCookieHeader(self, cookie):
      cookieHeader = ""
      for value in cookie.values():
          cookieHeader += "%s=%s; " % (value.key, value.value)
      return cookieHeader


def fetchHtml(urls):
    page = urlfetch.fetch(url = urls, method=urlfetch.GET,follow_redirects=False, deadline=10)
    return page.content

def fetchPOSTHtml(urls, data):
    page = urlfetch.fetch(url=urls, payload=urllib.urlencode(data), method=urlfetch.POST,follow_redirects=False, deadline=10)
    return page.content

def encode_big5(txt): return txt.encode("iso-8859-1").decode("big5")

def isdigit(str): return str.isdigit()

def print_json(self,json_value):
    self.response.headers['Content-Type'] = 'application/javascript'
    self.response.out.write(simplejson.dumps(json_value))
## Handler ##

class Notfound(webapp.RequestHandler):
    def get(self):
        self.error(404)
        self.response.out.write('404 Not Found.')
        
class DeptHandler(webapp.RequestHandler):
    def get(self):
        id = self.request.get("id")
        if id=="":
            department = Department.all()
            dept_list = [{dept.code: dept.name} for dept in department ]
            self.response.headers['Content-Type'] = 'application/javascript'
            self.response.out.write(simplejson.dumps(dept_list))       
        else:   # a particular department
            dept_obj = Department.gql("WHERE code = '"+id+"'").fetch(1)[0]
            dept = {'id': id, 'name':dept_obj.name}
            doctors = Doctor.gql("WHERE dept_code = '"+id+"'")
            doc_list = [{doc.code: doc.name} for doc in doctors]
            dept_time = Department_Time.gql("WHERE dept_code='"+id+"'")
            dept_time_list = [d_t.time for d_t in dept_time]
            dept['doctor'] = doc_list
            dept['time'] = dept_time_list
            self.response.out.write('[')
            print_json(self,dept)        
            self.response.out.write(']')
            
class DoctorHandler(webapp.RequestHandler):
    def get(self):
        id = self.request.get("id")
        if id=="":
            doctor = Doctor.all()
            doct_list = [{doct.code: doct.name} for doct in doctor ]
            self.response.headers['Content-Type'] = 'application/javascript'
            self.response.out.write(simplejson.dumps(doct_list))       
        else:   # a particular doctor
            doct_obj = Doctor.gql("WHERE code = '"+id+"'").fetch(1000)
            doct = {'id': id, 'name':doct_obj[0].name}
            doct_obj = [Department.gql("WHERE code = '"+i.dept_code+"'").fetch(1)[0] for i in doct_obj]
            doct_list = [{dep.code: dep.name} for dep in doct_obj]
            doct_time = Doctor_Time.gql("WHERE doct_code='"+id+"'")
            doct_time_list = [d_t.time for d_t in doct_time]
            doct['dept'] = doct_list
            doct['time'] = doct_time_list
            self.response.out.write('[')
            print_json(self,doct) 
            self.response.out.write(']') 

class RegisterHandler(webapp.RequestHandler):
    # def get(self): #for test
    #     self.response.out.write("<form action=\"./register\" method=\"post\"><input type=\"text\" name=\"dept\" value=\"0200\"><input type=\"text\" name=\"doctor\" value=\"95351\"><input type=\"text\" name=\"time\" value=\"2011-05-11-C\"><input type=\"text\" name=\"id\" value=\"AA20047115\"><input type=\"submit\" value=\"submit it!\"></form>")
    def post(self):
        id = self.request.get("id")
        dept_code = self.request.get("dept")
        doct_code = self.request.get("doctor")
        time_shift = self.request.get("time")
        
        t = date.today()+timedelta(days=1)
        sevenday = t+timedelta(days=7)
        opd_date = str(t.timetuple().tm_year-1911)+t.strftime("%m%d")
        opd_date2 = str(sevenday.timetuple().tm_year-1911)+sevenday.strftime("%m%d")
        time = str(int(time_shift[0:4])-1911)+time_shift[5:7]+time_shift[8:10]
        shift = ord(time_shift[11:12])-64
        status = '1'
        message = u"出現錯誤!"        
        data = {'Opd_date':opd_date, 'Opd_date2':opd_date2, 'dept_code':dept_code, 'doc_code':'','Submit1':'確認送出'}
        page = fetchPOSTHtml("http://www.wanfang.gov.tw/W402008web_new/opdreg.asp", data)
        soup = BeautifulSoup(page)
        table = soup.findAll('tr', align="middle")[0].parent

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
        print_json(self,json_value)
        

class CancelHandler(webapp.RequestHandler):
    # def get(self): #for test
    #     self.response.out.write("<form action=\"./cancel_register\" method=\"post\"><input type=\"text\" name=\"dept\" value=\"0200\"><input type=\"text\" name=\"doctor\" value=\"95351\"><input type=\"text\" name=\"time\" value=\"2011-05-11-C\"><input type=\"text\" name=\"id\" value=\"AA20047115\"><input type=\"submit\" value=\"submit it!\"></form>")
    def post(self):
        id = self.request.get("id")
        dept_code = self.request.get("dept")
        doct_code = self.request.get("doctor")
        time_shift = self.request.get("time")
        
        doct_obj = Doctor.gql("WHERE code = '"+doct_code+"'").fetch(1000)
        doctor = {'id': id, 'name':doct_obj[0].name}
        time = str(int(time_shift[0:4])-1911)+time_shift[5:7]+time_shift[8:10]
        shift = ord(time_shift[11:12])-64
        shift_descripts = {1:u"早上",2:u"下午",3:u"晚上"}
        status = '1'
        message = u"出現錯誤!"        
        cancel_url = "http://www.wanfang.gov.tw/W402008web_new/reg_Query.asp?Action=Y"
        data = urllib.urlencode({'UserID':id})
        opener = URLOpener()
        page = opener.open(cancel_url, data).content
        soup = BeautifulSoup(page)
        form = soup.findAll('form')
        
        if form == []:
            status = '1'
            message = u'出現錯誤.'
        else:
            div = form[0].findAll('div',align="center")
            if div != []:
                status = '1'
                message = div[0].text
            else:
                register_data_header = form[0].findAll(lambda tag: tag.name=="table")[1]
                register_data = register_data_header.findAll(lambda tag:tag.name=="tr" and len(tag.attrs)<1)
                if register_data == []:
                    status = '1'
                    message = u'找不到掛號資料.'                    
                else:
                    text = [i.text for i in register_data]
                    isexist = False
                    num = 1
                    for i in text:
                        if i.find(time)>-1 and i.find(doctor['name'])>-1 and i.find(shift_descripts[shift])>-1:
                            isexist = num
                        num+=1
                    if isexist == False:
                        status = '1'
                        message = u'找不到掛號資料.'
                    else:
                        row = register_data[isexist-1].findAll('td')
                        dept_room = urllib.quote(row[5].text.encode('big5'))
                        sNo=row[6].text
                        cancel_register='http://www.wanfang.gov.tw/W402008web_new/reg_Query.asp?Action=D&OpdKind=O&RegNo=&UserID='+id+'&chDate='+time+'&shift_no='+str(shift)+'&dept_code='+dept_code+'&dept_room='+dept_room+'&sNo='+sNo
                        cancel_it = opener.open(cancel_register).content
                        status = "0"
                        
        json_value = {'status':status, 'message':message}
        if status == "0":
            json_value = {'status':status}
        print_json(self,json_value)
        
        
def main():
    application = webapp.WSGIApplication([('/', Notfound),
                                          (r'/wanfang/dept',DeptHandler),
                                          (r'/wanfang/doctor',DoctorHandler),
                                          (r'/wanfang/register',RegisterHandler),
                                          (r'/wanfang/cancel_register',CancelHandler)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
