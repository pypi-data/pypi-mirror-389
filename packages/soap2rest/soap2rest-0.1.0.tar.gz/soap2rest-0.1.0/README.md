# soap2rest

Convert any SOAP WSDL service to a REST API using FastAPI.

## Features

- 🔄 **Automatic Conversion**: Automatically converts SOAP operations to REST endpoints
- 🚀 **FastAPI Powered**: Built on FastAPI for high performance and automatic API documentation
- 🔧 **Zero Configuration**: No manual endpoint configuration needed
- 📚 **Interactive Docs**: Automatic Swagger/OpenAPI documentation at `/docs`
- 🛡️ **Error Handling**: Proper HTTP status codes for SOAP faults, timeouts, and connection errors
- ⚡ **Async Support**: Non-blocking SOAP calls using thread pool execution

## Installation

### From Source

```bash
git clone https://github.com/yourusername/soap2rest.git
cd soap2rest
pip install .
```

### From PyPI (when published)

```bash
pip install soap2rest
```

## Quick Start

1. **Start the server** with a WSDL URL:

```bash
soap2rest --wsdl https://www.dataaccess.com/webservicesserver/NumberConversion.wso?WSDL --port 8000
```

2. **View the API documentation**:

Open http://localhost:8000/docs in your browser to see the interactive Swagger UI.

3. **Call the REST API**:

```bash
curl -X POST http://localhost:8000/call/NumberToWords \
  -H "Content-Type: application/json" \
  -d '{"ubiNum": "123"}'
```

## Usage

### Basic Usage

```bash
soap2rest --wsdl <WSDL_URL> --port 8000
```

### Advanced Options

```bash
soap2rest \
  --wsdl https://example.com/service.wsdl \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info \
  --reload
```

### Environment Variables

You can also configure the server using environment variables:

```bash
export SOAP2REST_WSDL="https://example.com/service.wsdl"
export SOAP2REST_PORT=8000
export SOAP2REST_HOST="0.0.0.0"
export SOAP2REST_WORKERS=4
export SOAP2REST_LOG_LEVEL="info"
export SOAP2REST_RELOAD="true"

soap2rest
```

### Command Line Options

- `--wsdl` (required): WSDL URL or file path
- `--host` (default: `0.0.0.0`): Host to bind to
- `--port` (default: `8000`): Port to bind to
- `--workers` (default: `1`): Number of worker processes
- `--log-level` (default: `info`): Logging level (critical, error, warning, info, debug, trace)
- `--reload` (default: `false`): Enable auto-reload for development
- `--timeout-keep-alive` (default: `5`): Keep-alive timeout in seconds

## How It Works

1. **WSDL Parsing**: The tool loads and parses the WSDL file/URL
2. **Operation Discovery**: Automatically discovers all SOAP operations
3. **REST Endpoint Generation**: Creates REST endpoints for each SOAP operation
4. **Dynamic Model Creation**: Generates Pydantic models for request validation
5. **Request Processing**: Converts REST requests to SOAP calls and returns JSON responses

## Example

Given a SOAP service with operation `NumberToWords`, the tool automatically creates:

- `GET /` - Lists all available operations
- `POST /call/NumberToWords` - REST endpoint for the SOAP operation

Request:
```json
POST /call/NumberToWords
{
  "ubiNum": "123"
}
```

Response:
```json
{
  "result": "one hundred and twenty three "
}
```

## Development

### Setting Up Development Environment

```bash
git clone https://github.com/yourusername/soap2rest.git
cd soap2rest
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Building the Package

```bash
python -m build
```

### Publishing to PyPI

```bash
python -m build
python -m twine upload dist/*
```

## Requirements

- Python 3.8+
- FastAPI
- Uvicorn
- Zeep (SOAP client)
- Pydantic
- AnyIO

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue on [GitHub](https://github.com/yourusername/soap2rest/issues).
