from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db
import os
import hashlib


class Account(db.Model):
    username = db.StringProperty()
    token = db.StringProperty()
    
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