// Licensed to the Apache Software Foundation (ASF) under one
// or more contributor license agreements.  See the NOTICE file
// distributed with this work for additional information
// regarding copyright ownership.  The ASF licenses this file
// to you under the Apache License, Version 2.0 (the
// "License"); you may not use this file except in compliance
// with the License.  You may obtain a copy of the License at
//
//   http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing,
// software distributed under the License is distributed on an
// "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
// KIND, either express or implied.  See the License for the
// specific language governing permissions and limitations
// under the License.

use pyo3::{pyclass, pymethods, Bound, PyAny, PyResult, Python};
use pyo3::types::PyAnyMethods;
use std::sync::Arc;

use datafusion::{
    catalog::CatalogProvider,
    common::tree_node::{TreeNode, TransformedResult},
    error::{DataFusionError, Result},
    execution::session_state::SessionStateBuilder,
    execution::context::SessionContext,
};
use datafusion_ffi::catalog_provider::FFI_CatalogProvider;
use pyo3::types::PyCapsule;

use crate::{
    context::PySessionContext,
    utils::wait_for_future,
};

use datafusion_iceberg::{
    catalog::catalog::IcebergCatalog,
    planner::{iceberg_transform, IcebergQueryPlanner},
};
use iceberg_rust::{
    catalog::Catalog,
    object_store::ObjectStoreBuilder,
};
use iceberg_glue_catalog::GlueCatalog;
use aws_config::BehaviorVersion;
use dirs::home_dir;
use log::{debug, warn, info};
use std::{
    env,
    time::Duration,
};
use reqwest;
use object_store::aws::{AmazonS3Builder, AmazonS3ConfigKey};

#[cfg(feature = "iceberg-file-catalog")]
use iceberg_file_catalog::FileCatalog;

#[cfg(feature = "iceberg-rest-catalog")]
use iceberg_rest_catalog::RestCatalog;

#[derive(Debug, Clone)]
struct AwsCredentials {
    access_key_id: String,
    secret_access_key: String,
    session_token: Option<String>,
}

/// Check if we're running on an EC2 instance by attempting to reach the metadata service
async fn is_ec2_instance() -> bool {
    debug!("Checking if running on EC2 instance...");
    
    // Try to reach the IMDSv2 token endpoint with a short timeout
    let client = reqwest::Client::builder()
        .timeout(Duration::from_millis(1000))
        .build()
        .unwrap();

    // First get a token for IMDSv2
    let token_result = client
        .put("http://169.254.169.254/latest/api/token")
        .header("X-aws-ec2-metadata-token-ttl-seconds", "21600")
        .send()
        .await;

    if let Ok(token_response) = token_result {
        if let Ok(token) = token_response.text().await {
            // Try to use the token to get instance metadata
            let metadata_result = client
                .get("http://169.254.169.254/latest/meta-data/instance-id")
                .header("X-aws-ec2-metadata-token", &token)
                .send()
                .await;
            
            let is_ec2 = metadata_result.is_ok();
            debug!("EC2 detection result: {}", is_ec2);
            return is_ec2;
        }
    }

    debug!("EC2 detection result: false");
    false
}

/// Check if we're running in an ECS container
fn is_ecs_container() -> bool {
    let is_ecs = env::var("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI").is_ok() 
        || env::var("AWS_CONTAINER_CREDENTIALS_FULL_URI").is_ok()
        || env::var("ECS_CONTAINER_METADATA_URI").is_ok()
        || env::var("ECS_CONTAINER_METADATA_URI_V4").is_ok();
    
    debug!("ECS detection result: {}", is_ecs);
    is_ecs
}

/// Read AWS credentials from the credentials file
fn read_aws_credentials_file(profile: Option<&str>) -> Option<AwsCredentials> {
    let profile = profile.unwrap_or("default");
    debug!("Reading AWS credentials file for profile: {}", profile);

    let mut credentials_path = home_dir()?;
    credentials_path.push(".aws");
    credentials_path.push("credentials");

    if !credentials_path.exists() {
        debug!("AWS credentials file not found at: {:?}", credentials_path);
        return None;
    }

    let contents = std::fs::read_to_string(&credentials_path).ok()?;
    
    // Simple INI parser for AWS credentials
    let mut in_target_section = false;
    let mut access_key_id = None;
    let mut secret_access_key = None;
    let mut session_token = None;
    
    let target_section = format!("[{}]", profile);
    
    for line in contents.lines() {
        let line = line.trim();
        
        if line.starts_with('[') && line.ends_with(']') {
            in_target_section = line == target_section;
        } else if in_target_section && line.contains('=') {
            let parts: Vec<&str> = line.splitn(2, '=').collect();
            if parts.len() == 2 {
                let key = parts[0].trim();
                let value = parts[1].trim();
                
                match key {
                    "aws_access_key_id" => access_key_id = Some(value.to_string()),
                    "aws_secret_access_key" => secret_access_key = Some(value.to_string()),
                    "aws_session_token" => session_token = Some(value.to_string()),
                    _ => {}
                }
            }
        }
    }

    if let (Some(access_key_id), Some(secret_access_key)) = (access_key_id, secret_access_key) {
        debug!("Successfully read credentials from file for profile: {}", profile);
        Some(AwsCredentials {
            access_key_id,
            secret_access_key,
            session_token,
        })
    } else {
        debug!("Could not find complete credentials for profile: {}", profile);
        None
    }
}

