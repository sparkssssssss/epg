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
import base64
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
#pool = redis.ConnectionPool(host=host, port=port,  db=13)
#pool = redis.ConnectionPool(host=host, port=port, password=password, db=9)
r = redis.Redis(connection_pool=pool)
#sched = BlockingScheduler()
logit = mylog.Mylog("epg","/home/epg/diyepg.log")
ua = UserAgent()

def gettvsou_epg(playtype):
    playreg = re.compile(u'CCTV[0-9]+[Kk+]?',re.I)
    today =  str(datetime.date.today().strftime("%Y-%m-%d"))
    hs = '''
        Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
        Accept-Encoding: gzip, deflate, br
        Accept-Language: en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7
        Cache-Control: max-age=0
        Connection: keep-alive
        DNT: 1
        Host: www.tvsou.com
        Upgrade-Insecure-Requests: 1
        User-Agent: Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36
''' 
    headers = header.get(hs)
    t = int(time.time())
    url = 'https://www.tvsou.com/epg/{}/'.format(playtype)
    s = requests.session()
    try:
        res = s.get(url,headers=headers)
        res.encoding = 'utf-8'
        html = etree.HTML(res.text)
        node_list = html.xpath('//ul[@class="c_list_main"]/li')
        channellist = {}
        for node in  node_list:
            try:
                url = node.xpath('./a/@href')[0]
                playname = node.xpath('./a/i/text()')[0]
                playname = re.sub(u'频道|电视台|-', '', playname)
                if url and playname:
                    channellist[playname] = url  
            except:
                pass
    except Exception,e:
        logit.info(str(e))
        print(str(e))
        return
    try:
        for key in channellist:
            try:
                rkey = playreg.findall(key)[0]
            except:
                rkey = key
            rkey = rkey.upper() + "@" + today
            if not r.exists(rkey):
                try:
                    headers['User-Agent'] = ua.chrome
                    channelurl = "https://www.tvsou.com" + channellist[key]
                    headers['Referer'] = channelurl
                    channelres = s.get(channelurl,headers=headers)
                    channelres.encoding = 'utf-8'
                    channelhtml = etree.HTML(channelres.text)
                    channel_node_list = channelhtml.xpath('//div[@class="layui-tab-item layui-show"]/table/tbody/tr')
                    channeldata = []
                except Exception,e:
                    logit.info(key+":"+str(e))
                    print key+":"+str(e)
                    continue
                for node in channel_node_list:
                    try:
                        playtime = node.xpath("./td[1]/a/text()")[0]
                        playname = node.xpath("./td[2]/a/text()")[0]
                    except:
                        playtime = ''
                        playname = ''
                    if playname and playtime:
                        channeldata.extend([[playtime,playname]])
                i = 0
                playlist=[]
                while i < len(channeldata) :
                    if channeldata[i][1]:
                        tempdict = {}
                        tempdict['start'] = channeldata[i][0]
                        if i < len(channeldata) - 1 :
                            tempdict['end'] = channeldata[i+1][0]
                        else:
                            tempdict['end'] = "23:59"
                        tempdict['title'] = channeldata[i][1].decode("utf-8")
                        tempdict['desc'] = ''
                        playlist.append(tempdict)
                    i = i + 1
                playdict = {}
                playdict["channel_name"] = key
                playdict["date"] = today
                playdict["epg_data"] = playlist
                playdict["url"] = channelurl
                r.set(rkey,json.dumps(playdict).decode("utf-8"))
                r.expire(rkey,604800)
                num=random.randint(1,3)      
                time.sleep(num)
    except Exception,e:
        logit.info(str(e))
        print(str(e))
        pass

def getallow(pro,key):
    sports8_allows = ['经','公共','都市','生活','CCTV','卫视','SITV','DOX','影','闻','少儿']
    tvmao_allows = [ "安徽卫视","北京卫视","重庆卫视","东南卫视","甘肃卫视","广东卫视","深圳卫视","广西卫视","贵州卫视","海南卫视","河北卫视","黑龙江卫视","河南卫视","湖北卫视","湖南卫视","江苏卫视","江西卫视","吉林卫视","辽宁卫视","内蒙古卫视","宁夏卫视","山西卫视","山东卫视","东方卫视","陕西卫视","四川卫视","天津卫视","新疆卫视","云南卫视","浙江卫视","青海卫视","延边卫视","兵团卫视","黄河卫视","三沙卫视" ]
    if pro == 'tvmao':
        for i in tvmao_allows:
            if i in key:
                return True
    return False

