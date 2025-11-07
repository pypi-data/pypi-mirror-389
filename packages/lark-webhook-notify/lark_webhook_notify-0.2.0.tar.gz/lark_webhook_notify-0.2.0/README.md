# Lark Webhook Notify

A Python library for sending rich notifications to Lark (Feishu) webhooks with configurable templates and hierarchical configuration management.

## Features

- **Flexible Template Builder**: Fluent API for creating custom card layouts with ease
- **Workflow Templates**: Pre-built factories for common workflow stages (network, task, result collection)
- **Hierarchical Configuration**: TOML file -> Environment variables -> CLI arguments
- **Multiple Templates**: Legacy, modern, simple message, and alert templates
- **Rich Notifications**: Collapsible panels, status indicators, markdown support, multiple columns
- **Secure**: Proper HMAC-SHA256 signature generation
- **CLI Interface**: Command-line tool for quick notifications
- **Python API**: Comprehensive programmatic interface

## Installation

```bash
# Install from PyPI
pip install lark-webhook-notify
# Or if you are using uv
uv add lark-webhook-notify
```

## Quick Start

### 1. Configuration

Create a configuration file or set environment variables:

```toml
# lark_webhook.toml
lark_webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_WEBHOOK_URL"
lark_webhook_secret = "YOUR_WEBHOOK_SECRET"
```

Or use environment variables:

```bash
export LARK_WEBHOOK_URL="https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_WEBHOOK_URL"
export LARK_WEBHOOK_SECRET="YOUR_WEBHOOK_SECRET"
```

### 2. Python API

```python
from lark_webhook_notify import send_task_notification, send_alert, send_simple_message

# Send task notification (cauldron compatible)
send_task_notification(
    task_name="deployment",
    status=0,  # 0=success, 1+=failed, None=running
    desc="Deploy application to production",
    group="artifacts",
    prefix="prod-deploy"
)

# Send alert notification
send_alert(
    alert_title="System Alert",
    alert_message="High memory usage detected on server",
    severity="warning"  # info, warning, error, critical
)

# Send simple message
send_simple_message(
    title="Build Complete",
    content="Application v2.1.0 built successfully ",
    color="green"
)
```

### 3. CLI Usage

```bash
# Task notifications
lark-weebhook-notify task "build-project" --desc "Building application" --status 0

# Alert notifications
lark-weebhook-notify alert "Service Down" "Database connection failed" --severity critical

# Simple messages
lark-weebhook-notify message "Hello" "This is a test message" --color blue

# List available templates
lark-weebhook-notify templates

# Test connection
lark-weebhook-notify test
```

## Configuration

### Configuration Hierarchy

Settings are loaded in order of precedence (highest to lowest):

1. **Command line arguments** / direct parameters
2. **Environment variables** (`LARK_WEBHOOK_URL`, `LARK_WEBHOOK_SECRET`)
3. **TOML file** (`lark_webhook.toml` by default)
4. **Default values**

### Configuration Files

#### TOML Configuration

```toml
# lark_webhook.toml
lark_webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_WEBHOOK_URL"
lark_webhook_secret = "YOUR_WEBHOOK_SECRET"
```

#### Environment Variables

```bash
# Required
export LARK_WEBHOOK_URL="https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_WEBHOOK_URL"
export LARK_WEBHOOK_SECRET="YOUR_WEBHOOK_SECRET"
```

#### Custom Configuration

```python
from lark_webhook_notify import create_settings, LarkWebhookNotifier

# Custom TOML file
settings = create_settings(toml_file="/path/to/custom.toml")

# Direct parameters (highest priority)
settings = create_settings(
    webhook_url="https://example.com/webhook",
    webhook_secret="custom-secret"
)
```

## Templates

### Available Templates

| Template  | Description                                                    |
| --------- | -------------------------------------------------------------- |
| `start`   | Task start notifications                                       |
| `task`    | Rich card with collapsible panels to report the result of task |
| `legacy`  | Simple template (old version compatible)                       |
| `message` | Basic text message                                             |
| `alert`   | Severity-based styling                                         |
| `raw`     | Raw card content passthrough                                   |

## Flexible Template Builder (New!)

