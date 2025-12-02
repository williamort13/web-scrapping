# Website Scraper

A Python-based website scraper that downloads entire websites or single pages with all their assets (CSS, JavaScript, images, fonts) for offline viewing, plus a link fixer utility to repair broken links in scraped sites.

## 📋 Overview

This project provides three powerful tools:

- **scraper.py** - Scrapes a single page (index.html) with all its resources
- **scrap-everything.py** - Recursively scrapes entire websites by following internal links
- **link-replacer.py** - Fixes broken links in scraped websites by replacing them with working URLs or local files

## ✨ Features

### Scraping Features

- **Complete Asset Download**: Downloads HTML, CSS, JavaScript, images, fonts, and other resources
- **Smart File Management**: Uses URL hashing to handle files with identical names but different query parameters
- **CSS Processing**: Automatically processes CSS files to download embedded resources (fonts, images)
- **Relative Path Conversion**: Converts all absolute URLs to relative paths for offline viewing
- **Duplicate Prevention**: Tracks downloaded resources to avoid duplicate downloads
- **Recursive Crawling**: (scrap-everything.py) Follows internal links to scrape entire websites
- **Configurable Limits**: Set maximum pages and request delays
- **Beautiful Sitemap**: Generates an HTML sitemap with statistics for scraped websites
- **Responsive Image Support**: Handles srcset attributes for responsive images

### Link Fixing Features

- **Automatic Broken Link Detection**: Identifies non-functional links in scraped websites
- **Flexible Replacement Options**: Replace broken links with external URLs or local files
- **Safe Backup System**: Creates backups before modifying files (optional)
- **Detailed Reporting**: Generates comprehensive reports of all fixed links
- **Easy Restore**: One-command restoration from backups
- **Batch Processing**: Processes entire directories recursively

## 🚀 Requirements

- Python 3.6+
- Required libraries:
  ```
  requests
  beautifulsoup4
  ```

## 📦 Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/website-scraper.git
   cd website-scraper
   ```

2. Install dependencies:
   ```bash
   pip install requests beautifulsoup4
   ```

## 📖 Usage Guide

### Single Page Scraping (scraper.py)

Use this for scraping just the homepage/index page with all its resources:

```python
# Edit the configuration in scraper.py
TARGET_URL = 'https://example.com/'
OUTPUT_DIR = 'my-website'

# Run the scraper
python scraper.py
```

**Output structure:**

```
my-website/
├── index.html
├── css/
│   ├── style_a1b2c3d4.css
│   └── theme_e5f6g7h8.css
├── js/
│   └── script_12345678.js
├── images/
│   └── logo_abcdef12.png
└── fonts/
    └── font_fedcba98.woff2
```

### Recursive Website Scraping (scrap-everything.py)

Use this for scraping entire websites by following internal links:

```python
# Edit the configuration in scrap-everything.py
TARGET_URL = 'https://example.com/'
OUTPUT_DIR = 'full-website'
MAX_PAGES = 100  # Set to None for unlimited
DELAY = 0.5      # Delay between requests in seconds

# Run the scraper
python scrap-everything.py
```

**Output structure:**

```
full-website/
├── index.html
├── about/
│   └── index.html
├── contact/
│   └── index.html
├── assets/
│   ├── css/
│   ├── js/
│   ├── images/
│   ├── fonts/
│   └── other/
└── sitemap.html
```

### Link Fixing (link-replacer.py)

Use this to fix broken links in already-scraped websites:

```python
# Edit the configuration in link-replacer.py
SCRAPED_DIRECTORY = '/path/to/scraped-website'
REPLACEMENT_URL = 'https://example.com/'
CREATE_BACKUP = True
USE_LOCAL_FALLBACK = False
LOCAL_FALLBACK_FILE = 'index.html'

# Run the link fixer
python link-replacer.py
```

## ⚙️ Configuration Options

### scraper.py

```python
TARGET_URL = 'https://example.com/'  # Website to scrape
OUTPUT_DIR = 'scraped_website'        # Output directory
```

### scrap-everything.py

```python
TARGET_URL = 'https://example.com/'   # Website to scrape
OUTPUT_DIR = 'scraped_website'        # Output directory
MAX_PAGES = 100                       # Maximum pages to scrape (None = unlimited)
DELAY = 0.5                           # Delay between requests (seconds)
```

### link-replacer.py

```python
# Directory containing scraped HTML files
SCRAPED_DIRECTORY = '/path/to/scraped-website'

