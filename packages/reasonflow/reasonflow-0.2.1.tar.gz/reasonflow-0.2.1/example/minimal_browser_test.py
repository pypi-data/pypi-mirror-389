from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright, Playwright
import asyncio
async def main():
    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch()
        print("Browser launched")
        
        print("Creating context...")
        context = await browser.new_context()
        print("Context created")
        
        print("Creating page...")
        page = await context.new_page()
        print("Page created")
        
        print("Setting timeout...")
        page.set_default_timeout(30000)
        print("Timeout set")
        
        print("Navigating to example.com...")
        await page.goto("https://example.com")
        print("Navigation complete")
        
        print("Getting page content...")
        content = await page.content()
        print(f"Content length: {len(content)}")
        
        print("Closing browser...")
        await browser.close()
        print("Browser closed")

if __name__ == "__main__":
    asyncio.run(main()) 

    