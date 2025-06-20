// BAML structure for Exa Search API integration

class ExaResult {
    id string
    title string
    url string
    score float?
    published_date string?
    text string?
}

class ExaSearchResults {
    query string
    num_results int
    results ExaResult[]
}

// Function to summarize Exa search results
function SummarizeExa(question: string, search_results: ExaSearchResults) -> string {
    client CustomGPT4oMini
    prompt #"
        You are a helpful research assistant. Based on the Exa search results provided, answer the following question with a clear, concise, and informative response.

        Question: {{ question }}

        Search Results from Exa:
        Query: {{ search_results.query }}
        Total Results: {{ search_results.num_results }}

        {% for result in search_results.results %}
        Result {{ loop.index }}:
        - Title: {{ result.title }}
        - URL: {{ result.url }}
        {% if result.score %}- Relevance Score: {{ result.score }}{% endif %}
        {% if result.published_date %}- Published: {{ result.published_date }}{% endif %}
        {% if result.text %}- Content: {{ result.text }}{% endif %}

        {% endfor %}

        Please provide a comprehensive answer to the question based on the search results above. Focus on accuracy and relevance. If the search results don't contain enough information to fully answer the question, mention what information is available and what might be missing.
    "#
}