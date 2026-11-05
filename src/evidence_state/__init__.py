from .models.entities import *
from .ledger.sqlite_ledger import EvidenceLedger
from .verification.verifier import StructuralVerifier, FaithfulnessVerifier
from .deduplication.dedup import DeduplicationEngine, exact_hash, normalize
from .contradictions.detector import ContradictionDetector
from .revisions.revision_engine import RevisionEngine
from .evaluation.evaluator import SufficiencyEvaluator
from .policies.policy_engine import PolicyEngine
from .provenance.provenance import ProvenanceEngine
from .embeddings.index import SemanticIndex
from .embeddings.adapter import OllamaEmbeddingAdapter

__version__ = "0.1.0"