"""Experimental repositories; callers must enforce institutional authorization.
Requires psycopg 3 and the separately applied office_runtime migration.
Each operation owns its transaction; no shared in-memory task cache.
"""
from datetime import datetime, timezone
from uuid import uuid4
from contextlib import contextmanager


class ConflictError(RuntimeError):
    """The persisted task changed since it was read."""


class PostgresOffice:
    def __init__(self, dsn):
        import psycopg
        from psycopg.rows import dict_row
        self._db = psycopg.connect(dsn, row_factory=dict_row, autocommit=True)
        try:
            with self._db.transaction():
                self._db.execute("SELECT 1 FROM office_runtime.tasks LIMIT 0")
                self._db.execute("SELECT 1 FROM office_runtime.events LIMIT 0")
                self._db.execute("SELECT 1 FROM office_runtime.knowledge LIMIT 0")
        except Exception:
            self._db.close()
            raise

    def close(self):
        self._db.close()

    @contextmanager
    def transaction(self):
        with self._db.transaction():
            yield self._db

    def get_task(self, ident):
        with self.transaction() as db:
            row = db.execute(
                "SELECT id::text, title, skill, payload, state, agent, result, review "
                "FROM office_runtime.tasks WHERE id=%s", (ident,)
            ).fetchone()
            if row is None:
                raise LookupError("Tarefa não encontrada")
            return row

    def list_tasks(self):
        with self.transaction() as db:
            return db.execute(
                "SELECT id::text, title, skill, payload, state, agent, result, review "
                "FROM office_runtime.tasks ORDER BY created_at,id"
            ).fetchall()

    def save_task(self, task, event, expected=None):
        """Insert a new task or compare the complete old snapshot under a row lock.
        The task and its audit event commit or roll back together.
        This is storage only, not a replacement for TaskEngine policy checks.
        """
        from psycopg.types.json import Jsonb
        fields = ("id", "title", "skill", "payload", "state", "agent", "result", "review")
        if event["task_id"] != task["id"] or event["state"] != task["state"]:
            raise ValueError("Evento incompatível com a tarefa")
        values = (task["id"], task["title"], task["skill"], Jsonb(task["payload"]),
                  task["state"], task["agent"], Jsonb(task["result"]), Jsonb(task["review"]))
        with self.transaction() as db:
            if expected is None:
                db.execute(
                    "INSERT INTO office_runtime.tasks(id,title,skill,payload,state,agent,result,review) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", values)
            else:
                if expected["id"] != task["id"]:
                    raise ValueError("Identificador incompatível")
                current = db.execute(
                    "SELECT id::text,title,skill,payload,state,agent,result,review "
                    "FROM office_runtime.tasks WHERE id=%s FOR UPDATE", (task["id"],)
                ).fetchone()
                if current is None or any(current[k] != expected[k] for k in fields):
                    raise ConflictError("Tarefa alterada; recarregue antes de repetir")
                db.execute(
                    "UPDATE office_runtime.tasks SET title=%s,skill=%s,payload=%s,state=%s,"
                    "agent=%s,result=%s,review=%s,updated_at=now() WHERE id=%s",
                    values[1:] + (values[0],))
            evidence = {k: event[k] for k in ("review", "result") if k in event}
            db.execute(
                "INSERT INTO office_runtime.events(task_id,actor,action,state,occurred_at,evidence) "
                "VALUES (%s,%s,%s,%s,%s,%s)",
                (task["id"],event["actor"],event["action"],event["state"],event["at"],Jsonb(evidence)))

    def list_events(self):
        with self.transaction() as db:
            rows = db.execute(
                "SELECT task_id::text,actor,action,state,occurred_at,evidence "
                "FROM office_runtime.events ORDER BY seq"
            ).fetchall()
        return [dict(task_id=r["task_id"], actor=r["actor"], action=r["action"],
                     state=r["state"], at=r["occurred_at"].isoformat(), **r["evidence"]) for r in rows]

    def propose(self, scope, content, source):
        if not all(isinstance(x,str) and x.strip() for x in (scope,content,source)):
            raise ValueError("Escopo, conteúdo e origem obrigatórios")
        ident = str(uuid4())
        with self.transaction() as db:
            db.execute(
                "INSERT INTO office_runtime.knowledge(id,scope,content,source,state,created_at) "
                "VALUES (%s,%s,%s,%s,'pending',%s)",
                (ident,scope,content,source,datetime.now(timezone.utc)))
        return ident

    def approve(self, scope, ident, reviewer):
        if not isinstance(reviewer,str) or not reviewer.strip():
            raise ValueError("Revisor obrigatório")
        with self.transaction() as db:
            result = db.execute(
                "UPDATE office_runtime.knowledge SET state='approved',reviewer=%s,reviewed_at=now() "
                "WHERE scope=%s AND id=%s AND state='pending'", (reviewer,scope,ident))
            if result.rowcount != 1:
                raise LookupError("Proposta pendente não encontrada no escopo")

    def search(self, scope, query):
        with self.transaction() as db:
            rows = db.execute(
                "SELECT id::text,scope,content,source,state,created_at,reviewer,reviewed_at "
                "FROM office_runtime.knowledge WHERE scope=%s AND state='approved' "
                "AND strpos(lower(content),lower(%s))>0 ORDER BY created_at,id", (scope,query)
            ).fetchall()
        for row in rows:
            for key in ("created_at","reviewed_at"):
                if row[key] is not None:
                    row[key] = row[key].isoformat()
        return rows
