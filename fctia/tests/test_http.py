"""HTTP smoke tests for the actual local server and static web assets."""
import json
import sys
import threading
import unittest
from pathlib import Path
from http.client import HTTPConnection
from http.server import HTTPServer
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from fctia.local_api import Office, handler_for

class HTTPTest(unittest.TestCase):
    def setUp(self):
        self.server=HTTPServer(("127.0.0.1",0),None)
        self.port=self.server.server_port
        self.host=f"127.0.0.1:{self.port}"
        self.token="test-only-token"
        self.ready=threading.Event()
        def serve():
            office=Office()
            self.server.RequestHandlerClass=handler_for(office,self.token,self.host)
            self.ready.set()
            try: self.server.serve_forever()
            finally: office.brain.close()
        self.thread=threading.Thread(target=serve,daemon=True)
        self.thread.start()
        self.ready.wait(5)
        self.addCleanup(self.close)
    def close(self):
        self.server.shutdown()
        self.thread.join(5)
        self.server.server_close()
    def request(self,path,method="GET",data=None,auth=True,headers=None):
        h={"Host":self.host}
        if auth: h["Authorization"]="Bearer "+self.token
        if data is not None: h["Content-Type"]="application/json"
        h.update(headers or {})
        conn=HTTPConnection("127.0.0.1",self.port,timeout=5)
        try:
            conn.request(method,path,body=None if data is None else json.dumps(data),headers=h)
            r=conn.getresponse()
            return r.status,dict(r.getheaders()),r.read().decode("utf-8")
        finally: conn.close()
    def test_assets(self):
        for path,expected in [("/","FCT.IA Office"),("/office.css","background"),("/office.js","api(")]:
            status,headers,body=self.request(path,auth=False)
            self.assertEqual(status,200)
            self.assertIn(expected,body)
            self.assertIn("frame-ancestors 'none'",headers["Content-Security-Policy"])
    def test_auth_and_origin(self):
        self.assertEqual(self.request("/api/agents",auth=False)[0],401)
        self.assertEqual(self.request("/api/agents",headers={"Origin":"https://example.invalid"})[0],403)
        self.assertEqual(self.request("/api/agents",headers={"Host":"example.invalid"})[0],403)
        self.assertEqual(len(json.loads(self.request("/api/agents")[2])),4)
        self.assertEqual(self.request("/../local_api.py")[0],404)
    def test_task_http(self):
        def post(path,data):
            status,_,body=self.request(path,"POST",data)
            self.assertEqual(status,200,body)
            return json.loads(body)
        task=post("/api/tasks",{"title":"Briefing fictício","skill":"briefing","payload":{"synthetic":True,"itens":["Reunião fictícia"]}})
        path="/api/tasks/"+task["id"]
        post(path+"/assign",{"agent":"executivo"})
        self.assertEqual(post(path+"/run",{})["state"],"awaiting_review")
        post(path+"/review",{"approve":True,"comment":"Revisado"})
        k=post(path+"/knowledge",{})
        post("/api/brain/approve",k)
        self.assertEqual(len(json.loads(self.request("/api/brain?scope=executivo")[2])),1)
