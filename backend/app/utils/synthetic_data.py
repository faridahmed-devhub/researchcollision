"""Synthetic demo data used by mock providers and the seed script.

EVERY record here is fictional and must be presented as
SYNTHETIC DEMO DATA — never as real research.
"""
from __future__ import annotations

SYNTHETIC_DATA_LABEL = "SYNTHETIC DEMO DATA"

# ---------------------------------------------------------------------------
# Synthetic researchers (fictional)
# ---------------------------------------------------------------------------
SYNTHETIC_RESEARCHERS: list[dict] = [
    {
        "name": "Dr. Amara Chen",
        "affiliation": "Institute of Applied Language Technology",
        "bio": "Works on low-resource NLP, multilingual models, and data-efficient learning.",
        "aliases": ["A. Chen", "Amara C."],
        "topics": ["low-resource nlp", "multilingual models", "data-efficient learning"],
        "methods": ["transfer learning", "data augmentation", "few-shot learning"],
        "domains": ["natural language processing"],
    },
    {
        "name": "Prof. Diego Alvarez",
        "affiliation": "Center for Climate Systems Modeling",
        "bio": "Climate model downscaling, extreme weather prediction, uncertainty quantification.",
        "aliases": ["D. Alvarez"],
        "topics": ["climate modeling", "extreme weather", "uncertainty quantification"],
        "methods": ["ensemble simulation", "statistical downscaling", "bayesian methods"],
        "domains": ["climate science"],
    },
    {
        "name": "Dr. Priya Raghavan",
        "affiliation": "Medical Imaging Research Lab",
        "bio": "Deep learning for medical image segmentation and clinical deployment.",
        "aliases": ["P. Raghavan"],
        "topics": ["medical imaging", "image segmentation", "clinical ai"],
        "methods": ["convolutional networks", "self-supervised learning", "active learning"],
        "domains": ["medical imaging", "healthcare ai"],
    },
    {
        "name": "Dr. Jonas Weber",
        "affiliation": "Graph Learning Group",
        "bio": "Graph neural networks, knowledge graphs, relational reasoning.",
        "aliases": ["J. Weber"],
        "topics": ["graph neural networks", "knowledge graphs", "relational reasoning"],
        "methods": ["message passing", "graph embeddings", "contrastive learning"],
        "domains": ["machine learning"],
    },
    {
        "name": "Prof. Mei-Ling Sun",
        "affiliation": "Robotics and Embodied AI Institute",
        "bio": "Sim-to-real transfer, robot manipulation, embodied agents.",
        "aliases": ["M. Sun"],
        "topics": ["robot manipulation", "sim-to-real transfer", "embodied ai"],
        "methods": ["reinforcement learning", "domain randomization", "imitation learning"],
        "domains": ["robotics"],
    },
    {
        "name": "Dr. Sofia Marino",
        "affiliation": "Computational Materials Discovery Center",
        "bio": "Machine learning for materials discovery and molecular property prediction.",
        "aliases": ["S. Marino"],
        "topics": ["materials discovery", "molecular property prediction", "crystal structure"],
        "methods": ["graph neural networks", "surrogate optimization", "high-throughput screening"],
        "domains": ["materials science"],
    },
    {
        "name": "Dr. Kwame Osei",
        "affiliation": "Global Health Analytics Unit",
        "bio": "Epidemic forecasting, spatiotemporal modeling, public health informatics.",
        "aliases": ["K. Osei"],
        "topics": ["epidemic forecasting", "spatiotemporal modeling", "public health"],
        "methods": ["time series models", "bayesian hierarchical models", "mobility data analysis"],
        "domains": ["computational epidemiology"],
    },
    {
        "name": "Prof. Elena Petrova",
        "affiliation": "Speech and Audio Systems Group",
        "bio": "Speech recognition for under-resourced languages and speech accessibility.",
        "aliases": ["E. Petrova"],
        "topics": ["speech recognition", "low-resource languages", "speech accessibility"],
        "methods": ["self-supervised speech models", "transfer learning", "data augmentation"],
        "domains": ["speech processing"],
    },
]

