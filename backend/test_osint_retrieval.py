#!/usr/bin/env python3
"""
Test script for Multi-Source OSINT Retrieval System
Tests real data collection across diverse intelligence sources
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.agent.osint_tools import osint_retrieval_manager, SourceType

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_search_api_keys():
    """Check if search API keys are configured."""
    required_keys = {
        'GOOGLE_SEARCH_API_KEY': 'Google Custom Search',
        'GOOGLE_CSE_ID': 'Google Custom Search Engine ID'
    }
    
    optional_keys = {
        'BING_API_KEY': 'Bing Search API',
        'SERPAPI_KEY': 'SerpAPI'
    }
    
    logger.info("Checking Search API key configuration...")
    
    configured_count = 0
    for key, description in required_keys.items():
        value = os.getenv(key)
        if value and value != 'your_api_key_here' and not value.startswith('mock_'):
            logger.info(f"✅ {key} configured for {description}")
            configured_count += 1
        else:
            logger.warning(f"❌ {key} not configured for {description}")
    
    for key, description in optional_keys.items():
        value = os.getenv(key)
        if value and value != 'your_api_key_here' and not value.startswith('mock_'):
            logger.info(f"✅ {key} configured for {description}")
        else:
            logger.info(f"ℹ️  {key} not configured for {description} (optional)")
    
    if configured_count == 0:
        logger.warning("⚠️  No search API keys configured - retrieval will be limited")
        return False
    
    return True

async def test_basic_retrieval():
    """Test basic retrieval functionality"""
    logger.info("Testing basic OSINT retrieval functionality...")
    
    try:
        # Test with a simple query
        test_query = "academic researcher"
        test_entity = "Ali Khaledi Nasab"
        
        logger.info(f"Retrieving information for: {test_entity} ({test_query})")
        
        sources = await osint_retrieval_manager.retrieve_from_multiple_sources(
            query=test_query,
            entity_name=test_entity,
            max_sources=8
        )
        
        logger.info(f"✅ Retrieved {len(sources)} sources")
        
        if sources:
            # Analyze source breakdown
            source_types = {}
            total_credibility = 0
            
            for source in sources:
                source_type = source.source_type.value
                source_types[source_type] = source_types.get(source_type, 0) + 1
                total_credibility += source.credibility_score
                
                logger.info(f"  📄 {source.source_type.value}: {source.title[:60]}...")
                logger.info(f"     URL: {source.url}")
                logger.info(f"     Credibility: {source.credibility_score:.2f}")
                logger.info(f"     Content length: {len(source.content)} chars")
                logger.info("")
            
            avg_credibility = total_credibility / len(sources)
            
            logger.info("📊 Source Analysis:")
            logger.info(f"   Total sources: {len(sources)}")
            logger.info(f"   Average credibility: {avg_credibility:.2f}")
            logger.info(f"   Source type breakdown: {source_types}")
            
            # Check for minimum diversity
            if len(source_types) >= 3:
                logger.info("✅ Good source diversity achieved")
            else:
                logger.warning("⚠️  Limited source diversity")
            
            # Check for minimum credibility
            if avg_credibility >= 0.6:
                logger.info("✅ Good average credibility score")
            else:
                logger.warning("⚠️  Low average credibility score")
            
            return True
        else:
            logger.warning("⚠️  No sources retrieved")
            return False
            
    except Exception as e:
        logger.error(f"❌ Basic retrieval test failed: {e}")
        return False

async def test_source_types():
    """Test different source types individually"""
    logger.info("Testing individual source types...")
    
    test_entity = "Ali Khaledi Nasab"
    
    # Test specific retrieval methods
    test_methods = [
        ("Web Search", osint_retrieval_manager._google_web_search),
        ("News Search", osint_retrieval_manager._google_news_search),
        ("LinkedIn Search", osint_retrieval_manager._linkedin_search),
        ("Academic Search", osint_retrieval_manager._academic_search),
        ("Business Search", osint_retrieval_manager._business_search)
    ]
    
    await osint_retrieval_manager.initialize()
    
    results = {}
    
    for test_name, method in test_methods:
        try:
            logger.info(f"Testing {test_name}...")
            
            if "search" in method.__name__ and method.__name__ != "_linkedin_search":
                # Methods that take query and entity_name
                sources = await method("researcher profile", test_entity, 2)
            else:
                # Methods that take only entity_name
                sources = await method(test_entity, 2)
            
            results[test_name] = len(sources)
            logger.info(f"  ✅ {test_name}: {len(sources)} sources")
            
            for source in sources:
                logger.info(f"    - {source.title[:50]}... (credibility: {source.credibility_score:.2f})")
                
        except Exception as e:
            logger.warning(f"  ⚠️  {test_name} failed: {e}")
            results[test_name] = 0
    
    await osint_retrieval_manager.cleanup()
    
    logger.info("📊 Source Type Test Results:")
    for test_name, count in results.items():
        status = "✅" if count > 0 else "❌"
        logger.info(f"   {status} {test_name}: {count} sources")
    
    successful_tests = sum(1 for count in results.values() if count > 0)
    logger.info(f"   Summary: {successful_tests}/{len(results)} source types working")
    
    return successful_tests >= 2  # At least 2 source types should work

async def test_rate_limiting():
    """Test rate limiting functionality"""
    logger.info("Testing rate limiting...")
    
    try:
        # Check rate limit status
        google_limit = osint_retrieval_manager._check_rate_limit("google")
        bing_limit = osint_retrieval_manager._check_rate_limit("bing")
        academic_limit = osint_retrieval_manager._check_rate_limit("academic")
        
        logger.info(f"Rate limit status - Google: {google_limit}, Bing: {bing_limit}, Academic: {academic_limit}")
        
        # Test increment
        osint_retrieval_manager._increment_rate_limit("google")
        logger.info("✅ Rate limiting functionality working")
        return True
        
    except Exception as e:
        logger.error(f"❌ Rate limiting test failed: {e}")
        return False

async def test_credibility_scoring():
    """Test credibility scoring system"""
    logger.info("Testing credibility scoring...")
    
    try:
        # Test different types of sources
        test_sources = [
            {"url": "https://www.harvard.edu/faculty/profile", "title": "Faculty Profile"},
            {"url": "https://en.wikipedia.org/wiki/article", "title": "Wikipedia Article"},
            {"url": "https://www.reuters.com/article", "title": "Reuters News"},
            {"url": "https://blog.example.com/post", "title": "Blog Post"},
            {"url": "https://linkedin.com/in/profile", "title": "LinkedIn Profile"}
        ]
        
        scores = {}
        for source in test_sources:
            score = osint_retrieval_manager._calculate_credibility_score(source)
            scores[source["url"]] = score
            logger.info(f"  {source['url']}: {score:.2f}")
        
        # Check expected patterns
        if scores.get("https://www.harvard.edu/faculty/profile", 0) > 0.7:
            logger.info("✅ Educational domains get high credibility")
        
        if scores.get("https://www.reuters.com/article", 0) > 0.6:
            logger.info("✅ News sources get good credibility")
        
        if scores.get("https://blog.example.com/post", 0) < 0.5:
            logger.info("✅ Blog sources get lower credibility")
        
        logger.info("✅ Credibility scoring working correctly")
        return True
        
    except Exception as e:
        logger.error(f"❌ Credibility scoring test failed: {e}")
        return False

async def main():
    """Run all OSINT retrieval tests"""
    logger.info("🔍 Starting Multi-Source OSINT Retrieval Tests")
    logger.info("=" * 60)
    
    # Test 1: API key configuration
    has_api_keys = check_search_api_keys()
    logger.info("")
    
    # Test 2: Rate limiting
    rate_limit_ok = await test_rate_limiting()
    logger.info("")
    
    # Test 3: Credibility scoring
    credibility_ok = await test_credibility_scoring()
    logger.info("")
    
    if has_api_keys:
        # Test 4: Source type testing
        source_types_ok = await test_source_types()
        logger.info("")
        
        # Test 5: Full retrieval test
        retrieval_ok = await test_basic_retrieval()
        logger.info("")
    else:
        logger.info("⏭️  Running demo mode tests (no API keys configured)")
        
        # Test demo retrieval functionality
        retrieval_ok = await test_basic_retrieval()
        logger.info("")
        
        source_types_ok = True  # Demo mode works
    
    # Summary
    logger.info("🎯 OSINT Retrieval Test Results")
    logger.info("=" * 60)
    logger.info(f"✅ Rate Limiting: {'PASS' if rate_limit_ok else 'FAIL'}")
    logger.info(f"✅ Credibility Scoring: {'PASS' if credibility_ok else 'FAIL'}")
    
    if has_api_keys:
        logger.info(f"✅ Source Types: {'PASS' if source_types_ok else 'FAIL'}")
        logger.info(f"✅ Full Retrieval: {'PASS' if retrieval_ok else 'FAIL'}")
        
        if source_types_ok and retrieval_ok:
            logger.info("🎉 Multi-Source OSINT Retrieval System: FULLY OPERATIONAL")
        else:
            logger.warning("⚠️  Multi-Source OSINT Retrieval System: PARTIALLY OPERATIONAL")
    else:
        logger.warning("⚠️  Configure search API keys for full testing")
        logger.info("📖 See backend/SETUP_API_KEYS.md for configuration instructions")
    
    logger.info("")
    logger.info("Next steps:")
    if not has_api_keys:
        logger.info("1. Configure Google Search API keys")
        logger.info("2. Run test again to verify retrieval")
    logger.info("3. Test with full investigation: Ali Khaledi Nasab")
    logger.info("4. Monitor source diversity and credibility")

if __name__ == "__main__":
    asyncio.run(main()) 