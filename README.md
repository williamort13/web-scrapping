# Website Scraper Suite

A comprehensive Python-based website scraping toolkit with multi-language support, asset consolidation, and link fixing capabilities. Download entire websites or single pages with all assets for offline viewing.

## 📋 Overview

This project provides **5 powerful scraping tools**:

1. **scraper.py** - Multi-language single page scraper with asset consolidation
2. **local_scraper.py** - Scrapes from local HTML files, fetching remote assets
3. **multi_page_scraper.py** - Scrapes multiple specific pages with flat output structure
4. **scrap-everything.py** - Recursively scrapes entire websites by following internal links
5. **link-replacer.py** - Fixes broken links in scraped websites

## ✨ Key Features

### 🌍 Multi-Language Support
- Scrape websites in multiple languages (Thai, English, Indonesian, etc.)
- Automatic language cookie and header management
- Geo-location simulation for region-specific content
- Language switcher generation for offline browsing

### 📦 Asset Management
- **Smart Asset Consolidation**: Merge all CSS into one file, all JS into one file
- **Font URL Preservation**: Keep fonts on CDN (faster, no licensing issues)
- **Filename Normalization**: Remove version hashes from filenames
- **Duplicate Prevention**: URL-based hashing to avoid duplicate downloads
- **Complete Asset Download**: CSS, JavaScript, images (with srcset support)

### 🔧 Advanced Processing
- **CSS Resource Extraction**: Downloads fonts, images referenced in CSS
- **Inline Style Processing**: Handles background images in style attributes
- **Relative Path Conversion**: All URLs converted for offline viewing
- **Responsive Image Support**: Handles srcset and picture elements
- **Favicon Extraction**: Downloads all icon formats

### 🚀 Performance & Reliability
- **Session Management**: Persistent connections for faster downloads
- **Configurable Delays**: Respectful crawling with rate limiting
- **Enhanced Headers**: Browser-like headers to bypass restrictions
- **Error Handling**: Graceful failure with detailed error messages
- **Progress Tracking**: Real-time download status

## 🚀 Requirements

```bash
# Core dependencies
pip install requests beautifulsoup4

# Optional (for Selenium-based scraping)
pip install selenium webdriver-manager
```

**Python Version**: 3.6+

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/website-scraper.git
cd website-scraper

# Install dependencies
pip install requests beautifulsoup4
```

## 📖 Usage Guide

### 1. Multi-Language Single Page Scraper (scraper.py)

**Best for**: Landing pages, homepages, single pages in multiple languages

**Features**:
- ✅ Multi-language support (scrapes same page in different languages)
- ✅ Asset consolidation (single CSS file, single JS file)
- ✅ Language switcher generation
- ✅ Filename normalization
- ✅ Font URL preservation

**Configuration**:
```python
TARGET_URL = 'https://example.com/'
OUTPUT_DIR = 'my-website'
LANGUAGES = ['th', 'en', 'id']  # Thai, English, Indonesian
CONSOLIDATE_ASSETS = True
```

**Run**:
```bash
python3 scraper.py
```

**Output Structure**:
```
my-website/
├── index-th.html          # Thai version
├── index-en.html          # English version
├── index-id.html          # Indonesian version
├── css/
│   └── all-styles.css     # Consolidated CSS
├── js/
│   └── all-scripts.js     # Consolidated JS
└── images/
    ├── logo.png           # Normalized filename (no hash)
    └── banner.jpg
```

**Example**:
```python
# In scraper.py
TARGET_URL = 'https://www.example.com/'
OUTPUT_DIR = 'example-multilang'
LANGUAGES = ['th', 'en', 'id']
CONSOLIDATE_ASSETS = True

# Run
python3 scraper.py
```

---

### 2. Local HTML Scraper (local_scraper.py)

**Best for**: Scraping from saved HTML files, bypassing Cloudflare/bot protection

**Features**:
- ✅ Scrapes from local HTML file
- ✅ Fetches remote CSS, JS, images
- ✅ Enhanced headers to bypass 403 Forbidden
- ✅ Asset consolidation
- ✅ Font URL preservation

**Use Cases**:
- Manually save page past Cloudflare → scrape assets locally
- Testing/development without hitting live server
- Scraping from archived HTML files

**Configuration**:
```python
TARGET_HTML = './saved-page.html'
OUTPUT_DIR = 'scraped-local'
BASE_URL = 'https://example.com/'  # For resolving relative URLs
CONSOLIDATE_ASSETS = True
```

**Run**:
```bash
python3 local_scraper.py
```

**Workflow Example**:
```bash
# Step 1: Manually save page in browser (bypasses Cloudflare)
# File → Save As → "Webpage, HTML Only" → saved-page.html

