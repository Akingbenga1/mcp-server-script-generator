import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Set
import re
import json

from .models import WebsiteAnalysis, WebsitePage

logger = logging.getLogger(__name__)

class WebsiteAnalyzer:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.visited_urls: Set[str] = set()
        self.max_pages = 10  # Limit pages to analyze
        logger.info("WebsiteAnalyzer initialized with max_pages=%d", self.max_pages)
        
    async def analyze(self, url: str) -> WebsiteAnalysis:
        """Analyze a website and extract its structure"""
        logger.info(f"Starting analysis of {url}")
        
        # Normalize URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            logger.info(f"Normalized URL to: {url}")
            
        self.visited_urls.clear()
        
        # Get main page
        logger.info("Fetching main page...")
        main_page = await self._fetch_page(url)
        if not main_page:
            raise Exception(f"Could not fetch main page: {url}")
            
        # Extract basic info
        title = main_page.title
        description = ''  # WebsitePage doesn't have description field
        logger.info(f"Extracted title: '{title}'")
        
        # Analyze pages
        pages = [main_page]
        logger.info("Starting page crawling...")
        await self._crawl_pages(url, pages)
        logger.info(f"Crawled {len(pages)} pages total")
        
        # Extract forms and API endpoints
        logger.info("Extracting forms...")
        forms = self._extract_forms(pages)
        logger.info(f"Found {len(forms)} forms")
        
        logger.info("Extracting API endpoints...")
        api_endpoints = self._extract_api_endpoints(pages)
        logger.info(f"Found {len(api_endpoints)} potential API endpoints")
        
        # Extract external resources
        logger.info("Extracting JavaScript files...")
        javascript_files = self._extract_javascript_files(pages)
        logger.info(f"Found {len(javascript_files)} JavaScript files")
        
        logger.info("Extracting CSS files...")
        css_files = self._extract_css_files(pages)
        logger.info(f"Found {len(css_files)} CSS files")
        
        logger.info("Extracting external APIs...")
        external_apis = self._extract_external_apis(pages)
        logger.info(f"Found {len(external_apis)} external API references")
        
        logger.info("Analysis completed successfully")
        return WebsiteAnalysis(
            url=url,
            title=title,
            description=description,
            pages=pages,
            forms=forms,
            api_endpoints=api_endpoints,
            javascript_files=javascript_files,
            css_files=css_files,
            external_apis=external_apis
        )
    
    async def _fetch_page(self, url: str) -> WebsitePage:
        """Fetch and parse a single page"""
        logger.debug(f"Fetching page: {url}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    logger.debug(f"Response status for {url}: {response.status}")
                    if response.status != 200:
                        logger.warning(f"Failed to fetch {url}, status: {response.status}")
                        return None
                        
                    html = await response.text()
                    logger.debug(f"Fetched {len(html)} characters from {url}")
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract title
                    title_tag = soup.find('title')
                    title = title_tag.get_text().strip() if title_tag else ''
                    logger.debug(f"Extracted title: '{title}'")
                    
                    # Extract description
                    desc_tag = soup.find('meta', attrs={'name': 'description'})
                    description = desc_tag.get('content', '') if desc_tag else ''
                    
                    # Extract forms
                    forms = self._parse_forms(soup, url)
                    logger.debug(f"Found {len(forms)} forms on {url}")
                    
                    # Extract links
                    links = []
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        full_url = urljoin(url, href)
                        if self._is_same_domain(url, full_url):
                            links.append(full_url)
                    logger.debug(f"Found {len(links)} internal links on {url}")
                    
                    # Extract scripts and stylesheets
                    scripts = []
                    for script in soup.find_all('script', src=True):
                        scripts.append(urljoin(url, script['src']))
                    logger.debug(f"Found {len(scripts)} script tags on {url}")
                    
                    stylesheets = []
                    for link in soup.find_all('link', rel='stylesheet'):
                        if link.get('href'):
                            stylesheets.append(urljoin(url, link['href']))
                    logger.debug(f"Found {len(stylesheets)} stylesheet links on {url}")
                    
                    page = WebsitePage(
                        url=url,
                        title=title,
                        content=html,
                        forms=forms,
                        links=links,
                        scripts=scripts,
                        stylesheets=stylesheets
                    )
                    logger.debug(f"Successfully parsed page: {url}")
                    return page
                    
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    async def _crawl_pages(self, base_url: str, pages: List[WebsitePage]):
        """Crawl additional pages from the main page with intelligent link discovery"""
        if len(pages) >= self.max_pages:
            return
            
        main_page = pages[0]
        
        # Intelligent link discovery - prioritize API-related links
        priority_links = self._find_priority_links(main_page.links)
        logger.info(f"Found {len(priority_links)} priority links out of {len(main_page.links)} total links")
        
        # Also include some regular links for broader coverage
        regular_links = [link for link in main_page.links if link not in priority_links][:3]
        urls_to_visit = priority_links + regular_links
        
        logger.info(f"Will visit {len(urls_to_visit)} pages: {len(priority_links)} priority + {len(regular_links)} regular")
        
        for url in urls_to_visit:
            if url in self.visited_urls or len(pages) >= self.max_pages:
                continue
                
            logger.debug(f"Crawling page: {url}")
            self.visited_urls.add(url)
            page = await self._fetch_page(url)
            if page:
                pages.append(page)
                logger.info(f"Successfully crawled page {len(pages)}: {url}")
            else:
                logger.warning(f"Failed to crawl page: {url}")
    
    def _find_priority_links(self, links: List[str]) -> List[str]:
        """Find priority links that are likely to contain API information"""
        priority_keywords = [
            'api', 'docs', 'documentation', 'developers', 'developer',
            'get-started', 'getting-started', 'start', 'guide', 'tutorial',
            'reference', 'swagger', 'openapi', 'rest', 'graphql',
            'sdk', 'client', 'library', 'integration', 'webhook',
            'auth', 'authentication', 'oauth', 'jwt', 'token',
            'endpoint', 'endpoints', 'v1', 'v2', 'v3', 'beta'
        ]
        
        priority_links = []
        
        for link in links:
            link_lower = link.lower()
            
            # Check if link contains priority keywords
            for keyword in priority_keywords:
                if keyword in link_lower:
                    priority_links.append(link)
                    logger.debug(f"Found priority link '{link}' (keyword: {keyword})")
                    break
            
            # Also check for common API documentation patterns
            if any(pattern in link_lower for pattern in ['/api/', '/docs/', '/developer/', '/guide/']):
                if link not in priority_links:
                    priority_links.append(link)
                    logger.debug(f"Found priority link '{link}' (pattern match)")
        
        # Limit to top 10 priority links to avoid overwhelming
        return priority_links[:10]
    
    def _parse_forms(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """Parse forms from HTML"""
        forms = []
        for form in soup.find_all('form'):
            form_data = {
                'action': urljoin(base_url, form.get('action', '')),
                'method': form.get('method', 'GET').upper(),
                'fields': []
            }
            
            # Extract form fields
            for input_tag in form.find_all(['input', 'textarea', 'select']):
                field = {
                    'name': input_tag.get('name', ''),
                    'type': input_tag.get('type', 'text'),
                    'required': input_tag.get('required') is not None,
                    'placeholder': input_tag.get('placeholder', '')
                }
                
                if input_tag.name == 'select':
                    field['options'] = [
                        option.get('value', option.get_text())
                        for option in input_tag.find_all('option')
                    ]
                
                form_data['fields'].append(field)
            
            forms.append(form_data)
        
        return forms
    
    def _extract_forms(self, pages: List[WebsitePage]) -> List[Dict[str, Any]]:
        """Extract all forms from pages"""
        all_forms = []
        for page in pages:
            all_forms.extend(page.forms)
        return all_forms
    
    def _extract_api_endpoints(self, pages: List[WebsitePage]) -> List[str]:
        """Extract potential API endpoints from JavaScript and forms"""
        endpoints = set()
        
        logger.info(f"Starting API endpoint extraction from {len(pages)} pages")
        
        for i, page in enumerate(pages):
            logger.debug(f"Analyzing page {i+1}/{len(pages)}: {page.url}")
            
            # Look for API endpoints in JavaScript
            logger.debug(f"Checking {len(page.scripts)} script URLs for API patterns")
            for script_url in page.scripts:
                logger.debug(f"Checking script URL: {script_url}")
                if 'api' in script_url.lower() or 'ajax' in script_url.lower():
                    logger.info(f"Found potential API endpoint in script: {script_url}")
                    endpoints.add(script_url)
            
            # Look for API patterns in forms
            logger.debug(f"Checking {len(page.forms)} forms for API patterns")
            for j, form in enumerate(page.forms):
                action = form.get('action', '')
                logger.debug(f"Checking form {j+1} action: {action}")
                if any(keyword in action.lower() for keyword in ['api', 'ajax', 'json', 'rest']):
                    logger.info(f"Found potential API endpoint in form action: {action}")
                    endpoints.add(action)
            
            # Look for API patterns in page content
            logger.debug("Searching page content for API patterns")
            api_patterns = [
                r'https?://[^/]+/api/[^\s"\'<>]+',
                r'https?://api\.[^/]+/[^\s"\'<>]+',
                r'https?://[^/]+/rest/[^\s"\'<>]+',
                r'https?://[^/]+/v\d+/[^\s"\'<>]+',
                r'["\'](/api/[^"\']+)["\']',
                r'["\'](/rest/[^"\']+)["\']',
                r'["\'](/v\d+/[^"\']+)["\']'
            ]
            
            for pattern in api_patterns:
                matches = re.findall(pattern, page.content)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0]
                    full_url = urljoin(page.url, match)
                    logger.info(f"Found potential API endpoint in content: {full_url}")
                    endpoints.add(full_url)
        
        result = list(endpoints)
        logger.info(f"Extracted {len(result)} potential API endpoints: {result}")
        return result
    
    def _extract_javascript_files(self, pages: List[WebsitePage]) -> List[str]:
        """Extract JavaScript file URLs"""
        js_files = set()
        for page in pages:
            js_files.update(page.scripts)
        return list(js_files)
    
    def _extract_css_files(self, pages: List[WebsitePage]) -> List[str]:
        """Extract CSS file URLs"""
        css_files = set()
        for page in pages:
            css_files.update(page.stylesheets)
        return list(css_files)
    
    def _extract_external_apis(self, pages: List[WebsitePage]) -> List[str]:
        """Extract external API references"""
        external_apis = set()
        
        for page in pages:
            # Look for common API patterns in content
            api_patterns = [
                r'https?://[^/]+/api/[^\s"\'<>]+',
                r'https?://api\.[^/]+/[^\s"\'<>]+',
                r'https?://[^/]+/rest/[^\s"\'<>]+',
                r'https?://[^/]+/v\d+/[^\s"\'<>]+'
            ]
            
            for pattern in api_patterns:
                matches = re.findall(pattern, page.content)
                external_apis.update(matches)
        
        return list(external_apis)
    
    def _is_same_domain(self, url1: str, url2: str) -> bool:
        """Check if two URLs are from the same domain"""
        try:
            domain1 = urlparse(url1).netloc
            domain2 = urlparse(url2).netloc
            return domain1 == domain2
        except:
            return False
