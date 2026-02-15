# 🌐 Agentic API

REST API server for the Agentic Scraper framework.

## Features

- **RESTful API**: Easy HTTP-based access to scraper
- **Batch Scraping**: Scrape multiple URLs at once
- **Tool Execution**: Execute individual tools via API
- **Memory API**: Access and update memory
- **Status Monitoring**: Track agent status

## Installation

```bash
cd agentic-api
pip install -r requirements.txt
```

## Run Server

```bash
python api.py
# Server runs on http://localhost:8000
```

## API Endpoints

### Scrape

```bash
POST /scrape
{
  "url": "https://example.com",
  "goal": "Extract article titles"
}
```

### Batch Scrape

```bash
POST /scrape/batch
{
  "targets": [
    {"url": "https://example.com", "goal": "Extract links"},
    {"url": "https://example.org", "goal": "Extract content"}
  ]
}
```

### Tools

```bash
GET /tools
POST /tools/execute
```

### Memory

```bash
GET /memory
POST /memory
GET /memory/recommendations?url=https://example.com
```

### Status

```bash
GET /status
GET /history
```

## OpenAPI Docs

Visit `http://localhost:8000/docs` for interactive API documentation.
