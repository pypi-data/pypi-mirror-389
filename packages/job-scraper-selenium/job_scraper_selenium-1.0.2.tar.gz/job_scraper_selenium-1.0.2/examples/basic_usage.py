"""
Basic usage example for job_scraper package
"""

from job_scraper import scrape_job

# Example job URLs
indeed_url = 'https://in.indeed.com/viewjob?jk=b0ffa875d50ea8b5&from=shareddesktop_copy'
linkedin_url = 'https://www.linkedin.com/jobs/view/4279541776'

print("="*60)
print("JOB SCRAPER - Basic Usage Example")
print("="*60)
print()

# Scrape Indeed job
print(">>> Scraping Indeed Job...\n")
indeed_job = scrape_job(indeed_url)

if indeed_job:
    print(f"\n✓ Successfully scraped: {indeed_job['title']}")
else:
    print("\n✗ Failed to scrape Indeed job")

print("\n" + "="*60)
print()

# Scrape LinkedIn job
print(">>> Scraping LinkedIn Job...\n")
linkedin_job = scrape_job(linkedin_url)

if linkedin_job:
    print(f"\n✓ Successfully scraped: {linkedin_job['title']}")
else:
    print("\n✗ Failed to scrape LinkedIn job")

print("\n" + "="*60)
print("\nDone!")

