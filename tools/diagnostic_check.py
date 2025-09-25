#!/usr/bin/env python3
"""
Diagnostic script to check system setup for OpenLegislation tools.
Checks GPU availability, Python version, and key library versions.
"""

import sys
import subprocess
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_python_version():
    """Check Python version"""
    logger.info(f"Python version: {sys.version}")
    version = sys.version_info
    if version.major == 3 and version.minor >= 10:
        logger.info("✓ Python version is 3.10 or higher")
    else:
        logger.warning("✗ Python version is below 3.10")

def check_gpu_availability():
    """Check if GPU is available"""
    try:
        import torch
        if torch.cuda.is_available():
            logger.info(f"✓ CUDA GPU available: {torch.cuda.get_device_name(0)}")
            logger.info(f"  CUDA version: {torch.version.cuda}")
            logger.info(f"  GPU count: {torch.cuda.device_count()}")
        else:
            logger.warning("✗ CUDA GPU not available")
    except ImportError:
        logger.warning("✗ PyTorch not installed, cannot check GPU")

    # Check NVIDIA drivers
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader,nounits'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"✓ NVIDIA GPU detected: {result.stdout.strip()}")
        else:
            logger.warning("✗ nvidia-smi failed")
    except FileNotFoundError:
        logger.warning("✗ nvidia-smi not found")

def check_key_libraries():
    """Check versions of key libraries"""
    libraries = ['psycopg2', 'pydantic', 'pydantic_settings', 'requests', 'pandas', 'numpy']

    for lib in libraries:
        try:
            module = __import__(lib.replace('_', ''))
            version = getattr(module, '__version__', 'unknown')
            logger.info(f"✓ {lib}: {version}")
        except ImportError:
            logger.warning(f"✗ {lib} not installed")

def check_legal_analysis_libs():
    """Check for legal document analysis libraries"""
    legal_libs = ['spacy', 'transformers', 'nltk', 'torch']

    for lib in legal_libs:
        try:
            module = __import__(lib)
            version = getattr(module, '__version__', 'unknown')
            logger.info(f"✓ {lib}: {version}")
        except ImportError:
            logger.warning(f"✗ {lib} not installed")

def check_sql_tools():
    """Check for SQL GUI tools availability"""
    tools = ['pgadmin3', 'dbeaver', 'sqlitebrowser']

    for tool in tools:
        try:
            result = subprocess.run(['which', tool], capture_output=True)
            if result.returncode == 0:
                logger.info(f"✓ {tool} available")
            else:
                logger.warning(f"✗ {tool} not available")
        except Exception:
            logger.warning(f"✗ Error checking {tool}")

if __name__ == "__main__":
    logger.info("Starting OpenLegislation diagnostic check")

    check_python_version()
    check_gpu_availability()
    check_key_libraries()
    check_legal_analysis_libs()
    check_sql_tools()

    logger.info("Diagnostic check complete")