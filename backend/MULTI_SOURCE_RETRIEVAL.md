# Multi-Source OSINT Retrieval System

## Overview

The AutoSpook OSINT system implements a comprehensive multi-source intelligence gathering capability that retrieves information from diverse open-source intelligence sources. The system performs 8-12 distinct retrievals per investigation across different source types with automatic credibility scoring and source validation.

## System Architecture

### Core Components

- **OSINTRetrievalManager**: Main orchestrator for multi-source data collection
- **Source Type Classification**: Categorizes sources by type and credibility
- **Rate Limiting**: Manages API quotas and prevents service abuse
- **Credibility Scoring**: Automatic assessment of source reliability
- **Demo Mode**: Functional demonstration without API keys

### Source Types Supported

1. **Web Search** (Google Custom Search, Bing)
   - News articles and press releases
   - Public websites and documentation
   - General web content

2. **Social Media** (LinkedIn, Twitter/X, Facebook)
   - Professional profiles and networks
   - Public social media posts
   - Social media mentions

3. **Academic Sources** (Google Scholar, ResearchGate, Academia.edu)
   - Research publications and papers
   - Academic profiles and citations
   - University websites and faculty pages

4. **News Sources** (Reuters, BBC, AP)
   - Recent news coverage
   - Press releases and announcements
   - Media mentions and interviews

5. **Business Records** (SEC filings, Crunchbase, Bloomberg)
   - Corporate registrations
   - Business intelligence databases
   - Financial records and filings

6. **Public Records** (Government databases, WhitePages)
   - Government databases
   - Public registries
   - Official records and documents

## Technical Implementation

### Real API Integration

When API keys are configured, the system performs actual web searches:

```python
# Google Custom Search
params = {
    "key": self.google_api_key,
    "cx": self.google_cse_id,
    "q": search_query,
    "num": max_results
}

# Bing Search API
headers = {"Ocp-Apim-Subscription-Key": self.bing_api_key}
params = {"q": search_query, "count": max_results}
```

### Demo Mode

Without API keys, the system uses realistic demo sources:

- Academic profiles with publication counts
- Professional LinkedIn-style profiles
- University faculty pages
- Conference speaker listings
- Research publications and citations

### Credibility Scoring Algorithm

Sources are automatically scored based on multiple factors:

- **Domain Authority**: `.gov` (0.3 boost), `.edu` (0.3 boost), news sites (0.25 boost)
- **Content Quality**: Title length, content depth, HTTPS usage
- **Source Type**: Academic sources get higher scores than blogs
- **Deductions**: Social media and forums receive lower scores

```python
def _calculate_credibility_score(self, source_data: Dict) -> float:
    score = 0.5  # Base score
    
    # High credibility domains
    if any(tld in domain for tld in [".gov", ".edu", ".org"]):
        score += 0.3
    elif any(news in domain for news in ["reuters", "bbc", "ap.org"]):
        score += 0.25
        
    # Content quality indicators
    if len(source_data.get("content", "")) > 200:
        score += 0.05
        
    return max(0.1, min(1.0, score))
```

### Rate Limiting

The system includes comprehensive rate limiting:

- **Google API**: 100 calls per day
- **Bing API**: 1000 calls per day  
- **Academic Sources**: 50 calls per hour
- **Automatic Reset**: Daily/hourly quota refreshes

### Parallel Processing

All source retrievals are executed in parallel for maximum efficiency:

```python
tasks = [
    self._google_web_search(query, entity_name, 3),
    self._bing_web_search(query, entity_name, 2),
    self._linkedin_search(entity_name, 2),
    self._academic_search(query, entity_name, 2),
    # ... more sources
]

results = await asyncio.gather(*tasks, return_exceptions=True)
```

## Configuration Requirements

### Required API Keys

For full functionality, configure these environment variables:

```bash
# Google Custom Search (Required)
GOOGLE_SEARCH_API_KEY=your_google_api_key
GOOGLE_CSE_ID=your_custom_search_engine_id

# Optional Additional Sources
BING_API_KEY=your_bing_api_key
SERPAPI_KEY=your_serpapi_key
```

### Setup Instructions