# URL to replace broken links with (when USE_LOCAL_FALLBACK = False)
REPLACEMENT_URL = 'https://example.com/'

# Create backup files before modifying
CREATE_BACKUP = True

# Use local file instead of external URL for replacement
USE_LOCAL_FALLBACK = False

# Local file to link to when USE_LOCAL_FALLBACK = True
LOCAL_FALLBACK_FILE = 'index.html'
```

## 💡 Usage Examples

### Example 1: Scrape a single landing page

```bash
python scraper.py
# Edit TARGET_URL to your desired page
# Open scraped_website/index.html in browser
```

### Example 2: Scrape entire documentation site

```python
# In scrap-everything.py
TARGET_URL = 'https://docs.example.com/'
OUTPUT_DIR = 'docs-offline'
MAX_PAGES = 500
DELAY = 1.0  # Be respectful with 1 second delay

# Run
python scrap-everything.py
```

### Example 3: Fix broken links with external URL

```python
# In link-replacer.py
SCRAPED_DIRECTORY = 'docs-offline'
REPLACEMENT_URL = 'https://docs.example.com/'
CREATE_BACKUP = True
USE_LOCAL_FALLBACK = False

# Run
python link-replacer.py
```

### Example 4: Fix broken links with local fallback

```python
# In link-replacer.py
SCRAPED_DIRECTORY = 'docs-offline'
CREATE_BACKUP = True
USE_LOCAL_FALLBACK = True
LOCAL_FALLBACK_FILE = 'index.html'  # Links to root index.html

# Run
python link-replacer.py
```

### Example 5: Complete workflow

```bash
# Step 1: Scrape website
python scrap-everything.py

# Step 2: Fix any broken links
python link-replacer.py

# Step 3: Open in browser
# Navigate to scraped_website/index.html
```

## 🔧 Link Replacer Details

### What Links Get Fixed?

The link replacer identifies and fixes:

1. **JavaScript Links**: `href="javascript:void(0)"` or other JS functions that don't work offline
2. **Missing Local Files**: Links to files that don't exist in the scraped directory
3. **Broken Relative Paths**: Internal routing paths like `/desktop/slots/pragmatic` that weren't downloaded
4. **Non-existent Resources**: Links pointing to resources that failed to download during scraping

### What Links Are Preserved?

The link replacer keeps these links intact:

- **External Links**: `http://` and `https://` links to other websites
- **Functional Anchors**: `#section` links within the same page
- **Email Links**: `mailto:` links
- **Phone Links**: `tel:` links
- **Existing Local Files**: Links to files that exist in the scraped directory

### Replacement Modes

#### Mode 1: External URL Replacement (Default)

```python
USE_LOCAL_FALLBACK = False
REPLACEMENT_URL = 'https://example.com/'
```

All broken links will be replaced with the external URL. Good for:

- Creating a hybrid online/offline site
- Linking back to the live website for missing pages
- Maintaining functionality for dynamic content

#### Mode 2: Local File Replacement

```python
USE_LOCAL_FALLBACK = True
LOCAL_FALLBACK_FILE = 'index.html'
```

All broken links will point to a local file. Good for:

- Fully offline websites
- Creating a fallback home page
- Redirecting to a custom error page

**Example configurations:**

```python
# Link to root homepage
LOCAL_FALLBACK_FILE = 'index.html'

# Link to contact page
LOCAL_FALLBACK_FILE = 'contact/index.html'

# Link to custom 404 page
LOCAL_FALLBACK_FILE = 'pages/404.html'
```

### Backup and Restore

#### Creating Backups

```python
CREATE_BACKUP = True  # Automatically creates .backup files
```

Before modifying any HTML file, a backup is created with `.backup` extension:

```
index.html          → Modified file
index.html.backup   → Original backup
```

#### Restoring from Backups

To undo all changes and restore original files:

```python
# In link-replacer.py main() function, uncomment:
fixer.restore_backups()

# Or run programmatically:
from link_replacer import LinkFixer

fixer = LinkFixer(directory='scraped_website', replacement_url='')
fixer.restore_backups()
```

