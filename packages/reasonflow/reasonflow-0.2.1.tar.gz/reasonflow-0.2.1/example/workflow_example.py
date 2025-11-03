"""
Enhanced Workflow Example - Demonstrating ReasonFlow's Flexible Provider System

This example showcases:
1. Multiple LLM providers (OpenAI, Groq, Ollama, Anthropic)
2. Different embedding providers (Sentence Transformers, OpenAI)
3. Multiple vector databases (FAISS, Pinecone)
4. Custom provider registration
5. Provider comparison and selection
6. Advanced RAG + LLM combinations
"""

import os
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
import asyncio
from reasonflow.orchestrator.workflow_builder import WorkflowBuilder
from reasonflow.tasks.task_manager import TaskManager
from reasonflow.integrations.rag_integrations import RAGIntegration
from reasonflow.integrations.llm_integrations import LLMIntegration
from reasontrack import (
    RuntimeMode,
    HardwareType,
    MetricsConfig,
    LLMConfig,
    VectorDBConfig,
    TaskConfig,
)
from reasonchain.memory import SharedMemory
import json
import yaml
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

def get_reasontrack_config(config_path: str) -> dict:
    """Get ReasonTrack configuration from YAML file.
    
    Args:
        config_path: Path to config file
        
    Returns:
        dict: Configuration dictionary
        
    Raises:
        FileNotFoundError: If config file not found
    """
    config_path = os.path.expanduser(config_path)
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    logger.info(f"Loading config from: {config_path}")
    
    # Load and parse YAML config
    with open(config_path, encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Process environment variables
    def process_env_vars(data):
        if isinstance(data, dict):
            return {k: process_env_vars(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [process_env_vars(item) for item in data]
        elif isinstance(data, str) and data.startswith('${') and data.endswith('}'):
            env_var = data[2:-1]
            value = os.getenv(env_var)
            if value is None:
                logger.warning(f"Environment variable {env_var} not set")
                return ''
            if ',' in value:  # Handle comma-separated lists
                return value.split(',')
            return value
        return data
    
    return process_env_vars(config)

def demonstrate_provider_flexibility():
    """Demonstrate the flexible provider system capabilities."""
    print("\n=== ReasonFlow Provider System Demonstration ===")
    
    # Show available providers
    print("\n1. Available LLM Providers:")
    available_llm_providers = LLMIntegration.list_available_providers()
    for provider in available_llm_providers:
        print(f"   - {provider}")
    
    print("\n2. Available Embedding Providers:")
    available_embedding_providers = RAGIntegration.list_available_embedding_providers()
    for provider in available_embedding_providers:
        print(f"   - {provider}")
    
    print("\n3. Supported Vector Databases:")
    supported_dbs = RAGIntegration.list_supported_vector_databases()
    for db in supported_dbs:
        print(f"   - {db}")

def setup_multiple_llm_providers():
    """Setup multiple LLM providers for different use cases."""
    providers = {}
    
    # Fast inference provider (Groq)
    if os.getenv("GROQ_API_KEY"):
        try:
            providers["fast"] = LLMIntegration(
                provider="groq", 
                model="llama-3.1-8b-instant"
            )
            print("✓ Fast LLM (Groq) initialized")
        except Exception as e:
            print(f"✗ Fast LLM (Groq) failed: {e}")
    
    # High quality provider (OpenAI)
    if os.getenv("OPENAI_API_KEY"):
        try:
            providers["quality"] = LLMIntegration(
                provider="openai", 
                model="gpt-4"
            )
            print("✓ Quality LLM (OpenAI) initialized")
        except Exception as e:
            print(f"✗ Quality LLM (OpenAI) failed: {e}")
    
    # Local/Privacy provider (Ollama)
    try:
        providers["local"] = LLMIntegration(
            provider="ollama", 
            model="llama3.1:latest"
        )
        print("✓ Local LLM (Ollama) initialized")
    except Exception as e:
        print(f"✗ Local LLM (Ollama) failed: {e}")
    
    # Anthropic provider (Claude)
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            providers["reasoning"] = LLMIntegration(
                provider="anthropic", 
                model="claude-3-opus-20240229"
            )
            print("✓ Reasoning LLM (Anthropic) initialized")
        except Exception as e:
            print(f"✗ Reasoning LLM (Anthropic) failed: {e}")
    
    return providers

def setup_multiple_rag_systems():
    """Setup multiple RAG systems with different configurations."""
    rag_systems = {}
    
    # Local RAG with Sentence Transformers
    try:
        rag_systems["local"] = RAGIntegration(
            db_path="local_knowledge.index",
            db_type="faiss",
            embedding_provider="sentence_transformers",
            embedding_model="all-mpnet-base-v2",
            use_gpu=True
        )
        print("✓ Local RAG (FAISS + Sentence Transformers) initialized")
    except Exception as e:
        print(f"✗ Local RAG failed: {e}")
    
    # Cloud RAG with OpenAI embeddings
    if os.getenv("OPENAI_API_KEY"):
        try:
            rag_systems["cloud"] = RAGIntegration(
                db_path="cloud_knowledge.index",
                db_type="faiss",
                embedding_provider="openai",
                embedding_model="text-embedding-3-small"
            )
            print("✓ Cloud RAG (FAISS + OpenAI Embeddings) initialized")
        except Exception as e:
            print(f"✗ Cloud RAG failed: {e}")
    
    # Production RAG with Pinecone (if configured)
    if os.getenv("PINECONE_API_KEY"):
        try:
            rag_systems["production"] = RAGIntegration(
                db_path="production-index",
                db_type="pinecone",
                embedding_provider="openai",
                embedding_model="text-embedding-3-small",
                api_key=os.getenv("PINECONE_API_KEY")
            )
            print("✓ Production RAG (Pinecone + OpenAI Embeddings) initialized")
        except Exception as e:
            print(f"✗ Production RAG failed: {e}")
    
    return rag_systems

def create_intelligent_assistant(llm_providers, rag_systems):
    """Create an intelligent assistant that can switch between providers."""
    
    def ask_question(question, llm_type="quality", rag_type="local", use_rag=True):
        """Ask a question using specified providers."""
        try:
            # Get LLM provider
            if llm_type not in llm_providers:
                available = list(llm_providers.keys())
                llm_type = available[0] if available else None
                if not llm_type:
                    return {"error": "No LLM providers available"}
            
            llm = llm_providers[llm_type]
            
            if use_rag and rag_systems:
                # Get RAG provider
                if rag_type not in rag_systems:
                    available = list(rag_systems.keys())
                    rag_type = available[0] if available else None
                
                if rag_type:
                    rag = rag_systems[rag_type]
                    
                    # Search knowledge base
                    search_results = rag.search(question, top_k=3)
                    
                    # Extract context
                    context = ""
                    if search_results.get("status") == "success":
                        for result in search_results.get("results", []):
                            context += f"{result.get('content', '')}\n\n"
                    
                    # Create enhanced prompt
                    enhanced_prompt = f"""
                    Based on the following context, answer the question. If the context doesn't contain relevant information, answer based on your general knowledge.
                    
                    Context:
                    {context}
                    
                    Question: {question}
                    
                    Provide a helpful, accurate response.
                    """
                    
                    response = llm.execute(enhanced_prompt)
                else:
                    response = llm.execute(question)
            else:
                response = llm.execute(question)
            
            return {
                "answer": response,
                "llm_provider": llm_type,
                "rag_provider": rag_type if use_rag else None,
                "used_rag": use_rag and rag_type is not None
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    return ask_question

def build_enhanced_workflow(llm_providers, rag_systems, shared_memory):
    """Build workflow configuration demonstrating flexible provider system"""
    
    # Select providers for different tasks based on requirements
    fast_llm = "fast" if "fast" in llm_providers else list(llm_providers.keys())[0]
    quality_llm = "quality" if "quality" in llm_providers else list(llm_providers.keys())[0]
    reasoning_llm = "reasoning" if "reasoning" in llm_providers else quality_llm
    
    local_rag = "local" if "local" in rag_systems else list(rag_systems.keys())[0] if rag_systems else None
    
    workflow_config = {
        "tasks": {
            "ingest-document-local": {
                "type": "data_retrieval",
                "config": {
                    "agent_config": {
                        "db_path": "vector_db_tesla_local.index",
                        "db_type": "faiss",
                        "embedding_provider": "sentence_transformers",
                        "embedding_model": "all-mpnet-base-v2",
                        "use_gpu": True,
                        "shared_memory": shared_memory
                    },
                    "params": {
                        "query": "Retrieve Tesla financial data using local embeddings",
                        "top_k": 5
                    }
                }
            },
            "ingest-document-cloud": {
                "type": "data_retrieval", 
                "config": {
                    "agent_config": {
                        "db_path": "vector_db_tesla_cloud.index",
                        "db_type": "faiss",
                        "embedding_provider": "openai",
                        "embedding_model": "text-embedding-3-small",
                        "use_gpu": False,
                        "shared_memory": shared_memory
                    },
                    "params": {
                        "query": "Retrieve Tesla financial data using OpenAI embeddings",
                        "top_k": 5
                    }
                }
            },
            "extract-highlights-fast": {
                "type": "llm",
                "config": {
                    "agent": llm_providers[fast_llm],
                    "params": {
                        "prompt": f"""[Using {fast_llm.upper()} LLM for fast extraction]
                        Extract key financial highlights from the following data: 
                        {{ingest-document-local.output}}
                        
                        Format your response as a bulleted list of the most important financial metrics and findings."""
                    }
                }
            },
            "extract-highlights-quality": {
                "type": "llm", 
                "config": {
                    "agent": llm_providers[quality_llm],
                    "params": {
                        "prompt": f"""[Using {quality_llm.upper()} LLM for high-quality extraction]
                        Extract comprehensive financial highlights from the following data:
                        {{ingest-document-cloud.output}}
                        
                        Provide detailed analysis with:
                        - Key financial metrics with context
                        - Year-over-year comparisons
                        - Notable trends and patterns
                        - Risk factors identified"""
                    }
                }
            },
            "analyze-trends-reasoning": {
                "type": "llm",
                "config": {
                    "agent": llm_providers[reasoning_llm],
                    "params": {
                        "prompt": f"""[Using {reasoning_llm.upper()} LLM for deep analysis]
                        Perform comprehensive financial trend analysis using both extraction results:
                        
                        Fast Extraction: {{extract-highlights-fast.output}}
                        Quality Extraction: {{extract-highlights-quality.output}}
                        
                        Provide detailed analysis focusing on:
                        - Revenue growth trends and sustainability
                        - Profitability metrics and margin analysis
                        - Cash flow patterns and liquidity
                        - Key business segments performance
                        - Competitive positioning
                        - Market dynamics impact"""
                    }
                }
            },
            "compare-provider-results": {
                "type": "llm",
                "config": {
                    "agent": llm_providers[quality_llm],
                    "params": {
                        "prompt": f"""[Provider Comparison Analysis]
                        Compare and contrast the results from different LLM providers:
                        
                        Fast Provider ({fast_llm}): {{extract-highlights-fast.output}}
                        Quality Provider ({quality_llm}): {{extract-highlights-quality.output}}
                        
                        Analyze:
                        1. Consistency between providers
                        2. Unique insights from each provider
                        3. Quality differences in analysis
                        4. Recommendations for provider selection"""
                    }
                }
            },
            "final-executive-summary": {
                "type": "llm",
                "config": {
                    "agent": llm_providers[reasoning_llm],
                    "params": {
                        "prompt": f"""[Final Executive Summary using {reasoning_llm.upper()}]
                        Create a comprehensive executive summary incorporating all analyses:
                        
                        Trend Analysis: {{analyze-trends-reasoning.output}}
                        Provider Comparison: {{compare-provider-results.output}}
                        
                        Include:
                        1. Overall financial health assessment
                        2. Key growth indicators and drivers
                        3. Risk factors and mitigation strategies
                        4. Future outlook and recommendations
                        5. Provider system insights and recommendations"""
                    }
                }
            }
        
        },
        "dependencies": [
            # Parallel document ingestion with different embedding providers
            {"from": "ingest-document-local", "to": "extract-highlights-fast"},
            {"from": "ingest-document-cloud", "to": "extract-highlights-quality"},
            
            # Analysis depends on both extractions
            {"from": "extract-highlights-fast", "to": "analyze-trends-reasoning"},
            {"from": "extract-highlights-quality", "to": "analyze-trends-reasoning"},
            
            # Provider comparison depends on both extractions
            {"from": "extract-highlights-fast", "to": "compare-provider-results"},
            {"from": "extract-highlights-quality", "to": "compare-provider-results"},
            
            # Final summary depends on analysis and comparison
            {"from": "analyze-trends-reasoning", "to": "final-executive-summary"},
            {"from": "compare-provider-results", "to": "final-executive-summary"}
        ]
    }
    
    print(f"\n=== Workflow Configuration ===")
    print(f"Fast LLM Provider: {fast_llm}")
    print(f"Quality LLM Provider: {quality_llm}")
    print(f"Reasoning LLM Provider: {reasoning_llm}")
    print(f"RAG System: {local_rag}")
    
    return workflow_config

async def print_task_status(engine, task_id, start_time, end_time):
    """Print task status with proper async handling."""
    try:
        status = await engine.get_task_status(task_id, start_time, end_time)
        print(f"\n{task_id}:")
        print(json.dumps(status, indent=2))
    except Exception as e:
        print(f"\n{task_id}:")
        print(f"Error getting task status: {str(e)}")

async def print_workflow_status(engine, workflow_id, start_time, end_time):
    """Print workflow status with proper async handling."""
    try:
        status = await engine.get_workflow_status(workflow_id, start_time, end_time)
        print("\nWorkflow Metrics:")
        print(json.dumps(status, indent=2))
    except Exception as e:
        print("\nWorkflow Metrics:")
        print(f"Error getting workflow status: {str(e)}")

async def main():
    print("🚀 Starting Enhanced ReasonFlow Workflow Example...")
    print("Demonstrating flexible LLM and RAG provider system")
    
    # Demonstrate provider capabilities
    demonstrate_provider_flexibility()
    
    # Initialize components
    config_path = os.path.join(os.path.dirname(__file__), "config", "reasontrack.yaml")
    print(f"\n📁 Loading config from: {config_path}")
    
    config = get_reasontrack_config(config_path)
    shared_memory = SharedMemory()
    task_manager = TaskManager(shared_memory=shared_memory)

    # Initialize metrics configuration
    metrics_config = MetricsConfig(
        task=TaskConfig(
            track_duration=True,
            track_memory=True,
            track_cpu=True,
            track_gpu=True,
            hardware_type=HardwareType.GPU
        ),
        llm=LLMConfig(
            track_tokens=True,
            track_cost=True,
            track_latency=True,
            track_hardware=True
        ),
        vectordb=VectorDBConfig(
            track_query_time=True,
            track_latency=True,
            track_embedding_time=True,
            runtime_mode=RuntimeMode.LOCAL
        ),
        enable_real_time=True,
        enable_cost_alerts=True,
        cost_threshold=1.0,
        sampling_interval=1.0
    )

    workflow_builder = WorkflowBuilder(
        task_manager=task_manager, 
        tracker_type="reasontrack", 
        tracker_config=config,
        metrics_config=metrics_config,
        config_path=config_path
    )

    # Setup multiple providers
    print("\n🔧 Setting up multiple LLM providers...")
    llm_providers = setup_multiple_llm_providers()
    
    print("\n🔧 Setting up multiple RAG systems...")
    rag_systems = setup_multiple_rag_systems()
    
    # Add documents to different RAG systems
    document_path = "tsla-20240930-gen.pdf"
    if os.path.exists(document_path):
        print(f"\n📄 Adding document to RAG systems: {document_path}")
        for name, rag_system in rag_systems.items():
            try:
                success = rag_system.add_documents([document_path])
                print(f"   ✓ Added to {name} RAG system: {success}")
            except Exception as e:
                print(f"   ✗ Failed to add to {name} RAG system: {e}")
    else:
        print(f"\n⚠️  Document not found: {document_path}")
        print("   Creating sample documents for demonstration...")
        # Add some sample text data
        sample_texts = [
            "Tesla reported strong Q3 2024 financial results with record revenue growth.",
            "The company's automotive segment showed significant improvement in margins.",
            "Energy storage and solar deployments reached new quarterly records.",
            "Tesla's Full Self-Driving technology continues to advance with new capabilities."
        ]
        for name, rag_system in rag_systems.items():
            try:
                success = rag_system.add_raw_data(sample_texts)
                print(f"   ✓ Added sample data to {name} RAG system: {success}")
            except Exception as e:
                print(f"   ✗ Failed to add sample data to {name} RAG system: {e}")
    
    # Create intelligent assistant
    if llm_providers and rag_systems:
        print("\n🤖 Creating intelligent assistant...")
        assistant = create_intelligent_assistant(llm_providers, rag_systems)
        
        # Test the assistant with different provider combinations
        test_questions = [
            "What are Tesla's key financial highlights?",
            "How is Tesla's automotive business performing?",
            "What are the growth prospects for Tesla's energy business?"
        ]
        
        print("\n🧪 Testing assistant with different provider combinations:")
        for i, question in enumerate(test_questions):
            llm_types = list(llm_providers.keys())
            rag_types = list(rag_systems.keys())
            
            if llm_types and rag_types:
                llm_type = llm_types[i % len(llm_types)]
                rag_type = rag_types[i % len(rag_types)]
                
                print(f"\n   Question {i+1}: {question}")
                print(f"   Using LLM: {llm_type}, RAG: {rag_type}")
                
                result = assistant(question, llm_type=llm_type, rag_type=rag_type)
                if "error" not in result:
                    print(f"   Answer: {result['answer']['output'][:200]}...")
                    print(f"   Providers used: LLM={result['llm_provider']}, RAG={result['rag_provider']}")
                else:
                    print(f"   Error: {result['error']}")

    # Build enhanced workflow if providers are available
    if llm_providers:
        print("\n🔄 Building enhanced workflow with multiple providers...")
        workflow_config = build_enhanced_workflow(llm_providers, rag_systems, shared_memory)
        
        # Execute enhanced workflow if providers are available
        if llm_providers:
            try:
                print("\n🚀 Executing enhanced multi-provider workflow...")
                start_time = datetime.now(timezone.utc)
                end_time = start_time + timedelta(hours=1)
                
                # Create workflow
                workflow_id = await workflow_builder.create_workflow(workflow_config)
                print(f"✓ Workflow created with ID: {workflow_id}")
                
                # Execute workflow
                results = await workflow_builder.execute_workflow(workflow_config, workflow_id=workflow_id)
                
                print("\n📊 === Enhanced Workflow Execution Results ===")
                
                # Display results with provider information
                for task_id, result in results.items():
                    print(f"\n🔹 Task: {task_id}")
                    if isinstance(result, dict) and 'output' in result:
                        output = result['output']
                        if isinstance(output, dict) and 'output' in output:
                            content = output['output'][:300] + "..." if len(str(output['output'])) > 300 else output['output']
                            print(f"   Result: {content}")
                            if 'metadata' in output:
                                metadata = output['metadata']
                                if 'provider' in metadata:
                                    print(f"   Provider: {metadata['provider']}")
                                if 'model' in metadata:
                                    print(f"   Model: {metadata['model']}")
                        else:
                            print(f"   Result: {str(result)[:300]}...")
                    else:
                        print(f"   Result: {str(result)[:300]}...")
                    
                    # Get task status
                    await print_task_status(workflow_builder.engine, task_id, start_time, end_time)

                # Workflow status
                await print_workflow_status(workflow_builder.engine, workflow_id, start_time, end_time)

                # Enhanced performance analysis
                print("\n📈 === Enhanced Performance Analysis ===")
                
                # Provider performance comparison
                print("\n🏆 Provider Performance Summary:")
                provider_performance = {}
                for task_id, result in results.items():
                    if isinstance(result, dict) and 'output' in result:
                        output = result['output']
                        if isinstance(output, dict) and 'metadata' in output:
                            metadata = output['metadata']
                            provider = metadata.get('provider', 'unknown')
                            if provider not in provider_performance:
                                provider_performance[provider] = {'tasks': 0, 'success': 0}
                            provider_performance[provider]['tasks'] += 1
                            if output.get('status') == 'success':
                                provider_performance[provider]['success'] += 1

                for provider, stats in provider_performance.items():
                    success_rate = (stats['success'] / stats['tasks']) * 100 if stats['tasks'] > 0 else 0
                    print(f"   {provider}: {stats['success']}/{stats['tasks']} tasks successful ({success_rate:.1f}%)")

                # System bottlenecks
                try:
                    bottlenecks = workflow_builder.engine.metrics_collector.analyze_bottlenecks(workflow_id)
                    if bottlenecks:
                        print("\n⚠️  Bottlenecks Detected:")
                        print(json.dumps(bottlenecks, indent=2))
                except Exception as e:
                    print(f"\n⚠️  Could not analyze bottlenecks: {e}")

                # Cost analysis
                try:
                    cost_analysis = workflow_builder.engine.metrics_collector.analyze_costs(workflow_id)
                    print("\n💰 Cost Analysis:")
                    print(json.dumps(cost_analysis, indent=2))
                except Exception as e:
                    print(f"\n💰 Could not analyze costs: {e}")

            except Exception as e:
                print(f"\n❌ Error executing enhanced workflow: {str(e)}")
                import traceback
                traceback.print_exc()
        else:
            print("\n⚠️  No LLM providers available - skipping workflow execution")
            print("   Please configure API keys for OpenAI, Groq, or Anthropic")
            print("   Or ensure Ollama is running locally")
    else:
        print("\n⚠️  No LLM providers available - skipping all workflow operations")
        
    print("\n🎉 Enhanced ReasonFlow demonstration completed!")
    print("This example showcased:")
    print("   ✓ Multiple LLM providers (OpenAI, Groq, Ollama, Anthropic)")
    print("   ✓ Multiple embedding providers (Sentence Transformers, OpenAI)")
    print("   ✓ Multiple vector databases (FAISS, Pinecone)")
    print("   ✓ Provider comparison and performance analysis")
    print("   ✓ Intelligent assistant with provider switching")
    print("   ✓ Enhanced workflow with parallel processing")


if __name__ == "__main__":
    asyncio.run(main()) 