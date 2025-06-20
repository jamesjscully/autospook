import os
from typing import List, Optional
from dataclasses import dataclass
from exa_py import Exa
from dotenv import load_dotenv

load_dotenv()

@dataclass
class ExaResult:
    """Holds a single Exa search result"""
    id: str
    title: str
    url: str
    score: Optional[float] = None
    published_date: Optional[str] = None
    text: Optional[str] = None

@dataclass 
class ExaSearchResults:
    """Holds collection of Exa search results"""
    query: str
    results: List[ExaResult]
    num_results: int
    
    def to_dict(self):
        """Convert to dictionary for BAML integration"""
        return {
            "query": self.query,
            "num_results": self.num_results,
            "results": [
                {
                    "id": r.id,
                    "title": r.title, 
                    "url": r.url,
                    "score": r.score,
                    "published_date": r.published_date,
                    "text": r.text
                }
                for r in self.results
            ]
        }

def search_exa(query: str, num_results: int = 10, include_text: bool = True) -> ExaSearchResults:
    """Search using Exa API and return structured results"""
    api_key = os.getenv("EXA_API_KEY")
    if not api_key:
        raise ValueError("EXA_API_KEY environment variable is required")
    
    exa = Exa(api_key)
    
    results = exa.search_and_contents(
        query=query,
        num_results=num_results,
        text=include_text
    )
    
    exa_results = [
        ExaResult(
            id=result.id,
            title=result.title,
            url=result.url,
            score=getattr(result, 'score', None),
            published_date=getattr(result, 'published_date', None),
            text=getattr(result, 'text', None) if include_text else None
        )
        for result in results.results
    ]
    
    return ExaSearchResults(
        query=query,
        results=exa_results,
        num_results=len(exa_results)
    )

# Test the integration
if __name__ == "__main__":
    try:
        results = search_exa("AI safety", num_results=3)
        print(f"Query: {results.query}")
        print(f"Number of results: {results.num_results}")
        
        for i, result in enumerate(results.results, 1):
            print(f"\nResult {i}:")
            print(f"  Title: {result.title}")
            print(f"  URL: {result.url}")
            print(f"  ID: {result.id}")
            if result.score:
                print(f"  Score: {result.score}")
            if result.text:
                print(f"  Content preview: {result.text[:100]}...")
                
        print("\n--- Testing to_dict() method ---")
        data_dict = results.to_dict()
        print(f"Dict keys: {list(data_dict.keys())}")
        print(f"First result title from dict: {data_dict['results'][0]['title']}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()