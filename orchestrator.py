"""
Light-weight bridge between the BAML pipeline and the Flask view.

It calls the existing `investigate()` control loop (which already
produces the full HTML report) and then asks a tiny BAML helper
`DistilReport` to distill that HTML into the fields required
by the front-end.
"""
from dataclasses import dataclass
from typing import List, Dict
from baml_client import b
from baml_client.types import (
    EvidenceSnippet, Question, QuestionStatus, HtmlReport
)
from exa_integration import search_exa  
from rate_limiter import rate_limiter

         # your Exa helper

MAX_DEPTH = 3
MAX_SNIPPETS = 5

def investigate(target_name: str, target_context: str) -> str:
    rate_limiter.wait_if_needed('anthropic')  # CustomSonnet
    stepback = b.InitialStepback(
        target_name=target_name,
        target_context=target_context,
    )

    rate_limiter.wait_if_needed('openai')  # CustomGPT4o
    topics = b.GenerateTopics(expanded_context=stepback.expanded_context)
    evidence: Dict[str, Dict[str, List[EvidenceSnippet]]] = {}
    question_queries: Dict[str, Dict[str, List[str]]] = {}  # Track queries per question

    for topic in topics:
        rate_limiter.wait_if_needed('openai')  # CustomGPT4o
        questions = b.GenerateQuestions(
            topic=topic, expanded_context=stepback.expanded_context
        )
        evidence[topic] = {q.text: [] for q in questions}
        question_queries[topic] = {q.text: [] for q in questions}

        depth = 0
        while depth < MAX_DEPTH:
            open_qs: List[Question] = []

            for q in questions:
                rate_limiter.wait_if_needed('openai')  # CustomGPT4oMini
                status = b.EvaluateQuestion(
                    question=q,
                    evidence=evidence[topic][q.text][:MAX_SNIPPETS],
                    expanded_context=stepback.expanded_context,
                    topic=topic,
                )
                if status.label == "OPEN":
                    open_qs.append(q)

            if not open_qs:
                break  # topic converged

            for q in open_qs:
                rate_limiter.wait_if_needed('openai')  # CustomFast (GPT-4o-mini/Haiku)
                queries = b.GenerateQueries(
                    question=q,
                    expanded_context=stepback.expanded_context,
                    topic=topic,
                    previous_queries=question_queries[topic][q.text] if question_queries[topic][q.text] else None
                )
                for query in queries:
                    question_queries[topic][q.text].append(query)  # Track this query
                    rate_limiter.wait_if_needed('exa')  # Exa API
                    res = search_exa(query, num_results=3, include_text=True)
                    for r in res.results:
                        evidence[topic][q.text].append(
                            EvidenceSnippet(
                                title=r.title,
                                url=r.url,
                                snippet=(r.text or "")[:280],
                                published_date=r.published_date,
                            )
                        )
            depth += 1

        # optional: call b.EvaluateTopic(...) here to log completion

    # Flatten evidence structure from {topic: {question: [evidence]}} to {topic: [evidence]}
    flattened_evidence = {}
    for topic, questions_dict in evidence.items():
        flattened_evidence[topic] = []
        for evidence_list in questions_dict.values():
            flattened_evidence[topic].extend(evidence_list)
    
    rate_limiter.wait_if_needed('anthropic')  # CustomSonnet
    html_report: HtmlReport = b.WriteReport(
        expanded_context=stepback.expanded_context,
        evidence_by_topic=flattened_evidence,
    )
    return html_report.html

# ─── Shape required by the template ───────────────────────────

@dataclass
class Analysis:
    target_name: str
    risk_level: str
    html_report: str


# ─── Adapt investigation output to template needs ─────────────

def generate_report(target_name: str, target_context: str) -> Analysis:
    """
    1. Run the heavy investigative pipeline → HTML.
    2. Assess overall risk level from the HTML report.
    """
    html_report: str = investigate(target_name, target_context)

    rate_limiter.wait_if_needed('openai')  # CustomGPT4oMini
    risk_level = b.AssessRisk(report_html=html_report)   # returns "Low" | "Medium" | "High"

    return Analysis(
        target_name=target_name,
        risk_level=risk_level,
        html_report=html_report,
    )