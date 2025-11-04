#!/usr/bin/env python3
"""
Solodit Web Scraper with Selenium
Collects vulnerability data from solodit.cyfrin.io (JavaScript-rendered site)

Author: AI Auditor System
Date: November 3, 2025
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
import time
import re
import logging
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SoloditSeleniumScraper:
    """Scraper for Solodit vulnerability database using Selenium."""
    
    def __init__(self, output_dir: str = "data/solodit", checkpoint_file: str = "collectors/checkpoints/solodit_checkpoint.json", headless: bool = True):
        self.base_url = "https://solodit.cyfrin.io"
        self.output_dir = Path(output_dir)
        self.checkpoint_file = Path(checkpoint_file)
        self.headless = headless
        
        # Statistics
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'start_time': None,
            'end_time': None
        }
        
        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load checkpoint
        self.checkpoint = self._load_checkpoint()
        
        # Initialize browser
        self.driver = None
        
    def _load_checkpoint(self) -> Dict:
        """Load checkpoint from file."""
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file, 'r') as f:
                return json.load(f)
        return {
            'last_index': 0,
            'processed_urls': [],
            'last_update': None
        }
    
    def _save_checkpoint(self):
        """Save checkpoint to file."""
        self.checkpoint['last_update'] = datetime.now().isoformat()
        with open(self.checkpoint_file, 'w') as f:
            json.dump(self.checkpoint, f, indent=2)
    
    def _init_driver(self):
        """Initialize Selenium WebDriver."""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        logger.info("WebDriver initialized")
    
    def _close_driver(self):
        """Close Selenium WebDriver."""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")
    
    def get_vulnerabilities_from_page(self) -> List[Dict]:
        """
        Extract vulnerability data from current page.
        
        Returns:
            List of vulnerability metadata dicts
        """
        vulnerabilities = []
        
        try:
            # Wait for content to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Additional wait for dynamic content
            time.sleep(3)
            
            # Find all links that point to /issues/
            links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/issues/"]')
            
            logger.info(f"Found {len(links)} potential vulnerability links")
            
            seen_urls = set()
            
            for link in links:
                try:
                    href = link.get_attribute('href')
                    if not href or href in seen_urls:
                        continue
                    
                    seen_urls.add(href)
                    
                    # Get link text (title)
                    title = link.text.strip()
                    if not title:
                        continue
                    
                    # Parse ID from title
                    id_match = re.match(r'\[([A-Z]-\d+)\]', title)
                    vuln_id = id_match.group(1) if id_match else None
                    
                    vulnerabilities.append({
                        'id': vuln_id,
                        'title': title,
                        'url': href
                    })
                    
                except Exception as e:
                    logger.debug(f"Error processing link: {e}")
                    continue
            
            logger.info(f"Extracted {len(vulnerabilities)} unique vulnerabilities")
            return vulnerabilities
            
        except TimeoutException:
            logger.error("Timeout waiting for page to load")
            return []
        except Exception as e:
            logger.error(f"Error extracting vulnerabilities: {e}")
            return []
    
    def parse_detail_page(self, url: str) -> Optional[Dict]:
        """
        Parse a vulnerability detail page.
        
        Args:
            url: Full URL to detail page
            
        Returns:
            Dict with vulnerability data or None if failed
        """
        logger.info(f"Parsing detail page: {url}")
        
        try:
            self.driver.get(url)
            
            # Wait for content
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )
            
            time.sleep(2)  # Additional wait for dynamic content
            
            # Extract title
            try:
                title_elem = self.driver.find_element(By.TAG_NAME, 'h1')
                full_title = title_elem.text.strip()
            except NoSuchElementException:
                logger.warning(f"No title found for {url}")
                return None
            
            # Parse ID and title
            id_match = re.match(r'\[([A-Z]-\d+)\]\s*(.*)', full_title)
            vuln_id = id_match.group(1) if id_match else None
            title = id_match.group(2) if id_match else full_title
            
            # Extract description (all paragraph text)
            description = ""
            try:
                paragraphs = self.driver.find_elements(By.TAG_NAME, 'p')
                description = '\n\n'.join([p.text.strip() for p in paragraphs if p.text.strip()])
            except:
                pass
            
            # Extract metadata
            page_text = self.driver.find_element(By.TAG_NAME, 'body').text
            
            # Extract severity (look for "Impact" section)
            severity = "UNKNOWN"
            if "Low" in page_text and "Impact" in page_text:
                severity = "LOW"
            elif "Medium" in page_text and "Impact" in page_text:
                severity = "MEDIUM"
            elif "High" in page_text and "Impact" in page_text:
                severity = "HIGH"
            elif "Critical" in page_text and "Impact" in page_text:
                severity = "CRITICAL"
            
            # Extract author - try multiple methods
            author = "Unknown"
            
            # Method 1: From title ("Author's finding: [ID] ...")
            title_author_match = re.match(r"^([^']+)'s finding:", full_title)
            if title_author_match:
                author = title_author_match.group(1).strip()
            
            # Method 2: From "Author(s)" section in page text
            if author == "Unknown":
                # Look for "Author(s)" followed by name on next line
                author_match = re.search(r'Author\(s\)\s+([^\n]+)', page_text)
                if author_match:
                    author = author_match.group(1).strip()
            
            # Method 3: From URL slug (contains author name)
            if author == "Unknown":
                url_parts = url.split('/')
                if len(url_parts) > 0:
                    slug = url_parts[-1]
                    # Format: id-title-author-project-date-format
                    slug_parts = slug.split('-')
                    # Author is typically after the title and before project
                    # This is a fallback and may not be 100% accurate
                    for i, part in enumerate(slug_parts):
                        if 'audit' in part.lower() or 'group' in part.lower():
                            # Found potential author indicator
                            author_parts = []
                            j = i
                            while j < len(slug_parts) and not any(x in slug_parts[j] for x in ['none', '20', '_']):
                                author_parts.append(slug_parts[j])
                                j += 1
                            if author_parts:
                                author = ' '.join(author_parts).title()
                                break
            
            # Extract project and date
            project = "Unknown"
            date = None
            project_match = re.search(r'([A-Z]{2,}_\d{4}-\d{2}-\d{2})', page_text)
            if project_match:
                project_date = project_match.group(1)
                parts = project_date.split('_')
                if len(parts) == 2:
                    project = parts[0]
                    date = parts[1]
            
            # Extract quality and rarity
            quality = "0.0"
            rarity = "0.0"
            quality_match = re.search(r'Quality[:\s]+(\d+\.?\d*)', page_text)
            if quality_match:
                quality = quality_match.group(1)
            rarity_match = re.search(r'Rarity[:\s]+(\d+\.?\d*)', page_text)
            if rarity_match:
                rarity = rarity_match.group(1)
            
            # Extract report URL
            report_url = None
            try:
                github_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="github.com"]')
                if github_links:
                    report_url = github_links[0].get_attribute('href')
            except:
                pass
            
            # Extract finding number
            finding_num = None
            finding_match = re.search(r'#(\d+)', page_text)
            if finding_match:
                finding_num = finding_match.group(1)
            
            vulnerability = {
                'id': vuln_id,
                'title': title,
                'description': description,
                'severity': severity,
                'author': author,
                'project': project,
                'date': date,
                'quality': quality,
                'rarity': rarity,
                'report_url': report_url,
                'finding_number': finding_num,
                'source_url': url,
                'scraped_at': datetime.now().isoformat()
            }
            
            logger.info(f"Successfully parsed: {vuln_id} - {title[:50]}...")
            return vulnerability
            
        except TimeoutException:
            logger.error(f"Timeout loading detail page: {url}")
            return None
        except Exception as e:
            logger.error(f"Error parsing detail page {url}: {e}")
            return None
    
    def scrape_sample(self, max_vulns: int = 10):
        """
        Scrape a sample of vulnerabilities for testing.
        
        Args:
            max_vulns: Maximum number of vulnerabilities to scrape
        """
        self.stats['start_time'] = datetime.now().isoformat()
        logger.info(f"Starting sample scrape (max {max_vulns} vulnerabilities)")
        
        try:
            self._init_driver()
            
            # Load main page
            url = f"{self.base_url}/?i=HIGH,MEDIUM,LOW,GAS"
            logger.info(f"Loading main page: {url}")
            self.driver.get(url)
            
            # Get vulnerabilities from page
            vulnerabilities = self.get_vulnerabilities_from_page()
            
            if not vulnerabilities:
                logger.warning("No vulnerabilities found on main page")
                return
            
            # Limit to max_vulns
            vulnerabilities = vulnerabilities[:max_vulns]
            
            # Process each vulnerability
            for vuln_meta in vulnerabilities:
                url = vuln_meta['url']
                
                # Skip if already processed
                if url in self.checkpoint['processed_urls']:
                    self.stats['skipped'] += 1
                    continue
                
                # Parse detail page
                vuln_data = self.parse_detail_page(url)
                
                if vuln_data:
                    # Save to file
                    self._save_vulnerability(vuln_data)
                    self.stats['successful'] += 1
                    
                    # Update checkpoint
                    self.checkpoint['processed_urls'].append(url)
                else:
                    self.stats['failed'] += 1
                
                self.stats['total_processed'] += 1
                
                # Save checkpoint every 5 vulnerabilities
                if self.stats['total_processed'] % 5 == 0:
                    self._save_checkpoint()
                    logger.info(f"Progress: {self.stats['total_processed']}/{len(vulnerabilities)} processed")
                
                # Small delay between requests
                time.sleep(1)
            
        finally:
            self._close_driver()
            self.stats['end_time'] = datetime.now().isoformat()
            self._save_checkpoint()
            self._save_stats()
            logger.info(f"Sample scraping complete. Stats: {self.stats}")
    
    def _save_vulnerability(self, vuln: Dict):
        """Save vulnerability to JSON file."""
        # Create filename from ID
        safe_id = vuln['id'].replace('/', '_') if vuln['id'] else 'unknown'
        safe_project = vuln['project'].replace('/', '_')
        safe_date = vuln['date'] if vuln['date'] else 'unknown'
        filename = f"{safe_id}_{safe_project}_{safe_date}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(vuln, f, indent=2)
    
    def _save_stats(self):
        """Save statistics to file."""
        stats_file = self.output_dir / 'scraping_stats.json'
        with open(stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2)


def main():
    """Main entry point for scraper."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape Solodit vulnerability database with Selenium')
    parser.add_argument('--max-vulns', type=int, default=10, help='Maximum vulnerabilities to scrape')
    parser.add_argument('--output-dir', type=str, default='data/solodit', help='Output directory')
    parser.add_argument('--no-headless', action='store_true', help='Show browser window')
    
    args = parser.parse_args()
    
    scraper = SoloditSeleniumScraper(
        output_dir=args.output_dir,
        headless=not args.no_headless
    )
    scraper.scrape_sample(max_vulns=args.max_vulns)
    
    print("\n" + "="*60)
    print("SCRAPING COMPLETE")
    print("="*60)
    print(f"Total processed: {scraper.stats['total_processed']}")
    print(f"Successful: {scraper.stats['successful']}")
    print(f"Failed: {scraper.stats['failed']}")
    print(f"Skipped: {scraper.stats['skipped']}")
    print("="*60)


if __name__ == '__main__':
    main()
