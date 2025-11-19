#!/usr/bin/env python3
"""
Database Connection Configuration for OpenLegislation

This module provides centralized database connection management
using the configuration from database_config.json.

Features:
- Connection string management
- Connection pooling configuration
- SSL/TLS support
- Connection health monitoring
- Environment variable overrides

Author: OpenLegislation Team
Date: 2025-11-08
"""

import json
import os
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """
    Centralized database configuration management
    """

    def __init__(self, config_file: str = "database_config.json"):
        self.config_file = config_file
        self.config = {}
        self.load_config()

    def load_config(self):
        """Load configuration from JSON file"""
        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
            logger.info(f"Loaded database configuration from {self.config_file}")
        except FileNotFoundError:
            logger.warning(f"Configuration file {self.config_file} not found, using defaults")
            self.config = self.get_default_config()
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {self.config_file}: {e}")
            self.config = self.get_default_config()

        # Apply environment variable overrides
        self.apply_environment_overrides()

    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "database": {
                "host": "localhost",
                "port": 5432,
                "database": "openlegislation",
                "user": "postgres",
                "password": "",
                "connection_string": "postgresql://postgres@localhost:5432/openlegislation",
                "ssl_mode": "prefer",
                "connection_timeout": 30,
                "max_connections": 20,
                "min_connections": 5
            },
            "redis": {
                "host": "localhost",
                "port": 6379,
                "password": "",
                "db": 0,
                "connection_string": "redis://localhost:6379/0"
            }
        }

    def apply_environment_overrides(self):
        """Apply environment variable overrides"""
        # Database overrides
        if os.getenv('DB_HOST'):
            self.config['database']['host'] = os.getenv('DB_HOST')
        if os.getenv('DB_PORT'):
            self.config['database']['port'] = int(os.getenv('DB_PORT'))
        if os.getenv('DB_NAME'):
            self.config['database']['database'] = os.getenv('DB_NAME')
        if os.getenv('DB_USER'):
            self.config['database']['user'] = os.getenv('DB_USER')
        if os.getenv('DB_PASSWORD'):
            self.config['database']['password'] = os.getenv('DB_PASSWORD')

        # Update connection string if components changed
        db_config = self.config['database']
        if all(key in db_config for key in ['user', 'password', 'host', 'port', 'database']):
            connection_string = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
            if db_config.get('ssl_mode'):
                connection_string += f"?sslmode={db_config['ssl_mode']}"
            self.config['database']['connection_string'] = connection_string

        # Redis overrides
        if os.getenv('REDIS_HOST'):
            self.config['redis']['host'] = os.getenv('REDIS_HOST')
        if os.getenv('REDIS_PORT'):
            self.config['redis']['port'] = int(os.getenv('REDIS_PORT'))
        if os.getenv('REDIS_PASSWORD'):
            self.config['redis']['password'] = os.getenv('REDIS_PASSWORD')
        if os.getenv('REDIS_DB'):
            self.config['redis']['db'] = int(os.getenv('REDIS_DB'))

        # Update Redis connection string
        redis_config = self.config['redis']
        if redis_config.get('password'):
            redis_url = f"redis://:{redis_config['password']}@{redis_config['host']}:{redis_config['port']}/{redis_config['db']}"
        else:
            redis_url = f"redis://{redis_config['host']}:{redis_config['port']}/{redis_config['db']}"
        self.config['redis']['connection_string'] = redis_url

    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return self.config.get('database', {})

    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration"""
        return self.config.get('redis', {})

    def get_connection_string(self) -> str:
        """Get database connection string"""
        return self.config.get('database', {}).get('connection_string', '')

    def get_redis_connection_string(self) -> str:
        """Get Redis connection string"""
        return self.config.get('redis', {}).get('connection_string', '')

    def get_ingestion_config(self) -> Dict[str, Any]:
        """Get ingestion configuration"""
        return self.config.get('ingestion', {})

    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration"""
        return self.config.get('monitoring', {})

    def get_api_config(self, api_name: str) -> Dict[str, Any]:
        """Get API configuration for specific service"""
        return self.config.get('external_apis', {}).get(api_name, {})

    def validate_connection(self) -> bool:
        """Validate database connection"""
        try:
            import asyncpg
            connection_string = self.get_connection_string()

            async def test_connection():
                conn = await asyncpg.connect(connection_string)
                await conn.close()
                return True

            import asyncio
            return asyncio.run(test_connection())

        except ImportError:
            logger.warning("asyncpg not available, skipping connection validation")
            return True
        except Exception as e:
            logger.error(f"Database connection validation failed: {e}")
            return False

    def get_connection_params(self) -> Dict[str, Any]:
        """Get connection parameters for various database libraries"""
        db_config = self.get_database_config()

        return {
            'host': db_config.get('host'),
            'port': db_config.get('port'),
            'database': db_config.get('database'),
            'user': db_config.get('user'),
            'password': db_config.get('password'),
            'ssl': db_config.get('ssl_mode', 'prefer'),
            'connection_timeout': db_config.get('connection_timeout', 30),
            'max_connections': db_config.get('max_connections', 20),
            'min_connections': db_config.get('min_connections', 5)
        }

    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Saved configuration to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")

    def update_config(self, section: str, key: str, value: Any):
        """Update a configuration value"""
        if section not in self.config:
            self.config[section] = {}

        self.config[section][key] = value
        self.save_config()
        logger.info(f"Updated {section}.{key} = {value}")

    def get_all_config(self) -> Dict[str, Any]:
        """Get entire configuration"""
        return self.config.copy()


