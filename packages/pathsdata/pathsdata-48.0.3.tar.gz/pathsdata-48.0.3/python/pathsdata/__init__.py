# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""PathsData Enhanced DataFusion with Iceberg Support.

This package provides a simplified, enhanced interface for working with
Apache Iceberg tables using DataFusion, specifically optimized for PathsData
workflows.

Key Features:
- Automatic Iceberg support with zero configuration
- Enhanced S3 credential discovery
- Simplified catalog management
- Full DataFusion compatibility

Quick Start:
    Basic usage with automatic Iceberg support:
    
    >>> from pathsdata import SessionContext
    >>> ctx = SessionContext()
    >>> catalog = ctx.create_catalog("warehouse", region="us-east-1")
    >>> 
    >>> # Create table
    >>> catalog.execute_ddl(ctx, '''
    ...     CREATE EXTERNAL TABLE warehouse.default.products (
    ...         id BIGINT,
    ...         name VARCHAR,
    ...         price DECIMAL(10,2)
    ...     ) STORED AS ICEBERG
    ...     LOCATION 's3://bucket/warehouse/products'
    ... ''')
    >>> 
    >>> # Insert data
    >>> ctx.sql("INSERT INTO warehouse.default.products VALUES (1, 'Laptop', 999.99)").collect()
    >>> 
    >>> # Query data
    >>> df = ctx.sql("SELECT * FROM warehouse.default.products")
    >>> results = df.collect()

Advanced Usage:
    Working with multiple catalog types:
    
    >>> from pathsdata import SessionContext, GlueCatalog, FileCatalog
    >>> 
    >>> ctx = SessionContext()
    >>> 
    >>> # AWS Glue catalog
    >>> glue = GlueCatalog("warehouse", region="us-east-1")
    >>> ctx.register_catalog_provider("glue", glue._internal)
    >>> 
    >>> # File-based catalog
    >>> file = FileCatalog("/path/to/catalog")
    >>> ctx.register_catalog_provider("local", file._internal)
"""

from __future__ import annotations

try:
    import importlib.metadata as importlib_metadata
except ImportError:
    import importlib_metadata

from .catalog import Catalog, FileCatalog, GlueCatalog, RestCatalog
from .context import SessionContext

# Version information
try:
    __version__ = importlib_metadata.version("pathsdata")
except importlib_metadata.PackageNotFoundError:
    __version__ = "unknown"

# Public API
__all__ = [
    "SessionContext",
    "Catalog", 
    "GlueCatalog",
    "FileCatalog", 
    "RestCatalog",
    # Convenience aliases
    "Glue",
    "File", 
    "Rest",
]

# Convenience aliases (imported from catalog.py)
from .catalog import Glue, File, Rest  # noqa: E402