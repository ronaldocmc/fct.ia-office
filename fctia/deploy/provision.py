"""Provision experimental organization through Paperclip's API.
Dry run by default; apply only to an isolated authenticated local instance.
"""
import argparse
import json
import os
import uuid
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlparse
from urllib.error import HTTPError

TEMPLATE = Path(__file__).resolve().parents[1] / "templates" / "organization-v01.json"

class API:
    def __init__(self, base, cookie):
        parsed = urlparse(base)
        if parsed.scheme != "http" or parsed.hostname not in ("localhost", "127.0.0.1") or parsed.username or parsed.password or parsed.path not in ("", "/") or parsed.query or parsed.fragment:
            raise ValueError("Use somente uma instância experimental local via loopback")
        self.base, self.cookie = base.rstrip("/"), cookie

    def call(self, method, path, payload=None):
        from urllib.request import build_opener, HTTPRedirectHandler
        class NoRedirect(HTTPRedirectHandler):
            def redirect_request(self, *args, **kwargs):
                return None
        req = Request(self.base + "/api" + path, method=method,
                      headers={"Cookie": self.cookie, "Content-Type": "application/json", "Origin": self.base},
                      data=None if payload is None else json.dumps(payload).encode())
        try:
            with build_opener(NoRedirect()).open(req, timeout=30) as res:
                return json.load(res)
        except HTTPError as exc:
            raise RuntimeError(f"{method} {path}: HTTP {exc.code}; nenhuma repetição automática") from None

def agent_payload(profile, parent, company_id):
    return {
        "setupId": str(uuid.uuid5(uuid.UUID(company_id), "fctia:" + profile["id"])),
        "name": profile["name"], "title": profile["area"],
        "role": "ceo" if parent is None else "general",
        "reportsTo": parent, "capabilities": profile["mission"],
        "adapterType": "process", "runner": "legacy",
        "adapterConfig": {"command": "/bin/false", "args": [], "timeoutSec": 10},
        "runtimeConfig": {"heartbeat": {"enabled": False, "intervalSec": 0}},
        "permissions": {"canCreateAgents": False, "canCreateSkills": False},
        "metadata": {"fctiaProfile": profile["id"]},
    }

def provision(api, spec):
    org = spec["organization"]
    companies = api.call("GET", "/companies")
    matches = [c for c in companies if c["name"] == org["name"]]
    if len(matches) > 1:
        raise RuntimeError("Organizações duplicadas; revisão manual necessária")
    company = matches[0] if matches else api.call("POST", "/companies", {"name":org["name"], "description":org["description"]})
    if company.get("description") != org["description"]:
        raise RuntimeError("Organização existente não corresponde ao experimento")
    cid = company["id"]
    existing = api.call("GET", f"/companies/{cid}/agents")
    if any(not a.get("metadata", {}).get("fctiaProfile") for a in existing):
        raise RuntimeError("Organização contém agentes fora do modelo; operação interrompida")
    ids = {}
    for p in spec["agents"]:
        parent = ids.get(p["reportsTo"])
        if p["reportsTo"] is not None and parent is None:
            raise RuntimeError("Hierarquia inválida")
        payload = agent_payload(p, parent, cid)
        found = [a for a in existing if a["id"] == payload["setupId"]]
        if found:
            agent = found[0]
        else:
            agent = api.call("POST", f"/companies/{cid}/agents", payload)
        if agent.get("id") != payload["setupId"] or agent.get("reportsTo") != parent:
            raise RuntimeError("Cadastro divergente; revisão manual")
        if "setup" not in agent.get("lifecycleHolds", []):
            raise RuntimeError("Agente sem bloqueio de setup; interrompa e revise manualmente")
        ids[p["id"]] = agent["id"]
    api.call("PATCH", f"/companies/{cid}", {"requireBoardApprovalForNewAgents": True})
    return {"companyId": cid, "agents": ids, "mode": "setup-only"}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://localhost:3100")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    spec = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    if not args.apply:
        print(json.dumps(spec, ensure_ascii=False, indent=2))
        return
    cookie = os.environ.get("FCTIA_BOARD_COOKIE")
    if not cookie:
        parser.error("Sessão de administrador experimental obrigatória em FCTIA_BOARD_COOKIE")
    print(json.dumps(provision(API(args.base, cookie), spec), indent=2))

if __name__ == "__main__":
    main()
