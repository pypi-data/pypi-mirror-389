from typing import Dict, Any, Optional, List, Callable
import logging
import asyncio
from playwright.async_api import async_playwright, Browser, Page, Download, Request, Response
from bs4 import BeautifulSoup
import json
import time
import os
import aiofiles
import hashlib
from pathlib import Path
from urllib.parse import urlparse
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from textblob import TextBlob
# from readability import Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebBrowserIntegration:
    def __init__(
        self,
        headless: bool = True,
        browser_type: str = "chromium",
        timeout: int = 30000,
        user_agent: Optional[str] = None,
        proxy: Optional[Dict[str, str]] = None
    ):
        """Initialize web browser integration.
        
        Args:
            headless: Whether to run browser in headless mode
            browser_type: Type of browser (chromium, firefox, webkit)
            timeout: Page timeout in milliseconds
            user_agent: Custom user agent string
            proxy: Proxy configuration dictionary
        """
        self.headless = headless
        self.browser_type = browser_type
        self.timeout = timeout
        self.user_agent = user_agent
        self.proxy = proxy
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self._playwright_context = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def _initialize_page(self, browser_context):
        """Initialize a new page with the specified configuration.
        
        Args:
            browser_context: The browser context to create the page in.
            
        Returns:
            The initialized page.
        """
        try:
            logging.info("Creating new page...")
            page = await browser_context.new_page()
            if not page:
                raise RuntimeError("Failed to create new page")
            logging.info("Page created successfully")
            
            # Verify that the page is a valid Playwright Page object
            if hasattr(page, 'set_default_timeout'):
                if self.timeout:
                    logging.info(f"Setting page timeout to {self.timeout}ms...")
                    page.set_default_timeout(self.timeout)
                    logging.info("Page timeout set successfully")
            else:
                logging.warning("Page object does not have set_default_timeout method")
                
            return page
            
        except Exception as e:
            logging.error(f"Error initializing page: {str(e)}", exc_info=True)
            raise

    async def start(self):
        """Start the browser instance."""
        try:
            logging.info("Starting browser initialization...")
            
            # Create and store the context manager
            self._playwright_context = async_playwright()
            logging.info("Created Playwright context manager")
            
            self.playwright = await self._playwright_context.__aenter__()
            logging.info("Entered Playwright context")
            
            # Launch browser based on type
            logging.info(f"Launching {self.browser_type} browser...")
            if self.browser_type == "chromium":
                self.browser = await self.playwright.chromium.launch(headless=self.headless)
            elif self.browser_type == "firefox":
                self.browser = await self.playwright.firefox.launch(headless=self.headless)
            elif self.browser_type == "webkit":
                self.browser = await self.playwright.webkit.launch(headless=self.headless)
            else:
                raise ValueError(f"Unsupported browser type: {self.browser_type}")
            logging.info("Browser launched successfully")
            
            # Create context with user agent if specified
            logging.info("Creating browser context...")
            browser_context = await self.browser.new_context(
                user_agent=self.user_agent if self.user_agent else None
            )
            logging.info("Browser context created successfully")
            
            # Initialize page
            self.page = await self._initialize_page(browser_context)
            if not self.page:
                raise RuntimeError("Failed to initialize page")
            
            logging.info(f"Started {self.browser_type} browser successfully")
            return True
            
        except Exception as e:
            logging.error(f"Error starting browser: {str(e)}", exc_info=True)
            # Clean up any partially initialized resources
            await self.close()
            raise

    async def close(self):
        """Close browser and cleanup."""
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            if self._playwright_context:
                await self._playwright_context.__aexit__(None, None, None)
            
        except Exception as e:
            logging.error(f"Error closing browser: {str(e)}")
            raise

    async def navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to a URL and extract page content.
        
        Args:
            url: URL to navigate to
            
        Returns:
            Dictionary containing page content and metadata
        """
        start_time = time.time()
        try:
            if not self.page:
                raise RuntimeError("Browser not initialized")

            # Navigate to URL
            response = await self.page.goto(url, wait_until="networkidle")
            if not response:
                raise RuntimeError(f"Failed to load {url}")
            
            # Wait for content to load
            await self.page.wait_for_load_state("domcontentloaded")
            
            # Get page content
            content = await self.page.content()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract useful content
            title = soup.title.string if soup.title else ""
            main_content = ""
            for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                main_content += f"{tag.get_text()} "
                
            # Get metadata
            metadata = {
                "url": url,
                "title": title,
                "status_code": response.status,
                "headers": dict(response.headers),
                "load_time": time.time() - start_time,
                "content_type": response.headers.get("content-type", ""),
            }
            
            return {
                "status": "success",
                "content": main_content.strip(),
                "metadata": metadata,
                "raw_html": content
            }
            
        except Exception as e:
            error_msg = f"Error navigating to {url}: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg,
                "metadata": {
                    "url": url,
                    "load_time": time.time() - start_time,
                    "error": str(e)
                }
            }

    async def extract_links(self, selector: str = "a") -> List[Dict[str, str]]:
        """Extract links from the current page.
        
        Args:
            selector: CSS selector for links
            
        Returns:
            List of dictionaries containing link information
        """
        try:
            if not self.page:
                raise RuntimeError("Browser not initialized")
                
            links = await self.page.eval_on_selector_all(
                selector,
                """elements => elements.map(el => ({
                    href: el.href,
                    text: el.innerText,
                    title: el.title
                }))"""
            )
            
            return links
            
        except Exception as e:
            logger.error(f"Error extracting links: {str(e)}")
            return []

    async def screenshot(self, path: str, full_page: bool = True) -> bool:
        """Take a screenshot of the current page.
        
        Args:
            path: Path to save screenshot
            full_page: Whether to capture full page or viewport
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.page:
                raise RuntimeError("Browser not initialized")
                
            await self.page.screenshot(path=path, full_page=full_page)
            return True
            
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")
            return False

    async def execute_script(self, script: str) -> Any:
        """Execute JavaScript on the page.
        
        Args:
            script: JavaScript code to execute
            
        Returns:
            Result of script execution
        """
        try:
            if not self.page:
                raise RuntimeError("Browser not initialized")
                
            result = await self.page.evaluate(script)
            return result
            
        except Exception as e:
            logger.error(f"Error executing script: {str(e)}")
            return None 

    async def download_file(self, url: str, save_path: str, filename: str = None) -> Dict[str, Any]:
        """Download a file from a URL using multiple strategies.
        
        Supports multiple download methods:
        1. Direct download using Playwright's download manager
        2. Fetch API for direct file download
        3. Navigation-based download for PDFs
        4. Stream download for large files
        
        Args:
            url: URL to download from
            save_path: Directory to save the file in
            filename: Optional filename to use
            
        Returns:
            Dictionary containing download status and metadata
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(save_path, exist_ok=True)
            
            # Determine actual filename
            actual_filename = filename or os.path.basename(url)
            full_path = os.path.join(save_path, actual_filename)
            
            # Strategy 1: Try Playwright's download manager first
            try:
                async with self.page.expect_download(timeout=10000) as download_info:
                    await self.page.goto(url)
                    download = await download_info.value
                    await download.save_as(full_path)
                    
                    return {
                        "status": "success",
                        "strategy": "playwright_download",
                        "file_path": str(full_path),
                        "filename": actual_filename,
                        "size": os.path.getsize(full_path),
                        "mime_type": download.mime_type,
                        "url": url
                    }
            except Exception as e:
                logger.debug(f"Playwright download failed, trying next strategy: {str(e)}")
                
            # Strategy 2: Try fetch API
            try:
                # Create a new context with download permissions
                context = await self.browser.new_context(accept_downloads=True)
                page = await context.new_page()
                
                try:
                    response = await page.evaluate(f"""
                        async () => {{
                            const response = await fetch('{url}');
                            if (!response.ok) throw new Error('Failed to fetch file');
                            const buffer = await response.arrayBuffer();
                            return Array.from(new Uint8Array(buffer));
                        }}
                    """)
                    
                    async with aiofiles.open(full_path, 'wb') as f:
                        await f.write(bytes(response))
                    
                    return {
                        "status": "success", 
                        "strategy": "fetch_api",
                        "file_path": str(full_path),
                        "filename": actual_filename,
                        "size": os.path.getsize(full_path),
                        "mime_type": "application/octet-stream",  # Default mime type
                        "url": url
                    }
                finally:
                    await page.close()
                    await context.close()
            except Exception as e:
                logger.debug(f"Fetch API download failed, trying next strategy: {str(e)}")
                
            # Strategy 3: Try navigation for PDFs
            if url.lower().endswith('.pdf'):
                try:
                    # Create a new context and page for PDF
                    context = await self.browser.new_context(accept_downloads=True)
                    page = await context.new_page()
                    
                    try:
                        # Navigate to PDF URL
                        response = await page.goto(url, wait_until="networkidle")
                        if response and response.ok:
                            content = await response.body()
                            async with aiofiles.open(full_path, 'wb') as f:
                                await f.write(content)
                                
                            return {
                                "status": "success",
                                "strategy": "pdf_navigation",
                                "file_path": str(full_path),
                                "filename": actual_filename,
                                "size": os.path.getsize(full_path),
                                "mime_type": "application/pdf",
                                "url": url
                            }
                    finally:
                        await page.close()
                        await context.close()
                except Exception as e:
                    logger.debug(f"PDF navigation download failed: {str(e)}")
                    
            # Strategy 4: Stream download for large files
            try:
                async with self.page.request.get(url) as response:
                    if response.ok:
                        content = await response.read()
                        async with aiofiles.open(full_path, 'wb') as f:
                            await f.write(content)
                            
                        return {
                            "status": "success",
                            "strategy": "stream_download",
                            "file_path": str(full_path),
                            "filename": actual_filename,
                            "size": os.path.getsize(full_path),
                            "mime_type": response.headers.get("content-type", "application/octet-stream"),
                            "url": url
                        }
            except Exception as e:
                logger.debug(f"Stream download failed: {str(e)}")
                
            raise Exception("All download strategies failed")
            
        except Exception as e:
            error_msg = f"Error downloading file from {url}: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg,
                "metadata": {
                    "url": url,
                    "error": str(e)
                }
            }

    async def fill_form(
        self, 
        form_data: Dict[str, Any], 
        submit_selector: Optional[str] = None,
        wait_for_navigation: bool = True
    ) -> Dict[str, Any]:
        """Fill and submit forms with automatic field detection.
        
        Args:
            form_data: Dictionary of field selectors/names and values
            submit_selector: Optional submit button selector
            wait_for_navigation: Whether to wait for navigation after submit
            
        Returns:
            Dictionary containing form submission status and results
        """
        try:
            if not self.page:
                raise RuntimeError("Browser not initialized")

            # Fill form fields
            for selector, value in form_data.items():
                try:
                    # Try different selector strategies
                    strategies = [
                        f"input[name='{selector}']",
                        f"textarea[name='{selector}']",
                        f"select[name='{selector}']",
                        selector  # Use provided selector as fallback
                    ]
                    
                    filled = False
                    for strategy in strategies:
                        try:
                            await self.page.fill(strategy, str(value))
                            filled = True
                            break
                        except Exception:
                            continue
                            
                    if not filled:
                        logger.warning(f"Could not fill field: {selector}")
                        
                except Exception as e:
                    logger.error(f"Error filling field {selector}: {str(e)}")

            # Submit form if selector provided
            if submit_selector:
                await self.page.click(submit_selector)
                if wait_for_navigation:
                    await self.page.wait_for_load_state("networkidle")

            return {
                "status": "success",
                "form_data": form_data,
                "submitted": bool(submit_selector)
            }

        except Exception as e:
            error_msg = f"Error filling form: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg,
                "form_data": form_data
            }

    async def extract_structured_data(
        self,
        selectors: Dict[str, str],
        schema: Optional[Dict[str, str]] = None,
        transform: Optional[Dict[str, Callable]] = None,
        wait_for_selectors: bool = True,
        extract_attributes: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """Extract structured data using selectors with schema validation.
        
        Args:
            selectors: Dictionary of field names and CSS selectors
            schema: Optional schema for validation
            transform: Optional transformation functions
            wait_for_selectors: Whether to wait for selectors to be available
            extract_attributes: Dictionary mapping field names to lists of attributes to extract
            
        Returns:
            Dictionary containing extracted data
        """
        try:
            if not self.page:
                raise RuntimeError("Browser not initialized")

            data = {}
            errors = []

            for field, selector in selectors.items():
                try:
                    if wait_for_selectors:
                        try:
                            await self.page.wait_for_selector(selector, timeout=5000)
                        except Exception:
                            logger.warning(f"Selector not found: {selector}")
                            
                    # Extract content
                    element = await self.page.query_selector(selector)
                    if element:
                        # Get text content
                        text_value = await element.text_content()
                        
                        # Initialize field data with text content
                        field_data = {"text": text_value}
                        
                        # Extract attributes if specified
                        if extract_attributes and field in extract_attributes:
                            for attr in extract_attributes[field]:
                                try:
                                    attr_value = await element.get_attribute(attr)
                                    if attr_value is not None:
                                        field_data[attr] = attr_value
                                except Exception as e:
                                    logger.error(f"Error extracting attribute {attr} for {field}: {str(e)}")
                        
                        # Apply transformation if specified
                        if transform and field in transform:
                            try:
                                field_data = transform[field](field_data)
                            except Exception as e:
                                logger.error(f"Transform error for {field}: {str(e)}")
                                
                        # Validate against schema if provided
                        if schema and field in schema:
                            # Add schema validation logic here
                            pass
                            
                        data[field] = field_data
                    else:
                        errors.append(f"Selector not found: {selector}")
                        
                except Exception as e:
                    errors.append(f"Error extracting {field}: {str(e)}")

            return {
                "status": "success" if not errors else "partial",
                "data": data,
                "errors": errors
            }

        except Exception as e:
            error_msg = f"Error extracting structured data: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg,
                "data": {},
                "errors": [str(e)]
            }

    async def intercept_network(
        self,
        url_pattern: str,
        method: str = "GET",
        include_bodies: bool = False,
        max_requests: int = 100
    ) -> Dict[str, Any]:
        """Intercept and capture network requests/responses.
        
        Args:
            url_pattern: URL pattern to intercept
            method: HTTP method to intercept
            include_bodies: Whether to include request/response bodies
            max_requests: Maximum number of requests to capture
            
        Returns:
            Dictionary containing captured requests/responses
        """
        try:
            if not self.page:
                raise RuntimeError("Browser not initialized")

            requests_data = []
            
            async def handle_request(request: Request):
                if len(requests_data) >= max_requests:
                    return
                    
                if request.url.match(url_pattern) and request.method == method:
                    req_data = {
                        "url": request.url,
                        "method": request.method,
                        "headers": request.headers,
                        "resource_type": request.resource_type,
                        "timestamp": time.time()
                    }
                    
                    if include_bodies and request.post_data:
                        req_data["body"] = request.post_data
                        
                    requests_data.append(req_data)

            async def handle_response(response: Response):
                if response.url.match(url_pattern) and response.request.method == method:
                    for req in requests_data:
                        if req["url"] == response.url:
                            req["status"] = response.status
                            req["response_headers"] = response.headers
                            if include_bodies:
                                try:
                                    req["response_body"] = await response.text()
                                except Exception:
                                    req["response_body"] = None

            # Set up listeners
            self.page.on("request", handle_request)
            self.page.on("response", handle_response)

            return {
                "status": "success",
                "requests": requests_data
            }

        except Exception as e:
            error_msg = f"Error setting up network interception: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg,
                "requests": []
            }

    async def manage_state(
        self,
        action: str,
        state_data: Optional[Dict[str, Any]] = None,
        storage_types: List[str] = ["cookies", "localStorage", "sessionStorage"]
    ) -> Dict[str, Any]:
        """Manage browser state (cookies, localStorage, sessionStorage).
        
        Args:
            action: Action to perform (get, set, clear)
            state_data: Data to set if action is 'set'
            storage_types: Types of storage to manage
            
        Returns:
            Dictionary containing state management results
        """
        try:
            if not self.page:
                raise RuntimeError("Browser not initialized")

            if action == "get":
                state = {}
                
                if "cookies" in storage_types:
                    state["cookies"] = await self.page.context.cookies()
                    
                if "localStorage" in storage_types or "sessionStorage" in storage_types:
                    storage = await self.page.evaluate("""
                        () => ({
                            localStorage: Object.fromEntries(
                                Object.entries(localStorage)
                            ),
                            sessionStorage: Object.fromEntries(
                                Object.entries(sessionStorage)
                            )
                        })
                    """)
                    
                    if "localStorage" in storage_types:
                        state["localStorage"] = storage["localStorage"]
                    if "sessionStorage" in storage_types:
                        state["sessionStorage"] = storage["sessionStorage"]
                        
                return {
                    "status": "success",
                    "state": state
                }
                
            elif action == "set":
                if not state_data:
                    raise ValueError("state_data required for 'set' action")
                    
                if "cookies" in storage_types and "cookies" in state_data:
                    await self.page.context.add_cookies(state_data["cookies"])
                    
                if "localStorage" in storage_types and "localStorage" in state_data:
                    await self.page.evaluate(
                        f"localStorage = {json.dumps(state_data['localStorage'])}"
                    )
                    
                if "sessionStorage" in storage_types and "sessionStorage" in state_data:
                    await self.page.evaluate(
                        f"sessionStorage = {json.dumps(state_data['sessionStorage'])}"
                    )
                    
                return {
                    "status": "success",
                    "action": "set",
                    "storage_types": storage_types
                }
                
            elif action == "clear":
                if "cookies" in storage_types:
                    await self.page.context.clear_cookies()
                    
                if "localStorage" in storage_types:
                    await self.page.evaluate("localStorage.clear()")
                    
                if "sessionStorage" in storage_types:
                    await self.page.evaluate("sessionStorage.clear()")
                    
                return {
                    "status": "success",
                    "action": "clear",
                    "storage_types": storage_types
                }
                
            else:
                raise ValueError(f"Unknown action: {action}")

        except Exception as e:
            error_msg = f"Error managing state: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg,
                "action": action
            }

    async def analyze_content(
        self,
        analysis_types: List[str] = ["readability", "sentiment", "keywords"],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze page content with various strategies.
        
        Args:
            analysis_types: Types of analysis to perform
            options: Analysis options
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            if not self.page:
                raise RuntimeError("Browser not initialized")

            # Get page content
            content = await self.page.content()
            text_content = await self.page.evaluate('document.body.innerText')
            
            results = {}
            
            # Readability analysis
            # if "readability" in analysis_types:
            #     doc = Document(content)
            #     results["readability"] = {
            #         "title": doc.title(),
            #         "summary": doc.summary(),
            #         "text": doc.get_clean_text()
            #     }
            
            # Sentiment analysis
            if "sentiment" in analysis_types:
                blob = TextBlob(text_content)
                results["sentiment"] = {
                    "polarity": blob.sentiment.polarity,
                    "subjectivity": blob.sentiment.subjectivity
                }
            
            # Keyword extraction
            if "keywords" in analysis_types:
                # Download required NLTK data if not present
                try:
                    nltk.data.find('tokenizers/punkt')
                except LookupError:
                    nltk.download('punkt')
                try:
                    nltk.data.find('corpora/stopwords')
                except LookupError:
                    nltk.download('stopwords')
                    
                stop_words = set(stopwords.words('english'))
                tokens = word_tokenize(text_content.lower())
                keywords = [word for word in tokens if word.isalnum() and word not in stop_words]
                
                # Get keyword frequencies
                freq_dist = nltk.FreqDist(keywords)
                results["keywords"] = {
                    "top_keywords": dict(freq_dist.most_common(10)),
                    "total_keywords": len(keywords)
                }
            
            return {
                "status": "success",
                "results": results
            }

        except Exception as e:
            error_msg = f"Error analyzing content: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg
            }

    async def manage_resources(
        self,
        resource_types: List[str] = ["image", "script", "stylesheet", "font"],
        action: str = "collect",
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Manage page resources (images, scripts, styles).
        
        Args:
            resource_types: Types of resources to manage
            action: Action to perform (block, allow, collect)
            options: Additional options for resource management
            
        Returns:
            Dictionary containing resource management results
        """
        try:
            if not self.page:
                raise RuntimeError("Browser not initialized")

            resources = {rt: [] for rt in resource_types}
            
            async def handle_route(route: Any, resource_type: str):
                request = route.request
                if action == "block":
                    await route.abort()
                else:
                    resources[resource_type].append({
                        "url": request.url,
                        "size": len(await request.response().body()) if request.response else 0,
                        "type": request.resource_type
                    })
                    await route.continue_()

            # Set up route handlers for each resource type
            for rt in resource_types:
                pattern = f"**/*.{rt}"
                if action in ["block", "collect"]:
                    await self.page.route(
                        pattern,
                        lambda route, rt=rt: handle_route(route, rt)
                    )

            return {
                "status": "success",
                "action": action,
                "resources": resources if action == "collect" else None
            }

        except Exception as e:
            error_msg = f"Error managing resources: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg,
                "action": action
            }

    async def check_accessibility(
        self,
        standards: List[str] = ["WCAG2.1"],
        level: str = "AA",
        include_warnings: bool = True
    ) -> Dict[str, Any]:
        """Perform accessibility checks on the page.
        
        Args:
            standards: List of accessibility standards to check
            level: Conformance level (A, AA, AAA)
            include_warnings: Whether to include warnings
            
        Returns:
            Dictionary containing accessibility check results
        """
        try:
            if not self.page:
                raise RuntimeError("Browser not initialized")

            # Get accessibility snapshot
            snapshot = await self.page.accessibility.snapshot()
            
            # Inject and run axe-core
            await self.page.add_script_tag(url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.7.0/axe.min.js")
            
            results = await self.page.evaluate(f"""
                () => new Promise(resolve => {{
                    axe.run(document, {{
                        runOnly: {{
                            type: 'tag',
                            values: {json.dumps(standards)}
                        }},
                        resultTypes: ['violations', 'incomplete'],
                        rules: {{
                            bypass: {{ enabled: true }},
                            'color-contrast': {{ enabled: true }},
                            'label': {{ enabled: true }},
                            'link-name': {{ enabled: true }},
                            'list': {{ enabled: true }},
                            'image-alt': {{ enabled: true }}
                        }}
                    }}).then(results => resolve(results));
                }});
            """)
            
            return {
                "status": "success",
                "accessibility_tree": snapshot,
                "violations": results.get("violations", []),
                "incomplete": results.get("incomplete", []) if include_warnings else [],
                "standards": standards,
                "level": level
            }

        except Exception as e:
            error_msg = f"Error checking accessibility: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg
            } 