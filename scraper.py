import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import hashlib
import time

class WebsiteScraper:
    def __init__(self, base_url, output_dir='scraped_website', languages=None, consolidate_assets=True):
        self.base_url = base_url
        self.output_dir = output_dir
        self.languages = languages or ['en']  # Default to English if not specified
        self.consolidate_assets = consolidate_assets
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'th-TH,th;q=0.9,en;q=0.8',  # Prefer Thai language
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
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
        
        # For consolidation
        self.all_css_content = []
        self.all_js_content = []
        
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
    
    def normalize_filename(self, filename):
        """Remove hash/version numbers from filename"""
        # Remove patterns like _3154c924, -3154c924, .3154c924 before extension
        name, ext = os.path.splitext(filename)
        
        # Remove hash patterns (underscore/dash followed by hex digits)
        name = re.sub(r'[_-][a-f0-9]{6,}$', '', name)
        
        # Remove version query strings patterns
        name = re.sub(r'\?v=[^&]*', '', name)
        
        return f"{name}{ext}"
    
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
        
        # Normalize filename for images (remove hashes)
        if subdir == 'images':
            unique_filename = self.normalize_filename(base_filename)
            # If normalized name already exists, add a counter
            counter = 1
            test_filename = unique_filename
            while any(path.endswith(test_filename) for path in self.downloaded_files.values()):
                name_part, ext_part = os.path.splitext(unique_filename)
                test_filename = f"{name_part}_{counter}{ext_part}"
                counter += 1
            unique_filename = test_filename
        elif self.consolidate_assets and (subdir == 'css' or subdir == 'js'):
            # For CSS/JS, we'll consolidate them later, but still need unique temp names
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            unique_filename = f"{name}_{url_hash}{ext}"
        else:
            # For other files, keep hash for uniqueness
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            unique_filename = f"{name}_{url_hash}{ext}"
        
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
    
    def process_images(self, soup):
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
                        self.process_srcset(tag, attr_name)
                    else:
                        # Handle single src attribute
                        img_url = urljoin(self.base_url, tag[attr_name])
                        local_path = self.get_local_path(img_url, 'images')
                        
                        if self.download_file(img_url, local_path):
                            tag[attr_name] = os.path.relpath(local_path, self.output_dir)
        
        # Also handle regular img srcset
        for img in soup.find_all('img', srcset=True):
            self.process_srcset(img, 'srcset')
    
    def process_srcset(self, tag, attr_name):
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
            
            img_url = urljoin(self.base_url, img_url_part)
            local_path = self.get_local_path(img_url, 'images')
            
            if self.download_file(img_url, local_path):
                rel_path = os.path.relpath(local_path, self.output_dir)
                srcset_parts.append(f"{rel_path} {descriptor}".strip())
        
        if srcset_parts:
            tag[attr_name] = ', '.join(srcset_parts)
    
    def scrape_page(self, language=None):
        """Scrape a single page for a specific language"""
        url = self.base_url
        if language:
            print(f"\nFetching page for language: {language}")
            # Try common language URL patterns
            # Some sites use query params, some use path segments
            url = f"{self.base_url}?lang={language}"
        else:
            print(f"Fetching main page: {self.base_url}")
        
        try:
            # Set language cookie if specified
            domain = urlparse(self.base_url).netloc
            if language:
                self.session.cookies.set('language', language, domain=domain)
                self.session.cookies.set('lang', language, domain=domain)
                self.session.cookies.set('locale', language, domain=domain)
                # Update Accept-Language header for this request
                self.session.headers['Accept-Language'] = f'{language},{language.split("-")[0]};q=0.9,en;q=0.8'
            
            # Set geo-location cookies to simulate being in Thailand
            if language == 'th' or (not language and 'th' in self.languages):
                self.session.cookies.set('country', 'TH', domain=domain)
                self.session.cookies.set('geo', 'TH', domain=domain)
                self.session.cookies.set('region', 'TH', domain=domain)
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
        except Exception as e:
            print(f"Error fetching page: {str(e)}")
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup
    
    def scrape(self):
        """Main scraping function"""
        # Scrape the first language (main page)
        main_language = self.languages[0] if self.languages else None
        soup = self.scrape_page(main_language)
        
        if soup is None:
            return False
        
        # Download CSS files
        print("\n=== Processing CSS files ===")
        css_links = []
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
                        
                        if self.consolidate_assets:
                            # Add to consolidated CSS with a comment header
                            self.all_css_content.append(f"\n/* Source: {css_url} */\n{processed_css}")
                            css_links.append(link)
                        else:
                            with open(local_path, 'w', encoding='utf-8') as f:
                                f.write(processed_css)
                            link['href'] = os.path.relpath(local_path, self.output_dir)
                    except Exception as e:
                        print(f"Error processing CSS {css_url}: {str(e)}")
        
        # If consolidating, create single CSS file and update links
        if self.consolidate_assets and self.all_css_content:
            consolidated_css_path = os.path.join(self.output_dir, 'css', 'all-styles.css')
            with open(consolidated_css_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.all_css_content))
            print(f"Created consolidated CSS: {consolidated_css_path}")
            
            # Remove all CSS links except the first one, update it to point to consolidated file
            if css_links:
                css_links[0]['href'] = 'css/all-styles.css'
                for link in css_links[1:]:
                    link.decompose()
        
        # Download JavaScript files
        print("\n=== Processing JavaScript files ===")
        js_scripts = []
        for script in soup.find_all('script', src=True):
            js_url = urljoin(self.base_url, script['src'])
            local_path = self.get_local_path(js_url, 'js')
            
            if self.download_file(js_url, local_path):
                if self.consolidate_assets:
                    # Read JS content and add to consolidated
                    try:
                        with open(local_path, 'r', encoding='utf-8', errors='ignore') as f:
                            js_content = f.read()
                        self.all_js_content.append(f"\n/* Source: {js_url} */\n{js_content}")
                        js_scripts.append(script)
                    except Exception as e:
                        print(f"Error reading JS {js_url}: {str(e)}")
                        script['src'] = os.path.relpath(local_path, self.output_dir)
                else:
                    script['src'] = os.path.relpath(local_path, self.output_dir)
        
        # If consolidating, create single JS file and update scripts
        if self.consolidate_assets and self.all_js_content:
            consolidated_js_path = os.path.join(self.output_dir, 'js', 'all-scripts.js')
            with open(consolidated_js_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.all_js_content))
            print(f"Created consolidated JS: {consolidated_js_path}")
            
            # Remove all script tags except the first one, update it to point to consolidated file
            if js_scripts:
                js_scripts[0]['src'] = 'js/all-scripts.js'
                for script in js_scripts[1:]:
                    script.decompose()
        
        # Process all images (including amp-img)
        self.process_images(soup)
        
        # Download favicon
        print("\n=== Processing favicon ===")
        for link in soup.find_all('link', rel=['icon', 'shortcut icon']):
            if link.get('href'):
                icon_url = urljoin(self.base_url, link['href'])
                local_path = self.get_local_path(icon_url, 'images')
                
                if self.download_file(icon_url, local_path):
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
                    
                    abs_url = urljoin(self.base_url, resource_url)
                    local_path = self.get_local_path(abs_url, 'images')
                    
                    if abs_url not in self.downloaded_files or not os.path.exists(local_path):
                        self.download_file(abs_url, local_path)
                    
                    rel_path = os.path.relpath(local_path, self.output_dir)
                    return f'url({rel_path})'
                
                tag['style'] = re.sub(url_pattern, replace_inline_url, style_content)
        
        # Add language switcher script if multiple languages
        if len(self.languages) > 1:
            self.add_language_switcher(soup)
        
        # Save modified HTML for main language
        main_lang = self.languages[0] if self.languages else 'default'
        output_html = os.path.join(self.output_dir, f'index-{main_lang}.html')
        with open(output_html, 'w', encoding='utf-8') as f:
            f.write(str(soup.prettify()))
        
        # Also save as index.html for convenience
        main_index = os.path.join(self.output_dir, 'index.html')
        with open(main_index, 'w', encoding='utf-8') as f:
            f.write(str(soup.prettify()))
        
        # Scrape additional languages
        if len(self.languages) > 1:
            for lang in self.languages[1:]:
                print(f"\n{'='*50}")
                print(f"Scraping language: {lang}")
                print(f"{'='*50}")
                lang_soup = self.scrape_page(lang)
                
                if lang_soup:
                    # Update CSS/JS references to use consolidated files
                    if self.consolidate_assets:
                        # Update all CSS links to point to consolidated file
                        for link in lang_soup.find_all('link', rel='stylesheet'):
                            if link.get('href'):
                                link['href'] = 'css/all-styles.css'
                                break  # Keep only first one
                        # Remove other CSS links
                        for link in lang_soup.find_all('link', rel='stylesheet')[1:]:
                            link.decompose()
                        
                        # Update all JS scripts to point to consolidated file
                        for script in lang_soup.find_all('script', src=True):
                            if script.get('src'):
                                script['src'] = 'js/all-scripts.js'
                                break  # Keep only first one
                        # Remove other script tags
                        for script in lang_soup.find_all('script', src=True)[1:]:
                            script.decompose()
                    
                    # Process resources for this language page
                    self.process_language_page(lang_soup, lang)
        
        print(f"\n=== Scraping complete! ===")
        print(f"Files saved to: {self.output_dir}")
        print(f"Total unique files downloaded: {len(self.downloaded_files)}")
        print(f"Languages scraped: {', '.join(self.languages)}")
        print(f"Open {main_index} in your browser")
        
        return True
    
    def process_language_page(self, soup, language):
        """Process and save a language-specific page"""
        # Add language switcher
        if len(self.languages) > 1:
            self.add_language_switcher(soup)
        
        # Save the language-specific HTML
        output_html = os.path.join(self.output_dir, f'index-{language}.html')
        with open(output_html, 'w', encoding='utf-8') as f:
            f.write(str(soup.prettify()))
        
        print(f"Saved {language} version: {output_html}")
    
    def add_language_switcher(self, soup):
        """Add or update language switcher to work with local files"""
        # Find existing language selector
        lang_selectors = soup.find_all('li', class_='language_selector')
        
        if lang_selectors:
            print(f"Found {len(lang_selectors)} language selectors, updating links...")
            for selector in lang_selectors:
                lang_code = selector.get('data-language')
                if lang_code in self.languages:
                    # Update the selector to link to local file
                    selector['onclick'] = f"window.location.href='index-{lang_code}.html'"
                    selector['style'] = 'cursor: pointer;'
        
        # Also add a simple language switcher script
        script = soup.new_tag('script')
        script.string = f"""
        document.addEventListener('DOMContentLoaded', function() {{
            // Handle language selector clicks
            var languageSelectors = document.querySelectorAll('.language_selector');
            languageSelectors.forEach(function(selector) {{
                selector.addEventListener('click', function(e) {{
                    e.preventDefault();
                    var lang = this.getAttribute('data-language');
                    var availableLanguages = {self.languages};
                    if (availableLanguages.includes(lang)) {{
                        window.location.href = 'index-' + lang + '.html';
                    }}
                }});
            }});
            
            // Also handle the trigger dropdown
            var trigger = document.getElementById('language_selector_trigger');
            if (trigger) {{
                trigger.style.cursor = 'pointer';
            }}
        }});
        """
        
        # Add script to body
        if soup.body:
            soup.body.append(script)

if __name__ == '__main__':
    # Configuration
    TARGET_URL = ''
    OUTPUT_DIR = ''
    
    # Languages to scrape (add or remove as needed)
    # Available: en, id, kr, cn, jp, th, my, kh, hi, ta, te, vi, bn, pt
    LANGUAGES = ['id']  # Thai, English, Indonesian
    
    # Consolidate JS/CSS files and normalize image names
    CONSOLIDATE_ASSETS = True
    
    # Create scraper and run
    scraper = WebsiteScraper(TARGET_URL, OUTPUT_DIR, languages=LANGUAGES, consolidate_assets=CONSOLIDATE_ASSETS)
    scraper.scrape()