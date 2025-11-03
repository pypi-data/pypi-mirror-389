import asyncio
import os
from reasonflow.tasks.task_manager import TaskManager
from reasonflow.observability.basic_tracker import BasicMetricsCollector
import json


async def main():
    # Initialize task manager with metrics collector
    metrics_collector = BasicMetricsCollector()
    task_manager = TaskManager(metrics_collector=metrics_collector)
    
    try:
        # 1. Shell Task - List directory contents
        shell_task_config = {
            "command": "ls -la",
            "cwd": os.getcwd()
        }
        shell_result = await task_manager.execute_task(
            task_id="shell_task_1",
            task_type="shell",
            config=shell_task_config
        )
        print("\nShell Task Result:")
        if "error" not in shell_result:
            print(f"Command output:\n{shell_result.get('stdout', '')}")
        else:
            print(f"Error: {shell_result['error']}")

        # 2. HTTP Task - Make a GET request
        http_task_config = {
            "method": "GET",
            "url": "https://api.github.com/repos/openai/openai-python",
            "headers": {
                "Accept": "application/json"
            }
        }
        http_result = await task_manager.execute_task(
            task_id="http_task_1",
            task_type="http",
            config=http_task_config
        )
        print("\nHTTP Task Result:")
        if "error" not in http_result:
            print(f"Status Code: {http_result.get('status_code')}")
            body = http_result.get('body', {})
            if isinstance(body, str):
                try:
                    body = json.loads(body)
                except json.JSONDecodeError:
                    body = {}
            print(f"Repository Name: {body.get('name')}")
        else:
            print(f"Error: {http_result['error']}")

        # 3. Web Browser Task - Automate browser actions
        browser_task_config = {
            "agent_config": {
                "headless": True,
                "browser": "chromium",
                "timeout": 30000,
                "user_agent": "Mozilla/5.0 (X11; Linux x86_64) ReasonFlow Browser",
                "proxy": None  # Optional proxy configuration
            },
            "params": {
                "actions": [
                    # Navigate and analyze content
                    {
                        "action": "navigate",
                        "url": "https://developer.mozilla.org/en-US/docs/Web/API/Window/navigator"
                    },
                    # Extract structured data
                    {
                        "action": "extract_data",
                        "selectors": {
                            "title": "h1",
                            "description": "p",
                            "links": "a"
                        },
                        "wait_for_selectors": True
                    },
                    # Content analysis
                    {
                        "action": "analyze",
                        "analysis_types": ["sentiment", "keywords"],
                        "options": {
                            "min_keyword_length": 4,
                            "max_keywords": 10
                        }
                    },
                    # Form interaction
                    # {
                    #     "action": "fill_form",
                    #     "form_data": {
                    #         "search": "task automation",
                    #         "category": "software"
                    #     },
                    #     "submit_selector": "button[type='submit']",
                    #     "wait_for_navigation": True
                    # },
                    # Extract links after form submission
                    {
                        "action": "extract_links",
                        "selector": ".search-results a"
                    },
                    # Take screenshot of results
                    {
                        "action": "screenshot",
                        "path": "search_results.png",
                        "full_page": True
                    }
                ]
            }
        }
        browser_result = await task_manager.execute_task(
            task_id="browser_task_1",
            task_type="browser",
            config=browser_task_config
        )
        print("\nWeb Browser Task Result:")
        if browser_result.get("status") == "success":
            results = browser_result.get("results", {})
            
            # Print navigation results
            nav_content = results.get("content", "")
            print(f"Page Content Length: {len(nav_content)} characters")
            
            # Print extracted data
            extracted = results.get("extracted_data", {}).get("data", {})
            print("\nExtracted Data:")
            for field, value in extracted.items():
                print(f"{field}: {value[:100]}...")  # Truncate long values
                
            # Print content analysis
            analysis = results.get("analysis", {}).get("results", {})
            if "sentiment" in analysis:
                sentiment = analysis["sentiment"]
                print(f"\nContent Sentiment:")
                print(f"Polarity: {sentiment.get('polarity', 0)}")
                print(f"Subjectivity: {sentiment.get('subjectivity', 0)}")
            
            if "keywords" in analysis:
                keywords = analysis["keywords"].get("top_keywords", {})
                print("\nTop Keywords:")
                for word, count in list(keywords.items())[:5]:
                    print(f"{word}: {count}")
                    
            # Print form submission results
            form_result = results.get("form", {})
            print(f"\nForm Submission: {form_result.get('status', 'unknown')}")
            
            # Print extracted links
            links = results.get("links", [])
            print(f"\nExtracted Links: {len(links)} found")
            for link in links[:3]:  # Show first 3 links
                print(f"- {link.get('text', 'No text')}: {link.get('href', 'No URL')}")
                
            # Print screenshot status
            print(f"\nScreenshot Saved: {results.get('screenshot', False)}")
        else:
            print(f"Error: {browser_result.get('message', 'Unknown error')}")

        # 4. LLM Task - Generate text
        llm_task_config = {
            "agent_config": {
                "provider": "groq",
                "model": "mixtral-8x7b-32768",
                "api_key": os.getenv("GROQ_API_KEY")
            },
            "params": {
                "prompt": "Explain what a task manager does in a software system in one sentence.",
                "max_tokens": 100
            }
        }
        llm_result = await task_manager.execute_task(
            task_id="llm_task_1",
            task_type="llm",
            config=llm_task_config
        )
        print("\nLLM Task Result:")
        if "error" not in llm_result:
            print(f"Response: {llm_result.get('output', {}).get('content', '')}")
        else:
            print(f"Error: {llm_result['error']}")

        # # 4. Data Retrieval Task - Search vector database
        # data_retrieval_config = {
        #     "agent_config": {
        #         "db_path": "./data/vector_db",
        #         "db_type": "faiss",
        #         "embedding_provider": "sentence_transformers",
        #         "embedding_model": "all-MiniLM-L6-v2"
        #     },
        #     "params": {
        #         "query": "What are the key features of task management?",
        #         "top_k": 3
        #     }
        # }
        # retrieval_result = await task_manager.execute_task(
        #     task_id="data_retrieval_1",
        #     task_type="data_retrieval",
        #     config=data_retrieval_config
        # )
        # print("\nData Retrieval Task Result:")
        # if "error" not in retrieval_result:
        #     print(f"Found {retrieval_result.get('summary', {}).get('total_results', 0)} results")
        #     for idx, result in enumerate(retrieval_result.get('results', []), 1):
        #         print(f"\nResult {idx}:")
        #         print(f"Content: {result.get('content', '')}")
        #         print(f"Score: {result.get('score', 0.0)}")
        # else:
        #     print(f"Error: {retrieval_result['error']}")

        # 5. Python Task - Execute custom code
        python_task_config = {
            "code": """
import platform
result = {
    'python_version': platform.python_version(),
    'system': platform.system(),
    'processor': platform.processor()
}
"""
        }
        python_result = await task_manager.execute_task(
            task_id="python_task_1",
            task_type="python",
            config=python_task_config
        )
        print("\nPython Task Result:")
        if "error" not in python_result:
            print(f"System Info: {python_result.get('result', {})}")
        else:
            print(f"Error: {python_result['error']}")

        # 6. File System Task - Write a file
        fs_task_config = {
            "operation": "write",
            "path": "test_output.txt",
            "content": "This is a test of the file system task."
        }
        fs_result = await task_manager.execute_task(
            task_id="fs_task_1",
            task_type="filesystem",
            config=fs_task_config
        )
        print("\nFile System Task Result:")
        if "error" not in fs_result:
            print("File written successfully")
            
            # Read the file back
            read_config = {
                "operation": "read",
                "path": "test_output.txt"
            }
            read_result = await task_manager.execute_task(
                task_id="fs_task_2",
                task_type="filesystem",
                config=read_config
            )
            if "error" not in read_result:
                print(f"File contents: {read_result.get('content', '')}")
            else:
                print(f"Error reading file: {read_result['error']}")
        else:
            print(f"Error: {fs_result['error']}")

        # Get metrics for all tasks
        print("\nTask Metrics:")
        for task_id in ["shell_task_1", "http_task_1", "browser_task_1", "llm_task_1", "python_task_1", "fs_task_1"]:
            metrics = await task_manager.get_task_metrics(task_id)
            print(f"\n{task_id} Metrics:")
            print(json.dumps(metrics, indent=2))

    except Exception as e:
        print(f"Error executing tasks: {str(e)}")
    finally:
        # Cleanup
        await task_manager.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 