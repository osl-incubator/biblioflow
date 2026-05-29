"""Seed biblioflow-web with rich demo projects and datasets."""

from __future__ import annotations

import argparse
import json
import os
import sys
from io import BytesIO
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
BACKEND_ROOT = Path(__file__).resolve().parents[1]
BIBLIOFLOW_SRC = REPO_ROOT / "packages" / "biblioflow" / "src"
BACKEND_SRC = BACKEND_ROOT / "src"
for path in (BACKEND_SRC, BIBLIOFLOW_SRC):
    sys.path.insert(0, str(path))

import biblioflow as bf  # noqa: E402

from biblioflow_web_backend.core.config import default_data_dir  # noqa: E402
from biblioflow_web_backend.services.dataset_service import DatasetService  # noqa: E402
from biblioflow_web_backend.services.export_service import ExportService  # noqa: E402
from biblioflow_web_backend.services.file_store import FileStore  # noqa: E402
from biblioflow_web_backend.services.project_store import ProjectStore  # noqa: E402
from biblioflow_web_backend.services.screening_service import (  # noqa: E402
    ScreeningService,
)

SEED_MARKER = "biblioflow-web-demo-seed"
SEED_VERSION = "2026-05-28"


def ref(author: str, year: int, title: str, doi: str | None = None) -> str:
    """Return a citation-like reference string."""
    suffix = f" DOI {doi}" if doi else ""
    return f"{author}. {year}. {title}.{suffix}"