def gettvsports8_epg(cid):
    playreg = re.compile(u"CCTV[0-9]+[Kk+]?|.*卫视$",re.I)
    today =  str(datetime.date.today().strftime("%Y-%m-%d"))
    week =  time.strftime("%w",time.localtime())
    hs = '''
        Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
        Accept-Encoding: gzip, deflate, br
        Accept-Language: en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7
        Cache-Control: max-age=0
        Connection: keep-alive
        DNT: 1
        Host: sports8.com
        referer: https://sports8.com/program/913/1.htm
        Upgrade-Insecure-Requests: 1
        User-Agent: Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36
''' 
    headers = header.get(hs)
    t = int(time.time())
    url = 'https://sports8.com/program/{}/{}.htm'.format(str(cid),week)
    s = requests.session()
    try:
        res = s.get(url,headers=headers)
        res.encoding = 'utf-8'
        html = etree.HTML(res.text)
        node_list = html.xpath('//div[@class="current"]/ul/li')
        channellist = {}
        for node in  node_list:
            try:
                url = node.xpath('./a/@href')[0] if node.xpath('./a/@href') else None
                playname = node.xpath('./a/text()')[0] if node.xpath('./a/text()') else None
                playname = re.sub(u'频道|电视台|-', '', playname)
                if url and playname:
                    channellist[playname] = url  
            except:
                pass
    except Exception,e:
        print(str(e))
        return
    try:
        for key in channellist:
            try:
                rkey = playreg.findall(key)[0]
            except:
                if re.search(u'.*卫视.+',key):
                    continue
                rkey = key
            rkey = rkey.upper() + "@" + today
            if not r.exists(rkey) and 'HD' not in rkey and '高清' not in rkey and '(' not in rkey and '购'not in rkey and getallow('sports8',rkey):
                try:
                    headers['User-Agent'] = ua.chrome
                    channelurl = channellist[key]
                    channelres = s.get(channelurl,headers=headers)
                    channelres.encoding = 'utf-8'
                    channelhtml = etree.HTML(channelres.text)
                    mo_channel_node_list = channelhtml.xpath('//div[@id="Weepgprogram_epgInfo"]/div[1]/p')
                    af_channel_node_list = channelhtml.xpath('//div[@id="Weepgprogram_epgInfo"]/div[2]/p')
                    en_channel_node_list = channelhtml.xpath('//div[@id="Weepgprogram_epgInfo"]/div[3]/p')
                    channeldata = []
                except Exception,e:
                    logit.info(key+":"+str(e))
                    print key+":"+str(e)
                    continue
                all_channel_node_list = mo_channel_node_list + af_channel_node_list + en_channel_node_list
                for node in all_channel_node_list:
                    try:
                        playtime = node.xpath("./em/text()")[0] if node.xpath("./em/text()") else None
                        playname = node.xpath("./text()")[0] if node.xpath("./text()") else "精彩节目"
                    except:
                        logit.info(key+":"+str(e))
                        print str(e)
                        pass
                    if playname and playtime:
                        channeldata.extend([[playtime,playname]])
                i = 0
                playlist=[]
                if len(channeldata) < 6:
                    continue
                while i < len(channeldata) :
                    if channeldata[i][1]:
                        tempdict = {}
                        tempdict['start'] = channeldata[i][0]
                        if i < len(channeldata) - 1 :
                            tempdict['end'] = channeldata[i+1][0]
                        else:
                            tempdict['end'] = "23:59"
                        tempdict['title'] = channeldata[i][1].decode("utf-8")
                        tempdict['desc'] = ''
                        playlist.append(tempdict)
                    i = i + 1
                playdict = {}
                playdict["channel_name"] = key
                playdict["date"] = today
                playdict["epg_data"] = playlist
                playdict["url"] = channelurl
                r.set(rkey,json.dumps(playdict).decode("utf-8"))
                print rkey
                r.expire(rkey,604800)
                num=random.randint(5,10)
                time.sleep(num)
    except Exception,e:
        print(str(e))
        pass
        

def getaf(a, q, id):
    _keyStr = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";
    q = "|" + q;
    q = base64.b64encode(q.encode('utf-8'));
    aid = id+"|"+a;
    aid = base64.b64encode(aid.encode('utf-8'));
    w = time.strftime("%w");
    w = (7 if(int(w) == 0) else int(w));
    w = _keyStr[w * w];
 
    return (w + str(aid)+str(q));                
                
