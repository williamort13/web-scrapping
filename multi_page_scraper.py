import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import hashlib
import time

class MultiPageScraper:
    def __init__(self, target_urls, output_dir='scraped_website', consolidate_assets=True, delay=1.0):
        """
        Scrape multiple specific pages from a website
        
        Args:
            target_urls: List of URLs to scrape
            output_dir: Output directory
            consolidate_assets: Consolidate CSS/JS across all pages
            delay: Delay between page requests (seconds)
        """
        self.target_urls = target_urls if isinstance(target_urls, list) else [target_urls]
        self.output_dir = output_dir
        self.consolidate_assets = consolidate_assets
        self.delay = delay
        
        # Get base URL from first target
        self.base_url = self.target_urls[0] if self.target_urls else ''
        parsed = urlparse(self.base_url)
        self.base_domain = f"{parsed.scheme}://{parsed.netloc}"
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'th-TH,th;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        })
        
        # Set Thailand cookies
        domain = parsed.netloc
        self.session.cookies.set('language', 'th', domain=domain)
        self.session.cookies.set('lang', 'th', domain=domain)
        self.session.cookies.set('locale', 'th', domain=domain)
        self.session.cookies.set('country', 'TH', domain=domain)
        self.session.cookies.set('geo', 'TH', domain=domain)
        
        # Create output directories
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(f'{output_dir}/css', exist_ok=True)
        os.makedirs(f'{output_dir}/js', exist_ok=True)
        os.makedirs(f'{output_dir}/images', exist_ok=True)
        os.makedirs(f'{output_dir}/fonts', exist_ok=True)
        os.makedirs(f'{output_dir}/other', exist_ok=True)
        
        # Track downloaded files
        self.downloaded_files = {}
        
        # For consolidation
        self.all_css_content = []
        self.all_js_content = []
        self.css_urls = set()
        self.js_urls = set()
    
    def normalize_filename(self, filename):
        """Remove hash/version numbers from filename"""
        name, ext = os.path.splitext(filename)
        # Remove hash patterns
        name = re.sub(r'[_-][a-f0-9]{6,}$', '', name)
        name = re.sub(r'\?v=[^&]*', '', name)
        return f"{name}{ext}"
    
    def get_page_filename(self, url):
        """Generate HTML filename from URL"""
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        
        if not path or path == '':
            return 'index.html'
        
        # Extract the last meaningful part of the path
        # e.g., /desktop/about-us -> about-us.html
        parts = path.split('/')
        filename = parts[-1] if parts else 'page'
        
        # Remove file extension if present
        if '.' in filename:
            filename = os.path.splitext(filename)[0]
        
        # Clean filename
        filename = re.sub(r'[^a-zA-Z0-9_-]', '-', filename)
        
        return f"{filename}.html"
    
    def download_file(self, url, local_path):
        """Download a file from URL to local path"""
        try:
            print(f"  Downloading: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            with open(local_path, 'wb') as f:
                f.write(response.content)
            print(f"  ✓ Saved: {local_path}")
            return True
        except Exception as e:
            print(f"  ✗ Error downloading {url}: {str(e)}")
            return False
    
    def get_local_path(self, url, resource_type='other'):
        """Generate unique local path for a resource"""
        if url in self.downloaded_files:
            return self.downloaded_files[url]
        
        parsed = urlparse(url)
        base_filename = os.path.basename(parsed.path) or 'index.html'
        
        name, ext = os.path.splitext(base_filename)
        if not ext:
            if resource_type == 'css':
                ext = '.css'
            elif resource_type == 'js':
                ext = '.js'
            else:
                ext = '.html'
        
        ext_lower = ext.lower()
        
        if resource_type == 'css' or ext_lower == '.css':
            subdir = 'css'
        elif resource_type == 'js' or ext_lower == '.js':
            subdir = 'js'
        elif ext_lower in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.ico']:
            subdir = 'images'
        elif ext_lower in ['.woff', '.woff2', '.ttf', '.eot', '.otf']:
            subdir = 'fonts'
        else:
            subdir = 'other'
        
        # Normalize filename for images
        if subdir == 'images':
            unique_filename = self.normalize_filename(base_filename)
            counter = 1
            test_filename = unique_filename
            while any(path.endswith(test_filename) for path in self.downloaded_files.values()):
                name_part, ext_part = os.path.splitext(unique_filename)
                test_filename = f"{name_part}_{counter}{ext_part}"
                counter += 1
            unique_filename = test_filename
        elif self.consolidate_assets and (subdir == 'css' or subdir == 'js'):
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            unique_filename = f"{name}_{url_hash}{ext}"
        else:
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            unique_filename = f"{name}_{url_hash}{ext}"
        
        local_path = os.path.join(self.output_dir, subdir, unique_filename)
        self.downloaded_files[url] = local_path
        
        return local_path
    
    def process_css(self, css_content, css_url):
        """Process CSS and download referenced resources"""
        url_pattern = r'url\([\'"]?([^\'")\s]+)[\'"]?\)'
        
        def replace_url(match):
            resource_url = match.group(1)
            if resource_url.startswith('data:'):
                return match.group(0)
            
            abs_url = urljoin(css_url, resource_url)
            local_path = self.get_local_path(abs_url)
            
            if abs_url not in self.downloaded_files or not os.path.exists(local_path):
                self.download_file(abs_url, local_path)
            
            css_local_path = self.downloaded_files.get(css_url, css_url)
            rel_path = os.path.relpath(local_path, os.path.dirname(css_local_path))
            return f'url({rel_path})'
        
        return re.sub(url_pattern, replace_url, css_content)
    
    def process_images(self, soup, base_url):
        """Process all image tags"""
        print("  Processing images...")
        
        image_selectors = [
            ('img', 'src'),
            ('amp-img', 'src'),
            ('amp-anim', 'src'),
            ('source', 'src'),
            ('source', 'srcset'),
            ('img', 'data-src'),
            ('img', 'data-lazy-src'),
        ]
        
        for tag_name, attr_name in image_selectors:
            for tag in soup.find_all(tag_name):
                if tag.get(attr_name):
                    if attr_name == 'srcset':
                        self.process_srcset(tag, attr_name, base_url)
                    else:
                        img_url = urljoin(base_url, tag[attr_name])
                        local_path = self.get_local_path(img_url, 'images')
                        
                        if self.download_file(img_url, local_path):
                            tag[attr_name] = os.path.relpath(local_path, self.output_dir)
        
        for img in soup.find_all('img', srcset=True):
            self.process_srcset(img, 'srcset', base_url)
    
    def process_srcset(self, tag, attr_name, base_url):
        """Process srcset attribute"""
        srcset_parts = []
        for part in tag[attr_name].split(','):
            part = part.strip()
            if not part:
                continue
            
            split_part = part.rsplit(' ', 1)
            img_url_part = split_part[0]
            descriptor = split_part[1] if len(split_part) > 1 else ''
            
            img_url = urljoin(base_url, img_url_part)
            local_path = self.get_local_path(img_url, 'images')
            
            if self.download_file(img_url, local_path):
                rel_path = os.path.relpath(local_path, self.output_dir)
                srcset_parts.append(f"{rel_path} {descriptor}".strip())
        
        if srcset_parts:
            tag[attr_name] = ', '.join(srcset_parts)
    
    def scrape_page(self, url, page_filename):
        """Scrape a single page"""
        print(f"\n{'='*60}")
        print(f"Scraping: {url}")
        print(f"Output: {page_filename}")
        print(f"{'='*60}")
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
        except Exception as e:
            print(f"✗ Error fetching page: {str(e)}")
            return False
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Download CSS files
        print("\n--- Processing CSS ---")
        for link in soup.find_all('link', rel='stylesheet'):
            if link.get('href'):
                css_url = urljoin(url, link['href'])
                
                # Skip if already processed
                if css_url in self.css_urls:
                    local_path = self.downloaded_files.get(css_url)
                else:
                    local_path = self.get_local_path(css_url, 'css')
                    
                    if self.download_file(css_url, local_path):
                        try:
                            with open(local_path, 'r', encoding='utf-8', errors='ignore') as f:
                                css_content = f.read()
                            
                            processed_css = self.process_css(css_content, css_url)
                            
                            if self.consolidate_assets:
                                self.all_css_content.append(f"\n/* Source: {css_url} */\n{processed_css}")
                                self.css_urls.add(css_url)
                            else:
                                with open(local_path, 'w', encoding='utf-8') as f:
                                    f.write(processed_css)
                        except Exception as e:
                            print(f"  ✗ Error processing CSS: {str(e)}")
                
                # Update href
                if self.consolidate_assets:
                    link['href'] = 'css/all-styles.css'
                else:
                    link['href'] = os.path.relpath(local_path, self.output_dir) if local_path else link['href']
        
        # Remove duplicate CSS links if consolidating
        if self.consolidate_assets:
            css_links = soup.find_all('link', rel='stylesheet')
            if css_links:
                for link in css_links[1:]:
                    link.decompose()
        
        # Download JavaScript files
        print("\n--- Processing JavaScript ---")
        for script in soup.find_all('script', src=True):
            js_url = urljoin(url, script['src'])
            
            # Skip if already processed
            if js_url in self.js_urls:
                local_path = self.downloaded_files.get(js_url)
            else:
                local_path = self.get_local_path(js_url, 'js')
                
                if self.download_file(js_url, local_path):
                    if self.consolidate_assets:
                        try:
                            with open(local_path, 'r', encoding='utf-8', errors='ignore') as f:
                                js_content = f.read()
                            self.all_js_content.append(f"\n/* Source: {js_url} */\n{js_content}")
                            self.js_urls.add(js_url)
                        except Exception as e:
                            print(f"  ✗ Error reading JS: {str(e)}")
            
            # Update src
            if self.consolidate_assets:
                script['src'] = 'js/all-scripts.js'
            else:
                script['src'] = os.path.relpath(local_path, self.output_dir) if local_path else script['src']
        
        # Remove duplicate JS scripts if consolidating
        if self.consolidate_assets:
            js_scripts = soup.find_all('script', src=True)
            if js_scripts:
                for script in js_scripts[1:]:
                    script.decompose()
        
        # Process images
        self.process_images(soup, url)
        
        # Download favicon
        print("\n--- Processing favicon ---")
        for link in soup.find_all('link', rel=['icon', 'shortcut icon']):
            if link.get('href'):
                icon_url = urljoin(url, link['href'])
                local_path = self.get_local_path(icon_url, 'images')
                
                if self.download_file(icon_url, local_path):
                    link['href'] = os.path.relpath(local_path, self.output_dir)
        
        # Process inline styles
        print("\n--- Processing inline styles ---")
        for tag in soup.find_all(style=True):
            style_content = tag['style']
            if 'url(' in style_content:
                url_pattern = r'url\([\'"]?([^\'")\s]+)[\'"]?\)'
                
                def replace_inline_url(match):
                    resource_url = match.group(1)
                    if resource_url.startswith('data:'):
                        return match.group(0)
                    
                    abs_url = urljoin(url, resource_url)
                    local_path = self.get_local_path(abs_url, 'images')
                    
                    if abs_url not in self.downloaded_files or not os.path.exists(local_path):
                        self.download_file(abs_url, local_path)
                    
                    rel_path = os.path.relpath(local_path, self.output_dir)
                    return f'url({rel_path})'
                
                tag['style'] = re.sub(url_pattern, replace_inline_url, style_content)
        
        # Save HTML
        output_html = os.path.join(self.output_dir, page_filename)
        with open(output_html, 'w', encoding='utf-8') as f:
            f.write(str(soup.prettify()))
        
        print(f"\n✓ Saved page: {output_html}")
        return True
    
    def scrape(self):
        """Main scraping function"""
        print(f"{'='*60}")
        print(f"Multi-Page Scraper")
        print(f"{'='*60}")
        print(f"Output directory: {self.output_dir}")
        print(f"Pages to scrape: {len(self.target_urls)}")
        print(f"Consolidate assets: {self.consolidate_assets}")
        print(f"{'='*60}")
        
        success_count = 0
        
        for i, url in enumerate(self.target_urls):
            if i > 0 and self.delay > 0:
                print(f"\nWaiting {self.delay}s before next page...")
                time.sleep(self.delay)
            
            page_filename = self.get_page_filename(url)
            
            if self.scrape_page(url, page_filename):
                success_count += 1
        
        # Create consolidated files if enabled
        if self.consolidate_assets:
            print(f"\n{'='*60}")
            print("Creating consolidated files...")
            print(f"{'='*60}")
            
            if self.all_css_content:
                consolidated_css = os.path.join(self.output_dir, 'css', 'all-styles.css')
                with open(consolidated_css, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(self.all_css_content))
                print(f"✓ Consolidated CSS: {consolidated_css}")
                print(f"  Combined {len(self.css_urls)} CSS files")
            
            if self.all_js_content:
                consolidated_js = os.path.join(self.output_dir, 'js', 'all-scripts.js')
                with open(consolidated_js, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(self.all_js_content))
                print(f"✓ Consolidated JS: {consolidated_js}")
                print(f"  Combined {len(self.js_urls)} JS files")
        
        # Summary
        print(f"\n{'='*60}")
        print(f"Scraping Complete!")
        print(f"{'='*60}")
        print(f"Pages scraped: {success_count}/{len(self.target_urls)}")
        print(f"Total resources: {len(self.downloaded_files)}")
        print(f"Output directory: {self.output_dir}")
        print(f"{'='*60}\n")
        
        return True


if __name__ == '__main__':
    # Configuration
    TARGET_URLS = [
        ''
    ]
    
    OUTPUT_DIR = ''
    
    # Consolidate CSS/JS across all pages (RECOMMENDED)
    CONSOLIDATE_ASSETS = True
    
    # Delay between page requests (seconds) - be respectful to the server
    DELAY = 1.0
    
    # Create scraper and run
    scraper = MultiPageScraper(
        target_urls=TARGET_URLS,
        output_dir=OUTPUT_DIR,
        consolidate_assets=CONSOLIDATE_ASSETS,
        delay=DELAY
    )
    scraper.scrape()
