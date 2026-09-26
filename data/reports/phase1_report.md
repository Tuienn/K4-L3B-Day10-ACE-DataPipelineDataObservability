# Phase 1: Baseline Pipeline

## Source and indexing

- source_api: Crossref REST API
- source_query: agentic retrieval augmented generation large language model
- source_filter: from-pub-date:2026-03-30,has-abstract:true
- run_date: 2026-09-26T04:22:35.248314+00:00
- raw_records: 24
- clean_records: 24
- indexed_documents: 24
- test_questions: 10
- collection_name: papers-baseline
- embedding_model: sentence-transformers/all-MiniLM-L6-v2

## Baseline RAG evaluation

| Metric | Value |
| --- | ---: |
| Samples | 10 |
| Retrieval Hit Rate | 100.00% |
| Mean Token F1 | 1.0000 |
| Judge accuracy | 100.00% |
| Mean judge score | 5.0000 |

Ragas: {'skipped': 'Set RUN_RAGAS=1 to enable the slower Ragas pass.'}

## Great Expectations Quality Gate

- Overall gate: PASS
- Great Expectations: PASS
- Evaluated expectations: 6
- Successful expectations: 6
- Failed expectations: 0

## Freshness SLA

- Status: PASS
- Age threshold: 180 days
- Stale papers: 1 / 24
- Stale ratio: 4.17%
- Maximum stale ratio: 25.00%
- Latest publication: 2026-07-22
- Oldest publication: 2026-03-28
