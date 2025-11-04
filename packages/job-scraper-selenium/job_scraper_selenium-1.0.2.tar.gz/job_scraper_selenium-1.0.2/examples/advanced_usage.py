"""
Advanced usage example - scraping multiple jobs and saving to JSON
"""

import json
from job_scraper import scrape_job

# List of job URLs to scrape
job_urls = [
    'https://in.indeed.com/viewjob?jk=b0ffa875d50ea8b5&from=shareddesktop_copy',
    'https://www.linkedin.com/jobs/view/4279541776',
    # Add more URLs here
]

print("="*60)
print("ADVANCED USAGE - Scraping Multiple Jobs")
print("="*60)
print(f"\nScraping {len(job_urls)} jobs...\n")

jobs = []

for i, url in enumerate(job_urls, 1):
    print(f"[{i}/{len(job_urls)}] Processing: {url[:50]}...")
    
    # Scrape in silent mode
    job = scrape_job(url, verbose=False)
    
    if job:
        jobs.append(job)
        print(f"  ✓ Success: {job['title']}")
    else:
        print(f"  ✗ Failed to scrape")
    print()

# Display summary
print("="*60)
print(f"\nSummary: Successfully scraped {len(jobs)} out of {len(job_urls)} jobs\n")

# Display results
for i, job in enumerate(jobs, 1):
    print(f"{i}. {job['title']}")
    print(f"   Company: {job['company']}")
    print(f"   Location: {job['location']}")
    print(f"   Source: {job['source']}")
    print()

# Save to JSON file
if jobs:
    output_file = 'scraped_jobs.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)
    
    print("="*60)
    print(f"✓ Jobs saved to {output_file}")
    print("="*60)

# Filter jobs by keyword
keyword = "React"
filtered_jobs = [
    job for job in jobs 
    if keyword.lower() in (job.get('description', '') or '').lower()
]

if filtered_jobs:
    print(f"\n{len(filtered_jobs)} job(s) contain the keyword '{keyword}':")
    for job in filtered_jobs:
        print(f"  - {job['title']} at {job['company']}")

