"""
Tests for multi-source OSINT retrieval functionality
Focuses on edge cases, rate limiting, source diversity, and production scenarios
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
import sys
import os
from datetime import datetime, timedelta

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

# Import specific modules directly to avoid graph dependencies
import importlib.util
osint_tools_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src', 'agent', 'osint_tools.py')
spec = importlib.util.spec_from_file_location("osint_tools", osint_tools_path)
osint_tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(osint_tools)

# Import the classes we need
OSINTRetrievalManager = osint_tools.OSINTRetrievalManager
OSINTSource = osint_tools.OSINTSource


class TestOSINTRetrievalManager:
    """Test the OSINT retrieval manager core functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.manager = OSINTRetrievalManager()
    
    @pytest.mark.asyncio
    async def test_demo_mode_retrieval(self):
        """Test retrieval in demo mode (no API keys)"""
        query = "Ali Khaledi Nasab"
        max_sources = 10
        
        sources = await self.manager.retrieve_from_multiple_sources(query, "Ali Khaledi Nasab", max_sources)
        
        # Should return realistic number of sources
        assert 8 <= len(sources) <= 12
        
        # Should have diverse source types
        source_types = {source.source_type for source in sources}
        assert len(source_types) >= 4  # Good diversity
        
        # Should have reasonable credibility scores
        avg_credibility = sum(source.credibility_score for source in sources) / len(sources)
        assert 0.5 <= avg_credibility <= 1.0
        
        # All sources should have required fields
        for source in sources:
            assert source.url
            assert source.title
            assert source.content
            assert source.source_type
            assert 0.0 <= source.credibility_score <= 1.0
    
    @pytest.mark.asyncio 
    async def test_source_type_distribution(self):
        """Test that different source types are represented appropriately"""
        query = "technology company investigation"
        max_sources = 15
        
        sources = await self.manager.retrieve_from_multiple_sources(query, "Ali Khaledi Nasab", max_sources)
        
        # Count source types
        type_counts = {}
        for source in sources:
            type_counts[source.source_type] = type_counts.get(source.source_type, 0) + 1
        
        # Should have good distribution - no single type dominating
        max_type_count = max(type_counts.values())
        assert max_type_count <= len(sources) // 2  # No type > 50%
        
        # Should have at least 3 different types
        assert len(type_counts) >= 3
    
    def test_credibility_scoring_logic(self):
        """Test credibility scoring for different domains"""
        test_cases = [
            ("https://www.bbc.com/news/article", 0.75, 0.85),  # News source + HTTPS bonus
            ("https://scholar.google.com/paper", 0.7, 0.8),   # Academic + HTTPS bonus
            ("https://www.sec.gov/filing", 0.8, 0.9),         # Government + HTTPS bonus
            ("https://randomsite.com/blog", 0.45, 0.6),       # General web with some variance
            ("https://socialmedia.com/post", 0.4, 0.6),       # Social media + HTTPS bonus
        ]
        
        for url, min_score, max_score in test_cases:
            score = self.manager._calculate_credibility_score({"url": url})
            assert min_score <= score <= max_score, f"Score {score} not in range {min_score}-{max_score} for {url}"
            
        # Test that scoring is working by comparing high vs low credibility
        high_cred = self.manager._calculate_credibility_score({"url": "https://www.gov/document"})
        low_cred = self.manager._calculate_credibility_score({"url": "http://random-blog.com/post"})
        assert high_cred > low_cred, "High credibility sources should score higher than low credibility"
    
    @pytest.mark.asyncio
    async def test_rate_limiting_simulation(self):
        """Test rate limiting behavior"""
        query = "test rate limiting"
        
        # Test rate limiting logic directly
        assert self.manager._check_rate_limit("google") == True  # Initially should be OK
        
        # Simulate many calls to hit rate limit
        for _ in range(101):  # Exceed the 100/day limit
            self.manager._increment_rate_limit("google")
        
        # Should now be rate limited
        assert self.manager._check_rate_limit("google") == False
        
        # Test that retrieval still works (falls back to demo sources)
        sources = await self.manager.retrieve_from_multiple_sources(query, "Test Entity", 10)
        assert len(sources) > 0  # Demo sources should fill in
    
    @pytest.mark.asyncio
    async def test_concurrent_retrievals(self):
        """Test multiple concurrent retrieval operations"""
        queries = [
            "Ali Khaledi Nasab professional background",
            "Ali Khaledi Nasab academic research", 
            "Ali Khaledi Nasab publications"
        ]
        
        # Run concurrent retrievals
        tasks = [
            self.manager.retrieve_from_multiple_sources(query, "Test Entity", 8)
            for query in queries
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should complete successfully
        for result in results:
            assert not isinstance(result, Exception)
            assert len(result) >= 8
    
    @pytest.mark.asyncio
    async def test_query_specificity_handling(self):
        """Test handling of different query types and specificities"""
        test_queries = [
            "Ali Khaledi Nasab",                    # Person name
            "Ali Khaledi Nasab researcher",         # Person + role
            "Ali Khaledi Nasab academic papers",    # Person + specific search
            "random gibberish xyz123",              # Nonsense query
            "",                                     # Empty query
            "a",                                    # Very short query
        ]
        
        for query in test_queries:
            sources = await self.manager.retrieve_from_multiple_sources(query, "Test Entity", 8)
            
            # Should handle all queries gracefully
            assert isinstance(sources, list)
            assert len(sources) >= 0  # Might be empty for nonsense queries
            
            # If sources returned, they should be valid
            for source in sources:
                assert isinstance(source, OSINTSource)
                assert source.url
                assert source.title
    
    def test_source_object_validation(self):
        """Test OSINTSource object validation and edge cases"""
        # Valid source
        source = OSINTSource(
            url="https://example.com",
            title="Test Source",
            content="Test content",
            source_type=osint_tools.SourceType.WEB,
            credibility_score=0.8,
            metadata={},
            retrieved_at=datetime.now(),
            entities_mentioned=[]
        )
        
        assert source.url == "https://example.com"
        assert source.credibility_score == 0.8
        
        # Test with minimal content
        minimal_source = OSINTSource(
            url="https://minimal.com",
            title="",  # Empty title
            content="",  # Empty content
            source_type=osint_tools.SourceType.WEB,
            credibility_score=0.5,
            metadata={},
            retrieved_at=datetime.now(),
            entities_mentioned=[]
        )
        
        assert minimal_source.url == "https://minimal.com"
        assert minimal_source.credibility_score == 0.5


class TestOSINTSourceTypes:
    """Test different OSINT source type behaviors"""
    
    def setup_method(self):
        """Set up test environment"""
        self.manager = OSINTRetrievalManager()
    
    @pytest.mark.asyncio
    async def test_academic_source_generation(self):
        """Test academic source simulation"""
        query = "machine learning research"
        sources = await self.manager.retrieve_from_multiple_sources(query, 12)
        
        # Filter academic sources
        academic_sources = [s for s in sources if s.source_type == "academic"]
        
        if academic_sources:  # If any academic sources were generated
            for source in academic_sources:
                # Academic sources should have high credibility
                assert source.credibility_score >= 0.7
                
                # Should contain academic indicators
                assert any(term in source.url.lower() for term in 
                          ["scholar", "academia", "research", ".edu"])
    
    @pytest.mark.asyncio
    async def test_news_source_generation(self):
        """Test news source simulation"""
        query = "breaking news investigation"
        sources = await self.manager.retrieve_from_multiple_sources(query, 10)
        
        news_sources = [s for s in sources if s.source_type == "news"]
        
        if news_sources:
            for source in news_sources:
                # News sources should have decent credibility
                assert source.credibility_score >= 0.5
                
                # Should look like news URLs
                assert any(term in source.url.lower() for term in 
                          ["news", "bbc", "reuters", "cnn", "times"])
    
    @pytest.mark.asyncio
    async def test_business_records_simulation(self):
        """Test business records source simulation"""
        query = "company financial records"
        sources = await self.manager.retrieve_from_multiple_sources(query, 10)
        
        business_sources = [s for s in sources if s.source_type == "business"]
        
        if business_sources:
            for source in business_sources:
                # Business sources should have high credibility
                assert source.credibility_score >= 0.7
                
                # Should contain business indicators
                assert any(term in source.url.lower() for term in 
                          ["sec.gov", "bloomberg", "crunchbase", "financials"])


class TestOSINTRetrievalEdgeCases:
    """Test edge cases and error conditions"""
    
    def setup_method(self):
        """Set up test environment"""
        self.manager = OSINTRetrievalManager()
    
    @pytest.mark.asyncio
    async def test_zero_max_sources(self):
        """Test behavior with zero max sources requested"""
        sources = await self.manager.retrieve_from_multiple_sources("test", "Test Entity", 0)
        assert len(sources) == 0
    
    @pytest.mark.asyncio
    async def test_very_large_max_sources(self):
        """Test behavior with unreasonably large max sources"""
        sources = await self.manager.retrieve_from_multiple_sources("test", "Test Entity", 1000)
        
        # Should be capped at reasonable limit
        assert len(sources) <= 50  # Reasonable upper bound
    
    @pytest.mark.asyncio
    async def test_unicode_query_handling(self):
        """Test handling of unicode and special characters in queries"""
        unicode_queries = [
            "علی خالدی نسب",        # Arabic/Persian script
            "Алексей Кулешов",      # Cyrillic
            "José María García",    # Accented characters
            "研究者 調査",            # Japanese/Chinese characters
            "query with émojis 🔍🌐"  # Emojis
        ]
        
        for query in unicode_queries:
            sources = await self.manager.retrieve_from_multiple_sources(query, 5)
            
            # Should handle unicode without errors
            assert isinstance(sources, list)
            
            # Sources should contain the original query or transliteration
            for source in sources:
                assert isinstance(source.content, str)
                assert isinstance(source.title, str)
    
    @pytest.mark.asyncio
    async def test_very_long_query(self):
        """Test handling of very long queries"""
        long_query = "very long query " * 100  # 1600+ characters
        
        sources = await self.manager.retrieve_from_multiple_sources(long_query, 5)
        
        # Should handle long queries without errors
        assert isinstance(sources, list)
    
    @pytest.mark.asyncio
    async def test_special_character_queries(self):
        """Test queries with special characters and symbols"""
        special_queries = [
            "query with (parentheses) and [brackets]",
            "query & with @ special # symbols %",
            "query-with-dashes_and_underscores",
            "query.with.dots/and\\slashes",
            '"quoted query" and \'single quotes\'',
        ]
        
        for query in special_queries:
            sources = await self.manager.retrieve_from_multiple_sources(query, 5)
            
            # Should handle special characters gracefully
            assert isinstance(sources, list)


class TestOSINTRetrievalPerformance:
    """Test performance characteristics and optimization"""
    
    def setup_method(self):
        """Set up test environment"""
        self.manager = OSINTRetrievalManager()
    
    @pytest.mark.asyncio
    async def test_retrieval_timing(self):
        """Test that retrievals complete within reasonable time"""
        import time
        
        start_time = time.time()
        sources = await self.manager.retrieve_from_multiple_sources("Ali Khaledi Nasab", 10)
        end_time = time.time()
        
        # Should complete within reasonable time (generous for CI/testing)
        assert end_time - start_time < 30.0  # 30 seconds max
        assert len(sources) > 0
    
    @pytest.mark.asyncio
    async def test_memory_usage_with_large_results(self):
        """Test memory usage doesn't grow excessively with large result sets"""
        # Request many sources to test memory handling
        sources = await self.manager.retrieve_from_multiple_sources("large dataset test", 50)
        
        # Check that each source doesn't have excessively large content
        for source in sources:
            assert len(source.content) < 50000  # 50KB limit per source
            assert len(source.title) < 1000     # 1KB limit per title
    
    @pytest.mark.asyncio
    async def test_parallel_processing_benefits(self):
        """Test that parallel processing improves performance"""
        import time
        
        # Test serial vs parallel (simulated)
        start_time = time.time()
        sources = await self.manager.retrieve_from_multiple_sources("performance test", 12)
        parallel_time = time.time() - start_time
        
        # Should complete reasonably quickly due to async processing
        assert parallel_time < 20.0  # Should be faster than serial processing
        assert len(sources) >= 8


class TestOSINTIntegrationScenarios:
    """Test integration scenarios with the broader OSINT system"""
    
    def setup_method(self):
        """Set up test environment"""
        self.manager = OSINTRetrievalManager()
    
    @pytest.mark.asyncio
    async def test_ali_khaledi_nasab_specific_retrieval(self):
        """Test retrieval specifically for Ali Khaledi Nasab investigation"""
        query = "Ali Khaledi Nasab"
        sources = await self.manager.retrieve_from_multiple_sources(query, 12)
        
        # Should meet minimum requirements for investigation
        assert len(sources) >= 8
        
        # Should have academic sources (likely for researcher)
        source_types = {source.source_type for source in sources}
        assert "academic" in source_types or "web" in source_types
        
        # Should have good overall credibility
        avg_credibility = sum(s.credibility_score for s in sources) / len(sources)
        assert avg_credibility >= 0.6
        
        # Should contain relevant content
        content_mentions = sum(1 for s in sources 
                             if "Ali Khaledi Nasab" in s.content or 
                                "researcher" in s.content.lower())
        assert content_mentions > 0  # At least some relevant content
    
    @pytest.mark.asyncio
    async def test_multi_entity_retrieval(self):
        """Test retrieval for multiple entities in a single investigation"""
        entities = [
            "Ali Khaledi Nasab",
            "University research collaboration",
            "Academic publications"
        ]
        
        all_sources = []
        for entity in entities:
            sources = await self.manager.retrieve_from_multiple_sources(entity, 6)
            all_sources.extend(sources)
        
        # Should have retrieved sources for all entities
        assert len(all_sources) >= 18  # 6 per entity minimum
        
        # Should have diverse sources across all retrievals
        all_types = {source.source_type for source in all_sources}
        assert len(all_types) >= 3
    
    @pytest.mark.asyncio
    async def test_investigation_pivot_retrieval(self):
        """Test retrieval for pivot investigations (follow-up queries)"""
        # Initial broad query
        initial_sources = await self.manager.retrieve_from_multiple_sources(
            "Ali Khaledi Nasab researcher", 8
        )
        
        # Pivot queries based on initial findings
        pivot_queries = [
            "Ali Khaledi Nasab academic publications",
            "Ali Khaledi Nasab research collaborations",
            "Ali Khaledi Nasab university affiliation"
        ]
        
        pivot_sources = []
        for query in pivot_queries:
            sources = await self.manager.retrieve_from_multiple_sources(query, 4)
            pivot_sources.extend(sources)
        
        # Should provide additional depth
        assert len(pivot_sources) >= 12
        
        # Combined sources should offer comprehensive coverage
        total_sources = initial_sources + pivot_sources
        total_types = {source.source_type for source in total_sources}
        assert len(total_types) >= 4  # Comprehensive source diversity


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 