def gettvmao_epg(cid):
    baseurl = "https://www.tvmao.com"
    playreg = re.compile(u'CCTV[0-9]+[Kk+]?|.*卫视|CGTN',re.I)
    today =  str(datetime.date.today().strftime("%Y-%m-%d"))
    week =  time.strftime("%w",time.localtime())
    hs = '''
        Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
        Accept-Encoding: gzip, deflate, br
        Accept-Language: en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7
        Cache-Control: max-age=0
        Connection: keep-alive
        DNT: 1
        Host: www.tvmao.com
        referer: https://www.tvmao.com/program/
        Upgrade-Insecure-Requests: 1
        User-Agent: Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36
''' 
    headers = header.get(hs)
    t = int(time.time())
    url = 'https://www.tvmao.com/program/{}-w{}.html'.format(cid,week)
    s = requests.session()
    try:
        res = s.get(url,headers=headers)
        res.encoding = 'utf-8'
        html = etree.HTML(res.text)
        node_list = html.xpath('//div[@class="chlsnav"]/ul/li')
        channellist = {}
        for node in  node_list:
            try:
                url = node.xpath('./a/@href')[0] if node.xpath('./a/@href') else None
                playname = node.xpath('./a/text()')[0] if node.xpath('./a/text()') else None
                playname = re.sub(u'频道|电视台|-', '', playname)
                if url and playname:
                    channellist[playname] = url  
            except:
                pass
    except Exception,e:
        print(str(e))
        return
    try:
        for key in channellist:
            try:
                rkey = playreg.findall(key)[0]
            except:
                rkey = key
            rkey = rkey.upper() + "@" + today
            if not r.exists(rkey) and getallow('tvmao',rkey):
                try:
                    headers['User-Agent'] = ua.chrome
                    channelurl = baseurl + channellist[key]
                    channelres = s.get(channelurl,headers=headers)
                    channelres.encoding = 'utf-8'
                    channelhtml = etree.HTML(channelres.text)
                    q = channelhtml.xpath('//form[@id="searchform"]/@q')[0] if channelhtml.xpath('//form[@id="searchform"]/@q') else None
                    a = channelhtml.xpath('//form[@id="searchform"]/@a')[0] if channelhtml.xpath('//form[@id="searchform"]/@a') else None
                    pid = channelhtml.xpath('//form[@id="searchform"]/button/@id')[0] if channelhtml.xpath('//form[@id="searchform"]/button/@id') else None
                    if q and a and pid:
                        clickurl = "https://www.tvmao.com/api/pg?p={}".format(getaf(a,q,pid))
                    #print clickurl
                    headers['X-Requested-With'] = "XMLHttpRequest"
                    headers['referer'] = channelurl
                    clickres = s.get(clickurl,headers=headers)
                    clickres.encoding = 'utf-8'
                    try:
                        afres = eval(clickres.text)[1].replace('\\','')                 
                        clickhtml = etree.HTML(afres.decode('utf-8'))
                    except:
                        logit.info(key+":"+str(e))
                        print('午后失败')
                        clickhtml = None
                        pass
                    
                    
                    mo_channel_node_list = channelhtml.xpath('//ul[@id="pgrow"]/li')
                    af_channel_node_list = clickhtml.xpath('//li')
                except Exception,e:
                    logit.info(key+":"+str(e))
                    print key + ":" + str(e)
                    continue
                channeldata = []
                all_channel_node_list = mo_channel_node_list + af_channel_node_list
                for node in all_channel_node_list:
                    try:
                        playtime = node.xpath("./div/span[1]/text()")[0] if node.xpath("./div/span[1]/text()") else None
                        playname = node.xpath("./div/span[2]/a/text()")[0] if node.xpath("./div/span[2]/a/text()") else "精彩节目"
                        playsubname = node.xpath("./div/span[2]/text()")[0] if node.xpath("./div/span[2]/text()") else None
                        if playsubname:
                            playname = str(playname) + str(playsubname)
                    except Exception,e:
                        print str(e)
                        pass
                    if playname and playtime:
                        channeldata.extend([[playtime,playname]])
                i = 0
                playlist=[]
                if len(channeldata) < 10 :
                    continue
                while i < len(channeldata) :
                    if channeldata[i][1]:
                        tempdict = {}
                        tempdict['start'] = channeldata[i][0]
                        if i < len(channeldata) - 1 :
                            tempdict['end'] = channeldata[i+1][0]
                        else:
                            tempdict['end'] = "23:59"
                        tempdict['title'] = channeldata[i][1].decode("utf-8")
                        tempdict['desc'] = ''
                        playlist.append(tempdict)
                    i = i + 1
                playdict = {}
                playdict["channel_name"] = key
                playdict["date"] = today
                playdict["epg_data"] = playlist
                playdict["url"] = channelurl
                r.set(rkey,json.dumps(playdict).decode("utf-8"))
                r.expire(rkey,604800)
                num=random.randint(30)
                time.sleep(num)
    except Exception,e:
        print(str(e))
        pass
                

if __name__ == '__main__':
    num=random.randint(100,600)
    time.sleep(num)
    try:
        today = sys.argv[1]
    except:
        today =  str(datetime.date.today().strftime("%Y-%m-%d"))
    tomorrow = str((datetime.date.today()  + datetime.timedelta(days=1)).strftime("%Y-%m-%d"))


#tvsou 添加爬取类别
    channels = [
#"yangshi",
#"weishi",
"shuzi",
#"87303baa", #常州
"1877ed89", #风云
"b9ab3d11", #北广
"8083b901", #zhongshu
"406fbb96", #武进
"0a606d07", #兰州
"fac1ecf6", #甘肃
"da0c3f96", #福建
"9f005630", #香港有线电视台
"51e1655d", #TVB无线电视
"daede0a9", #NOW宽频
"65e0f71a", #凤凰卫视
"474cf0fb", #美亚电视台
"ff77bdd7"  #厦门
]
    for channel in channels:
        gettvsou_epg(channel)

#tvmao 爬取大类,此处填写大类中的任一名即可爬取整个大类
    gettvmao_epg('KAMBA-TV',tomorrow)

#sprots8 大类id,爬取整个大类,getallow函数控制爬取 关键字
    channels = [1,909,60,81,57,59,70,50,51,31,43,44,45,42,46,47,38,37,58,49,48,55,54,592,52,53,56]
    for channel in channels:
        gettvsports8_epg(channel)