# Step 2: Configure local_scraper.py
TARGET_HTML = './saved-page.html'
BASE_URL = 'https://example.com/'

# Step 3: Run scraper
python3 local_scraper.py

# Result: All CSS, JS, images downloaded from remote URLs
```

---

### 3. Multi-Page Scraper (multi_page_scraper.py)

**Best for**: Scraping specific pages (not entire site) with flat structure

**Features**:
- ✅ Scrapes multiple specific URLs
- ✅ Flat output structure (all HTML files at root level)
- ✅ Asset consolidation across all pages
- ✅ Smart filename generation from URLs
- ✅ Font URL preservation

**Configuration**:
```python
TARGET_URLS = [
    'https://example.com/',
    'https://example.com/about',
    'https://example.com/contact'
]
OUTPUT_DIR = 'multi-page-site'
CONSOLIDATE_ASSETS = True
DELAY = 1.0  # Seconds between requests
```

**Run**:
```bash
python3 multi_page_scraper.py
```

**Output Structure**:
```
multi-page-site/
├── index.html             # From https://example.com/
├── about.html             # From https://example.com/about
├── contact.html           # From https://example.com/contact
├── css/
│   └── all-styles.css     # Consolidated CSS from all pages
├── js/
│   └── all-scripts.js     # Consolidated JS from all pages
└── images/
    └── (shared images)
```

**URL to Filename Mapping**:
```
https://example.com/                    → index.html
https://example.com/about               → about.html
https://example.com/products/shoes      → shoes.html
https://example.com/blog/my-post        → my-post.html
```

---

### 4. Recursive Website Scraper (scrap-everything.py)

**Best for**: Downloading entire websites by following internal links

**Features**:
- ✅ Recursive crawling (follows internal links)
- ✅ Same-domain restriction
- ✅ Asset consolidation
- ✅ Sitemap generation
- ✅ Configurable depth/page limits
- ✅ Font URL preservation

**Configuration**:
```python
TARGET_URL = 'https://example.com/'
OUTPUT_DIR = 'full-website'
MAX_PAGES = 100        # Limit pages (None = unlimited)
DELAY = 0.5           # Seconds between requests
CONSOLIDATE_ASSETS = True
```

**Run**:
```bash
python3 scrap-everything.py
```

**Output Structure**:
```
full-website/
├── index.html
├── about/
│   └── index.html
├── products/
│   ├── index.html
│   └── shoes/
│       └── index.html
├── assets/
│   ├── css/
│   │   └── all-styles.css    # Consolidated CSS
│   ├── js/
│   │   └── all-scripts.js    # Consolidated JS
│   ├── images/
│   └── fonts/
└── sitemap.html              # Auto-generated sitemap
```

**Sitemap Features**:
- Beautiful gradient design
- Statistics (total pages, assets)
- Organized by directory
- Clickable links to all pages

---

### 5. Link Fixer (link-replacer.py)

**Best for**: Fixing broken links in already-scraped websites

**Features**:
- ✅ Automatic broken link detection
- ✅ Replace with external URL or local file
- ✅ Safe backup system
- ✅ Detailed reporting
- ✅ Batch processing

**Configuration**:
```python
SCRAPED_DIRECTORY = '/path/to/scraped-website'
REPLACEMENT_URL = 'https://example.com/'
CREATE_BACKUP = True
USE_LOCAL_FALLBACK = False
LOCAL_FALLBACK_FILE = 'index.html'
```

**Run**:
```bash
python3 link-replacer.py
```

**What Gets Fixed**:
- ❌ `javascript:void(0)` → ✅ `https://example.com/`
- ❌ `/missing-page` → ✅ `https://example.com/`
- ❌ Broken relative paths → ✅ Working URLs

**What's Preserved**:
- ✅ External links (`https://google.com`)
- ✅ Anchor links (`#section`)
- ✅ Email links (`mailto:`)
- ✅ Existing local files

---

## 🎯 Feature Comparison

| Feature | scraper.py | local_scraper.py | multi_page_scraper.py | scrap-everything.py |
|---------|-----------|------------------|----------------------|---------------------|
| Multi-language | ✅ | ❌ | ❌ | ❌ |
| Asset Consolidation | ✅ | ✅ | ✅ | ✅ |
| Font Preservation | ✅ | ✅ | ✅ | ✅ |
| Filename Normalization | ✅ | ✅ | ✅ | ✅ |
| Local HTML Input | ❌ | ✅ | ❌ | ❌ |
| Multiple Pages | ❌ | ❌ | ✅ | ✅ |
| Recursive Crawling | ❌ | ❌ | ❌ | ✅ |
| Flat Output | ❌ | ❌ | ✅ | ❌ |
| Sitemap Generation | ❌ | ❌ | ❌ | ✅ |
| Language Switcher | ✅ | ❌ | ❌ | ❌ |