/// Create an enhanced S3 object store builder with comprehensive credential discovery
async fn create_s3_object_store_builder(
    region: Option<&str>, 
    endpoint: Option<&str>,
    profile: Option<&str>,
) -> ObjectStoreBuilder {
    debug!("Creating enhanced S3 object store builder...");
    
    let mut builder = AmazonS3Builder::from_env();
    
    // Set region if provided
    if let Some(region) = region {
        debug!("Setting region to: {}", region);
        builder = builder.with_config(AmazonS3ConfigKey::Region, region);
    }
    
    // Set endpoint if provided
    if let Some(endpoint) = endpoint {
        debug!("Setting endpoint to: {}", endpoint);
        builder = builder.with_config(AmazonS3ConfigKey::Endpoint, endpoint);
    }

    // Credential discovery chain
    let mut credentials_found = false;

    // 1. Check environment variables first (AmazonS3Builder::from_env already handled this)
    if env::var("AWS_ACCESS_KEY_ID").is_ok() && env::var("AWS_SECRET_ACCESS_KEY").is_ok() {
        info!("Using AWS credentials from environment variables");
        credentials_found = true;
        
        // Add session token if available
        if let Ok(token) = env::var("AWS_SESSION_TOKEN") {
            debug!("Adding session token from environment");
            builder = builder.with_config(AmazonS3ConfigKey::Token, token);
        }
    }
    
    // 2. Try AWS credentials file if no env vars found
    if !credentials_found {
        if let Some(creds) = read_aws_credentials_file(profile) {
            info!("Using AWS credentials from credentials file");
            builder = builder.with_config(AmazonS3ConfigKey::AccessKeyId, &creds.access_key_id);
            builder = builder.with_config(AmazonS3ConfigKey::SecretAccessKey, &creds.secret_access_key);
            
            if let Some(token) = &creds.session_token {
                debug!("Adding session token from credentials file");
                builder = builder.with_config(AmazonS3ConfigKey::Token, token);
            }
            credentials_found = true;
        }
    }

    // 3. Check for EC2/ECS implicit credentials
    if !credentials_found {
        let is_ec2 = is_ec2_instance().await;
        let is_ecs = is_ecs_container();
        
        if is_ec2 {
            info!("Running on EC2 instance - will use instance profile credentials");
            credentials_found = true;
        } else if is_ecs {
            info!("Running in ECS container - will use task role credentials");
            credentials_found = true;
        }
    }

    // 4. Log if no explicit credentials found (will fall back to anonymous or default AWS credential chain)
    if !credentials_found {
        warn!("No explicit AWS credentials found. Will attempt anonymous access or default AWS credential provider chain.");
    }

    ObjectStoreBuilder::S3(Box::new(builder))
}

#[pyclass(
    name = "IcebergCatalogProvider", 
    module = "datafusion.catalog",
    subclass
)]
pub struct IcebergCatalogProvider;

impl IcebergCatalogProvider {
    pub async fn new_glue_catalog(
        warehouse_name: &str,
        region: &str,
        branch: Option<&str>,
    ) -> Result<Arc<IcebergCatalog>> {
        let region_owned = region.to_owned();
        let sdk_config = aws_config::defaults(BehaviorVersion::v2025_08_07())
            .region(aws_config::Region::new(region_owned))
            .load()
            .await;

        let object_store = create_s3_object_store_builder(
            Some(region), 
            None, // endpoint 
            None  // profile (use default)
        ).await;
        
        let glue_catalog: Arc<dyn Catalog> = Arc::new(
            GlueCatalog::new(&sdk_config, warehouse_name, object_store)
                .map_err(|e| DataFusionError::External(Box::new(e)))?
        );

        let iceberg_catalog = Arc::new(
            IcebergCatalog::new(glue_catalog, branch)
                .await
                .map_err(|e| DataFusionError::External(Box::new(e)))?
        );

        Ok(iceberg_catalog)
    }