### CardBuilder - Fluent API for Custom Templates

The `CardBuilder` provides a flexible, chainable API for creating custom notification templates. It makes template creation intuitive and consistent.

#### Simple Example

```python
from lark_webhook_notify import CardBuilder, LarkWebhookNotifier

# Create a custom template
template = (
    CardBuilder()
    .header("Task Complete", status="success", color="green")
    .metadata("Task Name", "data-processing")
    .metadata("Duration", "5 minutes")
    .columns()
        .column("Group", "production", width="auto")
        .column("Prefix", "s3://results/", width="weighted")
        .end_columns()
    .collapsible("Details", "Processing completed successfully", expanded=False)
    .build()
)

# Send the notification
notifier = LarkWebhookNotifier()
notifier.send_template(template)
```

#### Key Features

- **Multiple Blocks**: Add any number of metadata, collapsible sections, columns, etc.
- **Fluent Chaining**: Natural, readable syntax
- **Auto-Detection**: Automatically determines colors from status keywords
- **Flexible Layout**: Mix and match high-level helpers with low-level blocks

#### Available Methods

| Method                          | Description                  | Can Call Multiple Times |
| ------------------------------- | ---------------------------- | ----------------------- |
| `.header(title, status, color)` | Set card header              | ❌                      |
| `.metadata(label, value)`       | Add metadata row             | ✅                      |
| `.metadata_block(**kwargs)`     | Add multiple metadata fields | ✅                      |
| `.columns()...end_columns()`    | Create column layout         | ✅                      |
| `.column(label, value, width)`  | Add column to current set    | ✅                      |
| `.collapsible(title, content)`  | Add collapsible panel        | ✅                      |
| `.markdown(content)`            | Add markdown block           | ✅                      |
| `.divider()`                    | Add visual separator         | ✅                      |
| `.add_block(block)`             | Add raw block                | ✅                      |
| `.build()`                      | Build final template         | ❌                      |

#### Advanced Example - Multiple Collapsibles

```python
template = (
    CardBuilder()
    .header("Multi-Stage Analysis", status="success")
    .metadata("Analysis Name", "Performance Comparison")
    .metadata("Datasets", 3)
    # Multiple collapsible sections
    .collapsible("Stage 1: Data Collection",
                 "✓ Collected 1500 samples\n✓ Validation complete",
                 expanded=False)
    .collapsible("Stage 2: Analysis",
                 "✓ Statistical tests complete\n✓ P-value: 0.001",
                 expanded=False)
    .collapsible("Stage 3: Results",
                 "| Metric | Value |\n|:---|---:|\n| Improvement | 15.3% |",
                 expanded=True)
    .build()
)
```

### Workflow Templates

Pre-built template factories for common workflow stages:

#### Network Workflow

```python
from lark_webhook_notify import WorkflowTemplates, LarkWebhookNotifier

notifier = LarkWebhookNotifier()

# Network submission started
template = WorkflowTemplates.network_submission_start(
    network_set_name="experiment-networks",
    network_type="dynamic",
    group="research-team",
    prefix="s3://networks/",
    expected_count=100
)
notifier.send_template(template)

# Network submission complete
template = WorkflowTemplates.network_submission_complete(
    network_set_name="experiment-networks",
    submitted_count=100,
    duration="2 minutes"
)
notifier.send_template(template)
```

#### Task Workflow

```python
# Task submission started
template = WorkflowTemplates.task_submission_start(
    task_set_name="evaluation-tasks",
    network_set_name="experiment-networks",
    iterations=5,
    config_name="standard-config"
)

# Task set progress
template = WorkflowTemplates.task_set_progress(
    task_sets_progress={
        "task-set-1": {"complete": 45, "total": 100},
        "task-set-2": {"complete": 80, "total": 100},
    },
    overall_status="running"
)
```

#### Result Collection

```python
# Result collection complete
template = WorkflowTemplates.result_collection_complete(
    task_set_name="evaluation-tasks",
    row_count=500,
    column_count=25,
    group="research-team",
    duration="5 minutes"
)

# Comparison complete
template = WorkflowTemplates.comparison_complete(
    comparison_name="baseline_vs_optimized",
    task_set_count=2,
    common_network_count=45,
    result_rows=45,
    result_columns=15,
    comparison_table="| Metric | Before | After |\n|:---|---:|---:|\n| Throughput | 1000 | 1153 |"
)
```