## 🔧 Advanced Features

### Asset Consolidation

**Before** (without consolidation):
```
output/
├── css/
│   ├── style1_a1b2c3d4.css
│   ├── style2_e5f6g7h8.css
│   ├── theme_12345678.css
│   └── mobile_abcdef12.css
└── js/
    ├── main_11111111.js
    ├── vendor_22222222.js
    └── app_33333333.js
```

**After** (with consolidation):
```
output/
├── css/
│   └── all-styles.css      # All CSS merged
└── js/
    └── all-scripts.js      # All JS merged
```

**Benefits**:
- Fewer HTTP requests
- Easier to manage
- Smaller file count
- Faster page loads

### Font URL Preservation

**Why keep fonts external?**
- ✅ Fonts load from CDN (faster, cached)
- ✅ No licensing issues
- ✅ Smaller scraped output
- ✅ Always up-to-date

**Example**:
```css
/* Fonts stay on Google Fonts CDN */
@font-face {
    font-family: 'Roboto';
    src: url('https://fonts.googleapis.com/...woff2');  /* External! */
}
```

### Filename Normalization

**Before**:
```
images/
├── logo_3154c924.png
├── banner_desktop-js_3154c924.jpg
└── icon_a1b2c3d4e5f6.svg
```

**After**:
```
images/
├── logo.png           # Clean filename
├── banner.jpg
└── icon.svg
```

### Multi-Language Support

**scraper.py** can scrape the same page in multiple languages:

```python
LANGUAGES = ['th', 'en', 'id']
```

**Output**:
```
output/
├── index-th.html      # Thai version
├── index-en.html      # English version
├── index-id.html      # Indonesian version
└── (shared assets)
```

**Language Switcher**:
Each HTML file includes a language switcher that links to other language versions.

### Geo-Location Simulation

Scrapers automatically set cookies for region-specific content:

```python
# For Thai language
cookies: country=TH, geo=TH, region=TH
headers: Accept-Language: th-TH,th;q=0.9
```

## 💡 Common Workflows

### Workflow 1: Multi-Language Landing Page

```bash
# 1. Configure scraper.py
TARGET_URL = 'https://example.com/'
LANGUAGES = ['th', 'en', 'id']
CONSOLIDATE_ASSETS = True

# 2. Run scraper
python3 scraper.py

# 3. Result: 3 HTML files (one per language) with shared assets
```

### Workflow 2: Bypass Cloudflare Protection

```bash
# 1. Manually open site in browser
# 2. Wait for Cloudflare challenge to pass
# 3. Save page: File → Save As → "Webpage, HTML Only"

# 4. Configure local_scraper.py
TARGET_HTML = './saved-page.html'
BASE_URL = 'https://example.com/'

# 5. Run scraper (fetches all assets)
python3 local_scraper.py
```

### Workflow 3: Specific Pages Only

```bash
# 1. Configure multi_page_scraper.py
TARGET_URLS = [
    'https://example.com/',
    'https://example.com/about',
    'https://example.com/contact'
]

# 2. Run scraper
python3 multi_page_scraper.py

# 3. Result: Flat structure with 3 HTML files + shared assets
```

### Workflow 4: Entire Website

```bash
# 1. Configure scrap-everything.py
TARGET_URL = 'https://docs.example.com/'
MAX_PAGES = 500
DELAY = 1.0

# 2. Run scraper
python3 scrap-everything.py

# 3. Result: Full site with directory structure + sitemap
```

### Workflow 5: Fix Broken Links

```bash
# 1. Scrape website (any scraper)
python3 scrap-everything.py

# 2. Configure link-replacer.py
SCRAPED_DIRECTORY = 'scraped_website'
REPLACEMENT_URL = 'https://example.com/'

# 3. Fix links
python3 link-replacer.py

# 4. Check detailed report
```

## 🐛 Troubleshooting

### Scraping Issues

#### "403 Forbidden" Errors

**Solution 1**: Use `local_scraper.py`
```bash
# Manually save page in browser → scrape locally
```

**Solution 2**: Enhanced headers (already included)
```python
# All scrapers include browser-like headers
'User-Agent': 'Mozilla/5.0...'
'Accept-Language': 'th-TH,th;q=0.9'
```

#### "Connection Timeout"

**Solution**: Increase timeout
```python
response = self.session.get(url, timeout=60)  # Default: 30
```