def evidence_synthesis_records() -> list[dict[str, Any]]:
    """Return a detailed AI/evidence-synthesis demo collection."""
    return [
        {
            "source_id": "SCOPUS:BF-DEMO-001",
            "title": "Machine learning triage for systematic review screening",
            "abstract": (
                "Evaluates supervised machine-learning models for prioritising "
                "titles and abstracts during evidence synthesis workflows."
            ),
            "authors": ["Maya Chen", "Lucas Almeida", "Priya Nair"],
            "source_title": "Journal of Evidence Synthesis Methods",
            "publication_year": 2018,
            "doi": "10.5555/bf.2018.001",
            "url": "https://example.org/bf-demo/001",
            "keywords_author": [
                "systematic review",
                "machine learning",
                "screening",
            ],
            "keywords_index": ["evidence synthesis", "automation", "text mining"],
            "references": [
                ref("O'Neil K", 2016, "Active learning for citation screening"),
                ref("Singh P", 2017, "Reproducible evidence maps"),
            ],
            "document_type": "Article",
            "language": "English",
            "volume": "12",
            "issue": "1",
            "start_page": "1",
            "end_page": "14",
            "pages": "1-14",
            "issn": "2049-3630",
            "publisher": "Open Science Press",
            "affiliations": [
                "University of Lisbon, Lisbon, Portugal",
                "Institute for Evidence Systems, Boston, United States",
            ],
            "countries": ["Portugal", "United States"],
            "cited_by_count": 84,
        },
        {
            "source_id": "WOS:BF-DEMO-002",
            "title": "Reusable metadata pipelines for living reviews",
            "abstract": (
                "Describes an interoperable metadata pipeline for continuously "
                "updated systematic reviews and bibliometric dashboards."
            ),
            "authors": ["Helena Costa", "Maya Chen", "Noah Williams"],
            "source_title": "Research Synthesis Informatics",
            "publication_year": 2019,
            "doi": "10.5555/bf.2019.002",
            "url": "https://example.org/bf-demo/002",
            "keywords_author": ["living review", "metadata", "pipeline"],
            "keywords_index": ["interoperability", "automation", "open science"],
            "references": [
                ref(
                    "Chen M",
                    2018,
                    "Machine learning triage for systematic review screening",
                    "10.5555/bf.2018.001",
                ),
                ref("Garcia R", 2018, "Persistent identifiers in review updates"),
            ],
            "document_type": "Article",
            "language": "English",
            "volume": "3",
            "issue": "2",
            "start_page": "88",
            "end_page": "104",
            "pages": "88-104",
            "issn": "2764-1020",
            "publisher": "Evidence Systems Society",
            "affiliations": [
                "Federal University of Rio de Janeiro, Rio de Janeiro, Brazil",
                "University of Lisbon, Lisbon, Portugal",
            ],
            "countries": ["Brazil", "Portugal", "United Kingdom"],
            "cited_by_count": 63,
        },
        {
            "source_id": "PUBMED:BF-DEMO-003",
            "title": "Human-in-the-loop classifiers for rapid evidence appraisal",
            "abstract": (
                "Reports a mixed-methods evaluation of human-in-the-loop "
                "classification tools for rapid guideline development."
            ),
            "authors": ["Priya Nair", "Oliver Smith", "Fatima Haddad"],
            "source_title": "Implementation Science and Evidence",
            "publication_year": 2020,
            "doi": "10.5555/bf.2020.003",
            "url": "https://example.org/bf-demo/003",
            "keywords_author": [
                "rapid review",
                "classification",
                "human-in-the-loop",
            ],
            "keywords_index": ["guidelines", "active learning", "appraisal"],
            "references": [
                ref(
                    "Chen M",
                    2018,
                    "Machine learning triage for systematic review screening",
                    "10.5555/bf.2018.001",
                ),
                ref(
                    "Costa H",
                    2019,
                    "Reusable metadata pipelines for living reviews",
                    "10.5555/bf.2019.002",
                ),
            ],
            "document_type": "Article",
            "language": "English",
            "volume": "8",
            "issue": "4",
            "start_page": "211",
            "end_page": "229",
            "pages": "211-229",
            "issn": "2398-4012",
            "publisher": "Health Evidence Forum",
            "affiliations": [
                "National Institute of Health Analytics, Delhi, India",
                "University of Manchester, Manchester, United Kingdom",
            ],
            "countries": ["India", "United Kingdom", "Lebanon"],
            "cited_by_count": 77,
        },
        {
            "source_id": "OPENALEX:BF-DEMO-004",
            "title": "Benchmarking bibliographic deduplication algorithms",
            "abstract": (
                "Compares DOI, title, author, and fuzzy-matching approaches for "
                "deduplicating multi-database bibliographic search results."
            ),
            "authors": ["Lucas Almeida", "Sofia Rossi", "Maya Chen"],
            "source_title": "Scientometrics and Data Quality",
            "publication_year": 2020,
            "doi": "10.5555/bf.2020.004",
            "url": "https://example.org/bf-demo/004",
            "keywords_author": ["deduplication", "bibliographic data", "DOI"],
            "keywords_index": ["record linkage", "data quality", "metadata"],
            "references": [
                ref(
                    "Costa H",
                    2019,
                    "Reusable metadata pipelines for living reviews",
                    "10.5555/bf.2019.002",
                ),
                ref("Rossi S", 2019, "Fuzzy matching for scholarly metadata"),
            ],
            "document_type": "Conference Paper",
            "language": "English",
            "volume": "44",
            "issue": "S1",
            "start_page": "55",
            "end_page": "67",
            "pages": "55-67",
            "issn": "0138-9130",
            "publisher": "Metric Studies Association",
            "affiliations": [
                "University of São Paulo, São Paulo, Brazil",
                "University of Bologna, Bologna, Italy",
            ],
            "countries": ["Brazil", "Italy", "Portugal"],
            "cited_by_count": 52,
        },
        {
            "source_id": "SCOPUS:BF-DEMO-005",
            "title": "Topic modelling for evidence gap maps in public health",
            "abstract": (
                "Demonstrates topic modelling and expert validation for creating "
                "evidence gap maps in public-health interventions."
            ),
            "authors": ["Fatima Haddad", "Amara Okafor", "Priya Nair"],
            "source_title": "Global Public Health Reviews",
            "publication_year": 2021,
            "doi": "10.5555/bf.2021.005",
            "url": "https://example.org/bf-demo/005",
            "keywords_author": ["topic modelling", "evidence gap map", "public health"],
            "keywords_index": ["text mining", "semantic analysis", "health policy"],
            "references": [
                ref(
                    "Nair P",
                    2020,
                    "Human-in-the-loop classifiers for rapid evidence appraisal",
                    "10.5555/bf.2020.003",
                ),
                ref("Okafor A", 2020, "Equity dimensions in public health reviews"),
            ],
            "document_type": "Article",
            "language": "English",
            "volume": "16",
            "issue": "3",
            "start_page": "310",
            "end_page": "331",
            "pages": "310-331",
            "issn": "1744-1692",
            "publisher": "Global Health Review Press",
            "affiliations": [
                "American University of Beirut, Beirut, Lebanon",
                "University of Lagos, Lagos, Nigeria",
            ],
            "countries": ["Lebanon", "Nigeria", "India"],
            "cited_by_count": 91,
        },
        {
            "source_id": "CROSSREF:BF-DEMO-006",
            "title": "Open citation graphs for systematic review updates",
            "abstract": (
                "Uses open citation graphs to detect newly relevant studies and "
                "prioritise updates for mature systematic reviews."
            ),
            "authors": ["Noah Williams", "Helena Costa", "Sofia Rossi"],
            "source_title": "Open Research Infrastructure",
            "publication_year": 2021,
            "doi": "10.5555/bf.2021.006",
            "url": "https://example.org/bf-demo/006",
            "keywords_author": ["open citations", "review update", "citation graph"],
            "keywords_index": [
                "bibliographic coupling",
                "direct citation",
                "open science",
            ],
            "references": [
                ref(
                    "Costa H",
                    2019,
                    "Reusable metadata pipelines for living reviews",
                    "10.5555/bf.2019.002",
                ),
                ref(
                    "Almeida L",
                    2020,
                    "Benchmarking bibliographic deduplication algorithms",
                    "10.5555/bf.2020.004",
                ),
            ],
            "document_type": "Review",
            "language": "English",
            "volume": "7",
            "issue": "1",
            "start_page": "15",
            "end_page": "39",
            "pages": "15-39",
            "issn": "2752-4491",
            "publisher": "Open Infrastructure Collective",
            "affiliations": [
                "University College London, London, United Kingdom",
                "Federal University of Rio de Janeiro, Rio de Janeiro, Brazil",
            ],
            "countries": ["United Kingdom", "Brazil", "Italy"],
            "cited_by_count": 68,
        },
        {
            "source_id": "WOS:BF-DEMO-007",
            "title": "Responsible AI principles for evidence synthesis platforms",
            "abstract": (
                "Synthesises transparency, auditability, human oversight, and bias "
                "monitoring principles for AI-enabled review tools."
            ),
            "authors": ["Maya Chen", "Fatima Haddad", "Jonas Müller"],
            "source_title": "AI and Society in Health Research",
            "publication_year": 2022,
            "doi": "10.5555/bf.2022.007",
            "url": "https://example.org/bf-demo/007",
            "keywords_author": ["responsible AI", "evidence synthesis", "auditability"],
            "keywords_index": ["bias", "transparency", "governance"],
            "references": [
                ref(
                    "Nair P",
                    2020,
                    "Human-in-the-loop classifiers for rapid evidence appraisal",
                    "10.5555/bf.2020.003",
                ),
                ref(
                    "Haddad F",
                    2021,
                    "Topic modelling for evidence gap maps in public health",
                    "10.5555/bf.2021.005",
                ),
            ],
            "document_type": "Review",
            "language": "English",
            "volume": "5",
            "issue": "2",
            "start_page": "140",
            "end_page": "165",
            "pages": "140-165",
            "issn": "2632-7001",
            "publisher": "Society and Algorithms Press",
            "affiliations": [
                "Institute for Evidence Systems, Boston, United States",
                "University of Heidelberg, Heidelberg, Germany",
            ],
            "countries": ["United States", "Lebanon", "Germany"],
            "cited_by_count": 112,
        },
        {
            "source_id": "PUBMED:BF-DEMO-008",
            "title": "Automated extraction of PICO elements from clinical trials",
            "abstract": (
                "Evaluates sequence-labelling models for extracting population, "
                "intervention, comparator, and outcome elements from trial reports."
            ),
            "authors": ["Oliver Smith", "Priya Nair", "Leila Mansour"],
            "source_title": "Biomedical Text Mining",
            "publication_year": 2022,
            "doi": "10.5555/bf.2022.008",
            "url": "https://example.org/bf-demo/008",
            "keywords_author": ["PICO", "information extraction", "clinical trials"],
            "keywords_index": [
                "natural language processing",
                "text mining",
                "appraisal",
            ],
            "references": [
                ref(
                    "Nair P",
                    2020,
                    "Human-in-the-loop classifiers for rapid evidence appraisal",
                    "10.5555/bf.2020.003",
                ),
                ref("Mansour L", 2021, "Entity extraction in biomedical abstracts"),
            ],
            "document_type": "Article",
            "language": "English",
            "volume": "11",
            "issue": "6",
            "start_page": "455",
            "end_page": "478",
            "pages": "455-478",
            "issn": "2468-0641",
            "publisher": "Biomedical NLP Association",
            "affiliations": [
                "University of Manchester, Manchester, United Kingdom",
                "National Institute of Health Analytics, Delhi, India",
                "Qatar Computing Research Institute, Doha, Qatar",
            ],
            "countries": ["United Kingdom", "India", "Qatar"],
            "cited_by_count": 73,
        },
        {
            "source_id": "SCOPUS:BF-DEMO-009",
            "title": "Interactive dashboards for bibliometric review exploration",
            "abstract": (
                "Introduces dashboard patterns for moving from descriptive "
                "bibliometrics to review decisions in multidisciplinary teams."
            ),
            "authors": ["Sofia Rossi", "Lucas Almeida", "Noah Williams"],
            "source_title": "Scientometrics and Data Quality",
            "publication_year": 2023,
            "doi": "10.5555/bf.2023.009",
            "url": "https://example.org/bf-demo/009",
            "keywords_author": ["bibliometrics", "dashboard", "science mapping"],
            "keywords_index": ["visual analytics", "user interface", "open science"],
            "references": [
                ref(
                    "Almeida L",
                    2020,
                    "Benchmarking bibliographic deduplication algorithms",
                    "10.5555/bf.2020.004",
                ),
                ref(
                    "Williams N",
                    2021,
                    "Open citation graphs for systematic review updates",
                    "10.5555/bf.2021.006",
                ),
            ],
            "document_type": "Article",
            "language": "English",
            "volume": "47",
            "issue": "4",
            "start_page": "501",
            "end_page": "528",
            "pages": "501-528",
            "issn": "0138-9130",
            "publisher": "Metric Studies Association",
            "affiliations": [
                "University of Bologna, Bologna, Italy",
                "University of São Paulo, São Paulo, Brazil",
                "University College London, London, United Kingdom",
            ],
            "countries": ["Italy", "Brazil", "United Kingdom"],
            "cited_by_count": 59,
        },
        {
            "source_id": "OPENALEX:BF-DEMO-010",
            "title": "Network meta-evidence maps using keyword co-occurrence",
            "abstract": (
                "Combines keyword co-occurrence, expert coding, and citation "
                "links to identify clusters in complex intervention literatures."
            ),
            "authors": ["Amara Okafor", "Fatima Haddad", "Maya Chen"],
            "source_title": "Global Public Health Reviews",
            "publication_year": 2023,
            "doi": "10.5555/bf.2023.010",
            "url": "https://example.org/bf-demo/010",
            "keywords_author": ["co-occurrence", "evidence map", "network"],
            "keywords_index": ["science mapping", "public health", "clustering"],
            "references": [
                ref(
                    "Haddad F",
                    2021,
                    "Topic modelling for evidence gap maps in public health",
                    "10.5555/bf.2021.005",
                ),
                ref(
                    "Rossi S",
                    2023,
                    "Interactive dashboards for bibliometric review exploration",
                    "10.5555/bf.2023.009",
                ),
            ],
            "document_type": "Article",
            "language": "English",
            "volume": "18",
            "issue": "2",
            "start_page": "188",
            "end_page": "214",
            "pages": "188-214",
            "issn": "1744-1692",
            "publisher": "Global Health Review Press",
            "affiliations": [
                "University of Lagos, Lagos, Nigeria",
                "American University of Beirut, Beirut, Lebanon",
            ],
            "countries": ["Nigeria", "Lebanon", "United States"],
            "cited_by_count": 46,
        },
        {
            "source_id": "WOS:BF-DEMO-011",
            "title": "Reproducible search strategies as executable research objects",
            "abstract": (
                "Proposes packaging search strings, database metadata, and import "
                "logs as executable objects for transparent review updates."
            ),
            "authors": ["Jonas Müller", "Helena Costa", "Leila Mansour"],
            "source_title": "Open Research Infrastructure",
            "publication_year": 2024,
            "doi": "10.5555/bf.2024.011",
            "url": "https://example.org/bf-demo/011",
            "keywords_author": [
                "search strategy",
                "reproducibility",
                "research object",
            ],
            "keywords_index": ["metadata", "open science", "workflow"],
            "references": [
                ref(
                    "Costa H",
                    2019,
                    "Reusable metadata pipelines for living reviews",
                    "10.5555/bf.2019.002",
                ),
                ref(
                    "Williams N",
                    2021,
                    "Open citation graphs for systematic review updates",
                    "10.5555/bf.2021.006",
                ),
            ],
            "document_type": "Perspective",
            "language": "English",
            "volume": "10",
            "issue": "1",
            "start_page": "40",
            "end_page": "58",
            "pages": "40-58",
            "issn": "2752-4491",
            "publisher": "Open Infrastructure Collective",
            "affiliations": [
                "University of Heidelberg, Heidelberg, Germany",
                "Federal University of Rio de Janeiro, Rio de Janeiro, Brazil",
                "Qatar Computing Research Institute, Doha, Qatar",
            ],
            "countries": ["Germany", "Brazil", "Qatar"],
            "cited_by_count": 24,
        },
        {
            "source_id": "CROSSREF:BF-DEMO-012",
            "title": "Evaluation metrics for AI-assisted citation screening",
            "abstract": (
                "Defines recall-first metrics, workload saved over sampling, and "
                "calibration plots for AI-assisted citation screening systems."
            ),
            "authors": ["Maya Chen", "Oliver Smith", "Amara Okafor"],
            "source_title": "Journal of Evidence Synthesis Methods",
            "publication_year": 2024,
            "doi": "10.5555/bf.2024.012",
            "url": "https://example.org/bf-demo/012",
            "keywords_author": ["evaluation", "citation screening", "recall"],
            "keywords_index": ["machine learning", "benchmarking", "automation"],
            "references": [
                ref(
                    "Chen M",
                    2018,
                    "Machine learning triage for systematic review screening",
                    "10.5555/bf.2018.001",
                ),
                ref(
                    "Chen M",
                    2022,
                    "Responsible AI principles for evidence synthesis platforms",
                    "10.5555/bf.2022.007",
                ),
            ],
            "document_type": "Article",
            "language": "English",
            "volume": "18",
            "issue": "1",
            "start_page": "77",
            "end_page": "101",
            "pages": "77-101",
            "issn": "2049-3630",
            "publisher": "Open Science Press",
            "affiliations": [
                "Institute for Evidence Systems, Boston, United States",
                "University of Manchester, Manchester, United Kingdom",
                "University of Lagos, Lagos, Nigeria",
            ],
            "countries": ["United States", "United Kingdom", "Nigeria"],
            "cited_by_count": 38,
        },
    ]


