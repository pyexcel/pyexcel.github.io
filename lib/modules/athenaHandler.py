import sys


def printf(pattern, *args):
    print pattern % args


if sys.platform=='js':
    import js
    jq = js.globals['$']
    LOG = js.globals['console'].log
    if jq:
        side = 'drawThread'
    else:
        side = 'mainThread'
    ahbase = object
    handlers = {}
    cevents = {}
    def clientFunction(func):
        handlers[func.func_name] = func
        return func
    def clientEvent(func):
        cevents[func.func_name] = func
        return func
    expose = lambda x: x
else:
    LOG = lambda *x: printf("%r", x)
    sys.path.pop(0)
    jq = js = None
    from nevow.athena import LiveElement as ahbase
    from nevow.athena import expose
    side = 'server'
    clientFunction = lambda x: x
    clientEvent = lambda x: x

import multiprocessing


pendingCalls = []

if side != 'server':
    def callLater(delay, f):
        def wrappableCall(*a):
            pendingCalls.remove((wrapper, f))
            return f(*a)
        wrapper = js.Function(wrappableCall)
        pendingCalls.append((wrapper, f))
        return js.globals['setTimeout'](wrapper, delay)

SKIP = False
RELAY = True


def sided(targetSide, actionOnWrongSide=SKIP):
    def decorator(func):
        def executor(self, *args, **kw):
            if self.side == targetSide:
                func(self, *args, **kw)
            elif actionOnWrongSide == RELAY:
                newArgs = []
                for arg in args:
                    print 65, arg, targetSide, self.side
                    newArgs.append(convert(arg))
                print 67, newArgs
                if targetSide == 'server':
                    self.callRemote(func.func_name, *newArgs)
                else:
                    self.relay(func.func_name, newArgs, kw)
            else:
                js.globals['console'].log(
                    'Skipping call to %s: %s doesn\'t relay and I was called from the wrong side' % (
                        func.func_name, func.func_name))
        executor.func_name = func.func_name
        return executor
    return decorator


if side == 'server':
    def convert(l):
        return l
else:
    jgetattr = js.eval('jgetattr=function(o,attr){return o[attr];};')
    def convert(l):
        if not isinstance(l, (list, tuple, js.Array)):
            if isinstance(l, js.Number):
                return (float(l))
            elif isinstance(l, js.String):
                return (unicode(l))
            elif isinstance(l, js.Object):
                r = {}
                for i in ['name', 'id', 'class', 'value', 'type', '__id__', 'objectID', 'classIdentifier']:
                    r[i] = convert(jgetattr(l, i))
                print 94, r, side
                return r
            elif isinstance(l, js.Undefined):
                return None
            return l
        o = []
        for i in tuple(l):
            o.append(convert(i))
        return o


class AthenaHandler(ahbase):
    if side == 'server':
        def __init__(self):
            self.jq = None
            self.side = 'server'
            self.started = True
        def relay(self, fn, args, kw):
            print 99, fn, args, kw
            self.callRemote(fn, *args)
    else:
        def relay(self, fn, args, kw):
            self.outQ.put([fn, args, kw])
        @sided('drawThread', RELAY)
        def callRemote(self, *args):
            self.athena.callRemote(*args)
        def __init__(self):
            self.jq = None
            self.side = None
            self.inQ = self.outQ = None
            self.tickWrapper = None
            self.workerProcess = None
            self.dispatchEventWrapper = None
            self.started = False
        def handlerDispatch(self, fn):
            wrapper = js.eval('(function(){function %s(){'
                              'var args=[];'
                              'for (var i=1;i<arguments.length;i++){'
                              '   args.push(arguments[i]);'
                              '}'
                              '%s.handler(%r, args);'
                              '}; return %s})()' % (fn, fn, fn, fn))
            wrapper.handler = self.dispatchFunctionWrapper
            return wrapper
        def eventDispatch(self, fn):
            wrapper = js.eval('(function(){function %s(self, node){'
                              '%s.handler(%r, self, node);'
                              '}; return %s})()' % (fn, fn, fn, fn))
            wrapper.handler = self.dispatchEventWrapper
            return wrapper
        def dispatchEvent(self, fn, liveElement, node):
            func = getattr(self, str(fn))
            func(liveElement, node)
        def dispatchFunction(self, fn, arguments):
            args = []
            for arg in arguments:
                args.append(convert(arguments[arg]))
            func = getattr(self, str(fn))
            func(*args)
        def call(self, inQ, outQ):
            if jq:
                self.side = 'drawThread'
            elif js:
                self.side = 'mainThread'
            else:
                self.side = 'server'
            self.jq = jq
            self.inQ = inQ
            self.outQ = outQ
            if self.side == 'drawThread':
                self.dispatchFunctionWrapper = js.Function(self.dispatchFunction)
                self.dispatchEventWrapper = js.Function(self.dispatchEvent)
                self.athenaClass = js.globals['TestPage']
                self.athena = self.athenaClass.fromAthenaID(1)
                for method in handlers:
                    self.athenaClass.method(self.handlerDispatch(method))
                for event in cevents:
                    self.athenaClass.method(self.eventDispatch(event))
                self.startTick()
            return self
        def startTick(self):
            self.tickWrapper = js.Function(self.tick)
            self.started = True
            self.tick()
        def tick(self):
            try:
                v = self.inQ.get(False)
                if isinstance(v, tuple):
                    v = list(v)
                if isinstance(v, list):
                    if len(v) < 2:
                        v.append([])
                    if len(v) < 3:
                        v.append({})
            except Exception:
                return
            finally:
                callLater(100, self.tickWrapper)
            if callable(v[0]):
                return v[0](*v[1], **v[2])
            getattr(self, v[0])(*v[1], **v[2])
        def start(self):
            q1 = multiprocessing.Queue()
            q2 = multiprocessing.Queue()
            workerProcess = multiprocessing.Process(target=self.call, args=(q1, q2))
            def cont():
                workerProcess.start()
                self.workerProcess = workerProcess
                self.call(q2, q1).startTick()
            return callLater(100, cont)

if side=='server':
    import nevow.athena
    class MappingResource(nevow.athena.MappingResource):
        def resourceFactory(self, obj):
            if isinstance(obj, (str, unicode)):
                return nevow.static.File(obj)
            return obj

class LivePage(nevow.athena.LivePage):
    if side=='server':

        def child_jsmodule(self, ctx):
            return MappingResource(self.jsModules.mapping)
        def child_cssmodule(self, ctx):
            """
            Return a L{MappingResource} wrapped around L{cssModules}.
            """
            return MappingResource(self.cssModules.mapping)