1. **Google Custom Search API**:
   - Create project at [Google Cloud Console](https://console.cloud.google.com)
   - Enable Custom Search API
   - Create Custom Search Engine at [CSE Control Panel](https://cse.google.com)
   - Get API key and CSE ID

2. **Environment Configuration**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Testing Setup**:
   ```bash
   python test_osint_retrieval.py
   ```

## Performance Metrics

### Target Performance

- **Sources per Investigation**: 8-12 distinct sources
- **Source Diversity**: Minimum 3 different source types
- **Average Credibility**: Target ≥ 0.7 overall score
- **Retrieval Time**: < 30 seconds for 10 sources
- **Success Rate**: > 90% successful retrievals

### Current Demo Mode Results

```
📊 Source Analysis:
   Total sources: 8
   Average credibility: 0.84
   Source type breakdown: {
     'academic': 3, 
     'web': 2, 
     'news': 1, 
     'social_media': 1, 
     'business': 1
   }
✅ Good source diversity achieved
✅ Good average credibility score
```

## Integration with OSINT Graph

The retrieval system integrates seamlessly with the LangGraph workflow:

1. **Query Analysis**: Identifies target entities for retrieval
2. **Planning**: Determines search strategies across sources
3. **Retrieval**: Executes multi-source data collection
4. **Pivot Analysis**: Discovers new entities in retrieved content
5. **Synthesis**: Aggregates findings into comprehensive reports

### Memory Integration

All retrieved sources are automatically:

- Stored in persistent memory with source attribution
- Linked to discovered entities with confidence scores
- Cross-referenced for validation and fact-checking
- Tracked for credibility and reliability scoring

## Error Handling

### Graceful Degradation

- **API Failures**: Individual source failures don't stop investigation
- **Rate Limits**: Automatic fallback to available sources
- **Network Issues**: Retry logic with exponential backoff
- **No API Keys**: Demo mode ensures functionality

### Monitoring and Logging

```python
logger.info(f"Retrieved {len(osint_sources)} sources from OSINT tools")
logger.warning(f"Retrieval task failed: {result}")
logger.error(f"OSINT retrieval failed: {e}")
```

## Testing and Validation

### Automated Tests

- **Rate Limiting**: Verify quota management
- **Credibility Scoring**: Test scoring algorithm
- **Source Types**: Validate individual source retrievals
- **Full Integration**: End-to-end retrieval testing

### Manual Testing

```bash
# Run comprehensive tests
python test_osint_retrieval.py

# Test with specific entity
python -c "
import asyncio
from src.agent.osint_tools import osint_retrieval_manager

async def test():
    sources = await osint_retrieval_manager.retrieve_from_multiple_sources(
        'academic researcher', 
        'Ali Khaledi Nasab', 
        8
    )
    print(f'Retrieved {len(sources)} sources')

asyncio.run(test())
"
```

## Future Enhancements

### Planned Improvements

1. **Additional Sources**:
   - Academic databases (PubMed, ArXiv)
   - Government databases (SEC, USPTO)
   - Social platforms (Reddit, Stack Overflow)

2. **Advanced Features**:
   - Content similarity detection
   - Automated fact-checking
   - Temporal analysis and timeline construction
   - Network analysis and relationship mapping

3. **Performance Optimizations**:
   - Intelligent caching
   - Adaptive rate limiting
   - Source prioritization based on query type

### Integration Opportunities

- **NLP Enhancement**: Better entity extraction from sources
- **Credibility ML**: Machine learning-based credibility assessment
- **Real-time Updates**: Live monitoring of source changes
- **Cross-validation**: Automated source verification

## Compliance and Ethics

### Best Practices

- **Rate Limiting**: Respects API quotas and service terms
- **User Agents**: Proper identification in web requests
- **Data Usage**: Complies with source terms of service
- **Privacy**: No storage of personally identifiable information

### Legal Considerations

- All retrieved data is from publicly available sources
- Complies with robots.txt and API terms of service
- Implements appropriate delays and rate limiting
- Respects intellectual property and copyright

---

**Next Steps**: Configure API keys and run the "Ali Khaledi Nasab" investigation to see the full multi-source retrieval system in action. 