def climate_policy_records() -> list[dict[str, Any]]:
    """Return a second detailed demo collection for filters and facets."""
    rows: list[dict[str, Any]] = []
    topics = [
        (
            "Urban heat adaptation and health equity indicators",
            ["heat adaptation", "health equity", "urban climate"],
            ["equity", "vulnerability", "policy"],
            ["Aisha Rahman", "Mateo Silva", "Emily Turner"],
            "Climate and Health Policy",
            2017,
            "Article",
            ["Bangladesh", "Brazil", "Canada"],
            71,
        ),
        (
            "Bibliometric trends in climate-health adaptation research",
            ["bibliometrics", "climate health", "adaptation"],
            ["science mapping", "public health", "policy"],
            ["Emily Turner", "Jonas Müller", "Aisha Rahman"],
            "Environmental Evidence Maps",
            2018,
            "Review",
            ["Canada", "Germany", "Bangladesh"],
            66,
        ),
        (
            "Early warning systems for flood-related disease outbreaks",
            ["early warning", "floods", "disease outbreaks"],
            ["surveillance", "risk communication", "climate services"],
            ["Mateo Silva", "Noor Khan", "Aisha Rahman"],
            "Global Environmental Health",
            2019,
            "Article",
            ["Brazil", "Pakistan", "Bangladesh"],
            58,
        ),
        (
            "Heat-health action plans in rapidly urbanising cities",
            ["heat health", "action plans", "urbanisation"],
            ["governance", "adaptation", "public health"],
            ["Noor Khan", "Emily Turner", "Lina Park"],
            "Climate and Health Policy",
            2020,
            "Article",
            ["Pakistan", "Canada", "South Korea"],
            49,
        ),
        (
            "Community-led adaptation evidence in coastal regions",
            ["community adaptation", "coastal resilience", "evidence synthesis"],
            ["participatory research", "equity", "climate policy"],
            ["Lina Park", "Mateo Silva", "Aisha Rahman"],
            "Environmental Evidence Maps",
            2021,
            "Case Study",
            ["South Korea", "Brazil", "Bangladesh"],
            33,
        ),
        (
            "Machine learning nowcasting for climate-sensitive infections",
            ["machine learning", "nowcasting", "climate-sensitive infections"],
            ["forecasting", "surveillance", "public health"],
            ["Jonas Müller", "Noor Khan", "Emily Turner"],
            "Global Environmental Health",
            2022,
            "Article",
            ["Germany", "Pakistan", "Canada"],
            42,
        ),
        (
            "Policy dashboards for monitoring adaptation implementation",
            ["dashboard", "adaptation implementation", "monitoring"],
            ["visual analytics", "policy", "climate services"],
            ["Emily Turner", "Lina Park", "Mateo Silva"],
            "Policy Analytics Quarterly",
            2023,
            "Article",
            ["Canada", "South Korea", "Brazil"],
            27,
        ),
        (
            "Open data standards for climate-health evidence repositories",
            ["open data", "standards", "evidence repositories"],
            ["metadata", "interoperability", "climate health"],
            ["Aisha Rahman", "Jonas Müller", "Lina Park"],
            "Policy Analytics Quarterly",
            2024,
            "Perspective",
            ["Bangladesh", "Germany", "South Korea"],
            19,
        ),
    ]
    for index, (
        title,
        author_keywords,
        index_keywords,
        authors,
        source,
        year,
        doc_type,
        countries,
        citations,
    ) in enumerate(topics, start=1):
        doi = f"10.5555/climate.{year}.{index:03d}"
        rows.append(
            {
                "source_id": f"CLIMATE-DEMO-{index:03d}",
                "title": title,
                "abstract": (
                    f"Synthetic demo record about {title.lower()} for testing "
                    "filters, source summaries, collaboration networks, and "
                    "keyword analyses in biblioflow-web."
                ),
                "authors": authors,
                "source_title": source,
                "publication_year": year,
                "doi": doi,
                "url": f"https://example.org/bf-climate/{index:03d}",
                "keywords_author": author_keywords,
                "keywords_index": index_keywords,
                "references": [
                    ref("Rahman A", 2016, "Climate adaptation and public health"),
                    ref("Turner E", 2017, "Equity indicators for climate policy"),
                ],
                "document_type": doc_type,
                "language": "English",
                "volume": str(20 + index),
                "issue": str((index % 4) + 1),
                "start_page": str(100 + index * 10),
                "end_page": str(109 + index * 10),
                "pages": f"{100 + index * 10}-{109 + index * 10}",
                "issn": "2999-1000",
                "publisher": "Climate Evidence Collective",
                "affiliations": [f"Demo Institute {country}" for country in countries],
                "countries": countries,
                "cited_by_count": citations,
            }
        )
    return rows


