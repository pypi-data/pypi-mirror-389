#!/usr/bin/env python3
"""
Solodit Web Scraper
Collects vulnerability data from solodit.cyfrin.io

Author: AI Auditor System
Date: November 3, 2025
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
import logging
from typing import Dict, List, Optional
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_exponential
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SoloditScraper:
    """Scraper for Solodit vulnerability database."""
    
    def __init__(self, output_dir: str = "data/solodit", checkpoint_file: str = "collectors/checkpoints/solodit_checkpoint.json"):
        self.base_url = "https://solodit.cyfrin.io"
        self.output_dir = Path(output_dir)
        self.checkpoint_file = Path(checkpoint_file)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
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
        
    def _load_checkpoint(self) -> Dict:
        """Load checkpoint from file."""
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file, 'r') as f:
                return json.load(f)
        return {
            'last_page': 0,
            'processed_urls': [],
            'last_update': None
        }
    
    def _save_checkpoint(self):
        """Save checkpoint to file."""
        self.checkpoint['last_update'] = datetime.now().isoformat()
        with open(self.checkpoint_file, 'w') as f:
            json.dump(self.checkpoint, f, indent=2)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch_page(self, url: str, delay: float = 1.0) -> Optional[str]:
        """Fetch a page with retry logic."""
        time.sleep(delay)
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            raise
    
    def get_listing_page(self, page: int = 1, severity: str = "HIGH,MEDIUM,LOW,GAS") -> List[Dict]:
        """
        Get vulnerability listings from a page.
        
        Args:
            page: Page number (1-indexed)
            severity: Comma-separated severity levels
            
        Returns:
            List of vulnerability metadata dicts
        """
        # Calculate offset (assuming 50 results per page)
        offset = (page - 1) * 50
        
        url = f"{self.base_url}/?i={severity}&offset={offset}&sf=Recency&sd=Desc"
        logger.info(f"Fetching listing page {page} from {url}")
        
        try:
            html = self._fetch_page(url)
            soup = BeautifulSoup(html, 'lxml')
            
            vulnerabilities = []
            
            # Find all vulnerability cards
            # Based on analysis, look for links with vulnerability titles
            vuln_links = soup.find_all('a', href=re.compile(r'/issues/'))
            
            for link in vuln_links:
                href = link.get('href')
                if not href or href in self.checkpoint['processed_urls']:
                    continue
                
                # Extract title from link text
                title = link.get_text(strip=True)
                
                # Parse ID from title
                id_match = re.match(r'\[([A-Z]-\d+)\]', title)
                vuln_id = id_match.group(1) if id_match else None
                
                # Build full URL
                full_url = href if href.startswith('http') else f"{self.base_url}{href}"
                
                vulnerabilities.append({
                    'id': vuln_id,
                    'title': title,
                    'url': full_url,
                    'page': page
                })
            
            logger.info(f"Found {len(vulnerabilities)} vulnerabilities on page {page}")
            return vulnerabilities
            
        except Exception as e:
            logger.error(f"Error fetching listing page {page}: {e}")
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
            html = self._fetch_page(url, delay=0.5)
            soup = BeautifulSoup(html, 'lxml')
            
            # Extract title
            title_elem = soup.find('h1')
            if not title_elem:
                logger.warning(f"No title found for {url}")
                return None
            
            full_title = title_elem.get_text(strip=True)
            
            # Parse ID and title
            id_match = re.match(r'\[([A-Z]-\d+)\]\s*(.*)', full_title)
            vuln_id = id_match.group(1) if id_match else None
            title = id_match.group(2) if id_match else full_title
            
            # Extract description (main content)
            # Look for the main content area
            description = ""
            content_div = soup.find('div', class_=re.compile(r'description|content|vulnerability'))
            if content_div:
                description = content_div.get_text(strip=True, separator='\n')
            else:
                # Fallback: get all paragraph text
                paragraphs = soup.find_all('p')
                description = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
            
            # Extract metadata from sidebar or page
            severity = self._extract_text(soup, ['span', 'div'], ['severity', 'impact'], default='UNKNOWN')
            author = self._extract_text(soup, ['a', 'span'], ['author'], default='Unknown')
            
            # Extract project and date from title or metadata
            project = "Unknown"
            date = None
            
            # Try to find project/date in various places
            metadata_text = soup.get_text()
            project_match = re.search(r'([A-Z]{3,}_\d{4}-\d{2}-\d{2})', metadata_text)
            if project_match:
                project_date = project_match.group(1)
                parts = project_date.split('_')
                if len(parts) == 2:
                    project = parts[0]
                    date = parts[1]
            
            # Extract quality and rarity scores
            quality = self._extract_text(soup, ['span'], ['quality', 'score'], default='0.0')
            rarity = self._extract_text(soup, ['span'], ['rarity'], default='0.0')
            
            # Extract report URL
            report_url = None
            report_link = soup.find('a', href=re.compile(r'github\.com'))
            if report_link:
                report_url = report_link.get('href')
            
            # Extract finding number
            finding_num = None
            finding_match = re.search(r'#(\d+)', soup.get_text())
            if finding_match:
                finding_num = finding_match.group(1)
            
            vulnerability = {
                'id': vuln_id,
                'title': title,
                'description': description,
                'severity': severity.upper(),
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
            
        except Exception as e:
            logger.error(f"Error parsing detail page {url}: {e}")
            return None
    
    def _extract_text(self, soup, tags: List[str], classes: List[str], default: str = "") -> str:
        """Helper to extract text from elements matching tags and classes."""
        for tag in tags:
            for cls in classes:
                elem = soup.find(tag, class_=re.compile(cls, re.IGNORECASE))
                if elem:
                    return elem.get_text(strip=True)
        return default
    
    def scrape_all(self, max_pages: Optional[int] = None, start_page: int = 1):
        """
        Scrape all vulnerabilities from Solodit.
        
        Args:
            max_pages: Maximum number of pages to scrape (None = all)
            start_page: Page to start from (default: 1)
        """
        self.stats['start_time'] = datetime.now().isoformat()
        logger.info(f"Starting scrape from page {start_page}")
        
        # Resume from checkpoint if available
        if self.checkpoint['last_page'] > 0:
            start_page = self.checkpoint['last_page'] + 1
            logger.info(f"Resuming from checkpoint at page {start_page}")
        
        page = start_page
        consecutive_empty = 0
        
        while True:
            # Check if we've reached max pages
            if max_pages and page > max_pages:
                logger.info(f"Reached max pages limit: {max_pages}")
                break
            
            # Get listing page
            vulnerabilities = self.get_listing_page(page)
            
            # Check if page is empty
            if not vulnerabilities:
                consecutive_empty += 1
                logger.warning(f"Empty page {page} (consecutive: {consecutive_empty})")
                
                if consecutive_empty >= 3:
                    logger.info("Found 3 consecutive empty pages, stopping")
                    break
                
                page += 1
                continue
            
            consecutive_empty = 0
            
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
                
                # Save checkpoint every 10 vulnerabilities
                if self.stats['total_processed'] % 10 == 0:
                    self.checkpoint['last_page'] = page
                    self._save_checkpoint()
                    logger.info(f"Progress: {self.stats['total_processed']} processed, {self.stats['successful']} successful")
            
            # Move to next page
            page += 1
            
            # Save checkpoint after each page
            self.checkpoint['last_page'] = page - 1
            self._save_checkpoint()
        
        self.stats['end_time'] = datetime.now().isoformat()
        self._save_stats()
        logger.info(f"Scraping complete. Stats: {self.stats}")
    
    def _save_vulnerability(self, vuln: Dict):
        """Save vulnerability to JSON file."""
        # Create filename from ID
        filename = f"{vuln['id']}_{vuln['project']}_{vuln['date']}.json".replace('/', '_')
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
    
    parser = argparse.ArgumentParser(description='Scrape Solodit vulnerability database')
    parser.add_argument('--max-pages', type=int, default=None, help='Maximum pages to scrape')
    parser.add_argument('--start-page', type=int, default=1, help='Page to start from')
    parser.add_argument('--output-dir', type=str, default='data/solodit', help='Output directory')
    parser.add_argument('--test', action='store_true', help='Test mode (only 2 pages)')
    
    args = parser.parse_args()
    
    if args.test:
        args.max_pages = 2
        logger.info("Running in TEST mode (2 pages only)")
    
    scraper = SoloditScraper(output_dir=args.output_dir)
    scraper.scrape_all(max_pages=args.max_pages, start_page=args.start_page)
    
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