    pub async fn new_glue_catalog_simple(
        warehouse_name: &str,
        region: &str,
    ) -> Result<Arc<IcebergCatalog>> {
        Self::new_glue_catalog(warehouse_name, region, None).await
    }

    #[cfg(feature = "iceberg-file-catalog")]
    pub async fn new_file_catalog(
        path: &str,
        branch: Option<&str>,
    ) -> Result<Arc<IcebergCatalog>> {
        let object_store = create_s3_object_store_builder(
            None, // region - use from environment or default
            None, // endpoint 
            None  // profile (use default)
        ).await;
        
        let file_catalog: Arc<dyn Catalog> = Arc::new(
            FileCatalog::new(path, object_store)
                .await
                .map_err(|e| DataFusionError::External(Box::new(e)))?
        );

        let iceberg_catalog = Arc::new(
            IcebergCatalog::new(file_catalog, branch)
                .await
                .map_err(|e| DataFusionError::External(Box::new(e)))?
        );

        Ok(iceberg_catalog)
    }

    #[cfg(feature = "iceberg-rest-catalog")]
    pub async fn new_rest_catalog(
        endpoint: &str,
        access_token: Option<&str>,
        branch: Option<&str>,
    ) -> Result<Arc<IcebergCatalog>> {
        let rest_catalog: Arc<dyn Catalog> = Arc::new(
            RestCatalog::new(endpoint, access_token)
                .await
                .map_err(|e| DataFusionError::External(Box::new(e)))?
        );

        let iceberg_catalog = Arc::new(
            IcebergCatalog::new(rest_catalog, branch)
                .await
                .map_err(|e| DataFusionError::External(Box::new(e)))?
        );

        Ok(iceberg_catalog)
    }
}


// Wrapper to hold IcebergCatalog for Python FFI
#[pyclass(
    name = "IcebergCatalog", 
    module = "datafusion.catalog",
    subclass
)]
#[derive(Debug)]
pub struct PyIcebergCatalog {
    catalog: Arc<IcebergCatalog>,
}

impl PyIcebergCatalog {
    pub fn new(catalog: Arc<IcebergCatalog>) -> Self {
        Self { catalog }
    }
}

impl CatalogProvider for PyIcebergCatalog {
    fn as_any(&self) -> &dyn std::any::Any {
        // Return a reference to the IcebergCatalog for downcasting
        self.catalog.as_ref()
    }

    fn schema_names(&self) -> Vec<String> {
        self.catalog.schema_names()
    }

    fn schema(&self, name: &str) -> Option<Arc<dyn datafusion::catalog::SchemaProvider>> {
        self.catalog.schema(name)
    }

    fn register_schema(
        &self,
        name: &str,
        schema: Arc<dyn datafusion::catalog::SchemaProvider>,
    ) -> Result<Option<Arc<dyn datafusion::catalog::SchemaProvider>>> {
        self.catalog.register_schema(name, schema)
    }

    fn deregister_schema(
        &self,
        name: &str,
        cascade: bool,
    ) -> Result<Option<Arc<dyn datafusion::catalog::SchemaProvider>>> {
        self.catalog.deregister_schema(name, cascade)
    }
}