def quality_sandbox_records() -> list[dict[str, Any]]:
    """Return intentionally imperfect records for validation testing."""
    return [
        {
            "source_id": "QUALITY-001",
            "title": "Complete record for validation baseline",
            "authors": ["Iris Novak", "Yuki Tanaka"],
            "source_title": "Metadata Quality Reports",
            "publication_year": 2020,
            "doi": "10.5555/quality.001",
            "keywords_author": ["metadata", "validation"],
            "keywords_index": ["quality assurance"],
            "references": [],
            "document_type": "Article",
            "language": "English",
            "affiliations": ["University of Zagreb, Zagreb, Croatia"],
            "countries": ["Croatia", "Japan"],
            "cited_by_count": 12,
        },
        {
            "source_id": "QUALITY-002",
            "title": "Record missing DOI but useful for filters",
            "authors": ["Iris Novak"],
            "source_title": "Metadata Quality Reports",
            "publication_year": 2021,
            "keywords_author": ["missing doi", "data cleaning"],
            "keywords_index": ["validation"],
            "references": [],
            "document_type": "Note",
            "language": "English",
            "affiliations": ["University of Zagreb, Zagreb, Croatia"],
            "countries": ["Croatia"],
            "cited_by_count": 5,
        },
        {
            "source_id": "QUALITY-003",
            "title": "Record missing publication year",
            "authors": ["Yuki Tanaka", "Lars Jensen"],
            "source_title": "Data Repair Letters",
            "doi": "10.5555/quality.003",
            "keywords_author": ["missing year", "metadata repair"],
            "keywords_index": ["data quality"],
            "references": [],
            "document_type": "Letter",
            "language": "English",
            "affiliations": ["Kyoto Demo Lab, Kyoto, Japan"],
            "countries": ["Japan", "Denmark"],
            "cited_by_count": 2,
        },
        {
            "source_id": "QUALITY-004",
            "authors": ["Lars Jensen"],
            "source_title": "Data Repair Letters",
            "publication_year": 2022,
            "doi": "10.5555/quality.004",
            "keywords_author": ["missing title", "edge case"],
            "keywords_index": ["validation"],
            "references": [],
            "document_type": "Article",
            "language": "English",
            "affiliations": ["Copenhagen Data Methods, Copenhagen, Denmark"],
            "countries": ["Denmark"],
            "cited_by_count": 1,
        },
        {
            "source_id": "QUALITY-005",
            "title": "Duplicate DOI record A",
            "authors": ["Iris Novak", "Lars Jensen"],
            "source_title": "Metadata Quality Reports",
            "publication_year": 2023,
            "doi": "10.5555/quality.dup",
            "keywords_author": ["duplicate", "doi"],
            "keywords_index": ["deduplication"],
            "references": [],
            "document_type": "Article",
            "language": "English",
            "affiliations": ["University of Zagreb, Zagreb, Croatia"],
            "countries": ["Croatia", "Denmark"],
            "cited_by_count": 8,
        },
        {
            "source_id": "QUALITY-006",
            "title": "Duplicate DOI record B",
            "authors": ["Yuki Tanaka"],
            "source_title": "Data Repair Letters",
            "publication_year": 2023,
            "doi": "10.5555/quality.dup",
            "keywords_author": ["duplicate", "record linkage"],
            "keywords_index": ["deduplication"],
            "references": [],
            "document_type": "Preprint",
            "language": "English",
            "affiliations": ["Kyoto Demo Lab, Kyoto, Japan"],
            "countries": ["Japan"],
            "cited_by_count": 4,
        },
    ]


