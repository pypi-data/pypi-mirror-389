import asyncio
import os
import logging
from playwright.async_api import async_playwright
from reasonflow.integrations.web_browser_integration import WebBrowserIntegration

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_playwright_directly():
    """Test Playwright initialization directly without our wrapper"""
    logger.info("Testing direct Playwright initialization...")
    try:
        async with async_playwright() as playwright:
            logger.debug("Playwright context created")
            
            # Launch browser
            browser = await playwright.chromium.launch(headless=True)
            logger.debug("Browser launched")
            
            # Create context
            context = await browser.new_context()
            logger.debug("Browser context created")
            
            # Create page
            page = await context.new_page()
            logger.debug("Page created")
            
            # Set timeout
            logger.debug("Setting page timeout...")
            await page.set_default_timeout(30000)
            logger.debug("Page timeout set")
            
            # Navigate to a page
            logger.debug("Navigating to example.com...")
            await page.goto("https://example.com")
            logger.debug("Navigation complete")
            
            # Get page content
            content = await page.content()
            logger.debug(f"Page content length: {len(content)}")
            
            # Clean up
            await browser.close()
            logger.info("Direct Playwright test successful")
            return True
    except Exception as e:
        logger.error(f"Direct Playwright test failed: {str(e)}", exc_info=True)
        return False

async def test_web_browser_integration():
    """Test our WebBrowserIntegration wrapper"""
    logger.info("Testing WebBrowserIntegration...")
    try:
        browser = WebBrowserIntegration(
            headless=True,
            browser_type="chromium",
            timeout=30000
        )
        logger.debug("WebBrowserIntegration instance created")
        
        async with browser:
            logger.debug("Browser context started")
            result = await browser.navigate("https://example.com")
            logger.debug(f"Navigation result: {result}")
            
            if result.get("status") == "success":
                logger.info("WebBrowserIntegration test successful")
                return True
            else:
                logger.error(f"Navigation failed: {result.get('message')}")
                return False
                
    except Exception as e:
        logger.error(f"WebBrowserIntegration test failed: {str(e)}", exc_info=True)
        return False

async def main():
    """Run all tests"""
    try:
        # First test direct Playwright
        logger.info("=== Starting Direct Playwright Test ===")
        playwright_success = await test_playwright_directly()
        logger.info(f"Direct Playwright test {'succeeded' if playwright_success else 'failed'}")
        
        # Then test our integration
        logger.info("\n=== Starting WebBrowserIntegration Test ===")
        integration_success = await test_web_browser_integration()
        logger.info(f"WebBrowserIntegration test {'succeeded' if integration_success else 'failed'}")
        
    except Exception as e:
        logger.error(f"Test suite failed: {str(e)}", exc_info=True)
    finally:
        logger.info("Test suite completed")

if __name__ == "__main__":
    asyncio.run(main()) 