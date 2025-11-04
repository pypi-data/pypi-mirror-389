import logging
import os
from cmreslogging.handlers import CMRESHandler
from ecs_logging import StdlibFormatter

# This dictionary maps Python's log level numbers to their string representation
LOG_LEVEL_MAP = {
    logging.CRITICAL: "CRITICAL",
    logging.ERROR: "ERROR",
    logging.WARNING: "WARNING",
    logging.INFO: "INFO",
    logging.DEBUG: "DEBUG",
}

class EcsAndCmresFormatter(StdlibFormatter):
    """A custom formatter to produce ECS-compliant JSON for the CMRESHandler."""
    def format(self, record):
        ecs_document_str = super().format(record)
        import json
        document = json.loads(ecs_document_str)
        document['log']['level'] = LOG_LEVEL_MAP.get(record.levelno, "UNKNOWN")
        return document

def setup_logging(service_name: str, es_hosts: list):
    """
    Configures the root logger for DUAL output:
    1. Plain text to the console.
    2. Structured JSON to Elasticsearch.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO) # Set the minimum level for the logger itself

    # --- Important: Clear any existing handlers to prevent duplicate logs ---
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # ========================================================================
    # HANDLER 1: Send logs to Elasticsearch
    # ========================================================================
    try:
        es_handler = CMRESHandler(
            hosts=es_hosts,
            auth_type=CMRESHandler.AuthType.NO_AUTH,
            es_index_name="ingestion-logs", 
            es_additional_fields={"service": {"name": service_name, "version": "3.0.0"}}
        )
        # Use our special formatter that creates JSON
        es_formatter = EcsAndCmresFormatter()
        es_handler.setFormatter(es_formatter)
        
        # Add the configured Elasticsearch handler to the root logger
        root_logger.addHandler(es_handler)
        print(f"✅ Elasticsearch logging handler configured for service '{service_name}'.")

    except Exception as e:
        print(f"⚠️ Could not configure Elasticsearch logging handler: {e}")


    # ========================================================================
    # HANDLER 2: Send logs to the Console (Terminal)
    # ========================================================================
    console_handler = logging.StreamHandler()
    
    # Use a standard, human-readable formatter for the console
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # You can set a different log level for the console if you want!
    # For example, to see DEBUG messages on console but not in ES:
    # console_handler.setLevel(logging.DEBUG) 
    
    # Add the configured console handler to the root logger
    root_logger.addHandler(console_handler)
    print(f"✅ Console logging handler configured.")