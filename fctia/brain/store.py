"""Local experimental knowledge store. Not a production authorization boundary."""
import sqlite3
from datetime import datetime, timezone
from uuid import uuid4

class Brain:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("""CREATE TABLE IF NOT EXISTS knowledge (
            id TEXT PRIMARY KEY, scope TEXT NOT NULL, content TEXT NOT NULL,
            source TEXT NOT NULL, state TEXT NOT NULL CHECK(state IN ('pending','approved')),
            created_at TEXT NOT NULL, reviewer TEXT, reviewed_at TEXT)""")
        self.db.commit()
    def propose(self, scope, content, source):
        if not all(isinstance(x,str) and x.strip() for x in (scope,content,source)):
            raise ValueError("Escopo, conteúdo e origem obrigatórios")
        ident = str(uuid4())
        with self.db:
            self.db.execute("INSERT INTO knowledge VALUES (?,?,?,?,?,?,NULL,NULL)",
                (ident,scope,content,source,"pending",datetime.now(timezone.utc).isoformat()))
        return ident
    def approve(self, scope, ident, reviewer):
        if not isinstance(reviewer,str) or not reviewer.strip():
            raise ValueError("Revisor obrigatório")
        with self.db:
            cursor=self.db.execute("UPDATE knowledge SET state='approved', reviewer=?, reviewed_at=? WHERE scope=? AND id=? AND state='pending'",
                (reviewer,datetime.now(timezone.utc).isoformat(),scope,ident))
            if cursor.rowcount != 1:
                raise LookupError("Proposta pendente não encontrada no escopo")
    def search(self, scope, query):
        return [dict(r) for r in self.db.execute("SELECT * FROM knowledge WHERE scope=? AND state='approved' AND instr(lower(content),lower(?))>0 ORDER BY created_at",(scope,query))]
    def close(self):
        self.db.close()
