# Modeled Metrics Monitoring Library

A Python library for monitoring modeled metrics with Google Cloud Monitoring.

## Overview

This library provides a Python interface for working with Google Cloud Monitoring metric descriptors and writing metrics. It queries the Google Cloud Monitoring API to retrieve metric descriptors.

## Key Features

- **Direct API Integration**: Queries Google Cloud Monitoring API for metric descriptors
- **Type Safety**: Uses Google's protobuf `MetricDescriptor` objects
- **Flexible Metric Writing**: Supports all metric value types (BOOL, INT64, DOUBLE, STRING, DISTRIBUTION)
- **Error Handling**: Comprehensive exception handling for Google Cloud API errors

## Usage

### Development

```bash
# Install in development mode
pip install -e .

# Run the example
python -m modeled_metrics_monitoring.run
```

### Building and Distribution

```bash
# Build the package
./build.sh

# Install the built package
pip install dist/*.whl
```

### Using the Library

```python
from modeled_metrics_monitoring import get_metric_descriptor_by_type, write_metric

# Get a metric descriptor by type
descriptor = get_metric_descriptor_by_type(
    "custom.googleapis.com/contextual-data-monitoring/modeled-metrics-ml-ops/vertex_pipeline/foot_traffic/feature_null_ratio"
)

# Write a metric
write_metric(
    descriptor,
    0.1,
    metric_labels={
        "feature_group_id": "temporal",
        "feature_group_revision": "r0_1",
        "feature_id": "is_weekend"
    }
)

# Or write a metric using the type string directly
write_metric(
    "custom.googleapis.com/contextual-data-monitoring/modeled-metrics-ml-ops/vertex_pipeline/foot_traffic/feature_null_ratio",
    0.1,
    metric_labels={
        "feature_group_id": "temporal",
        "feature_group_revision": "r0_1",
        "feature_id": "is_weekend"
    }
)
```

## Architecture

- **Terraform**: Uses YAML files from `monitoring-metrics-definitions/metric-descriptors/*.yaml` to create metric descriptors in Google Cloud Monitoring
- **Python Library**: Queries Google Cloud Monitoring API directly to retrieve metric descriptors
- **Separation of Concerns**: Terraform handles infrastructure (creating metric descriptors), Python library handles runtime operations (querying and writing metrics)

This approach ensures that the Python library is always working with the current state of metric descriptors in Google Cloud Monitoring, while Terraform manages the infrastructure definitions.
