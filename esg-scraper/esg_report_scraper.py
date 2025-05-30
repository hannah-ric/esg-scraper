"""
ESG Report Scraper
Scrapes ESG reports from various sources including PDFs, websites, and APIs
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Any, Union
import logging
from urllib.parse import urlparse, urljoin
import re
from bs4 import BeautifulSoup
import PyPDF2
import pdfplumber
import requests
from io import BytesIO
import json
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)

class ESGReportScraper:
    """Advanced scraper for ESG reports from multiple sources"""
    
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Common ESG report URL patterns
        self.esg_patterns = [
            r'sustainability[\-_]report',
            r'esg[\-_]report',
            r'csr[\-_]report',
            r'annual[\-_]report',
            r'integrated[\-_]report',
            r'climate[\-_]report',
            r'tcfd[\-_]report',
            r'environmental[\-_]report',
            r'social[\-_]responsibility',
            r'non[\-_]financial[\-_]report'
        ]
        
        # Known ESG report repositories
        self.report_repositories = {
            'gri': 'https://database.globalreporting.org/',
            'cdp': 'https://www.cdp.net/en/responses',
            'sasb': 'https://www.sasb.org/company-use/sasb-reporters/'
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def scrape_company_esg_data(self, company_name: str, 
                                    company_website: Optional[str] = None,
                                    year: Optional[int] = None) -> Dict[str, Any]:
        """
        Scrape ESG data for a specific company
        
        Args:
            company_name: Name of the company
            company_website: Company website URL
            year: Specific year to look for (default: most recent)
        
        Returns:
            Dictionary containing scraped ESG data
        """
        
        results = {
            'company_name': company_name,
            'timestamp': datetime.now().isoformat(),
            'reports': [],
            'metrics': {},
            'sources': []
        }
        
        # 1. Search for reports on company website
        if company_website:
            website_reports = await self._scrape_company_website(company_website, year)
            results['reports'].extend(website_reports)
        
        # 2. Search in ESG databases
        database_reports = await self._search_esg_databases(company_name, year)
        results['reports'].extend(database_reports)
        
        # 3. Google search for reports
        google_reports = await self._google_search_reports(company_name, year)
        results['reports'].extend(google_reports)
        
        # 4. Process and extract content from found reports
        for report in results['reports'][:5]:  # Limit to top 5 reports
            content = await self._extract_report_content(report)
            if content:
                report['content'] = content
                results['sources'].append({
                    'url': report['url'],
                    'title': report['title'],
                    'type': report['type']
                })
        
        return results
    
    async def _scrape_company_website(self, website_url: str, 
                                    year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Scrape ESG reports from company website"""
        
        reports = []
        
        try:
            # Find investor relations or sustainability page
            base_url = website_url.rstrip('/')
            potential_urls = [
                f"{base_url}/sustainability",
                f"{base_url}/esg",
                f"{base_url}/investor-relations",
                f"{base_url}/investors",
                f"{base_url}/about/sustainability",
                f"{base_url}/corporate-responsibility",
                f"{base_url}/csr"
            ]
            
            for url in potential_urls:
                try:
                    async with self.session.get(url, timeout=10) as response:
                        if response.status == 200:
                            text = await response.text()
                            page_reports = await self._extract_report_links(text, url, year)
                            reports.extend(page_reports)
                except:
                    continue
            
            # Also check the main page
            async with self.session.get(base_url, timeout=10) as response:
                if response.status == 200:
                    text = await response.text()
                    main_reports = await self._extract_report_links(text, base_url, year)
                    reports.extend(main_reports)
        
        except Exception as e:
            logger.error(f"Error scraping company website: {e}")
        
        # Deduplicate reports
        seen = set()
        unique_reports = []
        for report in reports:
            report_id = report['url']
            if report_id not in seen:
                seen.add(report_id)
                unique_reports.append(report)
        
        return unique_reports
    
    async def _extract_report_links(self, html: str, base_url: str, 
                                  year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Extract ESG report links from HTML"""
        
        reports = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all links
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link['href']
            text = link.get_text(strip=True).lower()
            
            # Check if link matches ESG patterns
            if any(pattern in href.lower() or pattern in text for pattern in self.esg_patterns):
                # Check for PDF or report page
                if href.endswith('.pdf') or 'report' in text:
                    full_url = urljoin(base_url, href)
                    
                    # Extract year from link or text
                    year_match = re.search(r'20\d{2}', href + ' ' + text)
                    report_year = int(year_match.group()) if year_match else None
                    
                    # Filter by year if specified
                    if year and report_year and report_year != year:
                        continue
                    
                    reports.append({
                        'url': full_url,
                        'title': link.get_text(strip=True),
                        'type': 'pdf' if href.endswith('.pdf') else 'webpage',
                        'year': report_year,
                        'source': 'company_website'
                    })
        
        return reports
    
    async def _search_esg_databases(self, company_name: str, 
                                  year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search for reports in ESG databases"""
        
        reports = []
        
        # Simplified search - in production, would use actual APIs
        # This is a placeholder for demonstration
        
        # GRI Database search simulation
        gri_search_url = f"https://database.globalreporting.org/search/?q={company_name}"
        
        # CDP search simulation  
        cdp_search_url = f"https://www.cdp.net/en/responses?utf8=%E2%9C%93&queries%5Bname%5D={company_name}"
        
        # Add placeholder results
        if year:
            reports.append({
                'url': f"https://example.com/gri/{company_name}-{year}.pdf",
                'title': f"{company_name} GRI Report {year}",
                'type': 'pdf',
                'year': year,
                'source': 'gri_database'
            })
        
        return reports
    
    async def _google_search_reports(self, company_name: str, 
                                   year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search Google for ESG reports"""
        
        reports = []
        
        # Build search query
        query_parts = [f'"{company_name}"']
        query_parts.extend([
            '("sustainability report" OR "ESG report" OR "CSR report")',
            'filetype:pdf'
        ])
        
        if year:
            query_parts.append(str(year))
        
        query = ' '.join(query_parts)
        
        # Note: In production, you'd use Google Custom Search API
        # This is a placeholder
        logger.info(f"Would search Google for: {query}")
        
        return reports
    
    async def _extract_report_content(self, report: Dict[str, Any]) -> Optional[str]:
        """Extract text content from report"""
        
        try:
            if report['type'] == 'pdf':
                return await self._extract_pdf_content(report['url'])
            else:
                return await self._extract_webpage_content(report['url'])
        except Exception as e:
            logger.error(f"Error extracting content from {report['url']}: {e}")
            return None
    
    async def _extract_pdf_content(self, pdf_url: str) -> Optional[str]:
        """Extract text from PDF"""
        
        try:
            # Download PDF
            async with self.session.get(pdf_url, timeout=30) as response:
                if response.status == 200:
                    pdf_bytes = await response.read()
                    
                    # Try pdfplumber first (better for tables)
                    try:
                        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
                            text = ''
                            for page in pdf.pages[:50]:  # Limit to first 50 pages
                                page_text = page.extract_text()
                                if page_text:
                                    text += page_text + '\n'
                            return text
                    except:
                        # Fallback to PyPDF2
                        pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_bytes))
                        text = ''
                        for page_num in range(min(50, len(pdf_reader.pages))):
                            page = pdf_reader.pages[page_num]
                            text += page.extract_text() + '\n'
                        return text
        
        except Exception as e:
            logger.error(f"Error extracting PDF content: {e}")
            return None
    
    async def _extract_webpage_content(self, url: str) -> Optional[str]:
        """Extract text from webpage"""
        
        try:
            async with self.session.get(url, timeout=15) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    # Get text
                    text = soup.get_text()
                    
                    # Clean up text
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text = ' '.join(chunk for chunk in chunks if chunk)
                    
                    return text
        
        except Exception as e:
            logger.error(f"Error extracting webpage content: {e}")
            return None
    
    async def scrape_multiple_companies(self, companies: List[Dict[str, str]], 
                                      year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Scrape ESG data for multiple companies"""
        
        tasks = []
        for company in companies:
            task = self.scrape_company_esg_data(
                company['name'],
                company.get('website'),
                year
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error scraping {companies[i]['name']}: {result}")
            else:
                valid_results.append(result)
        
        return valid_results
    
    def extract_metrics_from_tables(self, html_or_text: str) -> List[Dict[str, Any]]:
        """Extract metrics from HTML tables"""
        
        metrics = []
        
        if '<table' in html_or_text:
            soup = BeautifulSoup(html_or_text, 'html.parser')
            tables = soup.find_all('table')
            
            for table in tables:
                # Check if table contains ESG metrics
                table_text = table.get_text().lower()
                if any(keyword in table_text for keyword in ['emission', 'energy', 'water', 'waste', 'diversity']):
                    # Extract table data
                    rows = table.find_all('tr')
                    headers = []
                    
                    for row in rows:
                        cells = row.find_all(['th', 'td'])
                        if not headers and cells:
                            headers = [cell.get_text(strip=True) for cell in cells]
                        else:
                            row_data = [cell.get_text(strip=True) for cell in cells]
                            if len(row_data) == len(headers):
                                metric_dict = dict(zip(headers, row_data))
                                metrics.append(metric_dict)
        
        return metrics


class ESGDataAggregator:
    """Aggregates ESG data from multiple sources"""
    
    def __init__(self):
        self.scraper = ESGReportScraper()
        self.sources = []
    
    async def aggregate_company_data(self, company_name: str, 
                                   company_website: Optional[str] = None,
                                   years: Optional[List[int]] = None) -> Dict[str, Any]:
        """Aggregate ESG data across multiple years"""
        
        if not years:
            years = [datetime.now().year - i for i in range(3)]  # Last 3 years
        
        aggregated_data = {
            'company_name': company_name,
            'data_by_year': {},
            'trends': {},
            'latest_metrics': {},
            'sources': []
        }
        
        async with self.scraper as scraper:
            for year in years:
                year_data = await scraper.scrape_company_esg_data(
                    company_name, company_website, year
                )
                aggregated_data['data_by_year'][year] = year_data
                aggregated_data['sources'].extend(year_data['sources'])
        
        # Calculate trends
        aggregated_data['trends'] = self._calculate_trends(aggregated_data['data_by_year'])
        
        return aggregated_data
    
    def _calculate_trends(self, data_by_year: Dict[int, Dict]) -> Dict[str, Any]:
        """Calculate trends from multi-year data"""
        
        trends = {}
        
        # Placeholder for trend calculation
        # In production, would analyze metrics across years
        
        return trends


# Example usage
async def main():
    """Example usage of ESG scraper"""
    
    async with ESGReportScraper() as scraper:
        # Scrape single company
        result = await scraper.scrape_company_esg_data(
            "Microsoft Corporation",
            "https://www.microsoft.com",
            2023
        )
        
        print(f"Found {len(result['reports'])} reports for {result['company_name']}")
        
        # Scrape multiple companies
        companies = [
            {'name': 'Apple Inc.', 'website': 'https://www.apple.com'},
            {'name': 'Google LLC', 'website': 'https://www.google.com'},
        ]
        
        results = await scraper.scrape_multiple_companies(companies, 2023)
        
        for result in results:
            print(f"{result['company_name']}: {len(result['reports'])} reports found")


if __name__ == "__main__":
    asyncio.run(main()) 