from __future__ import annotations
import sqlite3, json, hashlib, uuid
from pathlib import Path
from typing import Optional, List
from ..models.entities import *

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS documents (
  id TEXT PRIMARY KEY, source_uri TEXT NOT NULL, content_hash TEXT NOT NULL,
  source_type TEXT, retrieved_at TEXT, metadata TEXT, version INTEGER, content TEXT,
  status TEXT DEFAULT 'ACTIVE');
CREATE TABLE IF NOT EXISTS claims (
  id TEXT PRIMARY KEY, text TEXT NOT NULL, normalized TEXT, claim_type TEXT,
  created_at TEXT, status TEXT, revision_id TEXT);
CREATE TABLE IF NOT EXISTS evidence (
  id TEXT PRIMARY KEY, claim_id TEXT NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
  document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  quote TEXT, start_offset INTEGER, end_offset INTEGER, extraction_metadata TEXT,
  verification_status TEXT);
CREATE TABLE IF NOT EXISTS verifications (
  id TEXT PRIMARY KEY, claim_id TEXT NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
  evidence_ids TEXT, method TEXT, result TEXT, explanation TEXT,
  verifier_identity TEXT, timestamp TEXT);
CREATE TABLE IF NOT EXISTS contradictions (
  id TEXT PRIMARY KEY, claim_ids TEXT, classification TEXT, evidence_ids TEXT,
  resolution_status TEXT, resolution_provenance TEXT);
CREATE TABLE IF NOT EXISTS revisions (
  id TEXT PRIMARY KEY, previous_state_id TEXT, resulting_state_id TEXT,
  changed_entities TEXT, reason TEXT, timestamp TEXT, actor TEXT);
CREATE TABLE IF NOT EXISTS evaluations (
  id TEXT PRIMARY KEY, objective TEXT, required_criteria TEXT, satisfied_criteria TEXT,
  unsatisfied_criteria TEXT, missing_information TEXT, status TEXT, provenance TEXT);
CREATE TABLE IF NOT EXISTS audit (
  id INTEGER PRIMARY KEY AUTOINCREMENT, event TEXT, payload TEXT, ts TEXT);
