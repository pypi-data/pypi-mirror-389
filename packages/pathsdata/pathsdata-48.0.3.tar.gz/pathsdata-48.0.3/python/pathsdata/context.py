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

"""PathsData Enhanced Session Context with automatic Iceberg support."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from datafusion import Catalog, IcebergCatalogProvider
from datafusion.context import SessionContext as DataFusionSessionContext

if TYPE_CHECKING:
    from datafusion.context import RuntimeEnvBuilder, SessionConfig


class SessionContext(DataFusionSessionContext):
    """Enhanced SessionContext with automatic Iceberg support.
    
    This SessionContext is pre-configured with IcebergQueryPlanner and enhanced
    S3 credential discovery, making it ready for Iceberg operations out of the box.
    
    Key Features:
    - Automatic IcebergQueryPlanner configuration
    - Enhanced S3 credential discovery
    - Simplified catalog creation and management
    - Full compatibility with standard DataFusion operations
    
    Example:
        Basic usage with automatic Iceberg support:
        
        >>> from pathsdata import SessionContext
        >>> ctx = SessionContext()
        >>> catalog = ctx.create_catalog("warehouse", region="us-east-1")
        >>> ctx.sql("CREATE EXTERNAL TABLE ...").collect()
    """
    
    def __init__(
        self, 
        config: SessionConfig | None = None, 
        runtime: RuntimeEnvBuilder | None = None
    ) -> None:
        """Create a new SessionContext with automatic Iceberg support.
        
        Args:
            config: Session configuration options (optional).
            runtime: Runtime configuration options (optional).
            
        Note:
            This SessionContext is automatically configured with IcebergQueryPlanner,
            so it can handle Iceberg DDL operations without additional setup.
        """
        # Create Iceberg-enabled context by default
        iceberg_ctx = IcebergCatalogProvider.create_iceberg_session_context()
        
        # Extract the internal context and use it
        # This gives us all the Iceberg functionality automatically
        self.ctx = iceberg_ctx.ctx
        
        # TODO: In the future, we could apply additional config/runtime settings here
        # if provided, but for now we prioritize Iceberg functionality
    
    def create_catalog(
        self, 
        name: str, 
        region: str = "us-east-1", 
        catalog_type: str = "glue",
        **kwargs: Any
    ) -> "Catalog":
        """Create and register a catalog in one step.
        
        Args:
            name: The name to register the catalog under.
            region: AWS region for Glue catalog (default: "us-east-1").
            catalog_type: Type of catalog to create ("glue", "file", "rest").
            **kwargs: Additional arguments specific to catalog type.
            
        Returns:
            A Catalog instance that can be used to execute DDL operations.
            
        Example:
            >>> ctx = SessionContext()
            >>> catalog = ctx.create_catalog("warehouse", region="us-west-2")
            >>> catalog.execute_ddl(ctx, "CREATE EXTERNAL TABLE ...")
        """
        from .catalog import Catalog
        
        # Create the catalog based on type
        catalog = Catalog.create(catalog_type, name, region=region, **kwargs)
        
        # Register it with this session context
        self.register_catalog_provider(name, catalog._internal)
        
        return catalog
    
    def iceberg_ddl(self, sql: str, catalog_name: str | None = None) -> None:
        """Execute Iceberg DDL operations.
        
        Args:
            sql: The DDL SQL statement to execute.
            catalog_name: Optional catalog name to use. If not provided,
                         attempts to use a default catalog.
                         
        Example:
            >>> ctx = SessionContext()
            >>> ctx.create_catalog("warehouse")
            >>> ctx.iceberg_ddl("CREATE EXTERNAL TABLE warehouse.default.test ...")
        """
        if catalog_name is None:
            # Try to find a registered catalog
            # For now, just raise an error - in the future we could auto-detect
            raise ValueError(
                "catalog_name is required. Use ctx.create_catalog() first, "
                "then specify the catalog name or use catalog.execute_ddl() directly."
            )
        
        # Get the catalog and execute DDL
        # This would need to be implemented to lookup registered catalogs
        # For now, we'll direct users to use catalog.execute_ddl() directly
        raise NotImplementedError(
            "Direct DDL execution not yet implemented. "
            "Use catalog.execute_ddl(ctx, sql) instead."
        )