"""Evaluación del pipeline RAG contra tests/eval/queries.json (SPEC_RAG.md §8).

Corre contra infraestructura real (OpenAI embeddings + Supabase/pgvector) — no
es parte de la suite de pytest. Ejecutar:

    python scripts/evaluate_rag.py
    python scripts/evaluate_rag.py --k 3

Cuándo correrla (SPEC_RAG.md §8.6): al cerrar el hito 2 antes de presentar al
cliente, tras cualquier cambio en estrategias de chunking o parámetros de
recuperación, y tras cada carga masiva de corpus nuevo.
"""
import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

QUERIES_PATH = pathlib.Path(__file__).parent.parent / "tests" / "eval" / "queries.json"

# SPEC_RAG.md §8.4 — objetivos por métrica
TARGETS = {"recall_at_k": 0.85, "mrr": 0.65, "intent_acc": 0.80, "refusal_acc": 1.00}


def load_queries() -> list[dict]:
    return json.loads(QUERIES_PATH.read_text(encoding="utf-8"))


def evaluate(queries: list[dict], k: int = 5) -> dict:
    from app.integrations.openai_embeddings import embed_texts
    from app.modules.chat import retrieval

    recall_hits: list[int] = []
    reciprocal_ranks: list[float] = []
    intent_correct = intent_total = 0
    refusal_correct = refusal_total = 0
    per_query: list[dict] = []

    for q in queries:
        # Mismo camino que la ruta de chat (router.py): split + embed batcheado + search_multi.
        # Para queries simples split_subqueries devuelve [query] y esto es idéntico al flujo previo.
        subqueries = retrieval.split_subqueries(q["query"])
        predicted_intent = retrieval.classify_intent(q["query"]).name
        chunks, _stale = retrieval.search_multi(subqueries, embed_texts([sq.text for sq in subqueries]))

        entry = {"id": q["id"], "predicted_intent": predicted_intent, "n_subqueries": len(subqueries)}

        if q.get("intent_expected"):
            intent_total += 1
            correct = predicted_intent == q["intent_expected"]
            intent_correct += correct
            entry["intent_correct"] = correct

        category = q.get("category")
        if category == "fuera_de_corpus":
            refusal_total += 1
            correct = len(chunks) == 0
            refusal_correct += correct
            entry["refusal_correct"] = correct
            per_query.append(entry)
            continue

        relevant = q.get("relevant_chunk_contains") or []
        if not relevant:
            per_query.append(entry)
            continue  # ambiguas/generales (§8.3): no se mide recall/mrr

        rank = None
        for i, chunk_text in enumerate(chunks[:k], start=1):
            if any(s in chunk_text for s in relevant):
                rank = i
                break
        recall_hits.append(1 if rank else 0)
        reciprocal_ranks.append(1 / rank if rank else 0)
        entry["rank"] = rank
        per_query.append(entry)

    def _avg(values: list) -> float | None:
        return sum(values) / len(values) if values else None

    return {
        "recall_at_k": _avg(recall_hits),
        "mrr": _avg(reciprocal_ranks),
        "intent_acc": (intent_correct / intent_total) if intent_total else None,
        "refusal_acc": (refusal_correct / refusal_total) if refusal_total else None,
        "n_recall_queries": len(recall_hits),
        "n_intent_queries": intent_total,
        "n_refusal_queries": refusal_total,
        "per_query": per_query,
    }


def _print_report(report: dict, k: int) -> None:
    print(f"Evaluación RAG — k={k}\n")
    for metric, target in TARGETS.items():
        value = report[metric]
        if value is None:
            print(f"  {metric:14s}  sin datos (0 queries aplicables)")
            continue
        status = "OK" if value >= target else "BAJO OBJETIVO"
        print(f"  {metric:14s}  {value:.2f}  (objetivo >= {target:.2f})  {status}")
    print(
        f"\n  n_recall_queries={report['n_recall_queries']}  "
        f"n_intent_queries={report['n_intent_queries']}  "
        f"n_refusal_queries={report['n_refusal_queries']}"
    )

    failures = [e for e in report["per_query"] if e.get("rank") is None and "rank" in e]
    if failures:
        print("\n  Queries sin chunk relevante en el top-k:")
        for e in failures:
            print(f"    - {e['id']}")

    intent_misses = [e for e in report["per_query"] if e.get("intent_correct") is False]
    if intent_misses:
        print("\n  Intención mal clasificada:")
        for e in intent_misses:
            print(f"    - {e['id']}: predicho '{e['predicted_intent']}'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--k", type=int, default=5)
    args = parser.parse_args()

    report = evaluate(load_queries(), k=args.k)
    _print_report(report, args.k)