#### "Some Assets Not Downloading"

**Cause**: Server blocking requests

**Solution**: Increase delay between requests
```python
DELAY = 2.0  # Increase from 0.5 to 2.0 seconds
```

#### "Fonts Not Loading"

**This is normal!** Fonts are kept on external CDNs. They load from:
- Google Fonts: `fonts.googleapis.com`
- Adobe Fonts: `use.typekit.net`
- Custom CDNs

**Verify**: Open DevTools → Network → Filter "Font" → Should see external requests

#### "Images Not Loading Offline"

**Solution**: Use local server instead of `file://`
```bash
python3 -m http.server 8000
# Open http://localhost:8000
```

### Link Replacer Issues

#### "No Broken Links Found"

**Cause**: Links might be functional but point to non-downloaded content

**Solution**: Check detailed report and adjust settings

#### "Can't Restore Backups"

**Cause**: Backup files deleted

**Solution**: Backups are `.backup` files - don't delete them!

#### "Wrong Directory Path"

**Solution**: Use absolute paths
```python
import os
SCRAPED_DIRECTORY = os.path.abspath('scraped_website')
```

## ⚙️ Configuration Reference

### scraper.py
```python
TARGET_URL = 'https://example.com/'           # Website to scrape
OUTPUT_DIR = 'scraped_website'                # Output directory
LANGUAGES = ['th', 'en', 'id']                # Languages to scrape
CONSOLIDATE_ASSETS = True                     # Merge CSS/JS files
```

### local_scraper.py
```python
TARGET_HTML = './saved-page.html'             # Local HTML file
OUTPUT_DIR = 'scraped_website'                # Output directory
BASE_URL = 'https://example.com/'             # For resolving URLs
CONSOLIDATE_ASSETS = True                     # Merge CSS/JS files
```

### multi_page_scraper.py
```python
TARGET_URLS = [                               # List of URLs
    'https://example.com/',
    'https://example.com/about'
]
OUTPUT_DIR = 'scraped_website'                # Output directory
CONSOLIDATE_ASSETS = True                     # Merge CSS/JS files
DELAY = 1.0                                   # Delay between requests
```

### scrap-everything.py
```python
TARGET_URL = 'https://example.com/'           # Starting URL
OUTPUT_DIR = 'scraped_website'                # Output directory
MAX_PAGES = 100                               # Page limit (None = unlimited)
DELAY = 0.5                                   # Delay between requests
CONSOLIDATE_ASSETS = True                     # Merge CSS/JS files
```

### link-replacer.py
```python
SCRAPED_DIRECTORY = '/path/to/scraped'        # Directory to process
REPLACEMENT_URL = 'https://example.com/'      # Replacement URL
CREATE_BACKUP = True                          # Create .backup files
USE_LOCAL_FALLBACK = False                    # Use local file instead
LOCAL_FALLBACK_FILE = 'index.html'            # Local fallback file
```

## ⚠️ Important Notes

### Legal & Ethical
- ✅ Only scrape websites you have permission to scrape
- ✅ Respect robots.txt and terms of service
- ✅ Use appropriate delays (don't overwhelm servers)
- ✅ Check copyright and licensing

### Technical Limitations
- ❌ **JavaScript-rendered content**: Not captured (static HTML only)
- ❌ **Authentication**: Cannot scrape behind login walls
- ❌ **Dynamic content**: AJAX/fetch requests not executed
- ❌ **WebSockets**: Real-time content not captured

### Best Practices
- ✅ Start with small page limits (`MAX_PAGES = 10`)
- ✅ Use delays (`DELAY = 1.0` or higher)
- ✅ Create backups before link fixing
- ✅ Test on a copy first
- ✅ Monitor disk space for large sites

## 📚 Additional Documentation

- **FONT-HANDLING.md** - Details on font URL preservation
- **UPDATES.md** - Asset consolidation and normalization features
- **VPN-GUIDE.md** - When and how to use VPN for scraping
- **MULTI-PAGE-GUIDE.md** - Multi-page scraper usage guide
- **CLOUDFLARE-GUIDE.md** - Bypassing Cloudflare protection
- **FIREFOX-SETUP.md** - Using Firefox for better scraping

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🙋 Support

For questions, issues, or feature requests:
- Open a [GitHub Issue](https://github.com/yourusername/website-scraper/issues)
- Check existing issues for solutions
- Provide detailed error messages and reproduction steps

## 🌟 Acknowledgments

- Built with [Requests](https://requests.readthedocs.io/) and [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/)
- Inspired by wget and httrack

---

**Made with ❤️ for offline web archiving**
