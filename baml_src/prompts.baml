// ─── DOMAIN TYPES ─────────────────────────────────────────────

class Stepback {
  expanded_context string @description("One-paragraph expansion of the raw context")
}

enum Criticality {
  SECURITY_CRITICAL
  CONTEXTUAL
}

class Question {
  text string
  criticality Criticality
}

enum QuestionLabel {
  OPEN
  CLOSED
  UNANSWERABLE
}

class EvidenceSnippet {
  title string
  url string
  snippet string
  published_date string?
}

class QuestionStatus {
  question Question
  label QuestionLabel
  rationale string
  evidence EvidenceSnippet[]?
}

enum TopicCompletion {
  OPEN
  SATISFIED
  UNSATISFIABLE
}

class TopicStatus {
  topic string
  completion TopicCompletion
  rationale string
}

class HtmlReport {
  html string @description("Complete HTML fragment for the final report")
}


// ─── FUNCTION DEFINITIONS ─────────────────────────────────────

function InitialStepback(
  target_name: string,
  target_context: string
) -> Stepback {
  client CustomSonnet
  prompt #"
    You are an OSINT step-back analyst.  Expand the user-supplied context,
    flagging the security dimensions that most affect risk when engaging
    with the target.
    Focus on topics that can be investigated online through public data.
    Present the conclusions in an unbiased, objective manner that does not
    make assumptions about the conclusions of the investigation.
    Only set the scope, focus, and security dimensions of the investigation.

    Target Name: {{ target_name }}
    Raw Context: {{ target_context }}

    {{ ctx.output_format }}
  "#
}

function GenerateTopics(expanded_context: string) -> string[] {
  client CustomGPT4o
  prompt #"
    You are a senior intelligence analyst with expertise in planning open-source intel gathering operations.
    The context below describes the scope and the most important security dimensions of our investigation.
    {{ expanded_context }}
    
    For DEMO purposes, generate exactly 2-3 focused investigation topics that cover the most essential areas.
    Prioritize the most critical security-relevant topics only.
    
    Example topics might include:
    - Basic identifying information and background
    - Online presence and digital footprint
    - Professional/business associations
    
    Each topic should be a single sentence that describes the area of investigation.
    Keep the scope limited for demonstration purposes.
    
    {{ ctx.output_format }}
  "#
}

function GenerateQuestions(
  topic: string,
  expanded_context: string
) -> Question[] {
  client CustomGPT4o
  prompt #"
    You are an AI who is tasked with generating questions for an OSINT investigation.
    
    For DEMO purposes, generate exactly 1-2 focused questions per topic that can be answered through public data sources.
    Focus on the most essential questions only - quality over quantity.
    Each question will be subsequently broken down into web-search strings, so keep this in mind.

    Topic: {{ topic }}
    Context: {{ expanded_context }}

    Be specific about who the target is because the expanded context will not be used to generate queries from questions.
    For example, if the topic is "Online presence", and the target is "John Doe" you might ask:
    "What social media accounts are associated with John Doe?"

    Generate only the most critical 1-2 questions whose answers would provide the core information for this topic.
    Tag each as SECURITY_CRITICAL or CONTEXTUAL.

    {{ ctx.output_format }}
  "#
}

function GenerateQueries(
  question: Question,
  expanded_context: string,
  topic: string,
  previous_queries: string[]?
) -> string[] {
  client CustomFast
  prompt #"
    Investigation Context: {{ expanded_context }}
    
    Current Topic: {{ topic }}
    
    Question: {{ question.text }}
    Question Criticality: {{ question.criticality }}
    
    {% if previous_queries %}
    Previous queries for this question: {{ previous_queries | join(', ') }}
    {% endif %}

    For DEMO purposes, generate exactly 1-2 focused web-search strings (not 3) that are most likely to surface 
    primary sources to answer this question. Consider:
    
    - The overall investigation context and security focus
    - The specific topic being researched
    - The criticality level of this question
    - Avoid duplicating previous search approaches
    - Target the most authoritative and likely sources
    - Use specific terminology relevant to the context
    
    Quality over quantity - generate only the most effective search queries.

    {{ ctx.output_format }}
  "#
}

function EvaluateQuestion(
  question: Question,
  evidence: EvidenceSnippet[]?,
  expanded_context: string,
  topic: string
) -> QuestionStatus {
  client CustomGPT4oMini
  prompt #"
    Investigation Context: {{ expanded_context }}
    
    Current Topic: {{ topic }}
    
    Question: {{ question.text }}
    Question Criticality: {{ question.criticality }}
    
    Evidence Collected: {{ evidence }}

    Evaluate whether this question can be considered answered based on the evidence collected.
    Consider:
    
    - The overall investigation context and what we're trying to determine
    - The specific topic this question relates to
    - The criticality level - SECURITY_CRITICAL questions need stronger evidence
    - Quality and reliability of the evidence sources
    - Whether the evidence directly addresses the question
    
    Return OPEN, CLOSED, or UNANSWERABLE with a clear rationale explaining your decision.
    
    - OPEN: More evidence needed to adequately answer the question
    - CLOSED: Sufficient evidence exists to answer the question  
    - UNANSWERABLE: Question cannot be answered through available public sources
    
    If CLOSED, include the most relevant evidence snippets that support the answer.

    {{ ctx.output_format }}
  "#
}

function EvaluateTopic(
  topic: string,
  question_statuses: QuestionStatus[]
) -> TopicStatus {
  client CustomGPT4oMini
  prompt #"
    Topic: {{ topic }}
    Status objects: {{ question_statuses }}

    If every SECURITY_CRITICAL question is CLOSED -> SATISFIED.
    If any SECURITY_CRITICAL is OPEN -> OPEN.
    If all SECURITY_CRITICAL are UNANSWERABLE -> UNSATISFIABLE.

    {{ ctx.output_format }}
  "#
}

function WriteReport(
  expanded_context: string,
  evidence_by_topic: map<string, EvidenceSnippet[]>
) -> HtmlReport {
  client CustomSonnet
  prompt #"
    Draft an executive-level OSINT security report in clean HTML format.
    
    Context: {{ expanded_context }}
    Evidence: {{ evidence_by_topic }}

    Requirements:
    • Use <h2> for main sections and <h3> for subsections
    • Use <p> tags for paragraphs
    • Use <ul> and <li> for lists
    • Embed each source as <a href="URL" target="_blank" class="text-blue-400 hover:text-blue-300">Title</a>
    • Use <strong> for emphasis
    • Structure the report with clear sections: Executive Summary, Findings by Topic, Sources, Risk Assessment
    • Finish with a concise risk synopsis section
    • Do not include <html>, <head>, or <body> tags - just the content
    • Ensure all HTML is properly formatted and closed

    {{ ctx.output_format }}
  "#
}

function AssessRisk(report_html: string) -> string {
  client CustomGPT4oMini
  prompt #"
    Analyze this OSINT security report and assess the overall risk level:

    {{ report_html }}

    Based on the findings in the report, determine the security risk level.
    Consider factors such as:
    - Security vulnerabilities or concerns identified
    - Reputation and credibility issues
    - Potential for fraud, deception, or malicious activity
    - Quality and reliability of available information
    - Any red flags or concerning patterns

    Return only one of: "Low", "Medium", or "High"
    
    - Low: Minimal security concerns, generally trustworthy
    - Medium: Some concerns identified, proceed with caution
    - High: Significant security risks or red flags identified

    {{ ctx.output_format }}
  "#
}