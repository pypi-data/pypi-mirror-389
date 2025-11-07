from .client import LarkWebhookNotifier
from .config import LarkWebhookSettings, create_settings
from .templates import (
    LarkTemplate,
    LegacyTaskTemplate,
    StartTaskTemplate,
    ReportTaskResultTemplate,
    ReportFailureTaskTemplate,
    SimpleMessageTemplate,
    AlertTemplate,
    RawContentTemplate,
    GenericCardTemplate,
    CardBuilder,
    CardContent,
    SeverityLevel,
    ColorTheme,
)
from .convenience import (
    send_task_notification,
    send_alert,
    send_simple_message,
    send_task_start,
    send_task_result,
    send_task_failure,
)
from .workflow_templates import (
    WorkflowTemplates,
    create_custom_template,
)

__version__ = "0.1.0"

__all__ = [
    # Client
    "LarkWebhookNotifier",
    # Configuration
    "LarkWebhookSettings",
    "create_settings",
    # Templates
    "LarkTemplate",
    "LegacyTaskTemplate",
    "StartTaskTemplate",
    "ReportTaskResultTemplate",
    "ReportFailureTaskTemplate",
    "SimpleMessageTemplate",
    "AlertTemplate",
    "RawContentTemplate",
    "GenericCardTemplate",
    # Builder
    "CardBuilder",
    # Workflow templates
    "WorkflowTemplates",
    "create_custom_template",
    # Convenience functions
    "send_task_notification",
    "send_alert",
    "send_simple_message",
    "send_task_start",
    "send_task_result",
    "send_task_failure",
    # Types
    "CardContent",
    "SeverityLevel",
    "ColorTheme",
]