This will:

1. Find all `.backup` files
2. Restore them to original filenames
3. Delete the backup files
4. Print restoration summary

### Output Reports

The link replacer generates detailed reports:

```
============================================================
Starting Link Fixer
============================================================
Directory: scraped_website
Replacement URL: https://example.com/
Backup enabled: True
============================================================

Found 15 HTML file(s)

Processing: scraped_website/index.html
  ❌ Broken link found: /desktop/slots/pragmatic
  ✅ Replacing with: https://example.com/
  ❌ Broken link found: javascript:void(0)
  ✅ Replacing with: https://example.com/
  💾 Backup created: scraped_website/index.html.backup
  ✨ Fixed 2 broken link(s)

Processing: scraped_website/about/index.html
  ✓ No broken links found

============================================================
SUMMARY
============================================================
Files processed: 15
Total links fixed: 23

============================================================
DETAILED REPORT
============================================================

File: scraped_website/index.html
  Original: /desktop/slots/pragmatic
  Replaced: https://example.com/

File: scraped_website/index.html
  Original: javascript:void(0)
  Replaced: https://example.com/

============================================================
✅ All done!
============================================================
```

## 🎯 How It Works

### Scraping Process

1. **Fetches the HTML**: Downloads the target page(s)
2. **Parses Content**: Uses BeautifulSoup to parse HTML and find all resource links
3. **Downloads Assets**: Downloads CSS, JS, images, fonts, and other resources
4. **Processes CSS**: Scans CSS files for embedded resources (fonts, images in url())
5. **Updates Paths**: Converts all absolute URLs to relative paths
6. **Handles Duplicates**: Uses URL hashing to create unique filenames for resources with same names but different parameters
7. **Creates Sitemap**: (scrap-everything.py) Generates an HTML sitemap of all scraped pages

### Link Fixing Process

1. **Scans Directory**: Recursively finds all HTML files
2. **Parses HTML**: Uses BeautifulSoup to find all `<a>` tags with `href` attributes
3. **Validates Links**: Checks if each link is functional:
   - Tests if local files exist
   - Identifies JavaScript links
   - Detects broken relative paths
4. **Replaces Broken Links**: Updates broken links with replacement URL or local file
5. **Creates Backups**: Saves original files before modification (if enabled)
6. **Saves Changes**: Writes updated HTML with fixed links
7. **Generates Report**: Creates detailed summary of all changes

## 🔧 Advanced Features

### Unique Filename Generation

The scraper handles cases where multiple resources have the same filename but different query parameters:

```
/css/style.css?v=1.0  →  style_a1b2c3d4.css
/css/style.css?v=2.0  →  style_e5f6g7h8.css
```

### CSS Resource Processing

Automatically downloads resources referenced in CSS:

```css
/* Original CSS */
background-image: url("/images/bg.png");
font-face: url("/fonts/font.woff2");

/* Processed CSS */
background-image: url("../images/bg_12345678.png");
font-face: url("../fonts/font_abcdef12.woff2");
```

### Intelligent Link Detection

The link fixer intelligently categorizes links:

```html
<!-- FIXED: JavaScript link -->
<a href="javascript:void(0)">Click</a>
→ <a href="https://example.com/">Click</a>

<!-- FIXED: Missing local file -->
<a href="/pages/missing.html">Page</a>
→ <a href="https://example.com/">Page</a>

<!-- PRESERVED: Existing local file -->
<a href="about/index.html">About</a>
→ <a href="about/index.html">About</a>

<!-- PRESERVED: External link -->
<a href="https://google.com">Google</a>
→ <a href="https://google.com">Google</a>

<!-- PRESERVED: Anchor link -->
<a href="#section">Jump</a>
→ <a href="#section">Jump</a>
```

### Cross-Platform Path Handling

Automatically handles path separators across Windows, macOS, and Linux:

```python
# Windows: scraped_website\pages\index.html
# Unix: scraped_website/pages/index.html
# Output: Always uses forward slashes for web compatibility
```

### Respectful Crawling

- Configurable delay between requests
- Only follows links within the same domain
- Respects robots.txt (manual checking recommended)

