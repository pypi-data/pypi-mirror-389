import argparse
import os
import sys
import uvicorn
from soap2rest.api import create_app

def main():
    parser = argparse.ArgumentParser(description="Run a REST API for any SOAP WSDL")
    parser.add_argument("--wsdl", required=False, help="WSDL URL or file path",
                        default=os.getenv("SOAP2REST_WSDL"))
    parser.add_argument("--host", default=os.getenv("SOAP2REST_HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.getenv("SOAP2REST_PORT", "8000")))
    parser.add_argument("--reload", action="store_true", default=os.getenv("SOAP2REST_RELOAD", "false").lower() == "true")
    parser.add_argument("--workers", type=int, default=int(os.getenv("SOAP2REST_WORKERS", "1")))
    parser.add_argument("--log-level", default=os.getenv("SOAP2REST_LOG_LEVEL", "info"),
                        choices=["critical", "error", "warning", "info", "debug", "trace"])
    parser.add_argument("--timeout-keep-alive", type=int, default=int(os.getenv("SOAP2REST_TIMEOUT_KEEP_ALIVE", "5")))
    args = parser.parse_args()

    if not args.wsdl:
        print("Error: --wsdl is required (or set SOAP2REST_WSDL)", file=sys.stderr)
        sys.exit(2)

    try:
        # Early validation: attempts to parse WSDL; exceptions will be surfaced here
        app = create_app(args.wsdl)
    except Exception as exc:
        print(f"Failed to load WSDL '{args.wsdl}': {exc}", file=sys.stderr)
        sys.exit(1)

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,
        log_level=args.log_level,
        timeout_keep_alive=args.timeout_keep_alive,
    )
