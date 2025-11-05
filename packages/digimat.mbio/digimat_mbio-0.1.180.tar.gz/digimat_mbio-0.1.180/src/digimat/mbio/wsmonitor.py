import json
from .task import MBIOTask
from .xmlconfig import XMLConfig

from .wserver import TemporaryWebServer


class JQueryUI():
    def __init__(self, title=None):
        self._header=''
        self._body=''
        if title:
            self.header(f'<title>{title}</title>')

        # self.header('<link rel="stylesheet" href="/www/jquery-ui/jquery-ui.min.css">')
        # self.header('<script src="/www/jquery-ui/external/jquery/jquery.js"></script>')
        # self.header('<script src="/www/jquery-ui/jquery-ui.min.js"></script>')

        # https://jquery.com/download/
        self.header('<script src="/www/jquery/jquery.min.js"></script>')

        # https://getbootstrap.com/docs/5.0/getting-started/download/
        self.header('<link href="/www/Bootstrap/dist/css/bootstrap.min.css" rel="stylesheet">')
        self.header('<script src="/www/Bootstrap/dist/js/bootstrap.bundle.min.js"</script>')

        # https://datatables.net/download/
        self.header('<link href="/www/DataTables/datatables.min.css" rel="stylesheet">')
        self.header('<script src="/www/DataTables/datatables.min.js"></script>')

        self.style('.red-button {background-color: red; color: white;}')

    def header(self, data):
        if data:
            self._header+=data
            self._header+='\n'

    def style(self, data):
        if data:
            self.header(f'<style>{data}</style>')

    def body(self, data):
        if data:
            self._body+=data
            self._body+='\n'

    def write(self, data):
        self.body(data)

    def data(self):
        data='<html>'
        data+='<head>'
        data+=self._header
        data+='</head>'
        data+='<body>'
        data+=self._body
        data+='</body>'
        data+='</html>'
        return data

    def bytes(self):
        return self.data().encode('utf-8')
        self.write('</head>')
        self.write('<body>')

    def button(self, bid, name):
        self.write(f'<button id="{bid}" class="ui-button red-button ui-widget ui-corner-all">{name}</button>')





class MBIOWsMonitor(MBIOTask):
    def initName(self):
        return 'wsmon'

    @property
    def wserver(self) -> TemporaryWebServer:
        return self._wserver

    def onInit(self):
        self._wserver=None

    def cb_mycallback(self, handler, params):
        handler.send_response(200)
        handler.send_header("Content-Type", "text/html; charset=utf-8")
        handler.end_headers()

        h=JQueryUI('MBIO Processor Monitor')
        # h.button('test', 'Let\'s GO!')

        mbio=self.getMBIO()
        for g in mbio.gateways.all():
            h.button(g.name, str(g))

        handler.wfile.write(h.bytes())

    def cb_headers_json(self, handler):
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json; charset=utf-8")
        handler.end_headers()

    def cb_write_json(self, handler, data):
        self.cb_headers_json(handler)
        data=json.dumps(data)
        handler.wfile.write(data.encode('utf-8'))

    def cb_gettasks(self, handler, params):
        mbio=self.getMBIO()
        items=[]
        for t in mbio.tasks.all():
            item={'key': t.key}
            item['class']=t.__class__.__name__
            item['state']=t.statestr(),
            item['statetime']=int(t.statetime())
            item['error']=t.isError()
            items.append(item)

        data={'data': items}
        self.cb_write_json(handler, data)

    def cb_getgateways(self, handler, params):
        mbio=self.getMBIO()
        items=[]
        for g in mbio.gateways.all():
            item={'key': g.key, 'name': g.name, 'host': g.host, 'mac': g.MAC, 'model': g.model}
            item['class']=g.__class__.__name__
            state='CLOSED'
            if g.isOpen():
                state='OPEN'
            item['state']=state
            item['error']=g.isError()
            items.append(item)

        data={'data': items}
        self.cb_write_json(handler, data)

    def cb_getgatewaydevices(self, handler, params):
        mbio=self.getMBIO()
        g=mbio.gateway(params.get('gateway'))

        items=[]
        if g is not None:
            for d in g.devices.all():
                self.microsleep()
                item={'address': d.address, 'key': d.key, 'vendor': d.vendor, 'model': d.model, 'state': d.statestr()}
                item['class']=d.__class__.__name__
                item['version']=d.version
                item['statetime']=int(d.statetime())
                item['countmsg']=d.countMsg
                item['countmsgerr']=d.countMsgErr
                item['error']=d.isError()
                item['countvalues']=d.values.count()
                items.append(item)

        data={'data': items}
        self.cb_write_json(handler, data)

    def cb_getdevicevalues(self, handler, params):
        mbio=self.getMBIO()
        g=mbio.gateway(params.get('gateway'))

        items=[]
        if g is not None:
            d=g.device(params.get('device'))
            if d is not None:
                for v in d.values.all():
                    self.microsleep()
                    item={'key': v.key, 'value': v.value,
                          'valuestr': v.valuestr(),
                          'unit': v.unit, 'unitstr': v.unitstr(),
                          'flags': v.flags, 'age': int(v.age()), 'tag': v.tag}
                    item['class']=v.__class__.__name__
                    item['error']=v.isError()
                    item['writable']=v.isWritable()
                    item['digital']=v.isDigital()
                    items.append(item)

        data={'data': items}
        self.cb_write_json(handler, data)

    def cb_getvalues(self, handler, params):
        mbio=self.getMBIO()

        items=[]
        for v in mbio.values(params.get('filter')):
            self.microsleep()
            item={'key': v.key, 'value': v.value,
                    'valuestr': v.valuestr(),
                    'unit': v.unit, 'unitstr': v.unitstr(),
                    'flags': v.flags, 'age': int(v.age()), 'tag': v.tag}
            item['class']=v.__class__.__name__
            item['error']=v.isError()
            item['writable']=v.isWritable()
            item['digital']=v.isDigital()
            items.append(item)

        data={'data': items}
        self.cb_write_json(handler, data)

    def onLoad(self, xml: XMLConfig):
        mbio=self.getMBIO()
        port=xml.getInt('port', 8001)
        # interface=mbio.interface
        interface='0.0.0.0'
        ws=TemporaryWebServer('/tmp/wsmonitor', port=port, host=interface, logger=self.logger)
        if ws:
            ws.registerGetCallback('/api/v1/gettasks', self.cb_gettasks)
            ws.registerGetCallback('/api/v1/getgateways', self.cb_getgateways)
            ws.registerGetCallback('/api/v1/getgatewaydevices', self.cb_getgatewaydevices)
            ws.registerGetCallback('/api/v1/getdevicevalues', self.cb_getdevicevalues)
            ws.registerGetCallback('/api/v1/getvalues', self.cb_getvalues)
            ws.registerGetCallback('/test', self.cb_mycallback)
            self._wserver=ws

    def poweron(self):
        ws=self.wserver
        if ws:
            ws.disableAutoShutdown()
            ws.linkPath('/usr/lib/www')
            ws.linkPath('~/Dropbox/tmp/www')
            ws.start()
        return True

    def poweroff(self):
        ws=self.wserver
        if ws:
            ws.stop()
        return True

    def run(self):
        return 1.0


if __name__ == "__main__":
    pass
