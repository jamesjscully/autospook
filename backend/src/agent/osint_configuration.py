import os
from pydantic import BaseModel, Field
from typing import Any, Optional

from langchain_core.runnables import RunnableConfig
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableLambda
import logging

logger = logging.getLogger(__name__)


class OSINTConfiguration(BaseModel):
    """Configuration for the OSINT multi-agent system."""

    # Query Analysis Agent - Claude Sonnet 4
    query_analysis_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        metadata={
            "description": "Claude Sonnet 4 for query analysis and entity extraction"
        },
    )

    # Planning & Orchestration Agent - Claude Sonnet 4
    orchestration_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        metadata={
            "description": "Claude Sonnet 4 for strategic planning and orchestration"
        },
    )

    # Retrieval Agent - Claude Sonnet 4
    retrieval_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        metadata={
            "description": "Claude Sonnet 4 for multi-source retrieval operations"
        },
    )

    # Pivot Analysis Agent - GPT-4o
    pivot_analysis_model: str = Field(
        default="gpt-4o",
        metadata={
            "description": "GPT-4o for analytical reasoning and pivot generation"
        },
    )

    # Synthesis & Reporting Agent - Gemini 1.5 Pro
    synthesis_model: str = Field(
        default="gemini-1.5-pro",
        metadata={
            "description": "Gemini 1.5 Pro for large context synthesis and report generation"
        },
    )

    # Judge Agent - Claude Opus 4
    judge_model: str = Field(
        default="claude-3-opus-20240229",
        metadata={
            "description": "Claude Opus 4 for final quality assurance and validation"
        },
    )

    # OSINT Operation Parameters
    minimum_retrievals: int = Field(
        default=10,
        metadata={"description": "Minimum number of retrieval operations per investigation"},
    )

    max_research_loops: int = Field(
        default=3,
        metadata={"description": "Maximum number of investigation loops"},
    )

    parallel_retrieval_limit: int = Field(
        default=5,
        metadata={"description": "Maximum number of parallel retrieval operations"},
    )

    # Source Configuration
    enable_web_search: bool = Field(
        default=True,
        metadata={"description": "Enable web search capabilities"},
    )

    enable_social_media: bool = Field(
        default=True,
        metadata={"description": "Enable social media intelligence gathering"},
    )

    enable_public_records: bool = Field(
        default=True,
        metadata={"description": "Enable public records searches"},
    )

    enable_academic_search: bool = Field(
        default=True,
        metadata={"description": "Enable academic publication searches"},
    )

    # Memory Configuration
    enable_persistent_memory: bool = Field(
        default=True,
        metadata={"description": "Enable persistent memory across investigations"},
    )

    memory_retention_days: int = Field(
        default=90,
        metadata={"description": "Days to retain investigation memory"},
    )

    # Quality Thresholds
    minimum_confidence_threshold: float = Field(
        default=0.7,
        metadata={"description": "Minimum confidence score for report approval"},
    )

    source_credibility_threshold: float = Field(
        default=0.5,
        metadata={"description": "Minimum credibility score for source inclusion"},
    )

    # API Configuration
    google_search_api_key: Optional[str] = Field(
        default=None,
        metadata={"description": "Google Search API key for web searches"},
    )

    google_cse_id: Optional[str] = Field(
        default=None,
        metadata={"description": "Google Custom Search Engine ID"},
    )

    # Database Configuration
    postgres_url: Optional[str] = Field(
        default=None,
        metadata={"description": "PostgreSQL connection URL for persistent storage"},
    )

    redis_url: Optional[str] = Field(
        default=None,
        metadata={"description": "Redis connection URL for caching"},
    )

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "OSINTConfiguration":
        """Create an OSINTConfiguration instance from a RunnableConfig."""
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )

        # Get raw values from environment or config
        raw_values: dict[str, Any] = {
            name: os.environ.get(name.upper(), configurable.get(name))
            for name in cls.model_fields.keys()
        }

        # Special handling for API keys
        raw_values["google_search_api_key"] = os.environ.get("GOOGLE_SEARCH_API_KEY")
        raw_values["google_cse_id"] = os.environ.get("GOOGLE_CSE_ID")
        raw_values["postgres_url"] = os.environ.get("POSTGRES_URL")
        raw_values["redis_url"] = os.environ.get("REDIS_URL")

        # Filter out None values
        values = {k: v for k, v in raw_values.items() if v is not None}

        return cls(**values)


def get_model_config() -> OSINTConfiguration:
    """Get the current OSINT configuration."""
    return OSINTConfiguration.from_runnable_config()


def create_llm_client(agent_type: str, config: Optional[OSINTConfiguration] = None) -> Any:
    """Create the appropriate LLM client based on agent type."""
    if config is None:
        config = get_model_config()
    
    # Model mapping based on agent specialization
    model_map = {
        "query_analysis": config.query_analysis_model,
        "planning": config.orchestration_model,
        "retrieval": config.retrieval_model,
        "pivot_analysis": config.pivot_analysis_model,
        "synthesis": config.synthesis_model,
        "judge": config.judge_model
    }
    
    model_name = model_map.get(agent_type)
    if not model_name:
        raise ValueError(f"Unknown agent type: {agent_type}")
    
    try:
        # Create appropriate client based on model family
        if "claude" in model_name.lower():
            anthropic_key = os.getenv("ANTHROPIC_API_KEY")
            if not anthropic_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")
            
            return ChatAnthropic(
                model=model_name,
                api_key=anthropic_key,
                temperature=0.1,  # Low temperature for consistent OSINT analysis
                max_tokens=4096,
                timeout=60.0
            )
            
        elif "gpt" in model_name.lower():
            openai_key = os.getenv("OPENAI_API_KEY")
            if not openai_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            
            return ChatOpenAI(
                model=model_name,
                api_key=openai_key,
                temperature=0.1,
                max_tokens=4096,
                timeout=60.0
            )
            
        elif "gemini" in model_name.lower():
            gemini_key = os.getenv("GEMINI_API_KEY")
            if not gemini_key:
                raise ValueError("GEMINI_API_KEY environment variable not set")
            
            return ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=gemini_key,
                temperature=0.1,
                max_output_tokens=4096,
                timeout=60.0
            )
        else:
            raise ValueError(f"Unsupported model: {model_name}")
            
    except Exception as e:
        logger.error(f"Failed to create LLM client for {agent_type} with model {model_name}: {e}")
        raise


def create_agent(agent_type: str, system_prompt: str, config: Optional[OSINTConfiguration] = None):
    """Create an OSINT agent with the appropriate LLM and system prompt."""
    
    try:
        # Get LLM client
        llm = create_llm_client(agent_type, config)
        
        # Create agent with system message
        def agent_with_system_prompt(input_data):
            messages = input_data.get("messages", [])
            
            # Add system prompt as first message if not already present
            if not messages or not isinstance(messages[0], SystemMessage):
                messages = [SystemMessage(content=system_prompt)] + messages
            
            return llm.invoke(messages)
        
        agent = RunnableLambda(agent_with_system_prompt)
        
        logger.info(f"Created {agent_type} agent with model: {config.query_analysis_model if agent_type == 'query_analysis' else 'configured model'}")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create agent {agent_type}: {e}")
        
        # Fallback to a simple mock agent for development/testing
        logger.warning(f"Using mock agent for {agent_type} due to LLM client failure")
        
        def mock_agent(input_data):
            from langchain_core.messages import AIMessage
            return AIMessage(content=f"Mock response from {agent_type} agent. System prompt: {system_prompt[:100]}...")
        
        return RunnableLambda(mock_agent) 