#[pymethods]
impl PyIcebergCatalog {
    pub fn __datafusion_catalog_provider__<'py>(
        &self,
        py: Python<'py>,
    ) -> PyResult<Bound<'py, PyCapsule>> {
        let name = cr"datafusion_catalog_provider".into();
        // Pass the IcebergCatalog directly instead of wrapping it
        let catalog_provider = FFI_CatalogProvider::new(
            self.catalog.clone() as Arc<dyn CatalogProvider>,
            None,
        );

        PyCapsule::new(py, catalog_provider, Some(name))
    }

    /// Special method to get the IcebergCatalog directly for registration
    pub fn __iceberg_catalog__<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyCapsule>> {
        let name = cr"iceberg_catalog".into();
        PyCapsule::new(py, self.catalog.clone(), Some(name))
    }

    #[pyo3(signature = (ctx, sql_query))]
    pub fn execute_ddl(&self, ctx: Bound<'_, PyAny>, sql_query: &str, py: Python) -> PyResult<()> {
        // Handle both PySessionContext directly and wrapped SessionContext
        let py_session_ctx = if let Ok(direct_ctx) = ctx.extract::<PySessionContext>() {
            // Direct PySessionContext (from create_iceberg_session_context)
            direct_ctx
        } else {
            // Wrapped SessionContext with .ctx attribute
            let internal_ctx = ctx.getattr("ctx")
                .map_err(|e| pyo3::exceptions::PyTypeError::new_err(format!("Expected SessionContext object with .ctx attribute, got: {}", e)))?;
            internal_ctx.extract::<PySessionContext>()
                .map_err(|e| pyo3::exceptions::PyTypeError::new_err(format!("Failed to extract internal SessionContext: {}", e)))?
        };
        let ctx_clone = &py_session_ctx.ctx;
        
        // Create logical plan from SQL
        let state = ctx_clone.state();
        let plan_future = state.create_logical_plan(sql_query);
        let plan = wait_for_future(py, plan_future)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Failed to create logical plan: {}", e)))?
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("DataFusion error in logical plan: {}", e)))?;

        // Apply iceberg_transform to handle Iceberg-specific DDL operations
        let transformed = plan.transform(iceberg_transform).data()
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Failed to transform plan: {}", e)))?;

        // Execute the transformed plan
        let execution_future = ctx_clone.execute_logical_plan(transformed);
        let result = wait_for_future(py, execution_future)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Failed to execute plan: {}", e)))?
            .map_err(|e| {
                let err_str = format!("{}", e);
                if err_str.contains("No installed planner was able to convert the custom node") {
                    pyo3::exceptions::PyRuntimeError::new_err(format!(
                        "DataFusion error: {}. \n\n\
                        HINT: Your SessionContext doesn't have the IcebergQueryPlanner configured. \
                        To fix this, use IcebergCatalogProvider.create_iceberg_session_context() instead of SessionContext() \
                        to create an Iceberg-enabled context that can handle DDL operations.",
                        e
                    ))
                } else {
                    // Pass through the full error message from DataFusion/Iceberg
                    pyo3::exceptions::PyRuntimeError::new_err(format!("{}", e))
                }
            })?;

        // Collect results to ensure execution completes
        let collect_future = result.collect();
        wait_for_future(py, collect_future)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Failed to collect results: {}", e)))?
            .map_err(|e| {
                let err_str = format!("{}", e);
                if err_str.contains("No installed planner was able to convert the custom node") {
                    pyo3::exceptions::PyRuntimeError::new_err(format!(
                        "DataFusion error: {}. \n\n\
                        HINT: Your SessionContext doesn't have the IcebergQueryPlanner configured. \
                        To fix this, use IcebergCatalogProvider.create_iceberg_session_context() instead of SessionContext() \
                        to create an Iceberg-enabled context that can handle DDL operations.",
                        e
                    ))
                } else {
                    // Pass through the full error message from DataFusion/Iceberg
                    pyo3::exceptions::PyRuntimeError::new_err(format!("{}", e))
                }
            })?;

        Ok(())
    }
}

#[pymethods]
impl IcebergCatalogProvider {
    #[new]
    #[pyo3(signature = (_warehouse_name, _region = "us-east-1"))]
    pub fn py_new(
        _warehouse_name: &str,
        _region: &str,
    ) -> PyResult<Self> {
        // This is a factory, so we don't instantiate IcebergCatalogProvider
        // Instead we'll handle this in Python
        Ok(Self)
    }

    #[staticmethod]
    #[pyo3(signature = (warehouse_name, region = "us-east-1"))]
    pub fn create_catalog(
        warehouse_name: &str,
        region: &str,
    ) -> PyResult<PyIcebergCatalog> {
        let runtime = ::tokio::runtime::Runtime::new()
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Failed to create runtime: {}", e)))?;
        
        let result = runtime.block_on(Self::new_glue_catalog_simple(warehouse_name, region));
        let catalog = result.map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Failed to create Iceberg Glue catalog: {}", e)))?;

        Ok(PyIcebergCatalog::new(catalog))
    }

    #[staticmethod]
    #[pyo3(signature = (warehouse_name, region = "us-east-1", branch = None))]
    pub fn from_glue_catalog(
        warehouse_name: &str,
        region: &str,
        branch: Option<&str>,
    ) -> PyResult<PyIcebergCatalog> {
        let runtime = ::tokio::runtime::Runtime::new()
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Failed to create runtime: {}", e)))?;
        
        let result = runtime.block_on(Self::new_glue_catalog(warehouse_name, region, branch));
        let catalog = result.map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Failed to create Iceberg Glue catalog: {}", e)))?;

        Ok(PyIcebergCatalog::new(catalog))
    }

