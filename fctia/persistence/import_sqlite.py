"""Offline synthetic laboratory migration. Dry run unless --apply."""
import argparse
import json
import os
import sqlite3
from pathlib import Path
from datetime import datetime
from uuid import UUID

def timestamp(value):
    dt = datetime.fromisoformat(value)
    if dt.utcoffset() is None:
        raise ValueError("Timestamp without timezone")
    return dt

def read_source(path):
    db = sqlite3.connect(Path(path).resolve().as_uri()+"?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    try:
        db.execute("BEGIN")
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("SQLite integrity check failed")
        tasks = {}
        for row in db.execute("SELECT id,snapshot FROM office_tasks"):
            task = json.loads(row["snapshot"])
            if str(UUID(row["id"])) != task["id"] or task["payload"].get("synthetic") is not True:
                raise ValueError("Invalid or non-synthetic task")
            tasks[task["id"]] = task
        events = []
        by_task = {}
        for row in db.execute("SELECT seq,event FROM office_events ORDER BY seq"):
            event = json.loads(row["event"])
            if event["task_id"] not in tasks:
                raise ValueError("Orphan event")
            timestamp(event["at"])
            events.append((row["seq"],event))
            by_task.setdefault(event["task_id"],[]).append(event)
        for ident, task in tasks.items():
            history = by_task.get(ident,[])
            if not history or history[0]["action"] != "created" or history[-1]["state"] != task["state"]:
                raise ValueError("Incomplete or inconsistent task history")
            if task["state"] == "running":
                raise ValueError("Recover interrupted tasks before migration")
        knowledge = [dict(row) for row in db.execute("SELECT * FROM knowledge ORDER BY created_at,id")]
        for item in knowledge:
            UUID(item["id"])
            timestamp(item["created_at"])
            if item["reviewed_at"] is not None:
                timestamp(item["reviewed_at"])
        return tasks,events,by_task,knowledge
    finally:
        db.close()

def migrate(path, dsn=None, apply=False):
    tasks,events,by_task,knowledge = read_source(path)
    counts = {"tasks":len(tasks),"events":len(events),"knowledge":len(knowledge)}
    if not apply:
        return {"applied":False, **counts}
    import psycopg
    from psycopg.types.json import Jsonb
    with psycopg.connect(dsn) as db:
        if db.info.dbname != "fctia_office_runtime":
            raise ValueError("Dedicated runtime database required")
        db.execute("LOCK TABLE office_runtime.tasks,office_runtime.events,office_runtime.knowledge IN ACCESS EXCLUSIVE MODE")
        for table in counts:
            if db.execute("SELECT count(*) FROM office_runtime."+table).fetchone()[0]:
                raise ValueError("Target must be empty")
        for ident,t in tasks.items():
            h=by_task[ident]
            db.execute("INSERT INTO office_runtime.tasks(id,title,skill,payload,state,agent,result,review,created_at,updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (ident,t["title"],t["skill"],Jsonb(t["payload"]),t["state"],t["agent"],Jsonb(t["result"]),Jsonb(t["review"]),timestamp(h[0]["at"]),timestamp(h[-1]["at"])))
        for seq,e in events:
            evidence={k:v for k,v in e.items() if k not in ("task_id","actor","action","state","at")}
            db.execute("INSERT INTO office_runtime.events(seq,task_id,actor,action,state,occurred_at,evidence) OVERRIDING SYSTEM VALUE VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (seq,e["task_id"],e["actor"],e["action"],e["state"],timestamp(e["at"]),Jsonb(evidence)))
        for k in knowledge:
            db.execute("INSERT INTO office_runtime.knowledge(id,scope,content,source,state,created_at,reviewer,reviewed_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                tuple(k[key] for key in ("id","scope","content","source","state","created_at","reviewer","reviewed_at")))
        for table,count in counts.items():
            if db.execute("SELECT count(*) FROM office_runtime."+table).fetchone()[0] != count:
                raise ValueError("Count mismatch")
        if events:
            # Transactional sequence restart; no nontransactional setval.
            next_seq=max(seq for seq,_ in events)+1
            db.execute("ALTER TABLE office_runtime.events ALTER COLUMN seq RESTART WITH "+str(next_seq))
    return {"applied":True, **counts}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("source")
    p.add_argument("--apply",action="store_true")
    p.add_argument("--confirm-synthetic",action="store_true")
    a=p.parse_args()
    if a.apply and not a.confirm_synthetic:
        p.error("Explicit synthetic-data confirmation required")
    print(json.dumps(migrate(a.source,os.environ.get("FCTIA_MIGRATION_DSN"),a.apply)))

if __name__=="__main__":
    main()