"""

class EvidenceLedger:
    def __init__(self, db_path: str = "./evidence.db", admin_token: Optional[str] = None):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.executescript(SCHEMA)
        try:
            self.conn.execute("ALTER TABLE documents ADD COLUMN content TEXT")
        except Exception:
            pass
        try:
            self.conn.execute("ALTER TABLE documents ADD COLUMN status TEXT DEFAULT 'ACTIVE'")
        except Exception:
            pass
        self.conn.commit()
        self._trusted_verifiers = {}
        self._issued_verifications = set()
        self._admin_token = admin_token or str(uuid.uuid4())
        self._frozen = False

    def _audit(self, event, payload):
        self.conn.execute("INSERT INTO audit(event,payload,ts) VALUES(?,?,?)",
                          (event, json.dumps(payload), now().isoformat()))
        self.conn.commit()

    def register_document(self, source_uri, content, source_type=SourceType.DOCUMENT, metadata=None):
        h = hashlib.sha256(content.encode()).hexdigest()
        d = Document(source_uri=source_uri, content_hash=h, source_type=source_type, metadata=metadata or {})
        self.conn.execute("INSERT INTO documents VALUES(?,?,?,?,?,?,?,?,?)",
            (d.id, d.source_uri, d.content_hash, d.source_type.value, d.retrieved_at.isoformat(), json.dumps(d.metadata), d.version, content, "ACTIVE"))
        self.conn.commit()
        self._audit("register_document", {"id": d.id})
        return d

    def propose_claim(self, document_id, claim, source_quote, claim_type="factual", start_offset=None, end_offset=None):
        c = Claim(text=claim, normalized=claim.strip().lower(), claim_type=claim_type)
        ev = Evidence(claim_id=c.id, document_id=document_id, quote=source_quote, start_offset=start_offset, end_offset=end_offset)
        self.conn.execute("INSERT INTO claims VALUES(?,?,?,?,?,?,?)",
            (c.id, c.text, c.normalized, c.claim_type, c.created_at.isoformat(), c.status.value, c.revision_id))
        self.conn.execute("INSERT INTO evidence VALUES(?,?,?,?,?,?,?,?)",
            (ev.id, ev.claim_id, ev.document_id, ev.quote, ev.start_offset, ev.end_offset, json.dumps(ev.extraction_metadata), ev.verification_status.value))
        self.conn.commit()
        self._audit("propose_claim", {"claim_id": c.id, "evidence_id": ev.id})
        return c, ev

    def get_claim(self, claim_id):
        r = self.conn.execute("SELECT * FROM claims WHERE id=?", (claim_id,)).fetchone()
        if not r: return None
        return Claim(id=r["id"], text=r["text"], normalized=r["normalized"], claim_type=r["claim_type"], created_at=datetime.fromisoformat(r["created_at"]), status=r["status"], revision_id=r["revision_id"])

    def get_evidence(self, claim_id=None):
        q = "SELECT * FROM evidence" + (" WHERE claim_id=?" if claim_id else "")
        rows = self.conn.execute(q, (claim_id,) if claim_id else ()).fetchall()
        out = []
        for r in rows:
            out.append(Evidence(id=r["id"], claim_id=r["claim_id"], document_id=r["document_id"], quote=r["quote"], start_offset=r["start_offset"], end_offset=r["end_offset"], extraction_metadata=json.loads(r["extraction_metadata"] or "{}"), verification_status=r["verification_status"]))
        return out

    def get_document(self, doc_id):
        r = self.conn.execute("SELECT * FROM documents WHERE id=?", (doc_id,)).fetchone()
        if not r: return None
        return Document(id=r["id"], source_uri=r["source_uri"], content_hash=r["content_hash"], source_type=r["source_type"], retrieved_at=datetime.fromisoformat(r["retrieved_at"]), metadata=json.loads(r["metadata"] or "{}"), version=r["version"])

    def all_claims(self):
        rows = self.conn.execute("SELECT * FROM claims").fetchall()
        out=[]
        for r in rows:
            out.append(Claim(id=r["id"], text=r["text"], normalized=r["normalized"], claim_type=r["claim_type"], created_at=datetime.fromisoformat(r["created_at"]), status=r["status"], revision_id=r["revision_id"]))
        return out

    def get_document_content(self, doc_id):
        r = self.conn.execute("SELECT content, content_hash, status FROM documents WHERE id=?", (doc_id,)).fetchone()
        if not r: return None
        return r["content"], r["content_hash"], r["status"]

    def register_verifier(self, name, fn, token=None):
        if self._frozen:
            if token != self._admin_token:
                raise PermissionError("verifier registry is frozen")
        self._trusted_verifiers[name] = fn

    def freeze_verifiers(self, token=None):
        if token != self._admin_token:
            raise PermissionError("invalid admin token")
        self._frozen = True

    def run_verification(self, claim_id, evidence_ids, verifier_name):
        if not self._frozen:
            raise ValueError("verifier registry must be frozen")
        if verifier_name not in self._trusted_verifiers:
            raise ValueError(f"untrusted verifier: {verifier_name}")
        claim = self.get_claim(claim_id)
        evs = [e for e in self.get_evidence(claim_id) if e.id in evidence_ids]
        for e in evs:
            content, h, status = self.get_document_content(e.document_id)
            if status == "WITHDRAWN":
                raise ValueError("document withdrawn")
            if content is None:
                raise ValueError("source content required")
            if e.quote not in content:
                raise ValueError("fabricated quotation")
            if hashlib.sha256(content.encode()).hexdigest() != h:
                raise ValueError("source hash mismatch")
            if e.start_offset is not None or e.end_offset is not None:
                if e.start_offset is None or e.end_offset is None:
                    raise ValueError("partial offsets")
                if e.start_offset < 0 or e.end_offset < 0:
                    raise ValueError("negative offsets")
                if e.start_offset > e.end_offset:
                    raise ValueError("reversed offsets")
                if e.end_offset > len(content):
                    raise ValueError("out of range offsets")
                if content[e.start_offset:e.end_offset] != e.quote:
                    raise ValueError("offset mismatch")
        fn = self._trusted_verifiers[verifier_name]
        v = fn(claim, evs)
        if v.claim_id != claim_id:
            raise ValueError("claim_id mismatch")
        if sorted(v.evidence_ids) != sorted(evidence_ids):
            raise ValueError("evidence_ids mismatch")
        v.verifier_identity = verifier_name
        v.method = "run_verification"
        self._issued_verifications.add(v.id)
        self.record_verification(v)
        return v

    def record_verification(self, v: Verification):
        if v.id not in self._issued_verifications:
            raise ValueError("untrusted or unissued verification")
        self._issued_verifications.discard(v.id)
        # guard: PASS requires evidence
        if v.result == VerificationResult.PASS and not v.evidence_ids:
            raise ValueError("PASS verification requires evidence_ids")
        # guard: evidence must belong to claim
        for eid in v.evidence_ids:
            ev = self.conn.execute("SELECT claim_id FROM evidence WHERE id=?", (eid,)).fetchone()
            if not ev or ev["claim_id"] != v.claim_id:
                raise ValueError(f"evidence {eid} does not belong to claim {v.claim_id}")
        self.conn.execute("INSERT INTO verifications VALUES(?,?,?,?,?,?,?,?)",
            (v.id, v.claim_id, json.dumps(v.evidence_ids), v.method, v.result.value, v.explanation, v.verifier_identity, v.timestamp.isoformat()))
        # update evidence status
        for eid in v.evidence_ids:
            self.conn.execute("UPDATE evidence SET verification_status=? WHERE id=?", (v.result.value, eid))
        if v.result == VerificationResult.PASS:
            self.conn.execute("UPDATE claims SET status=? WHERE id=?", (ClaimStatus.VERIFIED.value, v.claim_id))
        elif v.result == VerificationResult.FAIL:
            self.conn.execute("UPDATE claims SET status=? WHERE id=?", (ClaimStatus.UNVERIFIED.value, v.claim_id))
        self.conn.commit()
        self._audit("record_verification", {"verification_id": v.id, "claim_id": v.claim_id})

    def record_contradiction(self, c: Contradiction):
        self.conn.execute("INSERT INTO contradictions VALUES(?,?,?,?,?,?)",
            (c.id, json.dumps(c.claim_ids), c.classification, json.dumps(c.evidence_ids), c.resolution_status, c.resolution_provenance))
        self.conn.commit()
        self._audit("record_contradiction", {"id": c.id})

    def contradictions(self):
        rows = self.conn.execute("SELECT * FROM contradictions").fetchall()
        out=[]
        for r in rows:
            out.append(Contradiction(id=r["id"], claim_ids=json.loads(r["claim_ids"]), classification=r["classification"], evidence_ids=json.loads(r["evidence_ids"] or "[]"), resolution_status=r["resolution_status"], resolution_provenance=r["resolution_provenance"]))
        return out

    def record_revision(self, r: Revision):
        self.conn.execute("INSERT INTO revisions VALUES(?,?,?,?,?,?,?)",
            (r.id, r.previous_state_id, r.resulting_state_id, json.dumps(r.changed_entities), r.reason, r.timestamp.isoformat(), r.actor))
        self.conn.commit()
        self._audit("record_revision", {"id": r.id})

    def revisions(self):
        rows = self.conn.execute("SELECT * FROM revisions").fetchall()
        out=[]
        for r in rows:
            out.append(Revision(id=r["id"], previous_state_id=r["previous_state_id"], resulting_state_id=r["resulting_state_id"], changed_entities=json.loads(r["changed_entities"] or "[]"), reason=r["reason"], timestamp=datetime.fromisoformat(r["timestamp"]), actor=r["actor"]))
        return out

    def record_evaluation(self, e: Evaluation):
        self.conn.execute("INSERT INTO evaluations VALUES(?,?,?,?,?,?,?,?)",
            (e.id, e.objective, json.dumps(e.required_criteria), json.dumps(e.satisfied_criteria), json.dumps(e.unsatisfied_criteria), json.dumps(e.missing_information), e.status.value, e.provenance))
        self.conn.commit()
        self._audit("record_evaluation", {"id": e.id, "status": e.status.value})

    def evaluations(self):
        rows = self.conn.execute("SELECT * FROM evaluations").fetchall()
        out=[]
        for r in rows:
            out.append(Evaluation(id=r["id"], objective=r["objective"], required_criteria=json.loads(r["required_criteria"] or "[]"), satisfied_criteria=json.loads(r["satisfied_criteria"] or "[]"), unsatisfied_criteria=json.loads(r["unsatisfied_criteria"] or "[]"), missing_information=json.loads(r["missing_information"] or "[]"), status=r["status"], provenance=r["provenance"]))
        return out

    def withdraw_document(self, doc_id):
        self.conn.execute("UPDATE documents SET status='WITHDRAWN' WHERE id=?", (doc_id,))
        evs = self.conn.execute("SELECT id,claim_id FROM evidence WHERE document_id=?", (doc_id,)).fetchall()
        changed=[]
        for ev in evs:
            self.conn.execute("UPDATE evidence SET verification_status=? WHERE id=?", (VerificationResult.FAIL.value, ev["id"]))
            self.conn.execute("UPDATE claims SET status=? WHERE id=?", (ClaimStatus.UNVERIFIED.value, ev["claim_id"]))
            changed.append(ev["claim_id"])
        self.conn.commit()
        self._audit("withdraw_document", {"doc_id": doc_id, "affected_claims": changed})
        return changed

    def verify_source_integrity(self, doc_id):
        r = self.conn.execute("SELECT content, content_hash FROM documents WHERE id=?", (doc_id,)).fetchone()
        if not r: return False
        content = r["content"]
        stored_hash = r["content_hash"]
        if content is None:
            return False  # cannot verify without retained content
        return hashlib.sha256(content.encode()).hexdigest() == stored_hash

    def close(self):
        self.conn.close()