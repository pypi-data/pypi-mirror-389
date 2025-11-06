# PathsData - Enhanced DataFusion with Iceberg Support

[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![Apache License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

**PathsData** provides a simplified, enhanced interface for working with Apache Iceberg tables using DataFusion, specifically optimized for modern data workflows.

## 🚀 Key Features

- ✅ **Zero Configuration**: Automatic Iceberg support with no manual setup
- ✅ **Enhanced S3 Credentials**: Comprehensive AWS credential discovery
- ✅ **Simplified API**: Clean, intuitive interface compared to raw DataFusion
- ✅ **Multi-Region Support**: Easy AWS region configuration
- ✅ **Multiple Catalog Types**: Support for AWS Glue, File-based, and REST catalogs
- ✅ **Full Compatibility**: All DataFusion functionality remains available

## 📦 Installation

```bash
pip install pathsdata
```

## 🏃‍♂️ Quick Start

### Basic Usage

```python
from pathsdata import SessionContext

# Create context (automatically Iceberg-enabled)
ctx = SessionContext()

# Create and register catalog in one step (Default: Iceberg Glue Catalog)
catalog = ctx.create_catalog("warehouse", region="us-east-1")

# Create table (DDL)
catalog.execute_ddl(ctx, """
    CREATE EXTERNAL TABLE warehouse.default.products (
        id BIGINT,
        name VARCHAR,
        price DECIMAL(10,2),
        category VARCHAR
    ) STORED AS ICEBERG
    LOCATION 's3://your-bucket/warehouse/products'
""")

# Insert data (DML)
ctx.sql("""
    INSERT INTO warehouse.default.products VALUES
    (1, 'Laptop', 999.99, 'Electronics'),
    (2, 'Book', 29.99, 'Education')
""").collect()

# Query data
df = ctx.sql("SELECT * FROM warehouse.default.products WHERE price > 100")
results = df.collect()
print(f"Found {len(results)} products")
```

## 🔧 Core Components

### SessionContext

The enhanced `SessionContext` is automatically configured with Iceberg support:

```python
from pathsdata import SessionContext

# Pre-configured with IcebergQueryPlanner and enhanced S3 credentials
ctx = SessionContext()

# Create catalog with simplified API
catalog = ctx.create_catalog("warehouse", region="us-east-1")
```

### Catalog Types

#### GlueCatalog (Default)
```python
from pathsdata import GlueCatalog

# AWS Glue-based catalog
catalog = GlueCatalog("warehouse", region="us-east-1")
```

#### FileCatalog
```python
from pathsdata import FileCatalog

# File-based catalog for local/distributed filesystems
catalog = FileCatalog("/path/to/catalog")
```

#### RestCatalog
```python
from pathsdata import RestCatalog

# REST API-based catalog
catalog = RestCatalog("https://catalog.example.com", access_token="token123")
```

## 🔐 AWS Credential Discovery

PathsData automatically discovers AWS credentials from multiple sources:

1. **Environment Variables**
   ```bash
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   export AWS_SESSION_TOKEN=your_session_token  # Optional
   ```

2. **AWS Credentials File** (`~/.aws/credentials`)
   ```ini
   [default]
   aws_access_key_id = your_access_key
   aws_secret_access_key = your_secret_key
   ```

3. **EC2 Instance Profile** - Automatic when running on EC2
4. **ECS Task Role** - Automatic when running in ECS containers
5. **Anonymous Access** - Fallback for public buckets

## 📚 Complete Examples

### E-commerce Analytics Pipeline

```python
from pathsdata import SessionContext

def analyze_sales():
    # Setup
    ctx = SessionContext()
    catalog = ctx.create_catalog("analytics", region="us-east-1")

    # Create sales table
    catalog.execute_ddl(ctx, """
        CREATE EXTERNAL TABLE analytics.default.sales (
            order_id BIGINT,
            customer_id BIGINT,
            product_id BIGINT,
            amount DECIMAL(10,2),
            order_date DATE
        ) STORED AS ICEBERG
        LOCATION 's3://analytics-bucket/sales'
    """)

    # Load sample data
    ctx.sql("""
        INSERT INTO analytics.default.sales VALUES
        (1001, 501, 101, 299.99, '2024-01-15'),
        (1002, 502, 102, 599.99, '2024-01-16'),
        (1003, 503, 103, 149.99, '2024-02-01')
    """).collect()

    # Monthly sales analysis
    monthly_sales = ctx.sql("""
        SELECT
            DATE_TRUNC('month', order_date) as month,
            COUNT(*) as total_orders,
            SUM(amount) as total_revenue,
            AVG(amount) as avg_order_value
        FROM analytics.default.sales
        GROUP BY DATE_TRUNC('month', order_date)
        ORDER BY month
    """)

    return monthly_sales.collect()

# Execute analysis
results = analyze_sales()
for row in results:
    print(f"Month: {row['month']}, Orders: {row['total_orders']}, Revenue: ${row['total_revenue']}")
```

### Multi-Catalog Data Pipeline

```python
from pathsdata import SessionContext, GlueCatalog, FileCatalog

def setup_multi_catalog_pipeline():
    ctx = SessionContext()

    # Production data in AWS Glue
    prod_catalog = GlueCatalog("production", "us-east-1")
    ctx.register_catalog_provider("prod", prod_catalog._internal)

    # Development data in local files
    dev_catalog = FileCatalog("/path/to/dev/catalog")
    ctx.register_catalog_provider("dev", dev_catalog._internal)

    # Cross-catalog query
    comparison = ctx.sql("""
        SELECT
            'production' as environment,
            COUNT(*) as record_count
        FROM prod.default.events

        UNION ALL

        SELECT
            'development' as environment,
            COUNT(*) as record_count
        FROM dev.default.events
    """)

    return comparison.collect()

# Run pipeline
results = setup_multi_catalog_pipeline()
for row in results:
    print(f"{row['environment']}: {row['record_count']} records")
```

### Multi-Region Data Access

```python
from pathsdata import SessionContext

def setup_global_data_access():
    ctx = SessionContext()

    # US East data
    us_catalog = ctx.create_catalog("us_data", region="us-east-1")

    # EU West data
    eu_catalog = ctx.create_catalog("eu_data", region="eu-west-1")

    # Query both regions
    global_summary = ctx.sql("""
        SELECT 'US' as region, COUNT(*) as user_count
        FROM us_data.default.users

        UNION ALL

        SELECT 'EU' as region, COUNT(*) as user_count
        FROM eu_data.default.users
    """)

    return global_summary.collect()
```

## 🛠️ Advanced Usage

### Custom Session Configuration

```python
from pathsdata import SessionContext
from datafusion import RuntimeEnvBuilder, SessionConfig

# Custom configuration (optional)
config = SessionConfig()
runtime = RuntimeEnvBuilder()

ctx = SessionContext(config=config, runtime=runtime)
```

### Error Handling

```python
from pathsdata import SessionContext

ctx = SessionContext()

try:
    catalog = ctx.create_catalog("warehouse", region="us-east-1")

    # DDL operations
    catalog.execute_ddl(ctx, create_table_sql)
    print("✓ Table created successfully")

    # DML operations
    result = ctx.sql(insert_sql)
    batches = result.collect()
    print(f"✓ Inserted data in {len(batches)} batches")

except Exception as e:
    error_str = str(e).lower()
    if "credentials" in error_str or "service error" in error_str:
        print("⚠️ AWS credentials/permissions issue - check your AWS setup")
    else:
        print(f"❌ Error: {e}")
```

## 🆘 Troubleshooting

### Common Issues

#### 1. AWS Credential Errors
```
Error: service error: ... credentials
```
**Solution**: Configure AWS credentials using one of the supported methods above.

#### 2. Region Mismatch
```
Error: ... region 'us-east-1' ... bucket in 'us-west-2'
```
**Solution**: Ensure catalog region matches your S3 bucket region.

#### 3. Import Errors
```
ImportError: No module named 'pathsdata'
```
**Solution**: Install the package with `pip install pathsdata`.

### Performance Tips

1. **Use appropriate regions**: Create catalogs in the same region as your data
2. **Batch operations**: Combine multiple INSERT statements when possible
3. **Optimize queries**: Use column pruning and predicate pushdown
4. **Connection pooling**: Reuse SessionContext instances when possible

## 🔗 API Reference

### Core Classes

- **`SessionContext`**: Main entry point with automatic Iceberg support
  - `__init__(config=None, runtime=None)`
  - `create_catalog(name, region="us-east-1", catalog_type="glue", **kwargs)`
  - All standard DataFusion methods (`sql`, `read_csv`, `read_parquet`, etc.)

- **`GlueCatalog`**: AWS Glue-based catalog
  - `__init__(warehouse_name, region="us-east-1")`
  - `execute_ddl(ctx, sql)`

- **`FileCatalog`**: File-based catalog
  - `__init__(path)`
  - `execute_ddl(ctx, sql)`

- **`RestCatalog`**: REST API-based catalog
  - `__init__(endpoint, access_token=None)`
  - `execute_ddl(ctx, sql)`

**Good news**: All existing DataFusion code continues to work! Refer to datafusion-python for more functionalities

## 📞 Support & Resources

- **Issues**: Report bugs and feature requests on GitHub
- **Migration**: Both PathsData and DataFusion APIs provide identical functionality
- **Community**: Join the DataFusion community for discussions and support