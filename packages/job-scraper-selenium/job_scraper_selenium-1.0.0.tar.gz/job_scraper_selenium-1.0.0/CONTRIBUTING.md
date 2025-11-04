# Contributing to Job Scraper

Thank you for your interest in contributing to Job Scraper! This document provides guidelines and instructions for contributing.

## 🤝 How to Contribute

### Reporting Bugs 🐛

If you find a bug, please open an issue with:
- A clear, descriptive title
- Steps to reproduce the bug
- Expected vs actual behavior
- Your environment (OS, Python version, etc.)
- Error messages or screenshots if applicable

### Suggesting Features 💡

We welcome feature suggestions! Please open an issue with:
- A clear description of the feature
- Use cases and benefits
- Any implementation ideas you have

### Code Contributions 🔧

#### Getting Started

1. **Fork the repository**
   ```bash
   # Click the 'Fork' button on GitHub
   ```

2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR-USERNAME/job-scraper.git
   cd job-scraper
   ```

3. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

4. **Install in development mode**
   ```bash
   pip install -e .
   pip install -r requirements.txt
   ```

#### Making Changes

1. **Write clean, readable code**
   - Follow PEP 8 style guidelines
   - Add docstrings to functions and classes
   - Use meaningful variable names

2. **Test your changes**
   ```bash
   # Run manual tests
   python examples/basic_usage.py
   ```

3. **Update documentation**
   - Update README.md if you add features
   - Add docstrings to new functions
   - Include usage examples

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add: brief description of your changes"
   ```
   
   Commit message prefixes:
   - `Add:` for new features
   - `Fix:` for bug fixes
   - `Update:` for improvements
   - `Docs:` for documentation changes
   - `Refactor:` for code refactoring

5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Open a Pull Request**
   - Go to the original repository
   - Click "New Pull Request"
   - Select your fork and branch
   - Describe your changes clearly

### Pull Request Guidelines ✅

Your PR should:
- Have a clear title and description
- Reference any related issues
- Include tests if applicable
- Update documentation if needed
- Pass all existing tests
- Follow the project's code style

## 📝 Code Style

- Follow [PEP 8](https://pep8.org/) Python style guide
- Use 4 spaces for indentation (no tabs)
- Maximum line length: 100 characters
- Use type hints where helpful

Example:
```python
def scrape_job(url: str, headless: bool = True) -> dict:
    """
    Scrape a job posting from the given URL
    
    Args:
        url: The job posting URL
        headless: Run browser in headless mode
    
    Returns:
        Dictionary containing job details
    """
    pass
```

## 🎯 Priority Areas

We especially welcome contributions in these areas:

1. **New Job Sites**
   - Add support for more job boards (Glassdoor, Monster, etc.)
   - Follow the existing scraper pattern

2. **Error Handling**
   - Improve robustness
   - Better error messages
   - Retry logic

3. **Performance**
   - Optimize scraping speed
   - Reduce resource usage
   - Parallel scraping support

4. **Documentation**
   - More examples
   - Video tutorials
   - Translations

5. **Testing**
   - Unit tests
   - Integration tests
   - CI/CD setup

## 🚀 Adding a New Job Site

To add support for a new job site:

1. Create a new function in `scraper.py`:
   ```python
   def scrape_sitename_job(url, headless=True, verbose=True):
       """Scrape from SiteName"""
       # Your implementation
       pass
   ```

2. Update the `scrape_job()` function to detect the new site:
   ```python
   def scrape_job(url, headless=True, verbose=True):
       if 'sitename.com' in url:
           return scrape_sitename_job(url, headless, verbose)
       # ... existing code
   ```

3. Export the function in `__init__.py`:
   ```python
   from .scraper import scrape_sitename_job
   __all__ = [..., 'scrape_sitename_job']
   ```

4. Add documentation and examples

## 🧪 Testing

Before submitting:

1. Test with actual URLs from each platform
2. Test both headless and non-headless modes
3. Test with verbose and silent modes
4. Check that all data fields are extracted correctly
5. Verify error handling works properly

## 📧 Questions?

If you have questions:
- Open a GitHub issue
- Email: your.email@example.com
- Include "Job Scraper" in the subject

## 📜 Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Help others learn

## 🎉 Recognition

Contributors will be:
- Listed in the README
- Credited in release notes
- Appreciated eternally 💙

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for making Job Scraper better! 🚀