    #[cfg(feature = "iceberg-file-catalog")]
    #[staticmethod]
    #[pyo3(signature = (path, branch = None))]
    pub fn from_file_catalog(
        path: &str,
        branch: Option<&str>,
    ) -> PyResult<PyIcebergCatalog> {
        let runtime = ::tokio::runtime::Runtime::new()
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Failed to create runtime: {}", e)))?;
        
        let result = runtime.block_on(Self::new_file_catalog(path, branch));
        let catalog = result.map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Failed to create Iceberg File catalog: {}", e)))?;

        Ok(PyIcebergCatalog::new(catalog))
    }

    #[cfg(feature = "iceberg-rest-catalog")]
    #[staticmethod]
    #[pyo3(signature = (endpoint, access_token = None, branch = None))]
    pub fn from_rest_catalog(
        endpoint: &str,
        access_token: Option<&str>,
        branch: Option<&str>,
    ) -> PyResult<PyIcebergCatalog> {
        let runtime = ::tokio::runtime::Runtime::new()
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Failed to create runtime: {}", e)))?;
        
        let result = runtime.block_on(Self::new_rest_catalog(endpoint, access_token, branch));
        let catalog = result.map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Failed to create Iceberg REST catalog: {}", e)))?;

        Ok(PyIcebergCatalog::new(catalog))
    }

    #[staticmethod]
    pub fn create_iceberg_session_context() -> PyResult<PySessionContext> {
        let state = SessionStateBuilder::new()
            .with_default_features()
            .with_query_planner(Arc::new(IcebergQueryPlanner::new()))
            .build();
        
        Ok(PySessionContext {
            ctx: SessionContext::new_with_state(state),
        })
    }

    #[pyo3(signature = (ctx, sql_query))]
    pub fn execute_ddl(&self, ctx: Bound<'_, PyAny>, sql_query: &str, py: Python) -> PyResult<()> {
        // Handle both PySessionContext directly and wrapped SessionContext
        let py_session_ctx = if let Ok(direct_ctx) = ctx.extract::<PySessionContext>() {
            // Direct PySessionContext (from create_iceberg_session_context)
            direct_ctx
        } else {
            // Wrapped SessionContext with .ctx attribute
            let internal_ctx = ctx.getattr("ctx")
                .map_err(|e| pyo3::exceptions::PyTypeError::new_err(format!("Expected SessionContext object with .ctx attribute, got: {}", e)))?;
            internal_ctx.extract::<PySessionContext>()
                .map_err(|e| pyo3::exceptions::PyTypeError::new_err(format!("Failed to extract internal SessionContext: {}", e)))?
        };
        let ctx_clone = &py_session_ctx.ctx;
        
        // Create logical plan from SQL
        let state = ctx_clone.state();
        let plan_future = state.create_logical_plan(sql_query);
        let plan = wait_for_future(py, plan_future)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Failed to create logical plan: {}", e)))?
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("DataFusion error in logical plan: {}", e)))?;

        // Apply iceberg_transform to handle Iceberg-specific DDL operations
        let transformed = plan.transform(iceberg_transform).data()
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Failed to transform plan: {}", e)))?;

        // Execute the transformed plan
        let execution_future = ctx_clone.execute_logical_plan(transformed);
        let result = wait_for_future(py, execution_future)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Failed to execute plan: {}", e)))?
            .map_err(|e| {
                let err_str = format!("{}", e);
                if err_str.contains("No installed planner was able to convert the custom node") {
                    pyo3::exceptions::PyRuntimeError::new_err(format!(
                        "DataFusion error: {}. \n\n\
                        HINT: Your SessionContext doesn't have the IcebergQueryPlanner configured. \
                        To fix this, use IcebergCatalogProvider.create_iceberg_session_context() instead of SessionContext() \
                        to create an Iceberg-enabled context that can handle DDL operations.",
                        e
                    ))
                } else {
                    // Pass through the full error message from DataFusion/Iceberg
                    pyo3::exceptions::PyRuntimeError::new_err(format!("{}", e))
                }
            })?;

        // Collect results to ensure execution completes
        let collect_future = result.collect();
        wait_for_future(py, collect_future)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Failed to collect results: {}", e)))?
            .map_err(|e| {
                let err_str = format!("{}", e);
                if err_str.contains("No installed planner was able to convert the custom node") {
                    pyo3::exceptions::PyRuntimeError::new_err(format!(
                        "DataFusion error: {}. \n\n\
                        HINT: Your SessionContext doesn't have the IcebergQueryPlanner configured. \
                        To fix this, use IcebergCatalogProvider.create_iceberg_session_context() instead of SessionContext() \
                        to create an Iceberg-enabled context that can handle DDL operations.",
                        e
                    ))
                } else {
                    // Pass through the full error message from DataFusion/Iceberg
                    pyo3::exceptions::PyRuntimeError::new_err(format!("{}", e))
                }
            })?;

        Ok(())
    }
}