"""Experimental task lifecycle, independent of Paperclip; no external actions."""
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from uuid import uuid4
from .skills import execute

TEMPLATE = Path(__file__).resolve().parents[1] / "templates" / "organization-v01.json"

class TaskEngine:
    def __init__(self, db=None):
        self.profiles = {a["id"]: a for a in json.loads(TEMPLATE.read_text(encoding="utf-8"))["agents"]}
        self.tasks = {}
        self.events = []
        self.db = db
        if db is not None:
            with db:
                db.execute('CREATE TABLE IF NOT EXISTS office_tasks (id TEXT PRIMARY KEY, snapshot TEXT NOT NULL)')
                db.execute('CREATE TABLE IF NOT EXISTS office_events (seq INTEGER PRIMARY KEY AUTOINCREMENT, event TEXT NOT NULL)')
            self.tasks = {row[0]: json.loads(row[1]) for row in db.execute('SELECT id,snapshot FROM office_tasks ORDER BY rowid')}
            self.events = [json.loads(row[0]) for row in db.execute('SELECT event FROM office_events ORDER BY seq')]
            for task in self.tasks.values():
                if task['state'] == 'running':
                    task['state'] = 'failed'
                    self._record(task, 'runtime-local', 'interrupted')

    def _record(self, task, actor, action):
        event = {"task_id": task["id"], "actor": actor, "action": action,
                 "state": task["state"], "at": datetime.now(timezone.utc).isoformat()}
        if action in ("approved", "revision_requested"):
            event["review"] = deepcopy(task["review"])
        if action == "draft_generated":
            event["result"] = deepcopy(task["result"])
        if self.db is not None:
            with self.db:
                self.db.execute("INSERT INTO office_tasks(id,snapshot) VALUES (?,?) ON CONFLICT(id) DO UPDATE SET snapshot=excluded.snapshot",
                                (task["id"],json.dumps(task,ensure_ascii=False)))
                self.db.execute("INSERT INTO office_events(event) VALUES (?)",(json.dumps(event,ensure_ascii=False),))
        self.events.append(event)

    def create(self, title, skill, payload):
        if not isinstance(title, str) or not title.strip() or len(title) > 200:
            raise ValueError("Título inválido")
        if not isinstance(payload, dict) or payload.get("synthetic") is not True:
            raise ValueError("Apenas exemplos fictícios")
        if skill not in {s for p in self.profiles.values() for s in p["skills"]}:
            raise ValueError("Skill desconhecida")
        task = {"id": str(uuid4()), "title": title, "skill": skill,
                "payload": deepcopy(payload), "state": "created", "agent": None,
                "result": None, "review": None}
        self.tasks[task["id"]] = task
        self._record(task, "gestor-demo", "created")
        return deepcopy(task)

    def assign(self, task_id, agent):
        task = self.tasks[task_id]
        if task["state"] not in ("created", "revision_requested", "failed"):
            raise ValueError("Estado não permite atribuição")
        if agent not in self.profiles or task["skill"] not in self.profiles[agent]["skills"]:
            raise ValueError("Skill não pertence ao perfil do agente")
        task.update(agent=agent, state="assigned", result=None, review=None)
        self._record(task, "coordenador-demo", "assigned")
        return deepcopy(task)

    def run(self, task_id):
        task = self.tasks[task_id]
        if task["state"] != "assigned":
            raise ValueError("Tarefa precisa estar atribuída")
        task["state"] = "running"
        self._record(task, task["agent"], "started")
        try:
            result = execute(task["skill"], task["payload"])
            if result.get("requires_human_review") is not True or result.get("external_action") is not False:
                raise ValueError("Resultado viola política experimental")
        except Exception:
            task["state"] = "failed"
            self._record(task, task["agent"], "failed")
            raise
        task.update(state="awaiting_review", result=result)
        self._record(task, task["agent"], "draft_generated")
        return deepcopy(task)

    def review(self, task_id, approve, reviewer, comment):
        task = self.tasks[task_id]
        if task["state"] != "awaiting_review":
            raise ValueError("Não existe resultado aguardando revisão")
        if type(approve) is not bool or not isinstance(reviewer, str) or not reviewer.strip() or not isinstance(comment, str) or not comment.strip():
            raise ValueError("Decisão, revisor e justificativa obrigatórios")
        task["review"] = {"reviewer": reviewer, "comment": comment, "approved": approve}
        task["state"] = "approved" if approve else "revision_requested"
        self._record(task, reviewer, task["state"])
        return deepcopy(task)

    def revise(self, task_id, payload):
        task = self.tasks[task_id]
        if task["state"] not in ("revision_requested", "failed"):
            raise ValueError("Revisão não autorizada neste estado")
        if not isinstance(payload, dict) or payload.get("synthetic") is not True:
            raise ValueError("Apenas exemplos fictícios")
        task.update(payload=deepcopy(payload), state="created", agent=None, result=None, review=None)
        self._record(task, "gestor-demo", "revised")
        return deepcopy(task)
