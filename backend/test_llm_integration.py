#!/usr/bin/env python3
"""
Test script to verify LLM integration and API key configuration
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

from src.agent.osint_configuration import create_agent, get_model_config, create_llm_client
from src.agent.osint_prompts import AGENT_PROMPTS

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_api_keys():
    """Check if API keys are configured."""
    required_keys = {
        'ANTHROPIC_API_KEY': 'Claude models',
        'OPENAI_API_KEY': 'GPT models', 
        'GEMINI_API_KEY': 'Gemini models'
    }
    
    logger.info("Checking API key configuration...")
    
    for key, description in required_keys.items():
        value = os.getenv(key)
        if value and value != 'your_api_key_here' and not value.startswith('mock_'):
            logger.info(f"✅ {key} configured for {description}")
        else:
            logger.warning(f"❌ {key} not configured for {description}")
    
    return True

def test_model_configuration():
    """Test the model configuration setup."""
    logger.info("Testing model configuration...")
    
    try:
        config = get_model_config()
        logger.info(f"✅ Configuration loaded successfully")
        logger.info(f"   Query Analysis Model: {config.query_analysis_model}")
        logger.info(f"   Pivot Analysis Model: {config.pivot_analysis_model}")
        logger.info(f"   Synthesis Model: {config.synthesis_model}")
        logger.info(f"   Judge Model: {config.judge_model}")
        return True
    except Exception as e:
        logger.error(f"❌ Configuration failed: {e}")
        return False

def test_llm_client_creation():
    """Test LLM client creation for each agent type."""
    logger.info("Testing LLM client creation...")
    
    agent_types = ["query_analysis", "pivot_analysis", "synthesis", "judge"]
    
    for agent_type in agent_types:
        try:
            client = create_llm_client(agent_type)
            logger.info(f"✅ {agent_type} client created successfully")
        except ValueError as e:
            if "API key" in str(e):
                logger.warning(f"⚠️  {agent_type} client failed - API key not configured: {e}")
            else:
                logger.error(f"❌ {agent_type} client failed: {e}")
        except Exception as e:
            logger.error(f"❌ {agent_type} client creation failed: {e}")

async def test_agent_creation():
    """Test agent creation with mock inputs."""
    logger.info("Testing agent creation...")
    
    agent_types = ["query_analysis", "planning", "retrieval", "pivot_analysis", "synthesis", "judge"]
    
    for agent_type in agent_types:
        try:
            prompt = AGENT_PROMPTS.get(agent_type, "Test prompt")
            agent = create_agent(agent_type, prompt)
            logger.info(f"✅ {agent_type} agent created successfully")
            
            # Test with a simple message
            test_input = {
                "messages": [{"role": "user", "content": f"Test message for {agent_type}"}]
            }
            
            # We expect this might fail with API key issues, but the agent should be created
            logger.info(f"   Agent {agent_type} is ready for invocation")
            
        except Exception as e:
            logger.error(f"❌ {agent_type} agent creation failed: {e}")

def test_prompt_completeness():
    """Test that all prompts are properly defined."""
    logger.info("Testing prompt completeness...")
    
    required_agents = ["query_analysis", "planning", "retrieval", "pivot_analysis", "synthesis", "judge"]
    
    for agent_type in required_agents:
        if agent_type in AGENT_PROMPTS:
            prompt = AGENT_PROMPTS[agent_type]
            if len(prompt) > 100:  # Basic length check
                logger.info(f"✅ {agent_type} prompt is properly defined ({len(prompt)} chars)")
            else:
                logger.warning(f"⚠️  {agent_type} prompt seems too short ({len(prompt)} chars)")
        else:
            logger.error(f"❌ {agent_type} prompt is missing")

async def main():
    """Run all tests."""
    logger.info("🔬 Starting LLM Integration Tests")
    logger.info("=" * 50)
    
    # Test 1: API key configuration
    check_api_keys()
    logger.info("")
    
    # Test 2: Model configuration
    test_model_configuration()
    logger.info("")
    
    # Test 3: Prompt completeness
    test_prompt_completeness()
    logger.info("")
    
    # Test 4: LLM client creation
    test_llm_client_creation()
    logger.info("")
    
    # Test 5: Agent creation
    await test_agent_creation()
    logger.info("")
    
    logger.info("🎯 LLM Integration Tests Complete")
    logger.info("=" * 50)
    logger.info("Next Steps:")
    logger.info("1. Configure real API keys in backend/.env")
    logger.info("2. Test actual LLM responses")
    logger.info("3. Run full OSINT investigation with real agents")

if __name__ == "__main__":
    asyncio.run(main()) 