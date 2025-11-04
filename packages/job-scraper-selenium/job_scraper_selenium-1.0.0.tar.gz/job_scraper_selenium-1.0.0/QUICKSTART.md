# Quick Start Guide 🚀

## Installation

Navigate to the package directory and install:

```bash
cd job_scraper_package
pip install -e .
```

Or install from PyPI (after publishing):

```bash
pip install job-scraper-selenium
```

## Usage in 30 Seconds ⚡

### 1. Import the package

```python
from job_scraper import scrape_job
```

### 2. Scrape a job

```python
job = scrape_job('https://in.indeed.com/viewjob?jk=...')
```

### 3. Access the data

```python
print(f"Title: {job['title']}")
print(f"Company: {job['company']}")
print(f"Location: {job['location']}")
print(f"Description: {job['description'][:200]}...")
```

## Complete Example

```python
from job_scraper import scrape_job

# Your job URL (Indeed or LinkedIn)
url = 'https://in.indeed.com/viewjob?jk=b0ffa875d50ea8b5'

# Scrape the job
job = scrape_job(url)

# Check if successful
if job:
    print(f"✓ Found: {job['title']} at {job['company']}")
    print(f"  Location: {job['location']}")
else:
    print("✗ Failed to scrape job")
```

## Run Examples

Try the included examples:

```bash
# Basic usage
python examples/basic_usage.py

# Advanced usage (multiple jobs + JSON export)
python examples/advanced_usage.py
```

## Common Use Cases

### Silent Mode (No Output)

```python
job = scrape_job(url, verbose=False)
```

### Show Browser (Debug Mode)

```python
job = scrape_job(url, headless=False)
```

### Scrape Multiple Jobs

```python
urls = [
    'https://in.indeed.com/viewjob?jk=...',
    'https://www.linkedin.com/jobs/view/...'
]

jobs = [scrape_job(url, verbose=False) for url in urls]
```

### Save to JSON

```python
import json

job = scrape_job(url)
with open('job.json', 'w') as f:
    json.dump(job, f, indent=2)
```

## Supported Platforms

- ✅ Indeed (all regions: US, UK, India, etc.)
- ✅ LinkedIn

## Next Steps

- Read the [full README](README.md) for detailed documentation
- Check [examples/](examples/) for more use cases
- See [CONTRIBUTING.md](CONTRIBUTING.md) to contribute
- Report issues on GitHub

## Getting Help

- 📖 [Documentation](README.md)
- 🐛 [Report a bug](https://github.com/yourusername/job-scraper/issues)
- 💬 [Ask a question](https://github.com/yourusername/job-scraper/discussions)

---

**Happy Scraping!** 🎉

