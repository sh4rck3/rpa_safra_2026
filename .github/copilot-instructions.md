# Python Web Automation Project - Copilot Instructions

## Project Overview
This is a Python project for web automation to login to websites and download PDF documents.

## Technology Stack
- Python 3.x
- Selenium (browser automation)
- Requests (HTTP requests)
- python-dotenv (environment variables)
- webdriver-manager (automatic ChromeDriver management)

## Project Status
- [x] Create copilot-instructions.md file
- [x] Get project setup information
- [x] Scaffold Python project structure
- [x] Create main automation script
- [x] Create configuration and README
- [x] Install dependencies
- [x] Finalize documentation

✅ **Project Setup Complete!**

## Development Guidelines
- Keep code organized in src/ directory
- Store credentials in .env file (never commit)
- Save downloaded PDFs to downloads/ directory
- Follow PEP 8 style guidelines
- Use virtual environment (venv) for dependencies

## Next Steps for User
1. Copy `.env.example` to `.env` and fill in your credentials
2. Adjust login fields in `src/login_download_pdf.py` according to your website
3. Run the script: `python src/login_download_pdf.py`

## Project Structure
```
phyton/
├── .github/copilot-instructions.md
├── src/login_download_pdf.py
├── downloads/
├── venv/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```
