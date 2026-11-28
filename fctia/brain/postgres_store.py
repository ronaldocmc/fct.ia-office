"""PostgreSQL knowledge and exact cosine retrieval. No external model calls.
Scope filtering is not an authorization boundary. Experimental data only.
"""
import hashlib
import math
from fctia.persistence.postgres import PostgresOffice

DIMENSION = 384

def vector_literal(values):
    values = list(values)
    if len(values) != DIMENSION or any(type(x) not in (int,float) or not math.isfinite(x) for x in values):
        raise ValueError("Expected 384 finite numeric coordinates")
    if not any(values):
        raise ValueError("Zero vector is invalid for cosine distance")
    if any(abs(x)>1e10 for x in values):
        raise ValueError("Vector out of range")
    return "[" + ",".join(str(float(x)) for x in values) + "]"

def digest(content):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

class PostgresBrain(PostgresOffice):
    def pending(self, scope):
        with self.transaction() as db:
            rows=db.execute("SELECT id::text,scope,content,source,state,created_at FROM office_runtime.knowledge WHERE scope=%s AND state='pending' ORDER BY created_at,id",(scope,)).fetchall()
        for row in rows:
            row["created_at"]=row["created_at"].isoformat()
        return rows

    def embed(self, scope, ident, model, values, content_sha256):
        if not isinstance(model,str) or not model.strip():
            raise ValueError("Versioned model identifier required")
        v=vector_literal(values)
        with self.transaction() as db:
            row=db.execute("SELECT content FROM office_runtime.knowledge WHERE scope=%s AND id=%s AND state='approved' FOR UPDATE",(scope,ident)).fetchone()
            if row is None:
                raise LookupError("Approved knowledge not found")
            if digest(row["content"]) != content_sha256:
                raise ValueError("Embedding source hash mismatch")
            db.execute("""INSERT INTO office_runtime.embeddings(knowledge_id,model,content_sha256,embedding)
                VALUES (%s,%s,%s,%s::public.vector)
                ON CONFLICT(knowledge_id,model) DO UPDATE SET
                content_sha256=excluded.content_sha256,embedding=excluded.embedding,created_at=now()""",(ident,model,content_sha256,v))

    def semantic_search(self, scope, model, values, limit=10):
        if type(limit) is not int or not 1<=limit<=50:
            raise ValueError("Limit must be 1..50")
        if not isinstance(model,str) or not model.strip():
            raise ValueError("Versioned model identifier required")
        v=vector_literal(values)
        with self.transaction() as db:
            rows=db.execute("""SELECT k.id::text,k.scope,k.content,k.source,e.content_sha256,
                1-(e.embedding OPERATOR(public.<=>) %s::public.vector) AS similarity
                FROM office_runtime.knowledge k JOIN office_runtime.embeddings e ON k.id=e.knowledge_id
                WHERE k.scope=%s AND k.state='approved' AND e.model=%s
                AND e.content_sha256=encode(sha256(convert_to(k.content,'UTF8')),'hex')
                ORDER BY e.embedding OPERATOR(public.<=>) %s::public.vector,k.id LIMIT %s""",
                (v,scope,model,v,limit)).fetchall()
        return rows