PROJECT_SPECS = [
    {
        "name": "Demo — AI Evidence Synthesis",
        "description": (
            "A rich, network-friendly demo project with recurring authors, "
            "sources, countries, keywords, DOIs, references, and citation counts."
        ),
        "filename": "ai_evidence_synthesis_demo.json",
        "records": evidence_synthesis_records,
        "tags": ["ai", "evidence synthesis", "complete", "networks"],
        "filters": {
            "year_min": 2020,
            "year_max": 2024,
            "keywords": ["machine learning", "evidence synthesis"],
            "include_missing_year": True,
        },
    },
    {
        "name": "Demo — Climate Health Policy",
        "description": (
            "A second complete project for testing facets, filters, source "
            "rankings, country collaboration, and keyword co-occurrence."
        ),
        "filename": "climate_health_policy_demo.json",
        "records": climate_policy_records,
        "tags": ["climate", "public health", "policy", "complete"],
        "filters": {
            "year_min": 2019,
            "sources": ["Climate and Health Policy", "Environmental Evidence Maps"],
            "include_missing_year": True,
        },
    },
    {
        "name": "Demo — Data Quality Sandbox",
        "description": (
            "An intentionally imperfect dataset for testing validation warnings, "
            "missing values, duplicate DOI detection, and edge-case rendering."
        ),
        "filename": "data_quality_sandbox_demo.json",
        "records": quality_sandbox_records,
        "tags": ["validation", "quality", "edge cases"],
        "filters": {"include_missing_year": False},
    },
]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        default=os.environ.get("BIBLIOFLOW_WEB_DATA_DIR") or str(default_data_dir()),
        help="biblioflow-web data directory to seed.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing demo-seeded projects before creating fresh ones.",
    )
    return parser.parse_args(argv)