## 🐛 Troubleshooting

### Scraping Issues

#### Issue: "Connection timeout"

**Solution**: Increase timeout in the code or check your internet connection

```python
response = self.session.get(url, timeout=60)  # Increase from 30 to 60
```

#### Issue: "Some CSS files are missing"

**Solution**: Check if CSS files have the same base name. The scraper now handles this with unique hashing.

#### Issue: "Images not loading in offline mode"

**Solution**: Ensure you're opening the HTML file via the `file://` protocol. Some browsers have security restrictions - try using a local server:

```bash
python -m http.server 8000
# Open http://localhost:8000 in browser
```

#### Issue: "Scraper stops after few pages"

**Solution**: Check `MAX_PAGES` setting or look for errors in console output. Increase `DELAY` if getting rate-limited.

### Link Replacer Issues

#### Issue: "No broken links found but links still don't work"

**Solution**: The link might be functional but points to non-downloaded content. Check the detailed report and adjust `REPLACEMENT_URL` or use `USE_LOCAL_FALLBACK = True`.

#### Issue: "Can't restore backups"

**Solution**: Make sure backup files (`.backup`) still exist in the directory and weren't manually deleted.

#### Issue: "Wrong directory path"

**Solution**: Use absolute paths or ensure relative paths are correct:

```python
import os

# Use absolute path
SCRAPED_DIRECTORY = os.path.abspath('scraped_website')

# Or current directory
SCRAPED_DIRECTORY = os.path.join(os.getcwd(), 'scraped_website')
```

#### Issue: "Local fallback file not found warning"

**Solution**: Make sure the `LOCAL_FALLBACK_FILE` exists in `SCRAPED_DIRECTORY`:

```python
# If using subdirectory
LOCAL_FALLBACK_FILE = 'pages/home.html'

# File must exist at: scraped_website/pages/home.html
```

#### Issue: "Links still broken after running script"

**Solution**:

1. Check if backups were created (files should have `.backup` copies)
2. Verify the SCRAPED_DIRECTORY path is correct
3. Check if HTML files were actually modified (compare timestamps)
4. Run with `CREATE_BACKUP = True` and check the detailed report

## ⚠️ Important Notes

### General

- **Legal**: Only scrape websites you have permission to scrape. Respect robots.txt and terms of service.
- **Rate Limiting**: Use appropriate delays to avoid overwhelming servers. Default is 0.5 seconds.
- **Large Websites**: For very large sites, set `MAX_PAGES` to limit the scrape or run overnight.
- **Dynamic Content**: This scraper works with static HTML. JavaScript-rendered content won't be captured.
- **Authentication**: Cannot scrape pages behind login walls or authentication.

### Link Replacer Specific

- **Always Create Backups First**: Set `CREATE_BACKUP = True` when first running on a new directory
- **Test Before Full Run**: Test on a copy of your scraped site first
- **Check Reports**: Review the detailed report to ensure links were replaced correctly
- **Verify Local Fallback**: Ensure the local fallback file exists before enabling `USE_LOCAL_FALLBACK`
- **Run After Scraping**: Use link-replacer.py as a post-processing step after scraping completes

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🙋 Support

For questions, issues, or feature requests:

- Open a [GitHub Issue](https://github.com/yourusername/website-scraper/issues)
- Check existing issues for solutions
- Provide detailed error messages and steps to reproduce

## 📚 Future Enhancements

### Scraping

- [ ] Resume interrupted scrapes
- [ ] Parallel downloading for faster scraping
- [ ] Exclude patterns (regex-based URL filtering)
- [ ] Progress bar with rich/tqdm
- [ ] Export to different formats (WARC, PDF)
- [ ] Better error reporting and logging

### Link Fixing

- [ ] Interactive mode for selective link fixing
- [ ] Custom replacement rules (regex-based)
- [ ] Link validation with HTTP requests
- [ ] HTML syntax error detection and fixing
- [ ] Batch processing multiple directories
- [ ] Configuration file support (JSON/YAML)
- [ ] GUI interface for easier configuration

## 🌟 Acknowledgments

- Built with [Requests](https://requests.readthedocs.io/) and [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/)
- Inspired by wget and httrack

---

**Made with ❤️ for offline web archiving**