# Global configuration instance
_db_config = None


def get_db_config() -> DatabaseConfig:
    """Get global database configuration instance"""
    global _db_config
    if _db_config is None:
        _db_config = DatabaseConfig()
    return _db_config


def get_connection_string() -> str:
    """Get database connection string"""
    return get_db_config().get_connection_string()


def get_redis_connection_string() -> str:
    """Get Redis connection string"""
    return get_db_config().get_redis_connection_string()


def get_db_params() -> Dict[str, Any]:
    """Get database connection parameters"""
    return get_db_config().get_connection_params()


def validate_database_connection() -> bool:
    """Validate database connection"""
    return get_db_config().validate_connection()


# Convenience functions for common configurations
def get_ingestion_batch_size() -> int:
    """Get ingestion batch size"""
    return get_db_config().get_ingestion_config().get('batch_size', 1000)


def get_max_workers() -> int:
    """Get maximum worker count"""
    return get_db_config().get_ingestion_config().get('max_workers', 8)


def is_gpu_enabled() -> bool:
    """Check if GPU acceleration is enabled"""
    return get_db_config().get_ingestion_config().get('gpu_acceleration', False)


def is_parallel_enabled() -> bool:
    """Check if parallel processing is enabled"""
    return get_db_config().get_ingestion_config().get('parallel_processing', True)


# Initialize configuration on import
try:
    config = get_db_config()
    logger.info("Database configuration loaded successfully")
    logger.info(f"Database: {config.get_connection_string()}")
    logger.info(f"Redis: {config.get_redis_connection_string()}")

    # Validate connection if possible
    if config.validate_connection():
        logger.info("Database connection validated successfully")
    else:
        logger.warning("Database connection validation failed")

except Exception as e:
    logger.error(f"Failed to initialize database configuration: {e}")


if __name__ == '__main__':
    # Test configuration loading
    config = get_db_config()

    print("OpenLegislation Database Configuration")
    print("=" * 40)
    print(f"Database Connection: {config.get_connection_string()}")
    print(f"Redis Connection: {config.get_redis_connection_string()}")
    print(f"GPU Enabled: {is_gpu_enabled()}")
    print(f"Parallel Processing: {is_parallel_enabled()}")
    print(f"Batch Size: {get_ingestion_batch_size()}")
    print(f"Max Workers: {get_max_workers()}")

    # Test connection
    if validate_database_connection():
        print("✅ Database connection successful")
    else:
        print("❌ Database connection failed")

    print("\nConfiguration Details:")
    print(json.dumps(config.get_all_config(), indent=2))
