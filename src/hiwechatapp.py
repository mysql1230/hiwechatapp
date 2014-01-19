#! /usr/bin/env python 
# -*- coding: utf-8 -*- 

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db
import os
import hashlib
import time

class Account(db.Model):
    username = db.StringProperty()
    token = db.StringProperty()


class WeChatMessage():
    def __init__(self,ToUserName='',FromUserName='',CreateTime='',MsgType='',Content='',MsgId='',Event=''):
        self.ToUserName = ToUserName
        self.FromUserName = FromUserName
        self.CreateTime = CreateTime
        self.MsgType = MsgType
        self.Content = str(Content)
        self.MsgId = MsgId
        self.Event = Event
    
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
        data = '<xml><ToUserName><![CDATA[' + self.ToUserName + ']]></ToUserName>'
        data += '<FromUserName><![CDATA[' + self.FromUserName + ']]></FromUserName>'
        data += '<CreateTime><![CDATA[' + self.CreateTime + ']]></CreateTime>'
        data += '<MsgType><![CDATA[' + self.MsgType + ']]></MsgType>'
        data += '<Content><![CDATA[' + self.Content.decode('utf-8') + ']]></Content></xml>'
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
                replyMessage.Content = '欢迎您订阅Burke空间！请回复1,2,3,4,5,6,7得到更多娱乐 :)'
            elif (receiveMessage.Event.find('unsubscribe') >=0):
                replyMessage.Content = '你竟然取消订阅了？！成功的路上怎么能缺少您的支持呢 :('
            else:
                replyMessage.Content = '订阅号暂不支持这个操作：' + receiveMessage.Event
        elif (receiveMessage.MsgType.find('text') >=0):
            if (receiveMessage.Content.find('1') >=0):
                replyMessage.Content = '你是最棒的!'
            elif (receiveMessage.Content.find('2') >=0):
                replyMessage.Content = '你马马虎虎吧!'
            elif (receiveMessage.Content.find('3') >=0):
                replyMessage.Content = '你是个傻瓜!'
            elif (receiveMessage.Content.find('4') >=0):
                replyMessage.Content = '笑话1：昨晚上与女友在烧烤店吃烧烤，点了份烤肉“骨肉相连”不一会服务员端着盘子走过来并温馨的说：你们的骨肉。。 哥顿了一下，，现在的人说话能不能别这么简洁。'
            elif (receiveMessage.Content.find('5') >=0):
                replyMessage.Content = '笑话2：“待我长发及腰娶我可好？”“不，我心有所属。”“她哪里比我好，她是个尼姑啊。”“不许你这么讲她，请自重！方丈……”'
            elif (receiveMessage.Content.find('6') >=0):
                replyMessage.Content = '罗素1：每一个人的生活都应该像河水一样——开始是细小的，被限制在狭窄的两岸之间，然后热烈地冲过巨石，滑下瀑布。渐渐地，河道变宽了，河岸扩展了，河水流得平稳了。最后河水流入了海洋，不再有明显的间断和停顿，而后便毫无痛苦地摆脱了自身的存在。'
            elif (receiveMessage.Content.find('7') >=0):
                replyMessage.Content = '罗素2：有那么两种类型的工作，一种是改变地球表面上和表面附近物体与其他物体的相对位置，另外一种是指挥别人从事第一项工作。'
            else:
                replyMessage.Content = '欢迎您来到Burke空间，请回复1,2,3,4,5,6,7得到更多娱乐 :)'
        else:
            replyMessage.Content = '对不起，目前只支持文本，暂不支持图片和语音等操作! 欢迎您来到Burke空间，请回复1,2,3,4,5,6,7得到更多娱乐 :)'
        
        self.response.headers.add_header("Content-type","text/xml")
        self.response.out.write(replyMessage.toXML())
        
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
        



application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                      ('/weChatApp/?(?P<op>[^/]*)/?(?P<user>[^/]*)', WeChatApp),
                                      ('/account/?(?P<op>[^/]*)', AccountApp),
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