def remove_seeded_projects(projects: ProjectStore) -> int:
    """Delete projects previously created by this seed script."""
    removed = 0
    for project in projects.list_projects():
        metadata = project.get("metadata") or {}
        if metadata.get("seeded_by") == SEED_MARKER:
            projects.delete_project(str(project["project_id"]))
            removed += 1
    return removed


def seed_project(
    spec: dict[str, Any],
    *,
    projects: ProjectStore,
    files: FileStore,
    datasets: DatasetService,
    exports: ExportService,
    screening: ScreeningService,
) -> dict[str, Any]:
    """Create one seeded project and return a summary."""
    project = projects.create_project(str(spec["name"]))
    project_id = str(project["project_id"])
    records = spec["records"]()

    # Exercise the public biblioflow loader before storing records, so the demo
    # seed fails early if the canonical schema changes unexpectedly.
    biblioflow_dataset = bf.load(records, provider="generic", format="records")
    summary = bf.summarize_dataset(biblioflow_dataset).to_dict()

    raw_json = json.dumps(records, indent=2, ensure_ascii=False).encode("utf-8")
    upload = files.save_upload(
        project_id,
        str(spec["filename"]),
        BytesIO(raw_json),
        content_type="application/json",
    )
    dataset_payload = datasets.load_dataset(
        project_id,
        [str(upload["upload_id"])],
        provider="generic",
        format="json",
    )
    screening_run = screening.create_run(
        project_id,
        origin_type="uploads",
        upload_ids=[str(upload["upload_id"])],
        source="generic",
        format="json",
        name=f"{spec['name']} staged import",
    )
    _apply_demo_screening_decisions(project_id, screening, screening_run)

    dataset_id = str(dataset_payload["dataset_id"])
    exports.export_dataset(project_id, dataset_id, format="json")
    exports.export_dataset(project_id, dataset_id, format="csv")

    project = projects.get_project(project_id)
    project["filters"] = dict(spec.get("filters") or {})
    project["metadata"] = {
        **dict(project.get("metadata") or {}),
        "seeded_by": SEED_MARKER,
        "seed_version": SEED_VERSION,
        "description": spec["description"],
        "tags": list(spec.get("tags") or []),
        "record_count": len(records),
        "summary": summary,
        "demo_notes": [
            "Generated by scripts/seed_demo_data.py.",
            "Records are synthetic and intended only for UI testing.",
            "A screening run is pre-created from the uploaded JSON file.",
            "JSON and CSV dataset exports are pre-generated for export testing.",
        ],
    }
    projects.save_project(project)

    return {
        "project_id": project_id,
        "name": project["name"],
        "dataset_id": dataset_payload["dataset_id"],
        "records": len(records),
        "warnings": len(dataset_payload.get("warnings", [])),
        "uploads": 1,
        "screening_runs": 1,
        "exports": 2,
    }


