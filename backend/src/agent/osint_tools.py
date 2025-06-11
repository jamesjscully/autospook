"""
OSINT Tools for Multi-Source Intelligence Gathering
Implements real data retrieval across diverse intelligence sources
"""

import os
import asyncio
import aiohttp
import json
import time
import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlencode, quote_plus
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

import httpx
from bs4 import BeautifulSoup
import requests

logger = logging.getLogger(__name__)

class SourceType(Enum):
    WEB = "web"
    SOCIAL_MEDIA = "social_media"
    ACADEMIC = "academic"
    NEWS = "news"
    PUBLIC_RECORDS = "public_records"
    BUSINESS = "business"
    GOVERNMENT = "government"

@dataclass
class OSINTSource:
    """Standardized OSINT source information"""
    url: str
    title: str
    content: str
    source_type: SourceType
    credibility_score: float
    metadata: Dict[str, Any]
    retrieved_at: datetime
    entities_mentioned: List[str] = None

class OSINTRetrievalManager:
    """Manages multi-source OSINT retrieval operations"""
    
    def __init__(self):
        self.google_api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        self.google_cse_id = os.getenv("GOOGLE_CSE_ID")
        self.bing_api_key = os.getenv("BING_API_KEY")
        self.serpapi_key = os.getenv("SERPAPI_KEY")
        
        self.session = None
        self.rate_limits = {
            "google": {"calls": 0, "reset_time": time.time() + 86400, "limit": 100},
            "bing": {"calls": 0, "reset_time": time.time() + 86400, "limit": 1000},
            "academic": {"calls": 0, "reset_time": time.time() + 3600, "limit": 50}
        }
        
    async def initialize(self):
        """Initialize HTTP session"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    "User-Agent": "AutoSpook-OSINT/1.0 (OSINT Research Tool)"
                }
            )
    
    async def cleanup(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    def _check_rate_limit(self, service: str) -> bool:
        """Check if service is within rate limits"""
        current_time = time.time()
        limits = self.rate_limits.get(service, {})
        
        if current_time > limits.get("reset_time", 0):
            limits["calls"] = 0
            limits["reset_time"] = current_time + (86400 if service != "academic" else 3600)
        
        return limits["calls"] < limits.get("limit", 100)
    
    def _increment_rate_limit(self, service: str):
        """Increment rate limit counter"""
        if service in self.rate_limits:
            self.rate_limits[service]["calls"] += 1
    
    def _calculate_credibility_score(self, source_data: Dict) -> float:
        """Calculate credibility score based on source characteristics"""
        score = 0.5  # Base score
        
        # Domain-based scoring
        domain = source_data.get("url", "").lower()
        
        # High credibility domains
        if any(tld in domain for tld in [".gov", ".edu", ".org"]):
            score += 0.3
        elif any(news in domain for news in ["reuters", "bbc", "ap.org", "npr"]):
            score += 0.25
        elif any(prof in domain for prof in ["linkedin", "researchgate", "scholar.google"]):
            score += 0.2
        
        # Medium credibility
        elif any(med in domain for med in [".com", "wikipedia", "academic"]):
            score += 0.1
        
        # Deductions
        if any(low in domain for low in ["blog", "forum", "social", "reddit"]):
            score -= 0.1
        
        # Content quality indicators
        if source_data.get("title") and len(source_data["title"]) > 10:
            score += 0.05
        
        if source_data.get("content") and len(source_data["content"]) > 200:
            score += 0.05
        
        # HTTPS bonus
        if source_data.get("url", "").startswith("https://"):
            score += 0.02
        
        return max(0.1, min(1.0, score))
    
    async def retrieve_from_multiple_sources(self, query: str, entity_name: str, max_sources: int = 12) -> List[OSINTSource]:
        """Retrieve information from multiple OSINT sources"""
        await self.initialize()
        
        all_sources = []
        tasks = []
        
        # Check if we have API keys for real retrieval
        has_api_keys = bool(
            self.google_api_key and 
            self.google_cse_id and 
            self.google_api_key != 'your_api_key_here' and 
            self.google_cse_id != 'your_cse_id_here' and
            not self.google_api_key.startswith('mock_') and
            not self.google_cse_id.startswith('mock_')
        )
        
        if has_api_keys:
            # Real API-based retrieval
            logger.info("Using real API-based OSINT retrieval")
            
            # Web search sources (4-6 sources)
            if self.google_api_key and self.google_cse_id:
                tasks.append(self._google_web_search(query, entity_name, max_results=3))
            
            if self.bing_api_key:
                tasks.append(self._bing_web_search(query, entity_name, max_results=2))
            
            # News search (2-3 sources)
            tasks.append(self._google_news_search(query, entity_name, max_results=2))
            
            # Social media search (2-3 sources)
            tasks.append(self._linkedin_search(entity_name, max_results=2))
            tasks.append(self._general_social_search(query, entity_name, max_results=1))
            
            # Academic sources (1-2 sources)
            tasks.append(self._academic_search(query, entity_name, max_results=2))
            
            # Public records/business (1-2 sources)
            tasks.append(self._business_search(entity_name, max_results=1))
            tasks.append(self._public_records_search(entity_name, max_results=1))
            
            # Execute all searches in parallel
            try:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, Exception):
                        logger.warning(f"Retrieval task failed: {result}")
                        continue
                    
                    if isinstance(result, list):
                        all_sources.extend(result)
                
            except Exception as e:
                logger.error(f"Error in parallel retrieval: {e}")
        else:
            # Demo/fallback sources for testing without API keys
            logger.info("Using demo OSINT sources (no API keys configured)")
            all_sources = await self._create_demo_sources(query, entity_name, max_sources)
        
        # Sort by credibility and return top sources
        all_sources.sort(key=lambda x: x.credibility_score, reverse=True)
        return all_sources[:max_sources]
    
    async def _create_demo_sources(self, query: str, entity_name: str, max_sources: int) -> List[OSINTSource]:
        """Create demo sources for testing without API keys"""
        demo_sources = []
        
        # Academic source
        demo_sources.append(OSINTSource(
            url=f"https://scholar.google.com/citations?user={entity_name.replace(' ', '')}",
            title=f"{entity_name} - Academic Publications and Research",
            content=f"Research profile for {entity_name}. Academic publications include studies in computer science, artificial intelligence, and machine learning. Published papers on topics related to {query}. Research affiliations with multiple universities and research institutions. Notable contributions to academic conferences and peer-reviewed journals.",
            source_type=SourceType.ACADEMIC,
            credibility_score=0.9,
            metadata={
                "platform": "google_scholar",
                "search_query": query,
                "demo": True,
                "h_index": "12",
                "citations": "234"
            },
            retrieved_at=datetime.utcnow(),
            entities_mentioned=[entity_name]
        ))
        
        # LinkedIn professional profile
        demo_sources.append(OSINTSource(
            url=f"https://linkedin.com/in/{entity_name.lower().replace(' ', '-')}",
            title=f"{entity_name} - Senior Researcher | PhD",
            content=f"Professional profile for {entity_name}. Current position: Senior Research Scientist at Technology Research Institute. Previous experience includes postdoctoral research, academic positions, and industry collaborations. Expertise in areas related to {query}. Educational background: PhD from prestigious university. Professional network includes leading researchers and industry professionals.",
            source_type=SourceType.SOCIAL_MEDIA,
            credibility_score=0.8,
            metadata={
                "platform": "linkedin",
                "search_query": query,
                "demo": True,
                "connections": "500+",
                "industry": "Research"
            },
            retrieved_at=datetime.utcnow(),
            entities_mentioned=[entity_name]
        ))
        
        # News article
        demo_sources.append(OSINTSource(
            url=f"https://techreview.edu/articles/{entity_name.replace(' ', '-').lower()}-research-breakthrough",
            title=f"Breakthrough Research by {entity_name} in Advanced Computing",
            content=f"Recent news coverage of {entity_name}'s groundbreaking research work. The study, published in a leading scientific journal, addresses key challenges in {query}. The research has potential applications in industry and academia. Colleagues praise the innovative approach and methodological rigor. The work has been cited by other researchers and featured in academic conferences.",
            source_type=SourceType.NEWS,
            credibility_score=0.85,
            metadata={
                "platform": "academic_news",
                "search_query": query,
                "demo": True,
                "published_date": "2024-03-15",
                "source_type": "university_press"
            },
            retrieved_at=datetime.utcnow(),
            entities_mentioned=[entity_name]
        ))
        
        # Research gate profile
        demo_sources.append(OSINTSource(
            url=f"https://researchgate.net/profile/{entity_name.replace(' ', '_')}",
            title=f"{entity_name} - ResearchGate Scientific Profile",
            content=f"Comprehensive research profile for {entity_name} on ResearchGate. Publication list includes peer-reviewed articles, conference papers, and book chapters. Research interests align with {query} and related fields. Collaboration network includes international researchers. Active participation in scientific community with regular publications and conference presentations.",
            source_type=SourceType.ACADEMIC,
            credibility_score=0.88,
            metadata={
                "platform": "researchgate",
                "search_query": query,
                "demo": True,
                "publications": "23",
                "reads": "1,234"
            },
            retrieved_at=datetime.utcnow(),
            entities_mentioned=[entity_name]
        ))
        
        # University webpage
        demo_sources.append(OSINTSource(
            url=f"https://university.edu/faculty/{entity_name.replace(' ', '-').lower()}",
            title=f"Faculty Profile: {entity_name} - University Department",
            content=f"Official university faculty page for {entity_name}. Academic position: Associate Professor in Computer Science Department. Research focus areas include {query} and computational methods. Teaching responsibilities include graduate and undergraduate courses. Grant funding from national research agencies. Supervision of PhD students and postdoctoral researchers.",
            source_type=SourceType.WEB,
            credibility_score=0.92,
            metadata={
                "platform": "university_website",
                "search_query": query,
                "demo": True,
                "department": "Computer Science",
                "position": "Associate Professor"
            },
            retrieved_at=datetime.utcnow(),
            entities_mentioned=[entity_name]
        ))
        
        # Conference presentation
        demo_sources.append(OSINTSource(
            url=f"https://conference2024.org/speakers/{entity_name.replace(' ', '-').lower()}",
            title=f"Keynote Speaker: {entity_name} at International Conference",
            content=f"Conference speaker profile for {entity_name}. Scheduled keynote presentation on topics related to {query}. Conference biography highlights significant contributions to the field. Speaking engagement demonstrates recognition by academic community. Presentation abstract indicates novel research findings and future directions.",
            source_type=SourceType.ACADEMIC,
            credibility_score=0.83,
            metadata={
                "platform": "conference_website",
                "search_query": query,
                "demo": True,
                "event": "International Conference 2024",
                "presentation_type": "keynote"
            },
            retrieved_at=datetime.utcnow(),
            entities_mentioned=[entity_name]
        ))
        
        # Business/professional registry
        demo_sources.append(OSINTSource(
            url=f"https://professionalregistry.org/member/{entity_name.replace(' ', '-').lower()}",
            title=f"{entity_name} - Professional Registry Profile",
            content=f"Professional registry entry for {entity_name}. Certified professional in research and development. Member of professional associations related to {query}. Credentials verified by professional bodies. Active participation in professional development and continuing education.",
            source_type=SourceType.BUSINESS,
            credibility_score=0.75,
            metadata={
                "platform": "professional_registry",
                "search_query": query,
                "demo": True,
                "certifications": "3",
                "membership_status": "active"
            },
            retrieved_at=datetime.utcnow(),
            entities_mentioned=[entity_name]
        ))
        
        # Industry publication
        demo_sources.append(OSINTSource(
            url=f"https://industryjournal.com/experts/{entity_name.replace(' ', '-').lower()}",
            title=f"Industry Expert Profile: {entity_name}",
            content=f"Industry journal profile highlighting {entity_name}'s expertise in {query}. Regular contributor to industry publications and technical magazines. Consultant for technology companies and research organizations. Expert commentary on industry trends and technological developments. Recognition as thought leader in the field.",
            source_type=SourceType.WEB,
            credibility_score=0.78,
            metadata={
                "platform": "industry_publication",
                "search_query": query,
                "demo": True,
                "articles_published": "15",
                "expert_status": "verified"
            },
            retrieved_at=datetime.utcnow(),
            entities_mentioned=[entity_name]
        ))
        
        return demo_sources[:max_sources]
    
    async def _google_web_search(self, query: str, entity_name: str, max_results: int = 3) -> List[OSINTSource]:
        """Search using Google Custom Search API"""
        if not self._check_rate_limit("google"):
            logger.warning("Google API rate limit exceeded")
            return []
        
        try:
            # Construct search query
            search_query = f'"{entity_name}" {query}'
            
            params = {
                "key": self.google_api_key,
                "cx": self.google_cse_id,
                "q": search_query,
                "num": max_results,
                "safe": "medium"
            }
            
            url = f"https://www.googleapis.com/customsearch/v1?{urlencode(params)}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    sources = []
                    
                    for item in data.get("items", []):
                        # Get page content
                        content = await self._fetch_page_content(item["link"])
                        
                        source = OSINTSource(
                            url=item["link"],
                            title=item.get("title", ""),
                            content=content,
                            source_type=SourceType.WEB,
                            credibility_score=self._calculate_credibility_score(item),
                            metadata={
                                "snippet": item.get("snippet", ""),
                                "search_engine": "google",
                                "search_query": search_query
                            },
                            retrieved_at=datetime.utcnow(),
                            entities_mentioned=[entity_name]
                        )
                        sources.append(source)
                    
                    self._increment_rate_limit("google")
                    return sources
                else:
                    logger.error(f"Google Search API error: {response.status}")
                    
        except Exception as e:
            logger.error(f"Google web search failed: {e}")
        
        return []
    
    async def _bing_web_search(self, query: str, entity_name: str, max_results: int = 2) -> List[OSINTSource]:
        """Search using Bing Search API"""
        if not self.bing_api_key or not self._check_rate_limit("bing"):
            return []
        
        try:
            search_query = f'"{entity_name}" {query}'
            
            headers = {"Ocp-Apim-Subscription-Key": self.bing_api_key}
            params = {
                "q": search_query,
                "count": max_results,
                "safeSearch": "Moderate"
            }
            
            url = f"https://api.bing.microsoft.com/v7.0/search?{urlencode(params)}"
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    sources = []
                    
                    for item in data.get("webPages", {}).get("value", []):
                        content = await self._fetch_page_content(item["url"])
                        
                        source = OSINTSource(
                            url=item["url"],
                            title=item.get("name", ""),
                            content=content,
                            source_type=SourceType.WEB,
                            credibility_score=self._calculate_credibility_score(item),
                            metadata={
                                "snippet": item.get("snippet", ""),
                                "search_engine": "bing",
                                "search_query": search_query
                            },
                            retrieved_at=datetime.utcnow(),
                            entities_mentioned=[entity_name]
                        )
                        sources.append(source)
                    
                    self._increment_rate_limit("bing")
                    return sources
                    
        except Exception as e:
            logger.error(f"Bing web search failed: {e}")
        
        return []
    
    async def _google_news_search(self, query: str, entity_name: str, max_results: int = 2) -> List[OSINTSource]:
        """Search for news articles about the entity"""
        if not self.google_api_key:
            return []
        
        try:
            search_query = f'"{entity_name}" {query}'
            
            params = {
                "key": self.google_api_key,
                "cx": self.google_cse_id,
                "q": search_query,
                "num": max_results,
                "searchType": "news",
                "sort": "date"
            }
            
            url = f"https://www.googleapis.com/customsearch/v1?{urlencode(params)}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    sources = []
                    
                    for item in data.get("items", []):
                        content = await self._fetch_page_content(item["link"])
                        
                        source = OSINTSource(
                            url=item["link"],
                            title=item.get("title", ""),
                            content=content,
                            source_type=SourceType.NEWS,
                            credibility_score=self._calculate_credibility_score(item) + 0.1,  # News gets slight boost
                            metadata={
                                "snippet": item.get("snippet", ""),
                                "search_engine": "google_news",
                                "search_query": search_query,
                                "published_date": item.get("publishedAt")
                            },
                            retrieved_at=datetime.utcnow(),
                            entities_mentioned=[entity_name]
                        )
                        sources.append(source)
                    
                    return sources
                    
        except Exception as e:
            logger.error(f"Google news search failed: {e}")
        
        return []
    
    async def _linkedin_search(self, entity_name: str, max_results: int = 2) -> List[OSINTSource]:
        """Search for LinkedIn profiles and professional information"""
        try:
            # Use Google to search LinkedIn specifically
            search_query = f'site:linkedin.com/in "{entity_name}" OR site:linkedin.com/pub "{entity_name}"'
            
            if self.google_api_key and self.google_cse_id:
                params = {
                    "key": self.google_api_key,
                    "cx": self.google_cse_id,
                    "q": search_query,
                    "num": max_results
                }
                
                url = f"https://www.googleapis.com/customsearch/v1?{urlencode(params)}"
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        sources = []
                        
                        for item in data.get("items", []):
                            # Extract professional info from LinkedIn results
                            content = item.get("snippet", "")
                            
                            source = OSINTSource(
                                url=item["link"],
                                title=item.get("title", ""),
                                content=content,
                                source_type=SourceType.SOCIAL_MEDIA,
                                credibility_score=0.8,  # LinkedIn generally reliable for professional info
                                metadata={
                                    "platform": "linkedin",
                                    "snippet": content,
                                    "search_query": search_query,
                                    "profile_type": "professional"
                                },
                                retrieved_at=datetime.utcnow(),
                                entities_mentioned=[entity_name]
                            )
                            sources.append(source)
                        
                        return sources
                        
        except Exception as e:
            logger.error(f"LinkedIn search failed: {e}")
        
        return []
    
    async def _general_social_search(self, query: str, entity_name: str, max_results: int = 1) -> List[OSINTSource]:
        """Search for general social media mentions"""
        try:
            # Search multiple social platforms
            platforms = ["twitter.com", "facebook.com", "instagram.com", "youtube.com"]
            search_query = f'("{entity_name}" {query}) AND (site:' + " OR site:".join(platforms) + ")"
            
            if self.google_api_key and self.google_cse_id:
                params = {
                    "key": self.google_api_key,
                    "cx": self.google_cse_id,
                    "q": search_query,
                    "num": max_results
                }
                
                url = f"https://www.googleapis.com/customsearch/v1?{urlencode(params)}"
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        sources = []
                        
                        for item in data.get("items", []):
                            platform = next((p for p in platforms if p in item["link"]), "social")
                            
                            source = OSINTSource(
                                url=item["link"],
                                title=item.get("title", ""),
                                content=item.get("snippet", ""),
                                source_type=SourceType.SOCIAL_MEDIA,
                                credibility_score=0.4,  # Social media generally lower credibility
                                metadata={
                                    "platform": platform,
                                    "snippet": item.get("snippet", ""),
                                    "search_query": search_query
                                },
                                retrieved_at=datetime.utcnow(),
                                entities_mentioned=[entity_name]
                            )
                            sources.append(source)
                        
                        return sources
                        
        except Exception as e:
            logger.error(f"Social media search failed: {e}")
        
        return []
    
    async def _academic_search(self, query: str, entity_name: str, max_results: int = 2) -> List[OSINTSource]:
        """Search academic sources and publications"""
        if not self._check_rate_limit("academic"):
            return []
        
        try:
            # Search academic sources
            academic_sites = ["scholar.google.com", "researchgate.net", "academia.edu", "arxiv.org", "pubmed.ncbi.nlm.nih.gov"]
            search_query = f'"{entity_name}" author OR researcher AND (site:' + " OR site:".join(academic_sites) + ")"
            
            if self.google_api_key and self.google_cse_id:
                params = {
                    "key": self.google_api_key,
                    "cx": self.google_cse_id,
                    "q": search_query,
                    "num": max_results
                }
                
                url = f"https://www.googleapis.com/customsearch/v1?{urlencode(params)}"
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        sources = []
                        
                        for item in data.get("items", []):
                            content = await self._fetch_page_content(item["link"])
                            
                            source = OSINTSource(
                                url=item["link"],
                                title=item.get("title", ""),
                                content=content,
                                source_type=SourceType.ACADEMIC,
                                credibility_score=0.9,  # Academic sources high credibility
                                metadata={
                                    "snippet": item.get("snippet", ""),
                                    "search_query": search_query,
                                    "academic_type": "publication"
                                },
                                retrieved_at=datetime.utcnow(),
                                entities_mentioned=[entity_name]
                            )
                            sources.append(source)
                        
                        self._increment_rate_limit("academic")
                        return sources
                        
        except Exception as e:
            logger.error(f"Academic search failed: {e}")
        
        return []
    
    async def _business_search(self, entity_name: str, max_results: int = 1) -> List[OSINTSource]:
        """Search for business registrations and corporate information"""
        try:
            # Search business-related sources
            business_sites = ["sec.gov", "crunchbase.com", "bloomberg.com", "reuters.com"]
            search_query = f'"{entity_name}" company OR business OR corporation AND (site:' + " OR site:".join(business_sites) + ")"
            
            if self.google_api_key and self.google_cse_id:
                params = {
                    "key": self.google_api_key,
                    "cx": self.google_cse_id,
                    "q": search_query,
                    "num": max_results
                }
                
                url = f"https://www.googleapis.com/customsearch/v1?{urlencode(params)}"
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        sources = []
                        
                        for item in data.get("items", []):
                            content = await self._fetch_page_content(item["link"])
                            
                            source = OSINTSource(
                                url=item["link"],
                                title=item.get("title", ""),
                                content=content,
                                source_type=SourceType.BUSINESS,
                                credibility_score=0.8,  # Business sources generally reliable
                                metadata={
                                    "snippet": item.get("snippet", ""),
                                    "search_query": search_query,
                                    "record_type": "business"
                                },
                                retrieved_at=datetime.utcnow(),
                                entities_mentioned=[entity_name]
                            )
                            sources.append(source)
                        
                        return sources
                        
        except Exception as e:
            logger.error(f"Business search failed: {e}")
        
        return []
    
    async def _public_records_search(self, entity_name: str, max_results: int = 1) -> List[OSINTSource]:
        """Search public records and government databases"""
        try:
            # Search government and public record sources
            govt_sites = [".gov", "whitepages.com", "yellowpages.com", "publicrecords.com"]
            search_query = f'"{entity_name}" public records OR government database AND (site:' + " OR site:".join(govt_sites) + ")"
            
            if self.google_api_key and self.google_cse_id:
                params = {
                    "key": self.google_api_key,
                    "cx": self.google_cse_id,
                    "q": search_query,
                    "num": max_results
                }
                
                url = f"https://www.googleapis.com/customsearch/v1?{urlencode(params)}"
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        sources = []
                        
                        for item in data.get("items", []):
                            content = await self._fetch_page_content(item["link"])
                            
                            source = OSINTSource(
                                url=item["link"],
                                title=item.get("title", ""),
                                content=content,
                                source_type=SourceType.PUBLIC_RECORDS,
                                credibility_score=0.85,  # Government sources high credibility
                                metadata={
                                    "snippet": item.get("snippet", ""),
                                    "search_query": search_query,
                                    "record_type": "public"
                                },
                                retrieved_at=datetime.utcnow(),
                                entities_mentioned=[entity_name]
                            )
                            sources.append(source)
                        
                        return sources
                        
        except Exception as e:
            logger.error(f"Public records search failed: {e}")
        
        return []
    
    async def _fetch_page_content(self, url: str, max_length: int = 2000) -> str:
        """Fetch and extract text content from a webpage"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    # Parse with BeautifulSoup
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    # Extract text
                    text = soup.get_text()
                    
                    # Clean up text
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text = ' '.join(chunk for chunk in chunks if chunk)
                    
                    # Truncate if too long
                    return text[:max_length] if len(text) > max_length else text
                    
        except Exception as e:
            logger.warning(f"Failed to fetch content from {url}: {e}")
        
        return ""


# Singleton instance
osint_retrieval_manager = OSINTRetrievalManager() 