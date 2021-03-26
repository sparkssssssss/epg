#coding:utf-8
import requests
import sys
import os
import re
import json
import time
import random
import datetime
import redis
import logging
import mylog
import header
import tolist
from lxml import etree
import xmltodict
from fake_useragent import UserAgent
#basedir = os.path.abspath(os.path.dirname(__file__))

reload(sys)
sys.setdefaultencoding('utf-8')




host = '127.0.0.1'
port = 6379
password = ''
pool = redis.ConnectionPool(host=host, port=port,  db=12, decode_responses=True,  encoding='utf-8')
r = redis.Redis(connection_pool=pool)
logit = mylog.Mylog("epg","/home/epg/diyepg.log")
ua = UserAgent()


def unix_local(t):
    time_local = time.localtime(t)
    dt = time.strftime("%H:%M",time_local)
    return dt

def getcctv_epg(pdate):
    #此文本需要包含格式 节目:id
    with open('/home/epg/migu','r') as f:
        vals = f.read()
    idname = header.get(vals)

    playreg = re.compile(u'CCTV[0-9]+[Kk+]?',re.I)
    today =  str(datetime.date.today().strftime("%Y-%m-%d"))
    playdate = pdate.replace('-','') 
    hs = '''
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
Accept-Encoding: gzip, deflate
Accept-Language: en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7
Cache-Control: no-cache
Connection: keep-alive
DNT: 1
Host: webapi.miguvideo.com
Pragma: no-cache
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36
''' 
    headers = header.get(hs)
    t = int(time.time())

    s = requests.session()
    for key in idname:
        try:
            pid = idname[key]
            url = 'http://webapi.miguvideo.com/gateway/live/v2/tv-programs-data/{0}/{1}'.format(pid,playdate)
            headers['User-Agent'] = ua.chrome
            res = s.get(url,headers=headers)
            rescode = json.loads(res.text)['code']
            if rescode != 200:
                logit.warning(key)
                continue
            migulists = json.loads(res.text)['body']['program'][0]['content']
            if migulists:
                rkey = key.upper() + "@" + pdate
                if r.exists(rkey):
                    continue
                playlist = [ {"start":x['startHours'],"end":x['endHours'],"title":x['contName'].replace("'",""),"desc":""} for x in migulists ]

                if len(playlist) < 6:
                    continue
                playdict = {}
                playdict["channel_name"] =  key.upper()
                playdict["date"] = pdate
                playdict["epg_data"] = playlist
                playdict["url"] = "migu.com"
                r.set(rkey,json.dumps(playdict).decode("utf-8"))
                r.expire(rkey,604800)
                logit.info(rkey)
                time.sleep(2)
        except Exception,e:
            logit.info(playtype + str(e))
            print playtype,e
            return 0
         


if __name__ == '__main__':
    num=random.randint(100,600)
    time.sleep(num)
    try:
        pdate = sys.argv[1]
    except:
        #pdate =  str(datetime.date.today().strftime("%Y-%m-%d"))
        pdate = str((datetime.date.today()  + datetime.timedelta(days=1)).strftime("%Y-%m-%d"))


    getcctv_epg(pdate)

#    i = 0
#    while i < 3 : 
#        time.sleep(2)
#        res = getcctv_epg(channel,pdate)
#        print res
#        if res > 0:
#            break
#        else:
#            i = i + 1
                
#
