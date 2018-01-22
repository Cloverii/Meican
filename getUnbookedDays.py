# -*- coding: utf-8 -*-
import re
import json
import time
import bisect
import urllib
import getpass
import hashlib
import urllib2
import datetime
import cookielib
# from PIL import Image
from HTMLParser import HTMLParser
# from bs4 import BeautifulSoup

  
class MyHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.locs = {}
        self.option = False
        self.curLoc = ''
  
    def handle_starttag(self, tag, attrs):
        if tag == "option":
            if len(attrs) != 0:
                for (variable, value)  in attrs:
                    if variable == 'value':
                        self.option = True
                        idx = value.rfind('/')
                        self.curLoc = value[ : idx]
                        
    def handle_data(self, data):
        if self.option == True and data.find('企业付') != -1:
            self.locs[self.curLoc] = ''.join(data.split())
        self.option = False


class Meican:
    def __init__(self):
        cookie = cookielib.CookieJar()
        # proxy= urllib2.ProxyHandler({'http':'122.114.31.177'})
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie)) #, proxy)
        self.locs = {}
        
    def login(self, username, password):
        postdata = urllib.urlencode({
            'username':username,
            'loginType':'username',
            'password':password,
            'remember':'true'
        })
        
        req = urllib2.Request(url='https://meican.com/account/directlogin', data=postdata)
        res = self.opener.open(req).read()
        # print res
        if res.find('选择地址') != -1:
            return 0
        elif res.find('用户名或密码错误') != -1:
            return -1
        else:
            return 1
        
    def close(self):
        self.opener.close()
        
    def getLocs(self):
        req = urllib2.Request(url='https://meican.com/orders/list/')
        res = self.opener.open(req).read()
        hp = MyHTMLParser()
        hp.feed(res)
        hp.close()
        self.locs = hp.locs
        # for str in self.locs:
            # print(str)
            # print self.locs[str].decode('utf-8')
        
    def getBookedDays(self, startDate, endDate):
        print startDate, endDate
        dateList = []
        postData = urllib.urlencode({
            'startDate':startDate,
            'endDate':endDate
        })
        for loc in self.locs:
            print 'loc', self.locs[loc].decode('utf-8')
            page = 0
            while True:
                page += 1
                req = urllib2.Request(url='https://meican.com' + loc + '/' + str(page) + '?' + postData)
                # print('https://meican.com' + loc + '/' + str(page) + '?' + postData)
                res = self.opener.open(req).read()
                # with open('sample.html', 'w') as f:
                    # f.write(res)
                tmpList = re.findall(r'(<td>\s*\d{4}-\d{2}-\d{2}\s\d{2}:\d{2})', res)
                # print tmpList
                if len(tmpList) == 0:
                    break
                for dt in tmpList:
                    idx = dt.find('-') - 4
                    print dt[idx : idx + 10]
                    dateList.append(''.join(dt[idx : idx + 10].split('-')))
        return dateList
            
    def getBookedDays1(startDate, endDate):
        postDic = {
            'startDate':startDate,
            'endDate':endDate,
            'page':'0'
        }
        while True:
            postDic['page'] = str(int(postDic['page']) + 1)
            # print(postDic)
            postData = urllib.urlencode(postDic)
            req = urllib2.Request(url='https://meican.com/payment/balance', data=postData)
            res = self.opener.open(req).read()
            with open('sample.html', 'w') as f:
                f.write(res)
            if res.find('暂无交易信息') != -1:
                break
            else:
                pattern = re.compile(r"(\d{2}-\d{2}\s)")
                test = re.findall(r"(\d{2}-\d{2}\s\d{2}:\d{2})", res)
                print test
                match = pattern.match(res)
                if match:
                    print match.group()

        
def main():
    print('Assume you are clever enough to understand the following input format!!!')
    uname = raw_input('username:')
    passwd = getpass.getpass('password:')
    mc = Meican()
    res = mc.login(uname, passwd)
    if res == 0:
        print 'You\'ve login successfully'
        mc.getLocs()
        
        st = raw_input('startDate(included, "YYYYMMDD", equal to or later than the day you started work with DIDI):\n')
        ed = raw_input('endDate(included, "YYYYMMDD", earlier than today):\n')
        # st, ed = ['20180101', '20180121']
        
        # %Y-%m-%d
        st1 = time.strftime('%Y-%m-%d', time.strptime(st,'%Y%m%d'))
        ed1 = time.strftime('%Y-%m-%d', time.strptime(ed,'%Y%m%d'))
        dateList = mc.getBookedDays(st1, ed1)
        mc.close()
        bookedDay = len(dateList)
        print 'bookedDay', bookedDay
        
        holidayList = []
        with open('annual_holidays', 'r') as f:
            for line in f:
                holidayList.append(line)
        lb = bisect.bisect_left(holidayList, st)
        edP1 = (datetime.date(int(ed[0:4]), int(ed[4:6]), int(ed[6:8])) + datetime.timedelta(days=1)).strftime("%Y%m%d")
        ub = bisect.bisect_left(holidayList, edP1) # What an interesting function!!!!!!
        holiday = ub - lb
        print 'holiday', holiday
        
        startDate = datetime.date(int(st[0:4]), int(st[4:6]), int(st[6:8]))
        endDate = datetime.date(int(ed[0:4]), int(ed[4:6]), int(ed[6:8]))
        total = (endDate - startDate).days + 1
        print 'total', total
        
        print 'unbookedDay', total - bookedDay - holiday
    
    elif res == -1:
        print 'Wrong username or password'
    else:
        print 'Unknown error'

if __name__ == '__main__':
    main()
