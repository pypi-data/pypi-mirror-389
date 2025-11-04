"""
Core scraper functionality for extracting job details from Indeed and LinkedIn
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time


def scrape_indeed_job(url, headless=True, verbose=True):
    """
    Scrape a single Indeed job posting using Selenium
    
    Args:
        url (str): The Indeed job posting URL
        headless (bool): Run browser in headless mode (default: True)
        verbose (bool): Print progress messages (default: True)
    
    Returns:
        dict: Job details containing title, company, location, and description
              Returns None if scraping fails
    
    Example:
        >>> from job_scraper import scrape_indeed_job
        >>> job = scrape_indeed_job('https://in.indeed.com/viewjob?jk=...')
        >>> print(job['title'])
    """
    
    # Setup Chrome options
    chrome_options = Options()
    if headless:
        chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = None
    try:
        if verbose:
            print(f"Starting browser...")
            print(f"Fetching job from: {url}\n")
        
        # Initialize the driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Load the page
        driver.get(url)
        time.sleep(3)  # Wait for page to load
        
        # Get page source and parse with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Extract job title
        title = None
        title_selectors = [
            ('h1', {'class': 'jobsearch-JobInfoHeader-title'}),
            ('h1', {'class': 'icl-u-xs-mb--xs'}),
            ('span', {'id': 'jobTitle'}),
            ('h2', {'class': 'jobsearch-JobInfoHeader-title'}),
        ]
        for tag, attrs in title_selectors:
            title_elem = soup.find(tag, attrs)
            if title_elem:
                title = title_elem.text.strip()
                break
        
        # If still not found, try with Selenium directly
        if not title:
            try:
                title_elem = driver.find_element(By.TAG_NAME, 'h1')
                title = title_elem.text.strip()
            except:
                pass
        
        # Extract company name
        company = None
        company_selectors = [
            ('div', {'class': 'jobsearch-InlineCompanyRating'}),
            ('div', {'data-company-name': True}),
            ('a', {'data-testid': 'inlineHeader-companyName'}),
            ('span', {'class': 'css-1f8zkg3'}),
        ]
        for tag, attrs in company_selectors:
            company_elem = soup.find(tag, attrs)
            if company_elem:
                company = company_elem.text.strip().split('\n')[0]
                break
        
        # Extract location
        location = None
        location_selectors = [
            ('div', {'data-testid': 'job-location'}),
            ('div', {'class': 'jobsearch-JobInfoHeader-subtitle'}),
            ('div', {'data-testid': 'inlineHeader-companyLocation'}),
        ]
        for tag, attrs in location_selectors:
            location_elem = soup.find(tag, attrs)
            if location_elem:
                location = location_elem.text.strip()
                break
        
        # Extract job description
        description = None
        desc_elem = soup.find('div', {'id': 'jobDescriptionText'})
        if desc_elem:
            description = desc_elem.text.strip()
        
        # Display results if verbose
        if verbose:
            print("="*60)
            print("JOB DETAILS")
            print("="*60)
            print(f"Title: {title or 'Not found'}")
            print(f"Company: {company or 'Not found'}")
            print(f"Location: {location or 'Not found'}")
            
            if description:
                print(f"\nDescription:")
                try:
                    print(description[:300] + "..." if len(description) > 300 else description)
                except UnicodeEncodeError:
                    print(description.encode('ascii', 'ignore').decode('ascii')[:300] + "...")
            else:
                print("\nDescription: Not found")
            
            print("="*60)
        
        return {
            'title': title,
            'company': company,
            'location': location,
            'description': description,
            'source': 'Indeed',
            'url': url
        }
    
    except Exception as e:
        if verbose:
            print(f"Error: {e}")
        return None
    finally:
        if driver:
            driver.quit()
            if verbose:
                print("\nBrowser closed.")


def scrape_linkedin_job(url, headless=True, verbose=True):
    """
    Scrape a single LinkedIn job posting using Selenium
    
    Args:
        url (str): The LinkedIn job posting URL
        headless (bool): Run browser in headless mode (default: True)
        verbose (bool): Print progress messages (default: True)
    
    Returns:
        dict: Job details containing title, company, location, and description
              Returns None if scraping fails
    
    Example:
        >>> from job_scraper import scrape_linkedin_job
        >>> job = scrape_linkedin_job('https://www.linkedin.com/jobs/view/...')
        >>> print(job['company'])
    """
    
    # Setup Chrome options
    chrome_options = Options()
    if headless:
        chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = None
    try:
        if verbose:
            print(f"Starting browser...")
            print(f"Fetching LinkedIn job from: {url}\n")
        
        # Initialize the driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Load the page
        driver.get(url)
        time.sleep(5)  # Wait longer for LinkedIn to load
        
        # Get page source and parse with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Extract job title
        title = None
        title_selectors = [
            ('h1', {'class': 'top-card-layout__title'}),
            ('h2', {'class': 'top-card-layout__title'}),
            ('h1', {}),
        ]
        for tag, attrs in title_selectors:
            title_elem = soup.find(tag, attrs)
            if title_elem:
                title = title_elem.text.strip()
                break
        
        # Extract company name
        company = None
        company_selectors = [
            ('a', {'class': 'topcard__org-name-link'}),
            ('span', {'class': 'topcard__flavor'}),
            ('div', {'class': 'topcard__org-name-link'}),
        ]
        for tag, attrs in company_selectors:
            company_elem = soup.find(tag, attrs)
            if company_elem:
                company = company_elem.text.strip()
                break
        
        # Extract location
        location = None
        location_selectors = [
            ('span', {'class': 'topcard__flavor--bullet'}),
            ('span', {'class': 'topcard__flavor'}),
        ]
        for tag, attrs in location_selectors:
            location_elem = soup.find(tag, attrs)
            if location_elem:
                location = location_elem.text.strip()
                break
        
        # Extract job description
        description = None
        desc_selectors = [
            ('div', {'class': 'show-more-less-html__markup'}),
            ('div', {'class': 'description__text'}),
            ('section', {'class': 'description'}),
        ]
        for tag, attrs in desc_selectors:
            desc_elem = soup.find(tag, attrs)
            if desc_elem:
                description = desc_elem.text.strip()
                break
        
        # Try to get more details from the page
        if not description:
            all_text_divs = soup.find_all('div')
            for div in all_text_divs:
                text = div.get_text(strip=True)
                if len(text) > 200:  # Likely description
                    description = text
                    break
        
        # Display results if verbose
        if verbose:
            print("="*60)
            print("LINKEDIN JOB DETAILS")
            print("="*60)
            print(f"Title: {title or 'Not found'}")
            print(f"Company: {company or 'Not found'}")
            print(f"Location: {location or 'Not found'}")
            
            if description:
                print(f"\nDescription:")
                try:
                    print(description[:300] + "..." if len(description) > 300 else description)
                except UnicodeEncodeError:
                    print(description.encode('ascii', 'ignore').decode('ascii')[:300] + "...")
            else:
                print("\nDescription: Not found")
            
            print("="*60)
        
        return {
            'title': title,
            'company': company,
            'location': location,
            'description': description,
            'source': 'LinkedIn',
            'url': url
        }
    
    except Exception as e:
        if verbose:
            print(f"Error: {e}")
        return None
    finally:
        if driver:
            driver.quit()
            if verbose:
                print("\nBrowser closed.")


def scrape_job(url, headless=True, verbose=True):
    """
    Automatically detect and scrape jobs from Indeed or LinkedIn
    
    Args:
        url (str): The job posting URL (Indeed or LinkedIn)
        headless (bool): Run browser in headless mode (default: True)
        verbose (bool): Print progress messages (default: True)
    
    Returns:
        dict: Job details containing title, company, location, description, source, and url
              Returns None if the platform is unsupported or scraping fails
    
    Example:
        >>> from job_scraper import scrape_job
        >>> job = scrape_job('https://in.indeed.com/viewjob?jk=...')
        >>> if job:
        ...     print(f"Found job: {job['title']} at {job['company']}")
    """
    if 'linkedin.com' in url:
        return scrape_linkedin_job(url, headless=headless, verbose=verbose)
    elif 'indeed.com' in url:
        return scrape_indeed_job(url, headless=headless, verbose=verbose)
    else:
        if verbose:
            print("Error: Unsupported job site. Currently supports Indeed and LinkedIn.")
        return None

