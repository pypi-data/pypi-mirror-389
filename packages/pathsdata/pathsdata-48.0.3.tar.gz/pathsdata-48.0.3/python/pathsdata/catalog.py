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

"""PathsData Catalog Management with enhanced Iceberg support."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from datafusion import IcebergCatalogProvider

if TYPE_CHECKING:
    from pathsdata.context import SessionContext


class Catalog:
    """Enhanced Iceberg Catalog with simplified API.
    
    This class wraps the IcebergCatalogProvider with a cleaner, more intuitive
    interface for catalog operations.
    
    Features:
    - Enhanced S3 credential discovery
    - Simplified DDL execution
    - Factory methods for different catalog types
    """
    
    def __init__(self, internal_catalog: Any) -> None:
        """Initialize catalog with internal implementation.
        
        Args:
            internal_catalog: The underlying IcebergCatalogProvider instance.
        """
        self._internal = internal_catalog
    
    @staticmethod
    def create(
        catalog_type: str, 
        name: str, 
        region: str = "us-east-1",
        **kwargs: Any
    ) -> "Catalog":
        """Create a catalog of the specified type.
        
        Args:
            catalog_type: Type of catalog ("glue", "file", "rest").
            name: Name of the catalog/warehouse.
            region: AWS region for Glue catalogs.
            **kwargs: Additional catalog-specific arguments.
            
        Returns:
            A Catalog instance ready for use.
            
        Raises:
            ValueError: If catalog_type is not supported.
        """
        if catalog_type == "glue":
            return GlueCatalog(name, region)
        elif catalog_type == "file":
            path = kwargs.get("path")
            if path is None:
                raise ValueError("path is required for file catalogs")
            return FileCatalog(path)
        elif catalog_type == "rest":
            endpoint = kwargs.get("endpoint")
            if endpoint is None:
                raise ValueError("endpoint is required for REST catalogs")
            token = kwargs.get("token")
            return RestCatalog(endpoint, token)
        else:
            raise ValueError(f"Unsupported catalog type: {catalog_type}")
    
    def execute_ddl(self, ctx: "SessionContext", sql: str) -> None:
        """Execute Iceberg DDL operations.
        
        Args:
            ctx: The SessionContext to execute against.
            sql: The DDL SQL statement to execute.
            
        Example:
            >>> catalog = GlueCatalog("warehouse", "us-east-1")
            >>> catalog.execute_ddl(ctx, '''
            ...     CREATE EXTERNAL TABLE warehouse.default.products (
            ...         id BIGINT,
            ...         name VARCHAR,
            ...         price DECIMAL(10,2)
            ...     ) STORED AS ICEBERG
            ...     LOCATION 's3://bucket/warehouse/products'
            ... ''')
        """
        return self._internal.execute_ddl(ctx, sql)
    
    def __repr__(self) -> str:
        """String representation of the catalog."""
        return f"{self.__class__.__name__}({self._internal!r})"


class GlueCatalog(Catalog):
    """AWS Glue-based Iceberg Catalog.
    
    Uses AWS Glue as the metadata store for Iceberg tables with enhanced
    S3 credential discovery for data access.
    
    Features:
    - Automatic AWS credential discovery
    - Multi-region support
    - Integration with AWS Glue Data Catalog
    """
    
    def __init__(self, warehouse_name: str, region: str = "us-east-1") -> None:
        """Create a new Glue-based Iceberg catalog.
        
        Args:
            warehouse_name: Name of the Iceberg warehouse in Glue.
            region: AWS region where the Glue catalog is located.
            
        Example:
            >>> catalog = GlueCatalog("my_warehouse", "us-west-2")
        """
        internal = IcebergCatalogProvider(warehouse_name, region)
        super().__init__(internal)
        self.warehouse_name = warehouse_name
        self.region = region
    
    def __repr__(self) -> str:
        """String representation of the Glue catalog."""
        return f"GlueCatalog(warehouse='{self.warehouse_name}', region='{self.region}')"


class FileCatalog(Catalog):
    """File-based Iceberg Catalog.
    
    Uses a local or distributed file system as the metadata store for
    Iceberg tables.
    """
    
    def __init__(self, path: str) -> None:
        """Create a new file-based Iceberg catalog.
        
        Args:
            path: Path to the catalog metadata directory.
            
        Example:
            >>> catalog = FileCatalog("/path/to/catalog")
        """
        # Note: This would need the file catalog feature enabled
        try:
            internal = IcebergCatalogProvider.from_file_catalog(path)
        except AttributeError:
            raise RuntimeError(
                "File catalog support is not enabled. "
                "Please rebuild with the 'iceberg-file-catalog' feature."
            )
        super().__init__(internal)
        self.path = path
    
    def __repr__(self) -> str:
        """String representation of the file catalog."""
        return f"FileCatalog(path='{self.path}')"


class RestCatalog(Catalog):
    """REST API-based Iceberg Catalog.
    
    Uses a REST API endpoint as the metadata store for Iceberg tables.
    """
    
    def __init__(self, endpoint: str, access_token: str | None = None) -> None:
        """Create a new REST API-based Iceberg catalog.
        
        Args:
            endpoint: REST API endpoint URL.
            access_token: Optional access token for authentication.
            
        Example:
            >>> catalog = RestCatalog("https://catalog.example.com", "token123")
        """
        # Note: This would need the REST catalog feature enabled
        try:
            internal = IcebergCatalogProvider.from_rest_catalog(endpoint, access_token)
        except AttributeError:
            raise RuntimeError(
                "REST catalog support is not enabled. "
                "Please rebuild with the 'iceberg-rest-catalog' feature."
            )
        super().__init__(internal)
        self.endpoint = endpoint
        self.access_token = access_token
    
    def __repr__(self) -> str:
        """String representation of the REST catalog."""
        return f"RestCatalog(endpoint='{self.endpoint}')"


# Aliases for backward compatibility and convenience
Glue = GlueCatalog
File = FileCatalog  
Rest = RestCatalog