# PopeFeed Scrapper

A Python-based web scraper that extracts papal documents from the Vatican website and generates a comprehensive API for the PopeFeed platform.

## 🎯 Overview

The PopeFeed Scrapper is responsible for:
- 📄 Scraping papal documents from Vatican.va
- 🖼️ Downloading official pope images
- 🌍 Multi-language content extraction
- 📊 Generating structured JSON API
- 🔄 Creating paginated social media feeds

This scrapper generates data for the [PopeFeed API](https://github.com/popefeed/api) which is consumed by the [PopeFeed Site](https://github.com/popefeed/site).

## ✨ Features

- **Multi-language Scraping**: Supports EN, ES, PT, IT, FR, LA
- **Document Types**: Encyclicals, Apostolic Letters, Motu Proprio, etc.
- **Vatican Image Integration**: Downloads official pope photographs
- **PDF Extraction**: Retrieves documents in multiple languages
- **Social Feed Generation**: Creates Instagram-style post feeds
- **Concurrent Processing**: Async/await for efficient scraping
- **Resume Capability**: Continue interrupted scraping sessions

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Setup

```bash
# Clone the repository
git clone https://github.com/popefeed/scrapper.git
cd scrapper

# Install dependencies
pip install -r requirements.txt

# Or use virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Dependencies

```txt
aiohttp>=3.8.0
beautifulsoup4>=4.11.0
langdetect>=1.0.9
aiofiles>=22.1.0
requests>=2.28.0
```

## 🚀 Usage

### Basic Scraping

```bash
# Scrape documents (English only by default)
python main.py

# Scrape with specific languages
python main.py --languages en,es,pt,it,fr,la

# Resume interrupted scrape
python main.py --resume

# Verbose output
python main.py --verbose
```

### Image Download

```bash
# Download pope images from Vatican website
python scrapper/image_downloader.py
```

### API Generation

```bash
# Generate posts API with pope images
python generate_posts_api.py
```

### Complete Workflow

```bash
# Full pipeline
python main.py                              # 1. Scrape documents
python scrapper/image_downloader.py         # 2. Download images
python generate_posts_api.py                # 3. Generate API
```

## 📁 Project Structure

```
scrapper/
├── scrapper/                   # Core scraping modules
│   ├── __init__.py
│   ├── base_scraper.py        # Base scraper class
│   ├── document_scraper.py    # Document extraction
│   ├── pope_scraper.py        # Pope information
│   ├── image_downloader.py    # Vatican image scraping
│   └── utils.py               # Utility functions
├── models/                     # Data models
│   ├── __init__.py
│   ├── pope.py                # Pope data model
│   └── document.py            # Document data model
├── api_generator/              # API generation
│   ├── __init__.py
│   ├── feed_generator.py      # Language feeds
│   └── posts_generator.py     # Social media posts
├── main.py                     # Main scraper entry point
├── generate_posts_api.py       # Posts API generator
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🔧 Configuration

### Command Line Options

```bash
python main.py [OPTIONS]

Options:
  --languages TEXT    Comma-separated list of languages (en,es,pt,it,fr,la)
  --resume           Resume interrupted scraping session
  --verbose          Enable verbose logging
  --output PATH      Output directory for API files (default: ../api)
  --help             Show help message
```

### Environment Variables

```bash
# Optional: Set custom output directory
export POPEFEED_API_DIR="/path/to/api"

# Optional: Set custom user agent
export POPEFEED_USER_AGENT="PopeFeed Scrapper 1.0"
```

## 📊 Data Models

### Pope Model

```python
@dataclass
class Pope:
    id: str
    names: Dict[str, str]
    image_url: Optional[str] = None
    local_image_path: Optional[str] = None
    coat_of_arms_url: Optional[str] = None
    local_coat_of_arms_path: Optional[str] = None
    reign_start: Optional[str] = None
    reign_end: Optional[str] = None
    biographies: Dict[str, str] = field(default_factory=dict)
```

### Document Model

```python
@dataclass
class Document:
    id: str
    pope_id: str
    type: str
    title: str
    date: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    available_languages: List[str] = field(default_factory=list)
    local_pdfs: Dict[str, str] = field(default_factory=dict)
    excerpts: Dict[str, str] = field(default_factory=dict)
```

## 🔄 Integration with Other Components

### With PopeFeed API

The scrapper generates data for the [PopeFeed API](https://github.com/popefeed/api):

```bash
# Scrapper output structure
../api/
├── popes.json              # Generated by scrapper
├── popes/                  # Pope images downloaded by image_downloader.py
├── documents/              # Document metadata
├── posts/                  # Generated by generate_posts_api.py
└── feed/                   # Language-specific feeds
```

### With PopeFeed Site

The scrapper prepares data consumed by the [PopeFeed Site](https://github.com/popefeed/site):

```bash
# Site configuration in hugo.toml
[params]
  api_base_url = "http://localhost:8000"  # Points to generated API
```

## 🌐 Vatican Website Structure

The scrapper understands Vatican.va URL patterns:

```
https://vatican.va/content/{pope}/{lang}/{doc-type}/
├── francesco/en/encyclicals/       # Pope Francis English encyclicals
├── francesco/es/encyclicals/       # Pope Francis Spanish encyclicals
├── francesco/img/biografia/        # Pope Francis images
├── benedictus-xvi/en/encyclicals/  # Benedict XVI English encyclicals
└── ...
```

## 🔍 Scraping Process

### 1. Pope Discovery
```python
# Discovers all popes from Vatican structure
popes = await discover_popes()
```

### 2. Document Extraction
```python
# For each pope and language
documents = await scrape_documents(pope_id, language)
```

### 3. Image Download
```python
# Downloads official Vatican images
await download_pope_images()
```

### 4. API Generation
```python
# Creates structured JSON API
await generate_api_files()
```

## 📈 Performance

- **Concurrent Processing**: Uses aiohttp for async requests
- **Rate Limiting**: Respects Vatican.va server limits
- **Resume Capability**: Continues from last successful scrape
- **Memory Efficient**: Processes documents in batches

### Typical Performance

- **Documents**: ~123 documents in 15-20 minutes
- **Images**: 12 pope images in 2-3 minutes
- **API Generation**: Complete API in 30-60 seconds

## 🛡️ Error Handling

- **Network Errors**: Automatic retry with exponential backoff
- **Invalid PDFs**: Validation and error reporting
- **Missing Content**: Graceful handling of unavailable documents
- **Rate Limiting**: Automatic throttling

## 🧪 Testing

```bash
# Test scraper components
python -m pytest tests/

# Test specific module
python -m pytest tests/test_document_scraper.py

# Run with coverage
python -m pytest --cov=scrapper tests/
```

## 📝 Logging

The scrapper provides detailed logging:

```bash
# Enable verbose logging
python main.py --verbose

# Log levels
INFO  - General progress information
WARN  - Non-critical issues (missing translations, etc.)
ERROR - Critical errors (network failures, invalid data)
```

## 🔗 Related Projects

- **[PopeFeed API](https://github.com/popefeed/api)** - Generated API data
- **[PopeFeed Site](https://github.com/popefeed/site)** - Frontend that consumes the API
- **[PopeFeed Main](https://github.com/popefeed/popefeed)** - Main repository with subtrees

## 🌍 Supported Languages

| Code | Language | Vatican.va Path |
|------|----------|----------------|
| `en` | English | `/en/` |
| `es` | Spanish | `/es/` |
| `pt` | Portuguese | `/pt/` |
| `it` | Italian | `/it/` |
| `fr` | French | `/fr/` |
| `la` | Latin | `/la/` |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Setup

```bash
# Clone for development
git clone https://github.com/popefeed/scrapper.git
cd scrapper

# Setup development environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Additional dev dependencies

# Run tests
python -m pytest
```

## 📄 Data Source

All content is sourced from the official Vatican website:
- **Main Site**: https://vatican.va
- **Document Structure**: https://vatican.va/content/{pope}/{lang}/{doc-type}/
- **Image Repository**: https://vatican.va/content/{pope}/img/biografia/
- **PDF Files**: https://vatican.va/content/dam/{pope}/pdf/

## 📜 License

MIT License - see LICENSE file for details.

## ⚠️ Usage Guidelines

- **Respect Vatican.va**: Use reasonable request rates
- **Attribution**: Credit Vatican.va as the source
- **Terms of Service**: Follow Vatican website terms
- **Educational Use**: Designed for educational and religious purposes

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/popefeed/scrapper/issues)
- **Documentation**: [PopeFeed Main Repo](https://github.com/popefeed/popefeed)
- **Vatican Source**: [Vatican.va](https://vatican.va)

## 🎉 Acknowledgments

- Vatican.va for providing official papal documents
- aiohttp team for excellent async HTTP library
- BeautifulSoup for HTML parsing capabilities