### Complete Workflow Example

```python
from lark_webhook_notify import CardBuilder, LarkWebhookNotifier

notifier = LarkWebhookNotifier()

# Create a comprehensive workflow notification
template = (
    CardBuilder()
    .header("Experiment Workflow Complete", status="success")
    .metadata("Experiment ID", "EXP-2024-001")
    .metadata("Duration", "5.5 hours")
    .divider()
    .collapsible("Stage 1: Network Generation",
                 "✓ 100 networks generated\n⏱ 15 minutes",
                 expanded=False)
    .collapsible("Stage 2: Task Submission",
                 "✓ 500 tasks submitted\n⏱ 10 minutes",
                 expanded=False)
    .collapsible("Stage 3: Execution",
                 "✓ 495 tasks completed (99%)\n⚠ 5 tasks failed\n⏱ 4.5 hours",
                 expanded=True)
    .divider()
    .columns()
        .column("Success Rate", "99%", width="auto")
        .column("Total Tasks", "500", width="auto")
        .end_columns()
    .build()
)

notifier.send_template(template)
```

See `examples/builder_usage.py` for more comprehensive examples.

## Blocks-Based Template Composition

To make building and customizing templates easier, the library provides a small set of reusable block helpers in `lark_webhook_notify.blocks`. Each function returns a dict matching Lark's interactive card schema, and templates compose these blocks to form a complete card.

Blocks to use:

- `markdown(content, text_align='left', text_size='normal', margin='0px 0px 0px 0px')`
- `column(elements, width='auto', vertical_spacing='8px', horizontal_align='left', vertical_align='top', weight=None)`
- `column_set(columns, background_style='grey-100', horizontal_spacing='12px', horizontal_align='left', margin='0px 0px 0px 0px')`
- `collapsible_panel(title_markdown_content, elements, expanded=False, background_color='grey-200', border_color='grey', corner_radius='5px', vertical_spacing='8px', padding='8px 8px 8px 8px')`
- `header(title=..., template=..., subtitle=None, text_tag_list=None, padding=None)`
- `text_tag(text, color)`
- `config_textsize_normal_v2()`
- `card(elements=[...], header=..., schema='2.0', config=None)`
- `template_reference(template_id=..., template_version_name=..., template_variable={...})`

Example usage:

```python
from lark_webhook_notify.blocks import (
    markdown, column, column_set, collapsible_panel,
    header, card, text_tag, config_textsize_normal_v2,
)

elements = [
    markdown("Task metadata here..."),
    column_set([
        column([markdown("**Group**\nartifacts", text_align="center", text_size="normal_v2")], width="auto"),
        column([markdown("**Prefix**\ns3://bucket/path", text_align="center", text_size="normal_v2")], width="weighted", weight=1),
    ]),
    collapsible_panel(
        title_markdown_content="**<font color='grey-800'>Result Overview</font>**",
        elements=[markdown("- OK\n- Done", text_size="normal_v2")],
        expanded=False,
    ),
]

hdr = header(
    title="Task Completion Notification",
    subtitle="",
    template="green",
    text_tag_list=[text_tag("Completed", "green")],
)

content = card(elements=elements, header=hdr, schema='2.0', config=config_textsize_normal_v2())
```

You can send this `content` via `LarkWebhookNotifier.send_raw_content`. Built-in templates internally use these blocks, so extending or writing new templates is straightforward.

### Debug Mode

Enable debug logging for detailed information:

```bash
# CLI
lark-webhook-notify --debug test
```

```python
# Python
import logging
logging.getLogger("lark-webhook-notify").setLevel(logging.DEBUG)
```

### Getting Help

- Check the [Issues](https://github.com/BobAnkh/lark-webhook-notify/issues) page
- Review this documentation
- Enable debug mode for detailed error information

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure code passes linting (`uvx ruff check`) and format (`uvx ruff format`)
5. Submit a pull request

## License

Apache-2.0 License. See [LICENSE](LICENSE) for details.
