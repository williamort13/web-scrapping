import os
import re
from bs4 import BeautifulSoup
from pathlib import Path

class LinkFixer:
    def __init__(self, directory, replacement_url, backup=True, use_local_fallback=False, local_fallback='index.html'):
        """
        Initialize the LinkFixer
        
        Args:
            directory: Directory containing HTML files to process
            replacement_url: URL to replace broken links with
            backup: Whether to create backup files (default: True)
            use_local_fallback: If True, use local file instead of external URL
            local_fallback: Local file to link to (default: 'index.html')
        """
        self.directory = directory
        self.replacement_url = replacement_url
        self.backup = backup
        self.use_local_fallback = use_local_fallback
        self.local_fallback = local_fallback
        self.stats = {
            'files_processed': 0,
            'links_fixed': 0,
            'broken_links_found': []
        }
    
    def is_broken_link(self, href):
        """
        Check if a link is broken/non-functional
        
        Returns True if the link is:
        - Relative path that doesn't exist locally
        - Points to non-existent file
        - Internal routing path (like /desktop/slots/pragmatic)
        - JavaScript functions that won't work offline
        """
        if not href:
            return False
        
        # Check for JavaScript links - these are broken offline
        if href.startswith('javascript:'):
            # These are non-functional JavaScript calls
            return True
        
        # Skip these - they're functional
        if href.startswith(('http://', 'https://', 'mailto:', 'tel:', '#')):
            return False
        
        # Check if it's a relative path
        if href.startswith('/') or href.startswith('./') or href.startswith('../'):
            # Try to resolve the path
            potential_path = os.path.join(self.directory, href.lstrip('/'))
            
            # Check if file exists
            if os.path.exists(potential_path):
                return False
            
            # Check with .html extension
            if os.path.exists(potential_path + '.html'):
                return False
            
            # Check if it's an index.html in a directory
            if os.path.exists(os.path.join(potential_path, 'index.html')):
                return False
            
            # If none of these exist, it's broken
            return True
        
        # Check relative paths without leading slash
        potential_path = os.path.join(self.directory, href)
        if not os.path.exists(potential_path) and not os.path.exists(potential_path + '.html'):
            return True
        
        return False
    
    def process_html_file(self, file_path):
        """Process a single HTML file and fix broken links"""
        print(f"\nProcessing: {file_path}")
        
        try:
            # Read the file
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            links_fixed = 0
            
            # Find all <a> tags with href
            for tag in soup.find_all('a', href=True):
                href = tag['href']
                
                if self.is_broken_link(href):
                    # Determine replacement link
                    if self.use_local_fallback:
                        # Calculate relative path to local fallback file
                        current_file_dir = os.path.dirname(file_path)
                        fallback_path = os.path.join(self.directory, self.local_fallback)
                        
                        # Get relative path from current file to fallback
                        replacement_link = os.path.relpath(fallback_path, current_file_dir)
                        # Normalize path separators for web
                        replacement_link = replacement_link.replace('\\', '/')
                    else:
                        replacement_link = self.replacement_url
                    
                    print(f"  ❌ Broken link found: {href}")
                    print(f"  ✅ Replacing with: {replacement_link}")
                    
                    tag['href'] = replacement_link
                    links_fixed += 1
                    
                    # Track for statistics
                    self.stats['broken_links_found'].append({
                        'file': file_path,
                        'original': href,
                        'replaced': replacement_link
                    })
            
            # Only save if changes were made
            if links_fixed > 0:
                # Create backup if enabled
                if self.backup:
                    backup_path = file_path + '.backup'
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"  💾 Backup created: {backup_path}")
                
                # Save modified HTML
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(str(soup.prettify()))
                
                print(f"  ✨ Fixed {links_fixed} broken link(s)")
                self.stats['links_fixed'] += links_fixed
            else:
                print(f"  ✓ No broken links found")
            
            self.stats['files_processed'] += 1
            
        except Exception as e:
            print(f"  ⚠️ Error processing file: {str(e)}")
    
    def process_directory(self):
        """Process all HTML files in the directory recursively"""
        print(f"{'='*60}")
        print(f"Starting Link Fixer")
        print(f"{'='*60}")
        print(f"Directory: {self.directory}")
        
        if self.use_local_fallback:
            print(f"Replacement: Local file -> {self.local_fallback}")
        else:
            print(f"Replacement URL: {self.replacement_url}")
        
        print(f"Backup enabled: {self.backup}")
        print(f"{'='*60}\n")
        
        # Find all HTML files
        html_files = []
        for root, dirs, files in os.walk(self.directory):
            for file in files:
                if file.endswith(('.html', '.htm')):
                    html_files.append(os.path.join(root, file))
        
        print(f"Found {len(html_files)} HTML file(s)\n")
        
        # Process each file
        for html_file in html_files:
            self.process_html_file(html_file)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print a summary of the operations"""
        print(f"\n{'='*60}")
        print(f"SUMMARY")
        print(f"{'='*60}")
        print(f"Files processed: {self.stats['files_processed']}")
        print(f"Total links fixed: {self.stats['links_fixed']}")
        
        if self.stats['broken_links_found']:
            print(f"\n{'='*60}")
            print(f"DETAILED REPORT")
            print(f"{'='*60}")
            
            for item in self.stats['broken_links_found']:
                print(f"\nFile: {item['file']}")
                print(f"  Original: {item['original']}")
                print(f"  Replaced: {item['replaced']}")
        
        print(f"\n{'='*60}")
        print(f"✅ All done!")
        print(f"{'='*60}\n")
    
    def restore_backups(self):
        """Restore all backup files (undo changes)"""
        print(f"\nRestoring backup files...")
        restored = 0
        
        for root, dirs, files in os.walk(self.directory):
            for file in files:
                if file.endswith('.backup'):
                    backup_path = os.path.join(root, file)
                    original_path = backup_path.replace('.backup', '')
                    
                    try:
                        # Read backup
                        with open(backup_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Restore original
                        with open(original_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        # Delete backup
                        os.remove(backup_path)
                        
                        print(f"  ✅ Restored: {original_path}")
                        restored += 1
                    except Exception as e:
                        print(f"  ⚠️ Error restoring {backup_path}: {str(e)}")
        
        print(f"\n✅ Restored {restored} file(s)")


def main():
    """Main function with configuration"""
    
    # =====================================================
    # CONFIGURATION
    # =====================================================
    
    # Directory containing the scraped HTML files
    SCRAPED_DIRECTORY = '/'
    
    # URL to replace broken links with (used when USE_LOCAL_FALLBACK = False)
    # Tambahkan link baru untuk merubah link yg lama dibawah
    REPLACEMENT_URL = ''
    
    # Create backup files before modifying (recommended)
    CREATE_BACKUP = True
    
    # =====================================================
    # LOCAL FALLBACK OPTIONS
    # =====================================================
    
    # Set to True to link broken links to a local file instead of external URL
    # Set to False to use REPLACEMENT_URL
    USE_LOCAL_FALLBACK = False
    
    # Local file to link to when USE_LOCAL_FALLBACK = True
    # Examples:
    #   'index.html'           -> Links to index.html in root directory
    #   'pages/home.html'      -> Links to pages/home.html
    #   'contact/index.html'   -> Links to contact/index.html
    LOCAL_FALLBACK_FILE = 'index.html'
    
    # =====================================================
    
    # Validate directory exists
    if not os.path.exists(SCRAPED_DIRECTORY):
        print(f"❌ Error: Directory '{SCRAPED_DIRECTORY}' not found!")
        print(f"Please update SCRAPED_DIRECTORY in the script.")
        return
    
    # Validate local fallback file exists if using local fallback
    if USE_LOCAL_FALLBACK:
        fallback_path = os.path.join(SCRAPED_DIRECTORY, LOCAL_FALLBACK_FILE)
        if not os.path.exists(fallback_path):
            print(f"⚠️ Warning: Local fallback file '{fallback_path}' not found!")
            print(f"Make sure '{LOCAL_FALLBACK_FILE}' exists in '{SCRAPED_DIRECTORY}'")
            response = input("Continue anyway? (y/n): ")
            if response.lower() != 'y':
                return
    
    # Create fixer and run
    fixer = LinkFixer(
        directory=SCRAPED_DIRECTORY,
        replacement_url=REPLACEMENT_URL,
        backup=CREATE_BACKUP,
        use_local_fallback=USE_LOCAL_FALLBACK,
        local_fallback=LOCAL_FALLBACK_FILE
    )
    
    # Process all HTML files
    fixer.process_directory()
    
    # Uncomment the line below if you want to restore backups (undo changes)
    # fixer.restore_backups()


if __name__ == '__main__':
    main()