"""Deterministic Mock LLM provider.

Mandatory for tests and local demo without API keys. Handlers are
*grounded*: they only reference content passed in `input_data` (names,
abstracts, evidence IDs) so the whole pipeline stays traceable even in
mock mode. Outputs are deterministic given the same inputs.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any

import structlog

from app.core.constants import (
    NOVELTY_LANGUAGE,
    SYNTHETIC_DATA_LABEL,
    TRAJECTORY_HEDGE,
)
from app.providers.llm.base import LLMResponse

logger = structlog.get_logger(__name__)

_STOPWORDS = {
    "the", "a", "an", "of", "and", "or", "to", "in", "on", "for", "with", "we",
    "our", "this", "that", "is", "are", "as", "by", "at", "from", "it", "its",
    "be", "can", "has", "have", "was", "were", "which", "using", "used", "into",
    "such", "these", "their", "than", "then", "over", "across", "between",
    "based", "results", "show", "shows", "propose", "proposed", "paper",
    "also", "how", "what", "new", "more", "most", "both", "each", "other",
}


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", (text or "").strip())
    return [p.strip() for p in parts if len(p.strip()) > 10]


def _keywords(text: str, limit: int = 6) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z\-]{3,}", (text or "").lower())
    counts: dict[str, int] = {}
    for w in words:
        if w in _STOPWORDS:
            continue
        counts[w] = counts.get(w, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [w for w, _ in ranked[:limit]]


def _title_case(phrase: str) -> str:
    return " ".join(w.capitalize() if w.islower() else w for w in phrase.split())


class MockLLMProvider:
    """Task-dispatched deterministic provider implementing LLMProvider."""

    name = "mock"
    model = "mock-deterministic-v1"

    async def generate(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
        max_tokens: int = 2000,
        seed: int | None = None,
    ) -> LLMResponse:
        prompt = messages[-1]["content"] if messages else ""
        digest = hashlib.sha256(prompt.encode()).hexdigest()[:12]
        content = (
            f"[{SYNTHETIC_DATA_LABEL}] MockLLMProvider does not produce free-form text. "
            f"Use structured_generate(task=...) . ref={digest}"
        )
        return LLMResponse(content=content, model=self.model, provider=self.name)

    async def structured_generate(
        self,
        *,
        task: str,
        input_data: dict[str, Any],
        schema_name: str,
        schema: dict[str, Any],
        temperature: float = 0.2,
        max_tokens: int | None = None,
        seed: int | None = None,
    ) -> dict[str, Any]:
        handler = getattr(self, f"_task_{task}", None)
        if handler is None:
            raise ValueError(f"MockLLMProvider has no handler for task {task!r}")
        result = handler(input_data)
        logger.debug("mock_llm.task", task=task, schema=schema_name)
        return result

    # ------------------------------------------------------------------
    # Task handlers
    # ------------------------------------------------------------------

    def _task_profile_extraction(self, data: dict[str, Any]) -> dict[str, Any]:
        """Heuristic section-aware CV parsing."""
        text = data.get("cv_text", "")
        sections: dict[str, list[str]] = {}
        current = "header"
        sections[current] = []
        for raw in text.splitlines():
            line = raw.strip()
            if not line:
                continue
            header_match = re.match(r"^([A-Z][A-Za-z /&+-]{2,60}):$", line)
            if header_match:
                current = header_match.group(1).strip().lower()
                sections.setdefault(current, [])
                continue
            sections.setdefault(current, []).append(line.lstrip("-•* ").strip())

        def items(*names: str) -> list[str]:
            out: list[str] = []
            for n in names:
                for v in sections.get(n, []):
                    if v and v not in out:
                        out.append(v)
            return out[:25]

        header = sections.get("header", [])
        name_line = next((h for h in header if len(h) > 3), "Unnamed Researcher")
        interests = items("research interests", "interests")
        domains = interests[:4] or [_title_case(k) for k in _keywords(" ".join(header), 2)]
        pubs = [
            p for p in items("publications", "selected publications")
            if any(ch.isdigit() for ch in p) or len(p) > 30
        ]
        skills = items("skills", "technical skills", "tools")
        datasets = items("datasets")
        experience = items("experience", "professional experience", "education")
        problems = items("research problems") or [
            f"{_title_case(d)}-related research problems stated in the CV" for d in domains[:2]
        ]
        return {
            "domains": domains,
            "research_problems": problems,
            "methods": items("methods"),
            "datasets": datasets,
            "tools": skills,
            "research_questions": items("research questions"),
            "publications": pubs,
            "technical_skills": skills,
            "research_interests": interests,
            "emerging_interests": items("emerging interests")[:6],
            "experience": experience,
        }

    def _task_paper_analysis(self, data: dict[str, Any]) -> dict[str, Any]:
        title = data.get("title", "")
        abstract = data.get("abstract", "") or title
        sents = _sentences(abstract)
        first = sents[0] if sents else abstract[:200]
        last = sents[-1] if len(sents) > 1 else first
        kws = _keywords(abstract)
        limitations = data.get("limitations") or []
        future_work = data.get("future_work") or []
        if not limitations and len(sents) > 2:
            limitations = [f"The abstract of '{title}' does not report evaluation beyond {kws[0] if kws else 'the proposed setting'}."]
        if not future_work:
            future_work = [f"Extending '{title}' to broader settings is suggested by the absence of such results in the abstract."]
        evidence_id = data.get("evidence_id")
        return {
            "research_problem": first,
            "research_question": f"How can {_title_case(kws[0]) if kws else 'the studied problem'} be addressed effectively?",
            "methodology": f"Approach described in '{title}': {(' '.join(sents[1:3])) if len(sents) > 2 else first}",
            "dataset": data.get("dataset_hint"),
            "main_result": last,
            "limitations": limitations[:3],
            "future_work": future_work[:3],
            "domain": data.get("domain_hint") or (_title_case(kws[0]) if kws else None),
            "methods": [_title_case(k) for k in kws[:4]],
            "technologies": [_title_case(k) for k in kws[4:6]],
            "evidence_ids": [evidence_id] if evidence_id else [],
        }

    def _task_trajectory_analysis(self, data: dict[str, Any]) -> dict[str, Any]:
        papers: list[dict] = sorted(
            data.get("papers", []),
            key=lambda p: p.get("year") or 0,
        )
        name = data.get("researcher_name", "The researcher")
        evidence_ids = list(data.get("evidence_ids", []))
        if not papers:
            return {
                "historical_focus": [], "current_focus": [], "emerging_interests": [],
                "methodology_shifts": [], "domain_shifts": [], "topic_transitions": [],
                "phases": [],
                "summary": f"No publications are available for {name}; no trajectory claims can be made.",
                "evidence_ids": [],
            }
        topics_by_year = [(p.get("year") or 0, p.get("topics") or [], p.get("methods") or []) for p in papers]
        all_topics = [t for _, ts, _ in topics_by_year for t in ts]
        all_methods = [m for _, _, ms in topics_by_year for m in ms]
        early = topics_by_year[: max(1, len(topics_by_year) // 2)]
        late = topics_by_year[len(topics_by_year) // 2 :]
        historical = list(dict.fromkeys(t for _, ts, _ in early for t in ts))[:5]
        current = list(dict.fromkeys(t for _, ts, _ in late for t in ts))[:5]
        emerging = [t for t in current if t not in historical][:4]
        method_shifts = [
            f"Methods shift from {', '.join(list(dict.fromkeys(m for _, _, ms in early for m in ms))[:3]) or 'earlier methods'} "
            f"to {', '.join(list(dict.fromkeys(m for _, _, ms in late for m in ms))[:3]) or 'later methods'}"
        ] if all_methods else []
        domain_shifts = [
            f"Topic emphasis moves from {historical[:2]} to {current[:2]}"
        ] if set(historical) - set(current) else []
        transitions = [f"{h} -> {c}" for h, c in zip(historical, reversed(current))][:3]
        phases = []
        if early:
            years = [y for y, _, _ in early if y]
            phases.append({
                "period": f"{min(years)}-{max(years)}" if years else "early period",
                "focus": ", ".join(historical[:3]) or "early research focus",
                "topics": historical[:4], "methods": list(dict.fromkeys(all_methods))[:3],
            })
        if late:
            years = [y for y, _, _ in late if y]
            phases.append({
                "period": f"{min(years)}-{max(years)}" if years else "recent period",
                "focus": ", ".join(current[:3]) or "recent research focus",
                "topics": current[:4], "methods": list(dict.fromkeys(all_methods))[-3:],
            })
        summary = (
            f"{TRAJECTORY_HEDGE} {name} worked on {', '.join(historical[:3]) or 'early topics'} "
            f"and more recently on {', '.join(current[:3]) or 'related topics'}."
        )
        return {
            "historical_focus": historical,
            "current_focus": current,
            "emerging_interests": emerging,
            "methodology_shifts": method_shifts,
            "domain_shifts": domain_shifts,
            "topic_transitions": transitions,
            "phases": phases,
            "summary": summary,
            "evidence_ids": evidence_ids,
        }

    def _task_gap_detection(self, data: dict[str, Any]) -> dict[str, Any]:
        analyses: list[dict] = data.get("paper_analyses", [])
        gaps: list[dict[str, Any]] = []
        seen: set[str] = set()
        for pa in analyses:
            ev = pa.get("evidence_id")
            for lim in pa.get("limitations", [])[:2]:
                key = ("lim", lim[:80])
                if key in seen:
                    continue
                seen.add(key)
                gaps.append({
                    "description": f"Explicit limitation reported: {lim}",
                    "gap_type": "explicit_limitation",
                    "confidence": 0.8,
                    "evidence_ids": [ev] if ev else [],
                })
            for fw in pa.get("future_work", [])[:2]:
                key = ("fw", fw[:80])
                if key in seen:
                    continue
                seen.add(key)
                gaps.append({
                    "description": f"Future-work opportunity: {fw}",
                    "gap_type": "future_work_opportunity",
                    "confidence": 0.65,
                    "evidence_ids": [ev] if ev else [],
                })
        if not analyses:
            gaps.append({
                "description": f"{NOVELTY_LANGUAGE} No analyzed papers were available to derive gaps.",
                "gap_type": "missing_evaluation",
                "confidence": 0.2,
                "evidence_ids": [],
            })
        return {"gaps": gaps[:20]}

    def _task_intersection_discovery(self, data: dict[str, Any]) -> dict[str, Any]:
        mode = data.get("mode", "normal")
        a = data.get("researcher_a", {})
        b = data.get("researcher_b", {})
        gaps: list[dict] = data.get("gaps", [])
        max_n = int(data.get("max_intersections", 5))
        a_traj = a.get("trajectory", {})
        b_traj = b.get("trajectory", {})
        a_all = list(dict.fromkeys(
            list(a_traj.get("current_focus", []))
            + list(a_traj.get("historical_focus", []))
            + list(a_traj.get("emerging_interests", []))
            + list(a.get("topics", []))
        ))
        b_all = list(dict.fromkeys(
            list(b_traj.get("current_focus", []))
            + list(b_traj.get("historical_focus", []))
            + list(b_traj.get("emerging_interests", []))
            + list(b.get("topics", []))
        ))
        a_cur = a_traj.get("current_focus", []) or a.get("topics", [])
        b_cur = b_traj.get("current_focus", []) or b.get("topics", [])
        a_meth = a_traj.get("methods_pool", []) or a.get("methods", [])
        b_meth = b_traj.get("methods_pool", []) or b.get("methods", [])
        from app.utils.text import topics_shared

        shared = topics_shared(a_all, b_all)
        complementary = sorted(set(a_meth) ^ set(b_meth))
        complementary = sorted(set(a_meth) ^ set(b_meth))

        def gap_text(g: dict | None) -> str:
            if not g:
                return NOVELTY_LANGUAGE
            return g.get("description", NOVELTY_LANGUAGE)

        intersections: list[dict[str, Any]] = []
        if shared:
            topic = shared[0]
            g = gaps[0] if gaps else None
            ev = list(dict.fromkeys((g or {}).get("evidence_ids", []) + list(a_traj.get("evidence_ids", [])[:2]) + list(b_traj.get("evidence_ids", [])[:2])))
            intersections.append({
                "title": f"Bridging {topic}: combining {a.get('name')} and {b.get('name')} expertise",
                "description": (
                    f"Both publication records touch '{topic}'. A joint direction could combine "
                    f"{', '.join(a_meth[:2]) or 'the methods of ' + a.get('name', 'A')} with "
                    f"{', '.join(b_meth[:2]) or 'the methods of ' + b.get('name', 'B')} "
                    f"to address the identified gap. {NOVELTY_LANGUAGE}"
                ),
                "shared_problem": f"How '{topic}' can be advanced by combining both groups' methods.",
                "complementary_expertise": (
                    f"{a.get('name')}: {', '.join(a_meth[:3]) or 'see trajectory'}; "
                    f"{b.get('name')}: {', '.join(b_meth[:3]) or 'see trajectory'}"
                ),
                "research_gap": gap_text(g),
                "why_researcher_a": f"{TRAJECTORY_HEDGE} recent work on {', '.join(a_cur[:3])}.",
                "why_researcher_b": f"{TRAJECTORY_HEDGE} recent work on {', '.join(b_cur[:3])}.",
                "novelty_confidence": 0.55 if shared else 0.35,
                "feasibility_confidence": 0.6,
                "evidence_ids": ev[:8],
                "gap_index": 0 if g else None,
            })
        if complementary and (len(intersections) < max_n):
            c1, c2 = (complementary + ["", ""])[:2]
            g = gaps[1] if len(gaps) > 1 else (gaps[0] if gaps else None)
            ev = list(dict.fromkeys((g or {}).get("evidence_ids", [])))
            intersections.append({
                "title": f"Cross-method opportunity: {c1} meets {c2}".rstrip(" :"),
                "description": (
                    f"The method profiles differ ({c1 or 'A-side methods'} vs {c2 or 'B-side methods'}), "
                    f"suggesting a transfer opportunity between {a.get('name')} and {b.get('name')}. "
                    f"This appears underexplored based on the retrieved literature."
                ),
                "shared_problem": f"Whether {c1 or 'method A'} can strengthen research on {b_cur[0] if b_cur else 'the target problem'}." if b_cur else "Method transfer potential.",
                "complementary_expertise": f"Difference set: {', '.join(filter(None, [c1, c2]))}",
                "research_gap": gap_text(g),
                "why_researcher_a": f"Methods pool includes {', '.join(a_meth[:3]) or 'distinct techniques'}.",
                "why_researcher_b": f"Methods pool includes {', '.join(b_meth[:3]) or 'distinct techniques'}.",
                "novelty_confidence": 0.45,
                "feasibility_confidence": 0.5,
                "evidence_ids": ev[:8],
                "gap_index": 1 if len(gaps) > 1 else (0 if gaps else None),
            })
        if mode == "serendipity":
            a_dom = set(a_traj.get("domains", []) or [])
            b_dom = set(b_traj.get("domains", []) or [])
            cross = sorted(a_dom ^ b_dom)
            if cross:
                g = gaps[0] if gaps else None
                intersections.append({
                    "title": f"Serendipitous direction: {' + '.join(cross[:2])}",
                    "description": (
                        f"An unexpected combination across domains ({', '.join(cross[:3])}) involving "
                        f"{a.get('name')} and {b.get('name')}. Plausible connection: shared methods may transfer. "
                        f"{NOVELTY_LANGUAGE}"
                    ),
                    "shared_problem": f"Applying {cross[0]} perspectives to {cross[1] if len(cross) > 1 else 'adjacent problems'}.",
                    "complementary_expertise": f"Domain difference: {', '.join(cross[:3])}",
                    "research_gap": gap_text(g),
                    "why_researcher_a": f"Domain exposure: {', '.join(sorted(a_dom)) or 'varied'}.",
                    "why_researcher_b": f"Domain exposure: {', '.join(sorted(b_dom)) or 'varied'}.",
                    "novelty_confidence": 0.4,
                    "feasibility_confidence": 0.35,
                    "evidence_ids": list(dict.fromkeys((g or {}).get("evidence_ids", [])))[:8],
                    "gap_index": 0 if g else None,
                })
        if not intersections:
            g = gaps[0] if gaps else None
            intersections.append({
                "title": f"Exploratory pairing: {a.get('name', 'A')} and {b.get('name', 'B')}",
                "description": (
                    f"Insufficient overlapping evidence was retrieved to establish a strong connection. "
                    f"{NOVELTY_LANGUAGE}"
                ),
                "shared_problem": "Undetermined from available evidence.",
                "complementary_expertise": "Insufficient evidence.",
                "research_gap": gap_text(g),
                "why_researcher_a": "No relevant evidence was found in the searched literature.",
                "why_researcher_b": "No relevant evidence was found in the searched literature.",
                "novelty_confidence": 0.1,
                "feasibility_confidence": 0.1,
                # stay grounded even without topic overlap: reuse the gap evidence
                "evidence_ids": list(dict.fromkeys((g or {}).get("evidence_ids", [])))[:8],
                "gap_index": 0 if g else None,
            })
        return {"intersections": intersections[:max_n]}

    def _task_hypothesis_generation(self, data: dict[str, Any]) -> dict[str, Any]:
        ix = data.get("intersection", {})
        known_datasets: list[str] = data.get("verified_datasets", [])
        ev = list(ix.get("evidence_ids", []))
        dataset = known_datasets[0] if known_datasets else "INFERRED: suitable public dataset to be selected during verification"
        title = ix.get("title", "the proposed intersection")
        return {
            "research_question": f"Can the direction '{title}' produce measurable improvements over existing baselines?",
            "hypothesis": (
                f"Combining the complementary expertise described in '{title}' will yield measurable gains "
                f"on the identified shared problem, as motivated by the cited evidence."
            ),
            "motivation": ix.get("description", "") or "Motivated by the detected research gap.",
            "method": ix.get("complementary_expertise", "") or "Combined methodology from both researchers.",
            "dataset": dataset,
            "baseline": "Standard baselines reported in the cited literature.",
            "metrics": "Metrics used in the cited papers; otherwise task-appropriate metrics to be confirmed.",
            "expected_contribution": "A validated combined approach plus an empirical analysis of when it helps.",
            "risks": "Dataset availability, integration cost, and negative or inconclusive results.",
            "evidence_ids": ev,
        }

    def _task_experiment_design(self, data: dict[str, Any]) -> dict[str, Any]:
        hyp = data.get("hypothesis", {})
        known_datasets: list[str] = data.get("verified_datasets", [])
        ds = hyp.get("dataset") or (known_datasets[0] if known_datasets else "TBD")
        status = "VERIFIED" if any(ds and k and k.lower() in ds.lower() for k in known_datasets) else "INFERRED"
        return {
            "baseline": hyp.get("baseline", "Published baselines from cited work."),
            "proposed_approach": hyp.get("method", "Combined approach from the intersection."),
            "dataset": ds,
            "dataset_status": status,
            "training_setup": "Standard splits from the chosen dataset; hyperparameters tuned on validation split.",
            "evaluation_setup": "Held-out test evaluation repeated with multiple seeds; report mean and variance.",
            "metrics": hyp.get("metrics", "Task-appropriate metrics."),
            "ablations": [
                "Remove researcher-A-side component",
                "Remove researcher-B-side component",
                "Vary dataset size / domain shift",
            ],
            "expected_outcomes": hyp.get("expected_contribution", "Measurable improvement over baseline."),
            "failure_conditions": hyp.get("risks", "Negative or inconclusive results; dataset unavailable."),
        }

    def _task_evaluation_llm_only(self, data: dict[str, Any]) -> dict[str, Any]:
        """Evaluation-framework LLM-only baseline (no retrieval).

        Returns plausible gaps/intersections/hypotheses derived solely from the
        researcher profiles passed in ``input_data`` — with zero citations,
        because a retrieval-free baseline cannot produce groundable evidence.
        """
        a = data.get("researcher_a") or {}
        b = data.get("researcher_b") or {}
        a_topics = [t for t in (a.get("topics") or []) if t]
        b_topics = [t for t in (b.get("topics") or []) if t]
        a_methods = [t for t in (a.get("methods") or []) if t]
        b_methods = [t for t in (b.get("methods") or []) if t]
        a_name = a.get("name") or "Researcher A"
        b_name = b.get("name") or "Researcher B"

        all_topics = list(dict.fromkeys(a_topics + b_topics))
        shared = sorted(
            {t.lower() for t in a_topics} & {t.lower() for t in b_topics}
        )
        complementary = sorted(set(a_methods) ^ set(b_methods))

        gaps = [
            {
                "description": (
                    f"Possible gap: '{t}' appears on only one side of this pairing "
                    f"({a_name} / {b_name}); joint or comparative evidence was not "
                    f"provided, so a combined treatment is worth empirical study."
                )
            }
            for t in all_topics[:4]
        ]
        if not gaps:
            gaps = [{
                "description": (
                    "No topics were provided for this pairing, so no concrete gap "
                    "can be identified beyond the need for joint investigation."
                )
            }]

        intersections: list[dict[str, Any]] = []
        if shared:
            topic = shared[0]
            intersections.append({
                "title": f"Shared focus: {' + '.join(shared[:2]) or topic}",
                "description": (
                    f"Both profiles reference '{topic}'. Combining {a_name}'s methods "
                    f"({', '.join(a_methods[:2]) or 'see profile'}) with {b_name}'s "
                    f"methods ({', '.join(b_methods[:2]) or 'see profile'}) may advance "
                    f"the shared problem."
                ),
            })
        if complementary:
            m1, m2 = (complementary + ["", ""])[:2]
            intersections.append({
                "title": f"Method transfer: {m1 or 'A-side'} + {m2 or 'B-side'}",
                "description": (
                    f"The method profiles are complementary ({m1 or 'A'} vs {m2 or 'B'}); "
                    f"transferring {m1 or 'the first method'} toward "
                    f"{b_name}'s problems appears underexplored."
                ),
            })
        if not intersections:
            intersections.append({
                "title": f"Exploratory pairing: {a_name} and {b_name}",
                "description": (
                    "The combined expertise suggests a joint direction, but no evidence "
                    "was retrieved to substantiate a specific intersection."
                ),
            })

        hypotheses = [
            {
                "text": (
                    f"Applying the combined methodology suggested by '{ix['title']}' will "
                    f"yield measurable gains on the shared problem; this remains to be "
                    f"empirically validated."
                )
            }
            for ix in intersections[:2]
        ]

        return {
            "gaps": gaps[:4],
            "intersections": intersections[:2],
            "hypotheses": hypotheses[:2],
            "evidence_titles": [],
        }

    def _task_paper_writing(self, data: dict[str, Any]) -> dict[str, Any]:
        """Deterministic, fully grounded paper-draft construction.

        Every sentence references only input data (stored evidence, the
        intersection, and the hypothesis/experiment design). No results,
        citations, DOIs, datasets, or statistics are invented.
        """
        ix = data.get("intersection", {})
        hyp = data.get("hypothesis", {}) or {}
        exp = data.get("experiment", {}) or {}
        evidence: list[dict] = data.get("evidence", []) or []
        ev_ids = [e["id"] for e in evidence]
        statuses: dict[str, str] = {e["id"]: e.get("status", "INFERRED") for e in evidence}
        titles = [e.get("source_title") for e in evidence if e.get("source_title")]
        title = ix.get("title") or "Research direction across complementary expertise"
        gap = ix.get("research_gap") or (
            hyp.get("motivation") or "A research gap identified from the retrieved literature."
        )
        question = hyp.get("research_question") or (
            f"How can the direction '{title}' be advanced using the stored evidence?"
        )
        hypothesis = hyp.get("hypothesis_text") or (
            f"The proposed direction '{title}' deserves empirical evaluation as suggested by the stored evidence."
        )
        method = hyp.get("method") or ix.get("complementary_expertise") or "Combined methodology (see experiment design)."
        dataset = hyp.get("dataset") or exp.get("dataset") or "TBD — to be selected during dataset verification."
        exp_design = exp.get("proposed_approach") or method
        if exp.get("dataset_status"):
            exp_design += f" Dataset status (from experiment design): {exp['dataset_status']}."
        baseline = hyp.get("baseline") or "Standard baselines reported in the cited literature."
        metrics = hyp.get("metrics") or "Metrics used in the cited papers; otherwise task-appropriate metrics."
        verified_ev = [e["id"] for e in evidence if e.get("status") == "VERIFIED"]
        related = (
            "The draft is grounded in the following stored papers retrieved by the backend: "
            + (", ".join(dict.fromkeys([t for t in titles if t])) or "none")
            + ". Reference texts are reproduced in the References section and trace to stored evidence."
        )
        expected = (
            "EXPECTED / PROPOSED outcomes only — this is a research proposal, not a results report. "
            f"If the proposed approach performs as hypothesized, we expect measurable gains over the baseline "
            f"({baseline}) on {metrics}. No experimental results have been collected or reported in this draft."
        )
        intro = (
            f"{title} combines complementary expertise identified from the stored literature. "
            f"Motivation: {ix.get('description') or hyp.get('motivation') or gap} "
            f"{len(verified_ev)} of the referenced evidence items are independently VERIFIED."
        )
        return {
            "title": title,
            "abstract": (
                f"This is an AI-generated research-paper DRAFT proposing a study that combines the "
                f"complementary expertise described in '{title}'. The proposal is grounded in "
                f"{len(ev_ids)} stored evidence items ({len(verified_ev)} VERIFIED). Expected outcomes are "
                f"hypotheses, not measured results."
            ),
            "introduction": intro,
            "related_work": related,
            "research_gap": gap,
            "research_question": question,
            "hypothesis": hypothesis,
            "methodology": method,
            "experiment_design": (
                f"Dataset: {dataset}. Baseline: {baseline}. Metrics: {metrics}. "
                f"Setup: {exp.get('evaluation_setup') or 'evaluation to be defined'}. "
                f"Ablations: {', '.join(exp.get('ablations') or []) or 'to be defined'}. "
                f"Failure conditions: {exp.get('failure_conditions') or 'to be defined'}."
            ),
            "expected_results": expected,
            "limitations": [
                "This document is a draft proposal; it reports no experimentally validated findings.",
                "Hypotheses and gaps are inferred from the retrieved literature and may overlook outside evidence.",
                "Datasets and metrics marked INFERRED require verification before experimentation.",
            ],
            "conclusion": (
                f"Motivated by {gap}, the proposed study '{title}' is worth evaluating with the described "
                f"experiment design. None of its expected outcomes have been empirically validated."
            ),
            "evidence_ids": ev_ids[:30],
            "citation_evidence_ids": [
                eid for eid in ev_ids if statuses.get(eid) in ("VERIFIED", "INFERRED")
            ][:30],
        }
