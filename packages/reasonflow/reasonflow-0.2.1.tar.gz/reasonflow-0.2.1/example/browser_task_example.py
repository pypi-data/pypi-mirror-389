import asyncio
import os
from reasonflow.tasks.task_manager import TaskManager
from reasonflow.observability.basic_tracker import BasicMetricsCollector
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def main():
    try:
        # Initialize task manager
        metrics_collector = BasicMetricsCollector()
        task_manager = TaskManager(metrics_collector=metrics_collector)
        
        # Create data directory if it doesn't exist
        os.makedirs("./data", exist_ok=True)
        
        # Simple browser task configuration
        browser_task_config = {
            "type": "browser",
            "config": {
                "url": "https://ir.tesla.com/financial-information/quarterly-results",
                "actions": [
                    {
                        "action": "navigate",
                        "url": "https://ir.tesla.com/financial-information/quarterly-results"
                    },
                    {
                        "action": "extract_data",
                        "selectors": {
                            "q3_link": "a.tds-link[href*='TSLA-Q3-2024-Update.pdf']"
                        },
                        "extract_attributes": {
                            "q3_link": ["href"]
                        }
                    },
                    {
                        "action": "validate",
                        "config": {
                            "input": "${extracted_data.data.q3_link.href}",
                            "validation_type": "url",
                            "pattern": ".*\\.pdf$"
                        }
                    },
                    {
                        "action": "download",
                        "config": {
                            "url": "${validated_url}",
                            "download_path": "./data",
                            "filename": "tesla_q3_2024.pdf"
                        }
                    }
                ]
            }
        }

        logger.info("Executing browser task...")
        browser_result = await task_manager.execute_task(
            task_id="browser_test",
            task_type="browser",
            config=browser_task_config
        )
        
        logger.info("Browser task completed")
        logger.debug(f"Full result: {browser_result}")
        
        if browser_result.get("status") == "success":
            results = browser_result.get("results", {})
            print("\nSuccess!")
            
            # Print extracted data
            print("\nExtracted Data:")
            extracted = results.get("extracted_data", {}).get("data", {})
            for field, value in extracted.items():
                print(f"{field}: {value}")
            
            # Print validation result
            print("\nValidation Result:")
            validated_url = results.get("validated_url")
            if validated_url:
                print(f"Validated URL: {validated_url}")
            
            # Print download result
            print("\nDownload Result:")
            download = results.get("download", {})
            if download.get("status") == "success":
                print(f"File downloaded to: {download.get('file_path')}")
                print(f"File size: {download.get('size')} bytes")
                print(f"MIME type: {download.get('mime_type')}")
            else:
                print(f"Download failed: {download.get('message')}")
        else:
            print(f"\nError: {browser_result.get('message', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"Error in main: {str(e)}", exc_info=True)
    finally:
        await task_manager.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 