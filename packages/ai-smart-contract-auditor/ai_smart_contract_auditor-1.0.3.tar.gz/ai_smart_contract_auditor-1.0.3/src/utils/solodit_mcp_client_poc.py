#!/usr/bin/env python3
"""
Proof-of-Concept: Solodit MCP Client
Tests connectivity and basic functionality with Solodit MCP server.
"""

import requests
import time
import logging
from typing import List, Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SoloditMCPClient:
    """Client for interacting with Solodit MCP server."""
    
    def __init__(self, mcp_url="http://localhost:3000/mcp", rate_limit=0.5):
        self.mcp_url = mcp_url
        self.rate_limit = rate_limit
        self.session = requests.Session()
        self.last_request_time = 0
        self.stats = {
            'searches': 0,
            'gets': 0,
            'errors': 0
        }
    
    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self.last_request_time = time.time()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def search(self, keywords: str) -> List[str]:
        """Search for vulnerability reports by keywords."""
        self._rate_limit()
        
        try:
            response = self.session.post(
                self.mcp_url,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                },
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "search",
                        "arguments": {"keywords": keywords}
                    }
                },
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            # Extract results from MCP response
            if 'result' in result and 'content' in result['result']:
                content = result['result']['content']
                if isinstance(content, list) and len(content) > 0:
                    # Parse the text content which contains the results
                    text_content = content[0].get('text', '[]')
                    import json as json_lib
                    results = json_lib.loads(text_content)
                else:
                    results = []
            else:
                results = []
            
            self.stats['searches'] += 1
            logger.info(f"Search '{keywords}' returned {len(results)} results")
            return results
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Search failed for '{keywords}': {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_by_title(self, title: str) -> Dict:
        """Get full report content by title."""
        self._rate_limit()
        
        try:
            response = self.session.post(
                self.mcp_url,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                },
                json={
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "get-by-title",
                        "arguments": {"title": title}
                    }
                },
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            # Extract report from MCP response
            if 'result' in result and 'content' in result['result']:
                content = result['result']['content']
                if isinstance(content, list) and len(content) > 0:
                    text_content = content[0].get('text', '{}')
                    import json as json_lib
                    report = json_lib.loads(text_content)
                else:
                    report = {}
            else:
                report = {}
            
            self.stats['gets'] += 1
            logger.info(f"Retrieved report: {title[:50]}...")
            return report
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Get failed for '{title}': {e}")
            raise
    
    def get_stats(self) -> Dict:
        """Get client statistics."""
        return self.stats


def test_mcp_connectivity():
    """Test MCP server connectivity and basic operations."""
    print("="*60)
    print("SOLODIT MCP CLIENT - PROOF OF CONCEPT")
    print("="*60)
    
    client = SoloditMCPClient()
    
    # Test 1: Basic search
    print("\n[TEST 1] Basic Search")
    try:
        results = client.search("reentrancy")
        print(f"✓ Search successful: {len(results)} results")
        if results:
            print(f"  Sample titles:")
            for title in results[:3]:
                print(f"    - {title[:60]}...")
    except Exception as e:
        print(f"✗ Search failed: {e}")
        return False
    
    # Test 2: Get by title
    print("\n[TEST 2] Get Report by Title")
    if results:
        try:
            report = client.get_by_title(results[0])
            print(f"✓ Get successful")
            print(f"  Title: {report.get('title', 'N/A')[:60]}...")
            print(f"  Keys: {list(report.keys())}")
        except Exception as e:
            print(f"✗ Get failed: {e}")
            return False
    
    # Test 3: Multiple searches
    print("\n[TEST 3] Multiple Search Terms")
    search_terms = ["integer overflow", "access control", "delegatecall"]
    all_titles = set()
    
    for term in search_terms:
        try:
            titles = client.search(term)
            all_titles.update(titles)
            print(f"✓ '{term}': {len(titles)} results")
        except Exception as e:
            print(f"✗ '{term}' failed: {e}")
    
    print(f"\n  Total unique titles: {len(all_titles)}")
    
    # Test 4: Performance benchmark
    print("\n[TEST 4] Performance Benchmark")
    start_time = time.time()
    
    sample_titles = list(all_titles)[:5]
    for title in sample_titles:
        try:
            client.get_by_title(title)
        except:
            pass
    
    elapsed = time.time() - start_time
    avg_time = elapsed / len(sample_titles)
    
    print(f"  Processed {len(sample_titles)} reports in {elapsed:.2f}s")
    print(f"  Average time per report: {avg_time:.2f}s")
    print(f"  Estimated time for 49K reports: {(avg_time * 49000) / 3600:.1f} hours")
    
    # Statistics
    print("\n[STATISTICS]")
    stats = client.get_stats()
    print(f"  Searches: {stats['searches']}")
    print(f"  Gets: {stats['gets']}")
    print(f"  Errors: {stats['errors']}")
    print(f"  Success rate: {((stats['searches'] + stats['gets'] - stats['errors']) / (stats['searches'] + stats['gets']) * 100):.1f}%")
    
    print("\n" + "="*60)
    print("POC COMPLETE")
    print("="*60)
    
    return True


if __name__ == "__main__":
    success = test_mcp_connectivity()
    exit(0 if success else 1)