# ---------------------------------------------------------------------------
# Synthetic papers (fictional titles/abstracts; DOIs are placeholders)
# ---------------------------------------------------------------------------
SYNTHETIC_PAPERS: list[dict] = [
    {
        "title": "Data-Efficient Adaptation of Multilingual Language Models for Low-Resource Languages",
        "abstract": (
            "Multilingual language models often underperform on low-resource languages due to limited "
            "training data. We propose a data-efficient adaptation strategy combining cross-lingual transfer "
            "with lightweight parameter tuning. Experiments across eight low-resource languages show consistent "
            "gains over strong baselines while using only a fraction of labeled data. Limitations include "
            "reliance on a related high-resource pivot language and evaluation restricted to text classification."
        ),
        "authors": ["Dr. Amara Chen"],
        "year": 2019,
        "venue": "Journal of Multilingual Computing (synthetic)",
        "doi": None,
        "provider_id": "syn-001",
        "topics": ["low-resource nlp", "multilingual models", "transfer learning"],
        "citation_count": 42,
    },
    {
        "title": "Few-Shot Named Entity Transfer with Synthetic Corpus Augmentation",
        "abstract": (
            "We study few-shot named entity recognition when almost no target-language annotations exist. "
            "A synthetic corpus augmentation pipeline generates pseudo-labeled examples from a related language. "
            "The method improves F1 by 6 points in the few-shot setting. Future work includes extending to "
            "structured prediction tasks beyond sequence labeling and reducing dependence on hand-built lexicons."
        ),
        "authors": ["Dr. Amara Chen"],
        "year": 2021,
        "venue": "Conference on Data-Efficient NLP (synthetic)",
        "doi": None,
        "provider_id": "syn-002",
        "topics": ["low-resource nlp", "data augmentation", "few-shot learning"],
        "citation_count": 18,
    },
    {
        "title": "Active Annotation Selection for Under-Resourced Text Analytics",
        "abstract": (
            "Annotation budgets dominate the cost of building NLP systems for under-resourced languages. "
            "We introduce an active annotation selection framework that combines uncertainty sampling with "
            "diversity constraints. Across three tasks the approach reaches baseline quality with 40% fewer labels. "
            "A key limitation is the assumption of a stable annotation interface, which may not hold in practice."
        ),
        "authors": ["Dr. Amara Chen"],
        "year": 2023,
        "venue": "Transactions on Human-Language Technologies (synthetic)",
        "doi": None,
        "provider_id": "syn-003",
        "topics": ["low-resource nlp", "active learning", "annotation"],
        "citation_count": 7,
    },
    {
        "title": "Statistical Downscaling of Precipitation Extremes under Nonstationary Climate",
        "abstract": (
            "We present a statistical downscaling framework for precipitation extremes that explicitly models "
            "nonstationarity in the climate system. Using ensemble simulations, the framework improves extreme-event "
            "quantile estimation relative to classical scaling approaches. Uncertainty remains large for rare events, "
            "and future work should integrate machine-learning emulators to reduce computational cost."
        ),
        "authors": ["Prof. Diego Alvarez"],
        "year": 2018,
        "venue": "Climate Dynamics Letters (synthetic)",
        "doi": None,
        "provider_id": "syn-004",
        "topics": ["climate modeling", "extreme weather", "uncertainty quantification"],
        "citation_count": 65,
    },
    {
        "title": "Bayesian Emulation of Regional Climate Model Ensembles",
        "abstract": (
            "Regional climate model ensembles are computationally expensive. We develop a Bayesian emulator that "
            "approximates ensemble outputs with calibrated uncertainty. The emulator reproduces temperature and "
            "precipitation response surfaces accurately at a fraction of the cost. Limitations include stationarity "
            "assumptions in the kernel design and limited testing outside temperate regions."
        ),
        "authors": ["Prof. Diego Alvarez"],
        "year": 2020,
        "venue": "Journal of Climate Computation (synthetic)",
        "doi": None,
        "provider_id": "syn-005",
        "topics": ["climate modeling", "uncertainty quantification", "bayesian methods"],
        "citation_count": 31,
    },
    {
        "title": "Deep Generative Downscaling for High-Resolution Climate Fields",
        "abstract": (
            "Generative models can produce high-resolution climate fields from coarse simulations. We adapt a "
            "conditional generative architecture to climate downscaling and evaluate on synthetic-orographic test "
            "cases. Generated fields preserve marginal statistics but underestimate spatial extremes. Evaluation "
            "beyond case studies and physical consistency constraints remain open challenges."
        ),
        "authors": ["Prof. Diego Alvarez"],
        "year": 2023,
        "venue": "Advances in Climate Machine Learning (synthetic)",
        "doi": None,
        "provider_id": "syn-006",
        "topics": ["climate modeling", "generative models", "extreme weather"],
        "citation_count": 12,
    },
    {
        "title": "Self-Supervised Pretraining for Medical Image Segmentation with Scarce Labels",
        "abstract": (
            "Labeled medical images are scarce and expensive. We study self-supervised pretraining strategies for "
            "segmentation under label scarcity, comparing contrastive and masked-image objectives. Pretraining "
            "improves Dice scores by up to 5 points on two modalities. Gains shrink for out-of-distribution scanners, "
            "motivating domain-general pretraining as future work."
        ),
        "authors": ["Dr. Priya Raghavan"],
        "year": 2021,
        "venue": "Medical Image Analysis Reports (synthetic)",
        "doi": None,
        "provider_id": "syn-007",
        "topics": ["medical imaging", "image segmentation", "self-supervised learning"],
        "citation_count": 54,
    },
    {
        "title": "Uncertainty-Aware Deep Segmentation for Clinical Decision Support",
        "abstract": (
            "Clinical adoption of deep segmentation requires trustworthy uncertainty estimates. We propose an "
            "uncertainty-aware segmentation network with calibration losses and evaluate clinician trust in a reader "
            "study. Calibration improves without sacrificing accuracy. The study size is small, and workflow "
            "integration in busy clinics remains untested."
        ),
        "authors": ["Dr. Priya Raghavan"],
        "year": 2023,
        "venue": "Clinical AI Transactions (synthetic)",
        "doi": None,
        "provider_id": "syn-008",
        "topics": ["medical imaging", "clinical ai", "uncertainty quantification"],
        "citation_count": 9,
    },
    {
        "title": "Contrastive Graph Representations for Relational Reasoning",
        "abstract": (
            "We introduce a contrastive objective for graph representation learning that captures relational "
            "structure without supervised labels. On link prediction and node classification benchmarks the method "
            "matches supervised baselines using 10x fewer labels. Scalability beyond million-node graphs and "
            "dynamic-graph settings are left open."
        ),
        "authors": ["Dr. Jonas Weber"],
        "year": 2020,
        "venue": "Graph Learning Workshop Proceedings (synthetic)",
        "doi": None,
        "provider_id": "syn-009",
        "topics": ["graph neural networks", "contrastive learning", "relational reasoning"],
        "citation_count": 77,
    },
    {
        "title": "Knowledge Graph Embeddings with Type Constraints for Scientific Facts",
        "abstract": (
            "Scientific knowledge graphs benefit from type-consistent embeddings. We propose type-constrained "
            "knowledge graph embeddings that respect entity schemas during training. The approach reduces implausible "
            "link predictions by half on a scientific-facts benchmark. Limitations include reliance on complete type "
            "ontologies, rarely available in emerging scientific domains."
        ),
        "authors": ["Dr. Jonas Weber"],
        "year": 2022,
        "venue": "Semantic Web Science (synthetic)",
        "doi": None,
        "provider_id": "syn-010",
        "topics": ["knowledge graphs", "graph embeddings", "scientific information"],
        "citation_count": 22,
    },
    {
        "title": "Sim-to-Real Transfer via Domain Randomization for Robotic Manipulation",
        "abstract": (
            "Sim-to-real gap limits deployment of learned manipulation policies. We quantify the effect of domain "
            "randomization schedules on transfer success rates across three manipulation tasks. Structured randomization "
            "curricula improve success by 15%. Results are limited to rigid objects; deformable objects remain an open "
            "challenge."
        ),
        "authors": ["Prof. Mei-Ling Sun"],
        "year": 2019,
        "venue": "Robotics Systems Journal (synthetic)",
        "doi": None,
        "provider_id": "syn-011",
        "topics": ["sim-to-real transfer", "robot manipulation", "domain randomization"],
        "citation_count": 88,
    },
    {
        "title": "Language-Conditioned Manipulation Policies from Demonstration",
        "abstract": (
            "We learn language-conditioned manipulation policies from human demonstrations using imitation learning. "
            "The policy generalizes to unseen object categories described by novel phrases in 60% of trials. Failure "
            "cases concentrate on long-horizon compositions, suggesting hierarchical decomposition as future work."
        ),
        "authors": ["Prof. Mei-Ling Sun"],
        "year": 2022,
        "venue": "Embodied AI Conference (synthetic)",
        "doi": None,
        "provider_id": "syn-012",
        "topics": ["robot manipulation", "imitation learning", "embodied ai"],
        "citation_count": 25,
    },
    {
        "title": "Graph Neural Surrogates for Crystal Property Screening",
        "abstract": (
            "High-throughput screening of candidate crystals is bottlenecked by expensive quantum calculations. "
            "We train graph neural surrogates to predict formation energies, enabling 100x faster screening with "
            "rank correlation above 0.95 against DFT. Extrapolation to unseen chemistries degrades sharply, "
            "highlighting the need for uncertainty-guided active screening."
        ),
        "authors": ["Dr. Sofia Marino"],
        "year": 2021,
        "venue": "Materials Intelligence (synthetic)",
        "doi": None,
        "provider_id": "syn-013",
        "topics": ["materials discovery", "molecular property prediction", "graph neural networks"],
        "citation_count": 61,
    },
    {
        "title": "Active Learning Loops for Accelerated Materials Discovery",
        "abstract": (
            "We close the loop between surrogate predictions and quantum calculations with an active learning loop "
            "for materials discovery. The loop discovers stable candidates 3x faster than random search on a "
            "benchmark family. The approach assumes cheap retraining and may not scale to multi-objective design, "
            "which we flag as a limitation."
        ),
        "authors": ["Dr. Sofia Marino"],
        "year": 2023,
        "venue": "Materials Intelligence (synthetic)",
        "doi": None,
        "provider_id": "syn-014",
        "topics": ["materials discovery", "active learning", "surrogate optimization"],
        "citation_count": 14,
    },
    {
        "title": "Bayesian Hierarchical Models for Epidemic Nowcasting with Mobility Data",
        "abstract": (
            "Timely epidemic nowcasting benefits from mobility signals. We develop a Bayesian hierarchical model "
            "fusing case reports with mobility indices, improving short-horizon forecasts in two synthetic districts. "
            "Mobility biases across demographic groups are not fully corrected, and equity implications require "
            "dedicated study."
        ),
        "authors": ["Dr. Kwame Osei"],
        "year": 2020,
        "venue": "Epidemic Analytics (synthetic)",
        "doi": None,
        "provider_id": "syn-015",
        "topics": ["epidemic forecasting", "bayesian hierarchical models", "public health"],
        "citation_count": 39,
    },
    {
        "title": "Spatiotemporal Graph Models for Disease Spread Prediction",
        "abstract": (
            "We model disease spread with spatiotemporal graphs whose edges encode human mobility. The model predicts "
            "district-level incidence with lower error than purely temporal baselines across simulated outbreaks. "
            "Robustness to reporting delays and sparse surveillance is identified as a key limitation."
        ),
        "authors": ["Dr. Kwame Osei"],
        "year": 2022,
        "venue": "Spatial Health Informatics (synthetic)",
        "doi": None,
        "provider_id": "syn-016",
        "topics": ["epidemic forecasting", "spatiotemporal modeling", "graph neural networks"],
        "citation_count": 17,
    },
    {
        "title": "Self-Supervised Speech Representations for Under-Resourced Languages",
        "abstract": (
            "Self-supervised speech models transfer poorly to very low-resource languages. We fine-tune with "
            "language-adaptive pretraining on unlabeled radio archives, cutting word error rate by 18% on two "
            "languages. Compute cost of adaptation is high, motivating parameter-efficient adaptation as future work."
        ),
        "authors": ["Prof. Elena Petrova"],
        "year": 2021,
        "venue": "Speech Technology Letters (synthetic)",
        "doi": None,
        "provider_id": "syn-017",
        "topics": ["speech recognition", "low-resource languages", "self-supervised learning"],
        "citation_count": 45,
    },
    {
        "title": "Accessible Voice Interfaces: Error Patterns for Dysarthric Speech",
        "abstract": (
            "We analyze recognition error patterns for dysarthric speech across commercial and research systems. "
            "A taxonomy of errors shows systematic confusions linked to prosodic patterns rather than articulation "
            "alone. Dataset diversity is limited and largely English-centric, which constrains generalization claims."
        ),
        "authors": ["Prof. Elena Petrova"],
        "year": 2023,
        "venue": "Accessibility and Speech (synthetic)",
        "doi": None,
        "provider_id": "syn-018",
        "topics": ["speech accessibility", "speech recognition", "low-resource languages"],
        "citation_count": 8,
    },
]


def synthetic_paper_metadata(paper: dict) -> dict:
    """Attach the synthetic marker to every exported field set."""
    return {**paper, "is_synthetic": True}
