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
password = '12qwaszx'
pool = redis.ConnectionPool(host=host, port=port,  db=12, decode_responses=True,  encoding='utf-8')
#pool = redis.ConnectionPool(host=host, port=port,  db=13)
#pool = redis.ConnectionPool(host=host, port=port, password=password, db=9)
r = redis.Redis(connection_pool=pool)
#sched = BlockingScheduler()
logit = mylog.Mylog("epg","/home/epg/diyepg.log")
ua = UserAgent()


def unix_local(t):
    time_local = time.localtime(t)
    dt = time.strftime("%H:%M",time_local)
    return dt

def getcctv_epg(playtype):
    playreg = re.compile(u'CCTV[0-9]+[Kk+]?',re.I)
    today =  str(datetime.date.today().strftime("%Y-%m-%d"))
    playdate =  str(datetime.date.today().strftime("%Y%m%d"))
    hs = '''
DNT: 1
Referer: https://tv.cctv.com/epg/
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36
''' 
    headers = header.get(hs)
    t = int(time.time())
    url = 'https://api.cntv.cn/epg/getEpgInfoByChannelNew?c={}&serviceId=tvcctv&d={}&t=jsonp&cb=setItem1'.format(playtype,playdate)
    s = requests.session()
    try:
        headers['User-Agent'] = ua.chrome
        res = s.get(url,headers=headers)
        res = re.findall(r'setItem1\((.*)\)',res.text)[0]
        res = json.loads(res)
        cntvlists =  res['data'][playtype]['list']
        if cntvlists:
            if playtype == "cctv5plus":
                playtype = 'cctv5+'
            if playtype == "cctv5jilu":
                playtype = 'cctv9'
            if playtype == "cctv5child":
                playtype = 'cctv14'
            rkey = playtype.upper() + "@" + today
            #if r.exists(rkey):
            #    return True
            playlist = [ {"start":unix_local(x['startTime']),"end":unix_local(x['endTime']),"title":x['title'].replace("'",""),"desc":""} for x in cntvlists ]

            if len(playlist) < 6:
                return False
            playdict = {}
            playdict["channel_name"] =  playtype.upper()
            playdict["date"] = today
            playdict["epg_data"] = playlist
            playdict["url"] = "cntv.cn"
            r.set(rkey,json.dumps(playdict).decode("utf-8"))
            r.expire(rkey,604800)
            return True
    except Exception,e:
        logit.info(playtype,e)
        print playtype,e
        return False
         


if __name__ == '__main__':
#    num=random.randint(100,600)
 #   time.sleep(num)
    try:
        today = sys.argv[1]
    except:
        today =  str(datetime.date.today().strftime("%Y-%m-%d"))
    tomorrow = str((datetime.date.today()  + datetime.timedelta(days=1)).strftime("%Y-%m-%d"))



    channels = ['cctv1', 'cctv2', 'cctv3', 'cctv4', 'cctv5', 'cctv6', 'cctv7', 'cctv8', 'cctvjilu', 'cctv10', 'cctv11', 'cctv12', 'cctv13', 'cctvchild', 'cctv15', 'cctv17', 'cctv5plus']
    for channel in channels:
        i = 0
        while i < 3 : 
            time.sleep(2)
            if getcctv_epg(channel):
                break
            else:
                i = i + 1
                
#
