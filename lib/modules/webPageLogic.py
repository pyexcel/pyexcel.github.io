from athenaHandler import AthenaHandler, expose, clientFunction, clientEvent, sided, SKIP, RELAY, js, side, LivePage
import os
from nevow.static import File
from twisted.python.filepath import FilePath
from nevow.loaders import xmlfile, stan
website = FilePath(__file__).sibling('website')

class ClientHandler(AthenaHandler):
    docFactory = xmlfile(website.child('testpage.html').path, 'TestPattern')
    docFactory.useDocType = '<!DOCTYPE html>'
    jsClass = u"TestPage"
    @clientFunction
    @sided('mainThread', RELAY)
    def helloClient(self, welcomeMessage):
        print welcomeMessage
    @clientEvent
    @sided('drawThread', SKIP)
    def greetServer(self, liveElement, node):
        self.helloServer('button pressed', '')
    @clientEvent
    @expose
    @sided('server', RELAY)
    def helloServer(self, le, node):
        print 15, le, node
        self.helloClient(u"Pleased to meet you")
    @expose
    def echo(self, msg):
        self.callRemote('echo', msg)

class TestPage(LivePage):
    docFactory = xmlfile(website.child('testpage.html').path)
    docFactory.useDocType = '<!DOCTYPE html>'
    def __init__(self, *args):
        LivePage.__init__(self, *args)
        self.jsModules.mapping[u'TestPage'] = website.child('js').child('testPage.js').path
        self.jsModules.mapping[u'PyPyWorker'] = website.child('js').child('PyPyWorker.js').path
        self.jsModules.mapping[u'jqconsole'] = website.child('js').child('jqconsole.min.js').path
        self.jsModules.mapping[u'pypyDrawThread'] = website.child('js').child('pypyDrawThread.js').path
        self.jsModules.mapping[u'PyPyJS'] = website.child('js').child('pypy.js-0.2.0').child('lib').child('pypy.js').path
        self.jsModules.mapping[u'lz_string'] = website.child('js').child('lz-string.min.js').path
    def render_TestElement(self, *_):
        """
        Replace the tag with a new L{MenuCreatorElement}.
        """
        c = ClientHandler()
        c.setFragmentParent(self)
        return c
    def locateChild(self, ctx, segments):
        if segments[0]=='sleep':
            import time
            time.sleep(float(segments[1]))
            return '', ()
        if segments[0] in os.listdir('website'):
            s=list(segments)
            p=website
            while p.exists() and s:
                p=p.child(s.pop(0))
            if p.exists:
                if p.isdir():
                    d = DirectoryLister('website/'+'/'.join(segments), os.listdir(p.path))
                    d.addSlash=True
                    return d, s
                return File(p.path), s
            else:
                return LivePage.locateChild(self, ctx, segments)
        if segments[0] == '':
            return self, ()
        return LivePage.locateChild(self, ctx, segments)
