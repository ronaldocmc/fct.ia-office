"""Single-user local laboratory. Never expose this server on a network."""
import argparse
import hmac
import json
import secrets
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlsplit, parse_qs
from pathlib import Path
from .runtime.tasks import TaskEngine
from .brain.store import Brain

class Office:
    def __init__(self, brain_path=":memory:"):
        self.engine = TaskEngine()
        self.brain = Brain(brain_path)
    def dispatch(self, method, path, data=None):
        url = urlsplit(path)
        parts = url.path.strip("/").split("/")
        data = {} if data is None else data
        if not isinstance(data, dict):
            raise ValueError("Objeto JSON obrigatório")
        if method == "GET":
            if parts == ["api","agents"]: return list(self.engine.profiles.values())
            if parts == ["api","tasks"]: return list(self.engine.tasks.values())
            if parts == ["api","events"]: return self.engine.events
            if parts == ["api","brain"]:
                q = parse_qs(url.query)
                scope = q.get("scope",[""])[0]
                if scope not in self.engine.profiles: raise ValueError("Escopo inválido")
                return self.brain.search(scope,q.get("q",[""])[0])
            if parts == ["api","brain","pending"]:
                return [dict(r) for r in self.brain.db.execute("SELECT * FROM knowledge WHERE state='pending' ORDER BY created_at")]
        if method == "POST":
            if parts == ["api","tasks"]:
                return self.engine.create(data["title"],data["skill"],data["payload"])
            if len(parts)==4 and parts[:2]==["api","tasks"]:
                tid, action = parts[2:]
                if action == "assign": return self.engine.assign(tid,data["agent"])
                if action == "run": return self.engine.run(tid)
                if action == "review": return self.engine.review(tid,data["approve"],"gestor-local",data["comment"])
                if action == "revise": return self.engine.revise(tid,data["payload"])
                if action == "knowledge":
                    task = self.engine.tasks[tid]
                    if task["state"] != "approved": raise ValueError("Tarefa ainda não aprovada")
                    source = "task:"+tid
                    row = self.brain.db.execute("SELECT id FROM knowledge WHERE source=? AND scope=?", (source,task["agent"])).fetchone()
                    ident = row["id"] if row else self.brain.propose(task["agent"],task["result"]["result"],source)
                    return {"id":ident,"scope":task["agent"]}
            if parts == ["api","brain","approve"]:
                if data["scope"] not in self.engine.profiles: raise ValueError("Escopo inválido")
                self.brain.approve(data["scope"],data["id"],"gestor-local")
                return {"approved":True}
        raise LookupError("Rota não encontrada")

def handler_for(office, token, authority):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def reply(self, status, obj):
            raw=json.dumps(obj,ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type","application/json; charset=utf-8")
            self.send_header("Cache-Control","no-store")
            self.send_header("X-Content-Type-Options","nosniff")
            self.send_header("Content-Length",str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
        def handle_api(self):
            if self.headers.get("Host") != authority:
                return self.reply(403,{"error":"Host inválido"})
            origin=self.headers.get("Origin")
            if origin is not None and origin != "http://"+authority:
                return self.reply(403,{"error":"Origem inválida"})
            if not hmac.compare_digest(self.headers.get("Authorization",""),"Bearer "+token):
                return self.reply(401,{"error":"Token local obrigatório"})
            try:
                data=None
                if self.command=="POST":
                    if self.headers.get_content_type()!="application/json":
                        return self.reply(415,{"error":"JSON obrigatório"})
                    length=int(self.headers.get("Content-Length","0"))
                    if not 0 < length <= 65536:
                        return self.reply(400,{"error":"Tamanho inválido"})
                    data=json.loads(self.rfile.read(length))
                self.reply(200,office.dispatch(self.command,self.path,data))
            except KeyError:
                self.reply(400,{"error":"Campo ou identificador inexistente"})
            except (ValueError,TypeError,AttributeError):
                self.reply(400,{"error":"Entrada ou estado inválido"})
            except LookupError:
                self.reply(404,{"error":"Recurso não encontrado"})
        do_GET=handle_api
        do_POST=handle_api
    return Handler

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--port",type=int,default=8765)
    parser.add_argument("--brain",default=":memory:")
    args=parser.parse_args()
    if not 1024<=args.port<=65535: parser.error("Porta inválida")
    token=secrets.token_urlsafe(32)
    office=Office(args.brain)
    server=HTTPServer(("127.0.0.1",args.port),handler_for(office,token,f"127.0.0.1:{args.port}"))
    print(f"Laboratório local: http://127.0.0.1:{args.port}",flush=True)
    print("Token de sessão (não compartilhar): "+token,flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally:
        server.server_close()
        office.brain.close()
if __name__=="__main__": main()
