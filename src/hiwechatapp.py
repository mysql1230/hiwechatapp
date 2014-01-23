#! /usr/bin/env python 
# -*- coding: utf-8 -*- 

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db 
import os
import hashlib
import time
import cgi
import random

class Account(db.Model):
    username = db.StringProperty()
    token = db.StringProperty()
    
class Info(db.Model):
    iType = db.StringProperty()
    text = db.StringProperty(multiline=True)


class WeChatMessage():
    def __init__(self,ToUserName='',FromUserName='',CreateTime='',MsgType='',Content='',MsgId='',Event='',MediaId=''):
        self.ToUserName = ToUserName
        self.FromUserName = FromUserName
        self.CreateTime = CreateTime
        self.MsgType = MsgType
        self.Content = str(Content)
        self.MsgId = MsgId
        self.Event = Event
        self.MediaId = MediaId
    
    def parseXML(self, data):
        import xml.dom.minidom
        root = xml.dom.minidom.parseString(data)
        self.ToUserName = self._getElementData(root,"ToUserName")
        self.FromUserName = self._getElementData(root,"FromUserName")
        self.CreateTime = self._getElementData(root,"CreateTime")
        self.MsgType = self._getElementData(root,"MsgType")
        self.Content = self._getElementData(root,"Content")
        self.MsgId = self._getElementData(root,"MsgId")
        self.Event = self._getElementData(root,"Event")
        
    def _getElementData(self, root, tagName):
        value = ''
        try:
            value = root.getElementsByTagName(tagName)[0].firstChild.data
        except:
            pass
        return value
    
    def toXML(self):
        if (self.MediaId == ''):
            return self._to_Text_XML()
        else:
            return self._to_Image_XML()
    
    def _to_Text_XML(self):
        data = '<xml><ToUserName><![CDATA[' + self.ToUserName + ']]></ToUserName>'
        data += '<FromUserName><![CDATA[' + self.FromUserName + ']]></FromUserName>'
        data += '<CreateTime><![CDATA[' + self.CreateTime + ']]></CreateTime>'
        data += '<MsgType><![CDATA[' + self.MsgType + ']]></MsgType>'
        data += '<Content><![CDATA[' + self.Content.decode('utf8') + ']]></Content></xml>'
        return data
    
    def _to_Image_XML(self):
        data = '<xml><ToUserName><![CDATA[' + self.ToUserName + ']]></ToUserName>'
        data += '<FromUserName><![CDATA[' + self.FromUserName + ']]></FromUserName>'
        data += '<CreateTime><![CDATA[' + self.CreateTime + ']]></CreateTime>'
        data += '<MsgType><![CDATA[' + 'image' + ']]></MsgType>'
        data += '<Image><MediaId><![CDATA[' + self.MediaId + ']]></MediaId></Image></xml>'
        return data
    
    
class MainPage(webapp.RequestHandler):
    def get(self):
        self.response.out.write(myTemplateRender('main.html', {}))
        

class WeChatApp(webapp.RequestHandler):
    def get(self, op, user):
        if (op == 'verify'):
            self.verify(user)
        elif (op == 'ls'):
            self.ls()
        else:
            self.ping()
    
    def post(self, op, user):
        receiveMessage = WeChatMessage()
        receiveMessage.parseXML(self.request.body)
        replyMessage = WeChatMessage(receiveMessage.FromUserName,receiveMessage.ToUserName,str(long(time.time())),'text')
        
        if (receiveMessage.MsgType.find('event') >=0):
            if (receiveMessage.Event.find('subscribe') >=0):
                replyMessage.Content = '欢迎您订阅Burke空间！请回复1(笑话),2(名言),3(其他)随机得到更多娱乐 :)'
            elif (receiveMessage.Event.find('unsubscribe') >=0):
                replyMessage.Content = '你竟然取消订阅了？！成功的路上怎么能缺少您的支持呢 :('
            else:
                replyMessage.Content = '订阅号暂不支持这个操作：' + receiveMessage.Event
        elif (receiveMessage.MsgType.find('text') >=0):
            if (receiveMessage.Content.find('1') >=0):
                replyMessage.Content = self._getRandomMessage('joke')
            elif (receiveMessage.Content.find('2') >=0):
                replyMessage.Content = self._getRandomMessage('ana')
            elif (receiveMessage.Content.find('3') >=0):
                replyMessage.Content = self._getRandomMessage('other')
            elif (receiveMessage.Content.find('0') >=0):
                replyMessage.Content = self._getRandomMessage('test')
            else:
                replyMessage.Content = '欢迎您来到Burke空间，请回复1(笑话),2(名言),3(其他)随机得到更多娱乐 :)'
        else:
            replyMessage.Content = '对不起，目前只支持文本，暂不支持图片和语音等操作! 欢迎您来到Burke空间，请回复1(笑话),2(名言),3(其他)随机得到更多娱乐 :)'
        
        self.response.headers.add_header("Content-type","text/xml")
        self.response.out.write(replyMessage.toXML())
    
    def _getRandomMessage(self, iType):
        infos = Info.gql("WHERE iType = :1", iType)
        num = random.randint(1, infos.count())
        message = infos.fetch(1, num-1)[0].text.encode('utf8')
        return message
        
    def ping(self):
        echostr = self.request.get('echostr')
        self.response.out.write(echostr)
        
    def ls(self):
        self.response.out.write(myTemplateRender('weChat/lsAPI.html', {}))
        
    def verify(self, user):
        signature = self.request.get('signature')
        timestamp = self.request.get('timestamp')
        nonce = self.request.get('nonce')
        echostr = self.request.get('echostr')
        isVerified = self.verifySignature(user, signature, timestamp, nonce)
        self.response.out.write(isVerified)
    
    def verifySignature(self, user, signature, timestamp, nonce):
        token = self.getToken(user)
        sortedLis = sorted([token, timestamp, nonce])
        sortedStr = ''.join(sortedLis)
        shaStr = hashlib.sha1(sortedStr).hexdigest()
        
        if (shaStr == signature):
            return "True"
        else:
            return "False"
        
    def getToken(self, user):
        apis = Account.gql("WHERE username = :1", user)
        for api in apis:
            token = api.token
            return token
        else:
            return ''
        

