import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import hashlib

class LocalHtmlScraper:
    def __init__(self, html_file, output_dir='scraped_website', base_url=None):
        self.html_file = html_file
        self.output_dir = output_dir
        self.base_url = base_url  # Optional: override base URL for resolving relative paths
        self.session = requests.Session()
        
        # Complete browser headers to bypass 403 Forbidden errors
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
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
        
    def detect_base_url(self, soup):
        """Detect base URL from HTML <base> tag or first absolute URL found"""
        # Check for <base> tag
        base_tag = soup.find('base', href=True)
        if base_tag:
            return base_tag['href']
        
        # Try to find from link/script tags
        for link in soup.find_all('link', href=True):
            href = link['href']
            if href.startswith('http://') or href.startswith('https://'):
                parsed = urlparse(href)
                return f"{parsed.scheme}://{parsed.netloc}/"
        
        for script in soup.find_all('script', src=True):
            src = script['src']
            if src.startswith('http://') or src.startswith('https://'):
                parsed = urlparse(src)
                return f"{parsed.scheme}://{parsed.netloc}/"
        
        for img in soup.find_all(['img', 'amp-img'], src=True):
            src = img['src']
            if src.startswith('http://') or src.startswith('https://'):
                parsed = urlparse(src)
                return f"{parsed.scheme}://{parsed.netloc}/"
        
        return None
        
    def download_file(self, url, local_path, referer=None):
        """Download a file from URL to local path"""
        try:
            print(f"Downloading: {url}")
            
            # Set Referer header to make request look like it comes from the original page
            headers = {}
            if referer:
                headers['Referer'] = referer
                headers['Origin'] = referer
            
            # Update Accept header based on file type
            parsed = urlparse(url)
            ext = os.path.splitext(parsed.path)[1].lower()
            if ext in ['.css']:
                headers['Accept'] = 'text/css,*/*;q=0.1'
            elif ext in ['.js', '.mjs']:
                headers['Accept'] = '*/*'
            elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.ico']:
                headers['Accept'] = 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
            elif ext in ['.woff', '.woff2', '.ttf', '.eot', '.otf']:
                headers['Accept'] = 'font/woff2,font/woff,application/font-woff,*/*;q=0.1'
            
            response = self.session.get(url, timeout=30, headers=headers, allow_redirects=True)
            
            # Check for 403 Forbidden - try with different approach
            if response.status_code == 403:
                print(f"  Got 403 Forbidden, trying with updated headers...")
                # Try without Sec-Fetch headers and with simpler Accept header
                retry_headers = {}
                if referer:
                    retry_headers['Referer'] = referer
                # Use a simpler, more permissive Accept header
                retry_headers['Accept'] = '*/*'
                response = self.session.get(url, timeout=30, headers=retry_headers, allow_redirects=True)
            
            response.raise_for_status()
            
            # Create directory if needed
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Write file
            with open(local_path, 'wb') as f:
                f.write(response.content)
            print(f"  ✓ Saved: {local_path}")
            return True
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                print(f"  ✗ 403 Forbidden: {url}")
                print(f"    (Server is blocking access to this resource)")
            else:
                print(f"  ✗ HTTP Error {e.response.status_code}: {url}")
            return False
        except Exception as e:
            print(f"  ✗ Error downloading {url}: {str(e)}")
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
    
    def is_remote_url(self, url):
        """Check if URL is a remote URL (http/https)"""
        return url.startswith('http://') or url.startswith('https://') or url.startswith('//')
    
    def make_absolute_url(self, url, base_url):
        """Convert a URL to absolute URL"""
        if url.startswith('//'):
            return 'https:' + url
        elif url.startswith('http://') or url.startswith('https://'):
            return url
        elif url.startswith('/'):
            # Absolute path from domain root
            parsed = urlparse(base_url)
            return f"{parsed.scheme}://{parsed.netloc}{url}"
        else:
            # Relative path
            return urljoin(base_url, url)
    
    def process_css(self, css_content, css_url):
        """Process CSS and download referenced resources"""
        # Find all URLs in CSS (url(...))
        url_pattern = r'url\([\'"]?([^\'")\s]+)[\'"]?\)'
        
        def replace_url(match):
            resource_url = match.group(1)
            if resource_url.startswith('data:'):
                return match.group(0)
            
            # Make absolute URL
            abs_url = self.make_absolute_url(resource_url, css_url)
            local_path = self.get_local_path(abs_url)
            
            # Download resource if not already downloaded
            if abs_url not in self.downloaded_files or not os.path.exists(local_path):
                self.download_file(abs_url, local_path, referer=css_url)
            
            # Return relative path from CSS directory
            css_local_path = self.downloaded_files.get(css_url, css_url)
            rel_path = os.path.relpath(local_path, os.path.dirname(css_local_path))
            return f'url({rel_path})'
        
        return re.sub(url_pattern, replace_url, css_content)
    
    def process_images(self, soup, base_url):
        """Process all image tags including amp-img, img, and others"""
        print("\n=== Processing images ===")
        
        # List of tags and attributes that can contain image sources
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
                        # Handle srcset (multiple images with different sizes)
                        self.process_srcset(tag, attr_name, base_url)
                    else:
                        # Handle single src attribute
                        src_value = tag[attr_name]
                        if self.is_remote_url(src_value) or base_url:
                            img_url = self.make_absolute_url(src_value, base_url)
                            local_path = self.get_local_path(img_url, 'images')
                            
                            if self.download_file(img_url, local_path, referer=base_url):
                                tag[attr_name] = os.path.relpath(local_path, self.output_dir)
        
        # Also handle regular img srcset
        for img in soup.find_all('img', srcset=True):
            self.process_srcset(img, 'srcset', base_url)
    
    def process_srcset(self, tag, attr_name, base_url):
        """Process srcset attribute which can contain multiple images"""
        srcset_parts = []
        for part in tag[attr_name].split(','):
            part = part.strip()
            if not part:
                continue
            
            # Split URL and descriptor (e.g., "image.jpg 2x")
            split_part = part.rsplit(' ', 1)
            img_url_part = split_part[0]
            descriptor = split_part[1] if len(split_part) > 1 else ''
            
            if self.is_remote_url(img_url_part) or base_url:
                img_url = self.make_absolute_url(img_url_part, base_url)
                local_path = self.get_local_path(img_url, 'images')
                
                if self.download_file(img_url, local_path, referer=base_url):
                    rel_path = os.path.relpath(local_path, self.output_dir)
                    srcset_parts.append(f"{rel_path} {descriptor}".strip())
        
        if srcset_parts:
            tag[attr_name] = ', '.join(srcset_parts)
    
    def scrape(self):
        """Main scraping function"""
        print(f"Reading local HTML file: {self.html_file}")
        
        # Read local HTML file
        try:
            with open(self.html_file, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()
        except Exception as e:
            print(f"Error reading HTML file: {str(e)}")
            return False
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Detect or use provided base URL
        base_url = self.base_url or self.detect_base_url(soup)
        
        if not base_url:
            print("Warning: Could not detect base URL. Only absolute URLs will be downloaded.")
            print("You can provide a base_url parameter to resolve relative URLs.")
        else:
            print(f"Using base URL: {base_url}")
        
        # Download CSS files
        print("\n=== Processing CSS files ===")
        for link in soup.find_all('link', rel='stylesheet'):
            if link.get('href'):
                href = link['href']
                if self.is_remote_url(href) or base_url:
                    css_url = self.make_absolute_url(href, base_url) if base_url else href
                    local_path = self.get_local_path(css_url, 'css')
                    
                    if self.download_file(css_url, local_path, referer=base_url):
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
            src = script['src']
            if self.is_remote_url(src) or base_url:
                js_url = self.make_absolute_url(src, base_url) if base_url else src
                local_path = self.get_local_path(js_url, 'js')
                
                if self.download_file(js_url, local_path, referer=base_url):
                    script['src'] = os.path.relpath(local_path, self.output_dir)
        
        # Process all images (including amp-img)
        self.process_images(soup, base_url)
        
        # Download favicon
        print("\n=== Processing favicon ===")
        for link in soup.find_all('link', rel=['icon', 'shortcut icon', 'apple-touch-icon']):
            if link.get('href'):
                href = link['href']
                if self.is_remote_url(href) or base_url:
                    icon_url = self.make_absolute_url(href, base_url) if base_url else href
                    local_path = self.get_local_path(icon_url, 'images')
                    
                    if self.download_file(icon_url, local_path, referer=base_url):
                        link['href'] = os.path.relpath(local_path, self.output_dir)
        
        # Process background images in style attributes
        print("\n=== Processing inline styles ===")
        for tag in soup.find_all(style=True):
            style_content = tag['style']
            if 'url(' in style_content:
                url_pattern = r'url\([\'"]?([^\'")\s]+)[\'"]?\)'
                
                def replace_inline_url(match):
                    resource_url = match.group(1)
                    if resource_url.startswith('data:'):
                        return match.group(0)
                    
                    if self.is_remote_url(resource_url) or base_url:
                        abs_url = self.make_absolute_url(resource_url, base_url) if base_url else resource_url
                        local_path = self.get_local_path(abs_url, 'images')
                        
                        if abs_url not in self.downloaded_files or not os.path.exists(local_path):
                            self.download_file(abs_url, local_path, referer=base_url)
                        
                        rel_path = os.path.relpath(local_path, self.output_dir)
                        return f'url({rel_path})'
                    return match.group(0)
                
                tag['style'] = re.sub(url_pattern, replace_inline_url, style_content)
        
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
    TARGET = ''  # Local HTML file path
    OUTPUT = ''    # Output directory
    BASE_URL = None               # Optional: override base URL (e.g., 'https://example.com/')
    
    # Create scraper and run
    scraper = LocalHtmlScraper(TARGET, OUTPUT, BASE_URL)
    scraper.scrape()


