import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import hashlib
import time

class WebsiteScraper:
    def __init__(self, base_url, output_dir='scraped_website'):
        self.base_url = base_url
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Create output directories
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(f'{output_dir}/css', exist_ok=True)
        os.makedirs(f'{output_dir}/js', exist_ok=True)
        os.makedirs(f'{output_dir}/images', exist_ok=True)
        os.makedirs(f'{output_dir}/fonts', exist_ok=True)
        os.makedirs(f'{output_dir}/other', exist_ok=True)
        
        # Track downloaded files to avoid duplicates
        self.downloaded_files = {}
        
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
        # If we've already downloaded this URL, return the existing path
        if url in self.downloaded_files:
            return self.downloaded_files[url]
        
        parsed = urlparse(url)
        # Get the base filename from URL path
        base_filename = os.path.basename(parsed.path) or 'index.html'
        
        # Get file extension
        name, ext = os.path.splitext(base_filename)
        if not ext:
            # Try to determine extension from resource type
            if resource_type == 'css':
                ext = '.css'
            elif resource_type == 'js':
                ext = '.js'
            else:
                ext = '.html'
        
        # Create a hash from the full URL (including query string) to ensure uniqueness
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        
        # Create unique filename: name_hash.ext
        unique_filename = f"{name}_{url_hash}{ext}"
        
        # Determine subdirectory based on extension or type
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
        
        local_path = os.path.join(self.output_dir, subdir, unique_filename)
        
        # Store in our tracking dict
        self.downloaded_files[url] = local_path
        
        return local_path
    
    def process_css(self, css_content, css_url):
        """Process CSS and download referenced resources"""
        # Find all URLs in CSS (url(...))
        url_pattern = r'url\([\'"]?([^\'")\s]+)[\'"]?\)'
        
        def replace_url(match):
            resource_url = match.group(1)
            if resource_url.startswith('data:'):
                return match.group(0)
            
            # Make absolute URL
            abs_url = urljoin(css_url, resource_url)
            local_path = self.get_local_path(abs_url)
            
            # Download resource if not already downloaded
            if abs_url not in self.downloaded_files or not os.path.exists(local_path):
                self.download_file(abs_url, local_path)
            
            # Return relative path from CSS directory
            css_local_path = self.downloaded_files.get(css_url, css_url)
            rel_path = os.path.relpath(local_path, os.path.dirname(css_local_path))
            return f'url({rel_path})'
        
        return re.sub(url_pattern, replace_url, css_content)
    
    def scrape(self):
        """Main scraping function"""
        print(f"Fetching main page: {self.base_url}")
        
        try:
            response = self.session.get(self.base_url, timeout=30)
            response.raise_for_status()
        except Exception as e:
            print(f"Error fetching main page: {str(e)}")
            return False
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Download CSS files
        print("\n=== Processing CSS files ===")
        for link in soup.find_all('link', rel='stylesheet'):
            if link.get('href'):
                css_url = urljoin(self.base_url, link['href'])
                local_path = self.get_local_path(css_url, 'css')
                
                if self.download_file(css_url, local_path):
                    # Process CSS content for embedded resources
                    try:
                        with open(local_path, 'r', encoding='utf-8', errors='ignore') as f:
                            css_content = f.read()
                        
                        processed_css = self.process_css(css_content, css_url)
                        
                        with open(local_path, 'w', encoding='utf-8') as f:
                            f.write(processed_css)
                    except Exception as e:
                        print(f"Error processing CSS {css_url}: {str(e)}")
                    
                    link['href'] = os.path.relpath(local_path, self.output_dir)
        
        # Download JavaScript files
        print("\n=== Processing JavaScript files ===")
        for script in soup.find_all('script', src=True):
            js_url = urljoin(self.base_url, script['src'])
            local_path = self.get_local_path(js_url, 'js')
            
            if self.download_file(js_url, local_path):
                script['src'] = os.path.relpath(local_path, self.output_dir)
        
        # Download images
        print("\n=== Processing images ===")
        for img in soup.find_all('img', src=True):
            img_url = urljoin(self.base_url, img['src'])
            local_path = self.get_local_path(img_url, 'images')
            
            if self.download_file(img_url, local_path):
                img['src'] = os.path.relpath(local_path, self.output_dir)
        
        # Download favicon
        print("\n=== Processing favicon ===")
        for link in soup.find_all('link', rel=['icon', 'shortcut icon']):
            if link.get('href'):
                icon_url = urljoin(self.base_url, link['href'])
                local_path = self.get_local_path(icon_url, 'images')
                
                if self.download_file(icon_url, local_path):
                    link['href'] = os.path.relpath(local_path, self.output_dir)
        
        # Save modified HTML
        output_html = os.path.join(self.output_dir, 'index.html')
        with open(output_html, 'w', encoding='utf-8') as f:
            f.write(str(soup.prettify()))
        
        print(f"\n=== Scraping complete! ===")
        print(f"Files saved to: {self.output_dir}")
        print(f"Total unique files downloaded: {len(self.downloaded_files)}")
        print(f"Open {output_html} in your browser")
        
        return True

if __name__ == '__main__':
    # Configuration
    TARGET_URL = ''
    OUTPUT_DIR = ''
    
    # Create scraper and run
    scraper = WebsiteScraper(TARGET_URL, OUTPUT_DIR)
    scraper.scrape()