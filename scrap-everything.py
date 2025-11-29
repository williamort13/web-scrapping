import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
import time
from collections import deque
import hashlib

class RecursiveWebsiteScraper:
    def __init__(self, base_url, output_dir='scraped_website', max_pages=None, delay=0.5):
        self.base_url = base_url
        self.output_dir = output_dir
        self.max_pages = max_pages
        self.delay = delay  # Delay between requests to be respectful
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Track visited URLs and downloaded resources
        self.visited_urls = set()
        self.downloaded_resources = {}  # Maps URL -> local path
        
        # Parse base domain
        parsed_base = urlparse(base_url)
        self.base_domain = parsed_base.netloc
        self.base_scheme = parsed_base.scheme
        
        # Create output directories
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(f'{output_dir}/assets/css', exist_ok=True)
        os.makedirs(f'{output_dir}/assets/js', exist_ok=True)
        os.makedirs(f'{output_dir}/assets/images', exist_ok=True)
        os.makedirs(f'{output_dir}/assets/fonts', exist_ok=True)
        os.makedirs(f'{output_dir}/assets/other', exist_ok=True)
        
    def is_same_domain(self, url):
        """Check if URL belongs to the same domain"""
        parsed = urlparse(url)
        return parsed.netloc == self.base_domain or parsed.netloc == ''
    
    def normalize_url(self, url):
        """Normalize URL for comparison"""
        parsed = urlparse(url)
        # Remove fragment
        normalized = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            ''  # Remove fragment
        ))
        # Remove trailing slash for consistency (except for root)
        if normalized.endswith('/') and normalized != f"{self.base_scheme}://{self.base_domain}/":
            normalized = normalized[:-1]
        return normalized
    
    def get_url_hash(self, url):
        """Generate a short hash for URL to use in filename"""
        return hashlib.md5(url.encode()).hexdigest()[:8]
    
    def download_file(self, url, local_path):
        """Download a file from URL to local path"""
        try:
            print(f"Downloading: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Create directory if needed
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Write file
            with open(local_path, 'wb') as f:
                f.write(response.content)
            print(f"Saved: {local_path}")
            return True
        except Exception as e:
            print(f"Error downloading {url}: {str(e)}")
            return False
    
    def get_local_path(self, url, resource_type='other'):
        """Generate unique local path for a resource"""
        # If already downloaded, return existing path
        if url in self.downloaded_resources:
            return self.downloaded_resources[url]
        
        parsed = urlparse(url)
        
        if resource_type == 'html':
            # For HTML pages, preserve URL structure
            path = parsed.path.strip('/')
            
            if not path or path.endswith('/'):
                # Root or directory path -> index.html
                local_path = os.path.join(self.output_dir, path, 'index.html')
            elif not os.path.splitext(path)[1]:
                # No extension, treat as directory
                local_path = os.path.join(self.output_dir, path, 'index.html')
            else:
                # Has extension
                if not path.endswith('.html') and not path.endswith('.htm'):
                    local_path = os.path.join(self.output_dir, path + '.html')
                else:
                    local_path = os.path.join(self.output_dir, path)
            
            # Handle query strings with hash to make unique
            if parsed.query:
                url_hash = self.get_url_hash(url)
                dir_path = os.path.dirname(local_path)
                base_name = os.path.splitext(os.path.basename(local_path))[0]
                local_path = os.path.join(dir_path, f"{base_name}_{url_hash}.html")
        else:
            # For assets (CSS, JS, images, etc.)
            filename = os.path.basename(parsed.path) or 'resource'
            filename = re.sub(r'[<>:"|?*]', '_', filename)
            
            # Get file extension
            name, ext = os.path.splitext(filename)
            if not ext:
                # Determine extension from resource type
                if resource_type == 'css':
                    ext = '.css'
                elif resource_type == 'js':
                    ext = '.js'
            
            ext_lower = ext.lower()
            
            # Determine subdirectory
            if resource_type == 'css' or ext_lower == '.css':
                subdir = 'assets/css'
            elif resource_type == 'js' or ext_lower == '.js':
                subdir = 'assets/js'
            elif ext_lower in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.ico']:
                subdir = 'assets/images'
            elif ext_lower in ['.woff', '.woff2', '.ttf', '.eot', '.otf']:
                subdir = 'assets/fonts'
            else:
                subdir = 'assets/other'
            
            # Create unique filename with hash (especially important for query strings)
            url_hash = self.get_url_hash(url)
            unique_filename = f"{name}_{url_hash}{ext}"
            
            local_path = os.path.join(self.output_dir, subdir, unique_filename)
        
        return local_path
    
    def process_css(self, css_content, css_url, css_local_path):
        """Process CSS and download referenced resources"""
        url_pattern = r'url\([\'"]?([^\'")\s]+)[\'"]?\)'
        
        def replace_url(match):
            resource_url = match.group(1)
            if resource_url.startswith('data:'):
                return match.group(0)
            
            abs_url = urljoin(css_url, resource_url)
            
            # Check if already downloaded
            if abs_url in self.downloaded_resources:
                local_path = self.downloaded_resources[abs_url]
            else:
                local_path = self.get_local_path(abs_url)
                if self.download_file(abs_url, local_path):
                    self.downloaded_resources[abs_url] = local_path
                else:
                    # If download failed, return original
                    return match.group(0)
            
            # Calculate relative path from CSS file location
            rel_path = os.path.relpath(local_path, os.path.dirname(css_local_path))
            # Normalize path separators for web
            rel_path = rel_path.replace('\\', '/')
            return f'url({rel_path})'
        
        return re.sub(url_pattern, replace_url, css_content)
    
    def extract_links(self, soup, current_url):
        """Extract all links from a page"""
        links = set()
        
        for tag in soup.find_all('a', href=True):
            href = tag['href']
            # Skip anchors, javascript, and mailto links
            if href.startswith('#') or href.startswith('javascript:') or href.startswith('mailto:'):
                continue
            
            abs_url = urljoin(current_url, href)
            normalized_url = self.normalize_url(abs_url)
            
            # Only add if same domain
            if self.is_same_domain(normalized_url):
                links.add(normalized_url)
        
        return links
    
    def process_page(self, url):
        """Process a single HTML page"""
        print(f"\n{'='*60}")
        print(f"Processing page: {url}")
        print(f"{'='*60}")
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
        except Exception as e:
            print(f"Error fetching page: {str(e)}")
            return set()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract links for crawling
        new_links = self.extract_links(soup, url)
        
        # Get the local path for this HTML page (needed for relative paths)
        page_local_path = self.get_local_path(url, 'html')
        page_dir = os.path.dirname(page_local_path)
        
        # Download CSS files
        print("\n--- Processing CSS files ---")
        for link in soup.find_all('link', rel='stylesheet'):
            if link.get('href'):
                css_url = urljoin(url, link['href'])
                
                if css_url in self.downloaded_resources:
                    local_path = self.downloaded_resources[css_url]
                else:
                    local_path = self.get_local_path(css_url, 'css')
                    
                    if self.download_file(css_url, local_path):
                        # Process CSS content for embedded resources
                        try:
                            with open(local_path, 'r', encoding='utf-8', errors='ignore') as f:
                                css_content = f.read()
                            
                            processed_css = self.process_css(css_content, css_url, local_path)
                            
                            with open(local_path, 'w', encoding='utf-8') as f:
                                f.write(processed_css)
                        except Exception as e:
                            print(f"Error processing CSS: {str(e)}")
                        
                        self.downloaded_resources[css_url] = local_path
                
                # Update link href with relative path
                rel_path = os.path.relpath(local_path, page_dir).replace('\\', '/')
                link['href'] = rel_path
        
        # Download JavaScript files
        print("\n--- Processing JavaScript files ---")
        for script in soup.find_all('script', src=True):
            js_url = urljoin(url, script['src'])
            
            if js_url in self.downloaded_resources:
                local_path = self.downloaded_resources[js_url]
            else:
                local_path = self.get_local_path(js_url, 'js')
                
                if self.download_file(js_url, local_path):
                    self.downloaded_resources[js_url] = local_path
            
            rel_path = os.path.relpath(local_path, page_dir).replace('\\', '/')
            script['src'] = rel_path
        
        # Download images
        print("\n--- Processing images ---")
        for img in soup.find_all('img', src=True):
            img_url = urljoin(url, img['src'])
            
            if img_url in self.downloaded_resources:
                local_path = self.downloaded_resources[img_url]
            else:
                local_path = self.get_local_path(img_url, 'images')
                
                if self.download_file(img_url, local_path):
                    self.downloaded_resources[img_url] = local_path
            
            rel_path = os.path.relpath(local_path, page_dir).replace('\\', '/')
            img['src'] = rel_path
        
        # Process srcset for responsive images
        for img in soup.find_all('img', srcset=True):
            srcset_parts = []
            for part in img['srcset'].split(','):
                part = part.strip()
                if not part:
                    continue
                
                # Split URL and descriptor (e.g., "image.jpg 2x")
                split_part = part.rsplit(' ', 1)
                img_url_part = split_part[0]
                descriptor = split_part[1] if len(split_part) > 1 else ''
                
                img_url = urljoin(url, img_url_part)
                
                if img_url in self.downloaded_resources:
                    local_path = self.downloaded_resources[img_url]
                else:
                    local_path = self.get_local_path(img_url, 'images')
                    if self.download_file(img_url, local_path):
                        self.downloaded_resources[img_url] = local_path
                
                rel_path = os.path.relpath(local_path, page_dir).replace('\\', '/')
                srcset_parts.append(f"{rel_path} {descriptor}".strip())
            
            if srcset_parts:
                img['srcset'] = ', '.join(srcset_parts)
        
        # Download favicon
        print("\n--- Processing favicon ---")
        for link in soup.find_all('link', rel=['icon', 'shortcut icon']):
            if link.get('href'):
                icon_url = urljoin(url, link['href'])
                
                if icon_url in self.downloaded_resources:
                    local_path = self.downloaded_resources[icon_url]
                else:
                    local_path = self.get_local_path(icon_url, 'images')
                    
                    if self.download_file(icon_url, local_path):
                        self.downloaded_resources[icon_url] = local_path
                
                rel_path = os.path.relpath(local_path, page_dir).replace('\\', '/')
                link['href'] = rel_path
        
        # Update internal links
        for tag in soup.find_all('a', href=True):
            href = tag['href']
            if not href.startswith('#') and not href.startswith('javascript:') and not href.startswith('mailto:'):
                abs_url = urljoin(url, href)
                normalized_url = self.normalize_url(abs_url)
                
                if self.is_same_domain(normalized_url):
                    target_local_path = self.get_local_path(normalized_url, 'html')
                    rel_path = os.path.relpath(target_local_path, page_dir).replace('\\', '/')
                    tag['href'] = rel_path
        
        # Save HTML file
        os.makedirs(os.path.dirname(page_local_path), exist_ok=True)
        
        with open(page_local_path, 'w', encoding='utf-8') as f:
            f.write(str(soup.prettify()))
        
        print(f"\nSaved page to: {page_local_path}")
        self.downloaded_resources[url] = page_local_path
        
        return new_links
    
    def scrape(self):
        """Main scraping function with BFS crawling"""
        print(f"Starting recursive scrape of: {self.base_url}")
        print(f"Max pages: {self.max_pages if self.max_pages else 'unlimited'}")
        
        # Queue for BFS
        queue = deque([self.normalize_url(self.base_url)])
        
        while queue and (self.max_pages is None or len(self.visited_urls) < self.max_pages):
            current_url = queue.popleft()
            
            # Skip if already visited
            if current_url in self.visited_urls:
                continue
            
            # Mark as visited
            self.visited_urls.add(current_url)
            
            # Process page and get new links
            new_links = self.process_page(current_url)
            
            # Add new links to queue
            for link in new_links:
                if link not in self.visited_urls:
                    queue.append(link)
            
            # Progress update
            print(f"\nProgress: {len(self.visited_urls)} pages scraped, {len(queue)} in queue")
            
            # Be respectful - delay between requests
            if queue:
                time.sleep(self.delay)
        
        # Create index page that links to all scraped pages
        self.create_sitemap()
        
        print(f"\n{'='*60}")
        print(f"Scraping complete!")
        print(f"{'='*60}")
        print(f"Total pages scraped: {len(self.visited_urls)}")
        print(f"Total resources downloaded: {len(self.downloaded_resources)}")
        print(f"Files saved to: {self.output_dir}")
        
        # Find and display the main index.html location
        main_index = os.path.join(self.output_dir, 'index.html')
        if os.path.exists(main_index):
            print(f"Main page: {main_index}")
        
        print(f"Site map: {os.path.join(self.output_dir, 'sitemap.html')}")
        
        return True
    
    def create_sitemap(self):
        """Create a sitemap page listing all scraped pages"""
        sitemap_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Site Map - Scraped Website</title>
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; 
            margin: 0; 
            padding: 40px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{ 
            max-width: 1200px; 
            margin: 0 auto; 
            background: white; 
            padding: 40px; 
            border-radius: 12px; 
            box-shadow: 0 20px 60px rgba(0,0,0,0.3); 
        }}
        h1 {{ 
            color: #2d3748; 
            border-bottom: 4px solid #667eea; 
            padding-bottom: 15px; 
            margin-top: 0;
            font-size: 2.5em;
        }}
        h2 {{
            color: #4a5568;
            margin-top: 40px;
            font-size: 1.8em;
        }}
        .stats {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px; 
            border-radius: 8px; 
            margin: 20px 0; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .stats strong {{ 
            display: block;
            font-size: 1.2em;
            margin-bottom: 10px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .stat-item {{
            background: rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 6px;
        }}
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            display: block;
        }}
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        ul {{ 
            line-height: 2; 
            padding-left: 0;
            list-style: none;
        }}
        li {{
            padding: 12px;
            margin: 8px 0;
            background: #f7fafc;
            border-radius: 6px;
            transition: all 0.2s;
        }}
        li:hover {{
            background: #edf2f7;
            transform: translateX(5px);
        }}
        a {{ 
            color: #667eea; 
            text-decoration: none; 
            font-weight: 500;
        }}
        a:hover {{ 
            text-decoration: underline; 
            color: #764ba2;
        }}
        .url {{ 
            font-size: 0.85em; 
            color: #718096; 
            display: block;
            margin-top: 5px;
            font-family: 'Courier New', monospace;
        }}
        .timestamp {{
            text-align: center;
            color: #718096;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e2e8f0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📄 Site Map</h1>
        <div class="stats">
            <strong>Scraping Statistics</strong>
            <div class="stats-grid">
                <div class="stat-item">
                    <span class="stat-number">{len(self.visited_urls)}</span>
                    <span class="stat-label">Pages</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">{len(self.downloaded_resources)}</span>
                    <span class="stat-label">Total Resources</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">{len([r for r in self.downloaded_resources.keys() if r.endswith(('.css', 'css'))])}</span>
                    <span class="stat-label">CSS Files</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">{len([r for r in self.downloaded_resources.keys() if r.endswith(('.js', 'js'))])}</span>
                    <span class="stat-label">JS Files</span>
                </div>
            </div>
            <div style="margin-top: 15px;">
                <strong>Base URL:</strong> <a href="{self.base_url}" target="_blank" style="color: white; text-decoration: underline;">{self.base_url}</a>
            </div>
        </div>
        
        <h2>📑 All Pages</h2>
        <ul>
"""
        
        for url in sorted(self.visited_urls):
            local_path = self.downloaded_resources.get(url, '')
            if local_path:
                rel_path = os.path.relpath(local_path, self.output_dir).replace('\\', '/')
                # Get page name from URL
                page_name = url.replace(self.base_url, '') or '/ (Home)'
                sitemap_html += f'            <li>\n                <a href="{rel_path}">{page_name}</a>\n                <span class="url">{url}</span>\n            </li>\n'
        
        sitemap_html += f"""        </ul>
        
        <div class="timestamp">
            Generated by Website Scraper
        </div>
    </div>
</body>
</html>"""
        
        with open(os.path.join(self.output_dir, 'sitemap.html'), 'w', encoding='utf-8') as f:
            f.write(sitemap_html)

if __name__ == '__main__':
    # Configuration
    TARGET_URL = 'https://' # <- put your scrap target url here
    OUTPUT_DIR = 'scrap-result' # <- this is the result folder name change according your needs
    MAX_PAGES = 100  # Set to None for unlimited, or a number to limit
    DELAY = 0.5  # Delay between requests in seconds
    
    # Create scraper and run
    scraper = RecursiveWebsiteScraper(
        TARGET_URL, 
        OUTPUT_DIR, 
        max_pages=MAX_PAGES,
        delay=DELAY
    )
    scraper.scrape()