class AccountApp(webapp.RequestHandler):
    def get(self,op):
        if (op == 'new' or op == 'update'):
            self.update()
        elif (op == 'delete'):
            self.delete()
        else:
            self.list()
            
    def list(self):
        template_values = {
            'accounts': Account.all(),
            }
        
        self.response.out.write(myTemplateRender('account/listAccounts.html', template_values))
    
    def update(self):
        template_values = {
            'username': self.request.get('username'),
            'token' : self.request.get('token'),
            }
        
        self.response.out.write(myTemplateRender('account/newAccount.html', template_values))
        
    def delete(self):
        username = self.request.get('username')
        for account in Account.gql("WHERE username = :1", username):
            account.delete()
            account.delete()
        
        self.list()

    def post(self, op):
        username = self.request.get('username')
        token = self.request.get('token')
        
        isNew = True
        for account in Account.gql("WHERE username = :1", username):
            account.token = token
            account.put()
            account.put()
            isNew = False
            
        if isNew:
            account = Account()
            account.username = username
            account.token = token
            account.put()
            account.put()
        
        self.list()
        

class InfoApp(webapp.RequestHandler):
    def get(self,op):
        if (op == 'new'):
            self.new()
        elif (op == 'update'):
            self.update()
        elif (op == 'delete'):
            self.delete()
        else:
            self.list()
            
    def list(self):
        template_values = {
            'infos': Info.all().order("-iType"),
            'types': ['笑话','名言','其他','测试'],
            }
        
        self.response.out.write(myTemplateRender('info/listInfos.html', template_values))
    
    def new(self):
        template_values = {
            'id': '',
            'iType' : '',
            'text' : '',
            'types': ['笑话','名言','其他','测试'],
            }
        
        self.response.out.write(myTemplateRender('info/newInfo.html', template_values))
        
    def update(self):
        infoId = self.request.get('id')
        info = Info.get_by_id(long(infoId))
        iType = info.iType
        text = info.text
        template_values = {
            'id': infoId,
            'iType' : iType,
            'text' : text,
            'types': ['笑话','名言','其他','测试'],
            }
        
        self.response.out.write(myTemplateRender('info/newInfo.html', template_values))
        
    def delete(self):
        infoId = self.request.get('id')
        info = Info.get_by_id(long(infoId))
        info.delete()
        info.delete()
        
        self.list()

    def post(self, op):
        infoId = self.request.get('id')
        iType = self.request.get('iType')
        text = self.request.get('text')
        try:
            import sys
            code = sys.getdefaultencoding()
            if code != 'utf8':   
                reload(sys)   
                sys.setdefaultencoding('utf8') 
            text = self.request.get('text')
        except:
            pass
        if infoId == '':
            info = Info()
            info.iType = iType
            info.text = text
            info.put()
            info.put()
        else:
            info = Info.get_by_id(long(infoId))
            info.iType = iType
            info.text = text
            info.put()
            info.put()
        
        self.list()



application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                      ('/weChatApp/?(?P<op>[^/]*)/?(?P<user>[^/]*)', WeChatApp),
                                      ('/account/?(?P<op>[^/]*)', AccountApp),
                                      ('/info/?(?P<op>[^/]*)', InfoApp),
                                     ], debug=True)

def myTemplateRender(template_file, template_values):
    APP_BASE = os.path.dirname(__file__)
    TEMPLATE_DIRS = os.path.join(APP_BASE, 'template')
    path = os.path.join(TEMPLATE_DIRS, template_file)
    template_values['TEMPLATE_DIRS'] = TEMPLATE_DIRS
    return template.render(path, template_values)
    
    
def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()