def _apply_demo_screening_decisions(
    project_id: str, screening: ScreeningService, screening_run: dict[str, Any]
) -> None:
    """Mark a few demo candidates so the Screening page has realistic states."""
    candidates = [
        candidate
        for candidate in screening_run.get("candidates", [])
        if isinstance(candidate, dict)
    ]
    candidate_ids = [str(candidate["candidate_id"]) for candidate in candidates]
    if not candidate_ids:
        return

    selected_ids = candidate_ids[: min(3, len(candidate_ids))]
    maybe_ids = candidate_ids[3:4]
    excluded_ids = candidate_ids[-1:] if len(candidate_ids) > 4 else []

    if selected_ids:
        screening.update_candidates(
            project_id,
            str(screening_run["screening_run_id"]),
            candidate_ids=selected_ids,
            status="selected",
            decision_reason="Pre-selected in demo data.",
            labels=["demo"],
        )
    if maybe_ids:
        screening.update_candidates(
            project_id,
            str(screening_run["screening_run_id"]),
            candidate_ids=maybe_ids,
            status="maybe",
            decision_reason="Needs reviewer attention in demo data.",
            labels=["demo", "review"],
        )
    if excluded_ids and not set(excluded_ids).intersection(selected_ids + maybe_ids):
        screening.update_candidates(
            project_id,
            str(screening_run["screening_run_id"]),
            candidate_ids=excluded_ids,
            status="excluded",
            decision_reason="Example exclusion in demo data.",
            labels=["demo", "excluded"],
        )


def main(argv: list[str] | None = None) -> None:
    """Seed demo data into the configured biblioflow-web data store."""
    args = parse_args(argv)
    data_dir = Path(args.data_dir).expanduser().resolve()
    projects = ProjectStore(data_dir)
    files = FileStore(projects)
    datasets = DatasetService(projects, files)
    exports = ExportService(projects, datasets)
    screening = ScreeningService(projects, files, datasets)

    removed = remove_seeded_projects(projects) if args.reset else 0
    summaries = [
        seed_project(
            spec,
            projects=projects,
            files=files,
            datasets=datasets,
            exports=exports,
            screening=screening,
        )
        for spec in PROJECT_SPECS
    ]

    print(f"Seeded biblioflow-web demo data in: {data_dir}")
    if args.reset:
        print(f"Removed existing seeded projects: {removed}")
    for summary in summaries:
        print(
            "- {name} ({project_id}) dataset={dataset_id} "
            "records={records} warnings={warnings} "
            "screening_runs={screening_runs} exports={exports}".format(**summary)
        )


if __name__ == "__main__":
    main()
