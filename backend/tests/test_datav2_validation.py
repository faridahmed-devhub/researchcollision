"""Phase 3H: validators for the v2 dataset pipeline (sampling + artifacts)."""
from __future__ import annotations

import hashlib
import json

import pytest

from evaluation.datav2 import sampling as s
from evaluation.datav2.validate_datasets import V1_CASE_IDS, check, default_protocol_path, validate_v2


def _sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


class TestSamplingDeterminism:
    def test_universe_size(self):
        pool = s.load_pool()
        assert len(s.universe(pool)) == 435

    def test_frame_is_deterministic_and_unique(self):
        pool = s.load_pool()
        f1 = s.build_frame(pool)
        f2 = s.build_frame(pool)
        assert f1 == f2  # exact reproducibility includes fields/order
        ids = [c["candidate_id"] for c in f1]
        assert len(ids) == s.N_FRAME
        assert len(set(ids)) == s.N_FRAME
        pairs = [c["pair_id"] for c in f1]
        assert len(set(pairs)) == s.N_FRAME

    def test_frame_has_required_metadata(self):
        for c in s.build_frame(s.load_pool()):
            for k in ("candidate_id", "pair_id", "group", "domain_a", "domain_b", "query_a", "query_b"):
                assert c.get(k), k

    def test_seed_fixed(self):
        assert s.SEED == 20260925

    def test_allocation_sums_to_eligible(self):
        alloc = s.allocate(4, s.group_sizes(s.load_pool()))
        assert sum(alloc.values()) == 4


class TestValidateV2:
    def _write_pool_protocol(self, root: pytest.TempPathFactory, protocol: bytes, pool_bytes: bytes, manifest: dict):
        # Pool is frozen via module constants; validator compares hashes from
        # the loaded pool/protocol. Give the temp root a matching manifest.
        pass

    def test_missing_dataset_is_skipped_not_failed(self, tmp_path):
        (tmp_path / "sampling_manifest.json").write_text(
            json.dumps(
                {
                    "protocol_sha256": _sha_bytes(default_protocol_path().read_bytes()),
                    "pool_sha256": s.pool_sha256(),
                    "screening_decisions": {},
                    "eligible": 0,
                }
            ),
            encoding="utf-8",
        )
        results = validate_v2(tmp_path)
        status = {r["rule"]: r["status"] for r in results}
        assert status["dataset_present"] == "skip"
        assert all(r["status"] != "fail" for r in results)

    def test_hard_failure_when_wrong_pool_hash(self, tmp_path):
        (tmp_path / "sampling_manifest.json").write_text(
            json.dumps({"protocol_sha256": "abc", "pool_sha256": "def", "screening_decisions": {}, "eligible": 0}),
            encoding="utf-8",
        )
        results = validate_v2(tmp_path)
        by_rule = {r["rule"]: r for r in results}
        assert by_rule["pool_frozen"]["status"] == "fail"

    def test_provider_failures_are_never_accepted_as_exclusions(self, tmp_path):
        """Acceptance gate: EX2 (provider unavailable) entries must fail validation."""
        (tmp_path / "sampling_manifest.json").write_text(
            json.dumps(
                {
                    "protocol_sha256": _sha_bytes(default_protocol_path().read_bytes()),
                    "pool_sha256": s.pool_sha256(),
                    "screening_decisions": {"excluded_provider": 3, "eligible": 5},
                    "eligible": 5,
                }
            ),
            encoding="utf-8",
        )
        results = validate_v2(tmp_path)
        by_rule = {r["rule"]: r for r in results}
        assert by_rule["no_provider_failure_excluded"]["status"] == "fail"

    def test_v1_case_ids_are_authoritative(self):
        assert len(V1_CASE_IDS) == 12
        assert len(set(V1_CASE_IDS)) == 12

    def test_check_helper(self):
        assert check("x", True)["status"] == "pass"
        assert check("x", False)["status"] == "fail"