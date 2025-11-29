# Website Scraper

A Python-based website scraper that downloads entire websites or single pages with all their assets (CSS, JavaScript, images, fonts) for offline viewing.

## 📋 Overview

This project provides two scraping tools:

- **scraper.py** - Scrapes a single page (index.html) with all its resources
- **scrap-everything.py** - Recursively scrapes entire websites by following internal links

## ✨ Features

- **Complete Asset Download**: Downloads HTML, CSS, JavaScript, images, fonts, and other resources
- **Smart File Management**: Uses URL hashing to handle files with identical names but different query parameters
- **CSS Processing**: Automatically processes CSS files to download embedded resources (fonts, images)
- **Relative Path Conversion**: Converts all absolute URLs to relative paths for offline viewing
- **Duplicate Prevention**: Tracks downloaded resources to avoid duplicate downloads
- **Recursive Crawling**: (scrap-everything.py) Follows internal links to scrape entire websites
- **Configurable Limits**: Set maximum pages and request delays
- **Beautiful Sitemap**: Generates an HTML sitemap with statistics for scraped websites
- **Responsive Image Support**: Handles srcset attributes for responsive images

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

### Example 3: Scrape with custom settings

```python
scraper = RecursiveWebsiteScraper(
    base_url='https://example.com',
    output_dir='my-output',
    max_pages=50,
    delay=2.0
)
scraper.scrape()
```

## 🎯 How It Works

1. **Fetches the HTML**: Downloads the target page(s)
2. **Parses Content**: Uses BeautifulSoup to parse HTML and find all resource links
3. **Downloads Assets**: Downloads CSS, JS, images, fonts, and other resources
4. **Processes CSS**: Scans CSS files for embedded resources (fonts, images in url())
5. **Updates Paths**: Converts all absolute URLs to relative paths
6. **Handles Duplicates**: Uses URL hashing to create unique filenames for resources with same names but different parameters
7. **Creates Sitemap**: (scrap-everything.py) Generates an HTML sitemap of all scraped pages

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

### Respectful Crawling

- Configurable delay between requests
- Only follows links within the same domain
- Respects robots.txt (manual checking recommended)

## 🐛 Troubleshooting

### Issue: "Connection timeout"

**Solution**: Increase timeout in the code or check your internet connection

```python
response = self.session.get(url, timeout=60)  # Increase from 30 to 60
```

### Issue: "Some CSS files are missing"

**Solution**: Check if CSS files have the same base name. The scraper now handles this with unique hashing.

### Issue: "Images not loading in offline mode"

**Solution**: Ensure you're opening the HTML file via the `file://` protocol. Some browsers have security restrictions - try using a local server:

```bash
python -m http.server 8000
# Open http://localhost:8000 in browser
```

### Issue: "Scraper stops after few pages"

**Solution**: Check `MAX_PAGES` setting or look for errors in console output. Increase `DELAY` if getting rate-limited.

### Issue: "Relative paths broken"

**Solution**: The scraper now properly handles path separators across platforms. Make sure you're using the latest version.

## ⚠️ Important Notes

- **Legal**: Only scrape websites you have permission to scrape. Respect robots.txt and terms of service.
- **Rate Limiting**: Use appropriate delays to avoid overwhelming servers. Default is 0.5 seconds.
- **Large Websites**: For very large sites, set `MAX_PAGES` to limit the scrape or run overnight.
- **Dynamic Content**: This scraper works with static HTML. JavaScript-rendered content won't be captured.
- **Authentication**: Cannot scrape pages behind login walls or authentication.

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

- [ ] JavaScript execution support (Selenium/Playwright integration)
- [ ] Resume interrupted scrapes
- [ ] Parallel downloading for faster scraping
- [ ] Exclude patterns (regex-based URL filtering)
- [ ] Progress bar with rich/tqdm
- [ ] Export to different formats (WARC, PDF)
- [ ] Better error reporting and logging

## 🌟 Acknowledgments

- Built with [Requests](https://requests.readthedocs.io/) and [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/)
- Inspired by wget and httrack

---

**Made with ❤️ for offline web archiving**
