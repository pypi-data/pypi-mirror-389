"""Template system for Lark webhook notifications.

This module provides seven predefined templates for different notification types:
1. LegacyTaskTemplate - A legacy template format
2. StartTaskTemplate - Task start notifications
3. ReportTaskResultTemplate - Task success notifications
4. ReportFailureTaskTemplate - Task failure notifications
5. SimpleMessageTemplate - Basic text messages
6. AlertTemplate - Urgent notifications with severity levels
7. RawContentTemplate - Direct card content passthrough

Each template is a class that can be instantiated with parameters and then
passed to the LarkWebhookNotifier client.
"""

from typing import Optional, Dict, Any, Literal
from datetime import datetime
from abc import ABC, abstractmethod
from .blocks import (
    markdown as md,
    column_set as colset,
    column as col,
    collapsible_panel as panel,
    card as make_card,
    header as make_header,
    text_tag,
    config_textsize_normal_v2,
    template_reference,
)
# from pathlib import Path

# Type aliases for better readability
SeverityLevel = Literal["info", "warning", "error", "critical"]
ColorTheme = Literal["blue", "green", "red", "orange", "wathet", "purple", "grey"]
CardContent = Dict[str, Any]
LanguageCode = Literal["zh", "en"]

# Translation dictionaries
TRANSLATIONS: Dict[LanguageCode, Dict[str, str]] = {
    "zh": {
        "task_name": "作业名称",
        "start_time": "开始时间",
        "completion_time": "完成时间",
        "task_description": "作业描述",
        "estimated_duration": "预计用时",
        "execution_duration": "执行时长",
        "execution_status": "执行状态",
        "result_storage": "结果存储",
        "storage_prefix": "存储前缀",
        "result_overview": "结果概览",
        "running_overview": "运行概览",
        "state_overview": "状态概览",
        "metadata_overview": "元数据概览",
        "running": "正在运行",
        "completed": "已成功完成",
        "failed": "失败",
        "success": "已完成",
        "failure": "失败",
        "task_notification": "作业运行情况通知",
        "task_completion_notification": "作业完成情况通知",
        "task_failure_notification": "作业失败情况通知",
        "no_description": "*No description provided*",
        "timestamp": "时间",
        "unknown_task": "未知任务",
        "return_code": "返回值",
        "group": "归属组别",
        # Workflow-specific translations
        "network_submission_started": "网络提交已开始",
        "network_submission_complete": "网络提交已完成",
        "network_submission_failed": "网络提交失败",
        "network_set_name": "网络集名称",
        "network_type": "网络类型",
        "expected_count": "预期数量",
        "submitted_count": "提交总数",
        "submitted": "已提交",
        "config_uploaded": "配置已上传",
        "config_name": "配置名称",
        "files_uploaded": "已上传文件数",
        "description": "配置描述",
        "uploaded_files": "已上传文件的标签",
        "task_submission_started": "任务提交已开始",
        "task_submission_complete": "任务提交已完成",
        "task_submission_failed": "任务提交失败",
        "task_set_name": "任务集名称",
        "iterations": "迭代次数",
        "duration": "持续时间",
        "submission_overview": "提交概览",
        "status": "状态",
        "successfully_completed": "已成功完成",
        "submitted_before_failure": "失败前已提交",
        "error_details": "错误详情",
        "task_set_complete": "任务集已完成",
        "task_set_failed": "任务集失败",
        "task_set_progress": "任务集进度",
        "task_set_count": "任务集数量",
        "result_collection_started": "结果收集已开始",
        "result_collection_complete": "结果收集已完成",
        "task_sets": "任务集",
        "rows": "行数",
        "columns": "列数",
        "comparison_complete": "比较已完成",
        "comparison_name": "比较名称",
        "task_sets_compared": "已比较任务集",
        "common_networks": "公共网络数",
        "result_rows": "结果行数",
        "result_columns": "结果列数",
        "comparison_results": "比较结果",
        "total_items": "总项目数",
        "summary": "摘要",
        "items": "项目",
    },
    "en": {
        "task_name": "Job Name",
        "start_time": "Start Time",
        "completion_time": "Completion Time",
        "task_description": "Job Description",
        "estimated_duration": "Estimated Duration",
        "execution_duration": "Execution Duration",
        "execution_status": "Execution Status",
        "result_storage": "Result Storage",
        "storage_prefix": "Storage Prefix",
        "result_overview": "Result Overview",
        "running_overview": "Running Overview",
        "state_overview": "State Overview",
        "metadata_overview": "Metadata Overview",
        "running": "Running Now",
        "completed": "Successfully Completed",
        "failed": "Failed",
        "success": "Completed",
        "failure": "Failed",
        "task_notification": "Job Status Notification",
        "task_completion_notification": "Job Completion Notification",
        "task_failure_notification": "Job Failure Notification",
        "no_description": "*No description provided*",
        "timestamp": "Timestamp",
        "unknown_task": "Unknown Task",
        "return_code": "Return Status",
        "group": "Group",
        # Workflow-specific translations
        "network_submission_started": "Network Submission Started",
        "network_submission_complete": "Network Submission Complete",
        "network_submission_failed": "Network Submission Failed",
        "network_set_name": "Network Set Name",
        "network_type": "Network Type",
        "expected_count": "Expected Count",
        "submitted_count": "Total Count Submitted",
        "submitted": "Submitted",
        "config_uploaded": "Configuration Uploaded",
        "config_name": "Config Name",
        "files_uploaded": "Files Uploaded",
        "description": "Config Description",
        "uploaded_files": "Labels of Uploaded Files",
        "task_submission_started": "Task Submission Started",
        "task_submission_complete": "Task Submission Complete",
        "task_submission_failed": "Task Submission Failed",
        "task_set_name": "Task Set Name",
        "iterations": "Iterations",
        "duration": "Duration",
        "submission_overview": "Submission Overview",
        "status": "Status",
        "successfully_completed": "Successfully Completed",
        "submitted_before_failure": "Submitted Before Failure",
        "error_details": "Error Details",
        "task_set_complete": "Task Set Complete",
        "task_set_failed": "Task Set Failed",
        "task_set_progress": "Task Set Progress",
        "task_set_count": "Task Set Count",
        "result_collection_started": "Result Collection Started",
        "result_collection_complete": "Result Collection Complete",
        "task_sets": "Task Sets",
        "rows": "Rows",
        "columns": "Columns",
        "comparison_complete": "Comparison Complete",
        "comparison_name": "Comparison Name",
        "task_sets_compared": "Task Sets Compared",
        "common_networks": "Common Networks",
        "result_rows": "Result Rows",
        "result_columns": "Result Columns",
        "comparison_results": "Comparison Results",
        "total_items": "Total Items",
        "summary": "Summary",
        "items": "Items",
    },
}


def get_translation(key: str, language: LanguageCode = "zh") -> str:
    """Get translation for a given key and language.

    Args:
        key: Translation key
        language: Language code (default: "zh")

    Returns:
        Translated string or the key itself if not found
    """
    return TRANSLATIONS.get(language, TRANSLATIONS["zh"]).get(key, key)


# def get_task_summary(log_file_path: str) -> str:
#     """Extract task summary from log file (compatible with cauldron format).
#
#     Parses the last few lines of a log file to extract task metrics and
#     format them as a markdown table. This maintains compatibility with
#     the cauldron log file format.
#
#     Args:
#         log_file_path: Path to the log file to parse
#
#     Returns:
#         Markdown table string containing task metrics, or error message
#     """
#     log_path = Path(log_file_path)
#
#     try:
#         if not log_path.exists():
#             return f"Error: Log file not found at {log_path}"
#
#         with log_path.open("r", encoding="utf-8") as f:
#             lines = f.readlines()
#
#         if len(lines) < 10:
#             return "Error: Log file too short to extract summary"
#
#         # Extract relevant lines (last 8 lines, excluding the final 2)
#         relevant_lines = lines[-10:-2]
#
#         markdown_table_rows = ["| 指标 | 样本数 | 误差 |", "|:---|:---|:---|"]
#         for line in relevant_lines:
#             line = line.strip()
#             if not line:
#                 continue
#
#             parts = line.split()
#             if len(parts) >= 5:
#                 metric = parts[0]
#                 sample_count = parts[2]
#                 error_info = f"{parts[3]} {parts[4]}"
#                 markdown_table_rows.append(
#                     f"| {metric} | {sample_count} | {error_info} |"
#                 )
#
#         if len(markdown_table_rows) <= 2:
#             return "No valid metric data found in log file"
#
#         markdown_table = "\n".join(markdown_table_rows)
#
#     except PermissionError:
#         markdown_table = f"Error: Permission denied reading {log_path}"
#     except Exception as e:
#         markdown_table = f"An error occurred while processing log file: {e}"
#
#     return markdown_table


class LarkTemplate(ABC):
    """Base class for Lark notification templates.

    All templates must implement the generate method which returns a dictionary
    representing the Lark card content structure.
    """

    def __init__(self, language: LanguageCode = "zh"):
        """Initialize base template.

        Args:
            language: Display language code (default: "zh")
        """
        self.language = language

    def _t(self, key: str) -> str:
        """Get translation for the current template language.

        Args:
            key: Translation key

        Returns:
            Translated string
        """
        return get_translation(key, self.language)

    @abstractmethod
    def generate(self) -> CardContent:
        """Generate the template card content.

        Returns:
            Dictionary containing the Lark card structure

        Raises:
            ValueError: If required parameters are missing or invalid
        """
        pass


class LegacyTaskTemplate(LarkTemplate):
    """Legacy template format compatible with cauldron (old=True).

    This template uses the original cauldron template structure for backward
    compatibility. It's a simpler format that relies on a predefined template ID.
    """

    def __init__(
        self,
        task_name: Optional[str] = None,
        status: int = 0,
        group: Optional[str] = None,
        prefix: Optional[str] = None,
        task_summary: Optional[str] = None,
        language: LanguageCode = "zh",
    ):
        """Initialize legacy task template.

        Args:
            task_name: Name of the task being reported
            status: Task status code (default: 0, 0=success, other=failed)
            group: Storage group identifier for task results
            prefix: Storage path prefix for task results
            task_summary: Markdown table summary of task results
            language: Display language code (default: "zh")
        """
        super().__init__(language)
        self.task_name = task_name or self._t("unknown_task")
        self.status = status
        self.group = group or ""
        self.prefix = prefix or ""
        self.task_summary = task_summary or ""

    def generate(self) -> CardContent:
        """Generate legacy task notification card."""
        task_time = datetime.now().strftime("%Y-%m-%d %H:%M")

        if self.status is not None and self.status != 0:
            task_status = f"<font color='red'> :CrossMark: {self._t('failed')}: {self._t('return_code')} {self.status}</font>"
        else:
            task_status = (
                f"<font color='green'> :CheckMark: {self._t('completed')}</font>"
            )
        return template_reference(
            template_id="AAqz08XD5HCzP",
            template_version_name="1.0.3",
            template_variable={
                "task_name": self.task_name,
                "task_time": task_time,
                "attachment_group": self.group,
                "attachment_prefix": self.prefix,
                "task_summary": self.task_summary,
                "task_status": task_status,
            },
        )


class StartTaskTemplate(LarkTemplate):
    """Template for task start notifications.

    This template is used to notify about tasks that are beginning execution.
    It provides a clean, informative card showing the task is in progress.
    """

    def __init__(
        self,
        task_name: str,
        desc: Optional[str] = None,
        group: Optional[str] = None,
        prefix: Optional[str] = None,
        msg: Optional[str] = None,
        estimated_duration: Optional[str] = None,
        language: LanguageCode = "zh",
    ):
        """Initialize start task template.

        Args:
            task_name: Name of the task being started
            desc: Human-readable task description
            group: Storage group identifier for future results
            prefix: Storage path prefix for future results
            estimated_duration: Expected duration (e.g., "5 minutes")
            language: Display language code (default: "zh")
        """
        super().__init__(language)
        self.task_name = task_name or self._t("unknown_task")
        self.desc = desc or self._t("no_description")
        self.group = group
        self.prefix = prefix
        self.msg = msg
        self.estimated_duration = estimated_duration

    def generate(self) -> CardContent:
        """Generate start task notification card."""
        task_time = datetime.now().strftime("%Y-%m-%d %H:%M")

        elements = []

        # Task metadata element
        task_desc_text = f"\n**{self._t('task_description')}:** {self.desc}"
        duration_text = (
            f"\n**{self._t('estimated_duration')}:** {self.estimated_duration}"
            if self.estimated_duration
            else ""
        )
        task_status = (
            f"<font color='wathet-400'> :StatusInFlight: {self._t('running')}</font>"
        )

        elements.append(
            md(
                f"**{self._t('task_name')}:** {self.task_name}\n**{self._t('start_time')}:** {task_time}{task_desc_text}{duration_text}\n**{self._t('execution_status')}:** {task_status}",
                text_align="left",
                text_size="normal",
                margin="0px 0px 0px 0px",
            )
        )

        # Storage information if provided
        if self.group or self.prefix:
            elements.append(
                colset(
                    [
                        col(
                            [
                                md(
                                    f"**{self._t('result_storage')}**\n{self.group or ''}",
                                    text_align="center",
                                    text_size="normal_v2",
                                    margin="0px 4px 0px 4px",
                                )
                            ],
                            width="auto",
                            vertical_spacing="8px",
                            horizontal_align="left",
                            vertical_align="top",
                        ),
                        col(
                            [
                                md(
                                    f"**{self._t('storage_prefix')}**\n{self.prefix or ''}",
                                    text_align="center",
                                    text_size="normal_v2",
                                )
                            ],
                            width="weighted",
                            vertical_spacing="8px",
                            horizontal_align="left",
                            vertical_align="top",
                            weight=1,
                        ),
                    ],
                    background_style="grey-100",
                    horizontal_spacing="12px",
                    horizontal_align="left",
                    margin="0px 0px 0px 0px",
                )
            )
        # Result summary (collapsible panel)
        if self.msg:
            elements.append(
                panel(
                    f"**<font color='grey-800'>{self._t('running_overview')}</font>**",
                    [
                        md(
                            f"{self.msg}",
                            text_align="left",
                            text_size="normal_v2",
                            margin="0px 0px 0px 0px",
                        )
                    ],
                    expanded=False,
                )
            )

        hdr = make_header(
            title=self._t("task_notification"),
            subtitle="",
            text_tag_list=[text_tag(self._t("running"), "wathet")],
            template="wathet",
            padding="12px 8px 12px 8px",
        )
        cfg = config_textsize_normal_v2()
        return make_card(elements=elements, header=hdr, schema="2.0", config=cfg)


class ReportTaskResultTemplate(LarkTemplate):
    """Template for task success notifications.

    This template is used to notify about successfully completed tasks.
    It always displays in success mode (green color, success status).
    """

    def __init__(
        self,
        task_name: str,
        status: int = 0,
        group: Optional[str] = None,
        prefix: Optional[str] = None,
        desc: Optional[str] = None,
        msg: Optional[str] = None,
        duration: Optional[str] = None,
        title: Optional[str] = None,
        language: LanguageCode = "zh",
    ):
        """Initialize task result template.

        Args:
            task_name: Name of the completed task
            status: Task status code (default: 0, used for display)
            group: Storage group identifier for task results
            prefix: Storage path prefix for task results
            desc: Human-readable task description
            msg: Custom result message
            duration: Task execution duration
            title: Custom card title (default: uses translation key)
            language: Display language code (default: "zh")
        """
        super().__init__(language)
        self.task_name = task_name
        self.status = status
        self.group = group
        self.prefix = prefix
        self.desc = desc
        self.duration = duration
        self.msg = msg
        self.title = title

    def generate(self) -> CardContent:
        """Generate task result notification card."""
        task_time = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Always use success styling
        task_status = f"<font color='green'> :CheckMark: {self._t('completed')}</font>"
        color = "green"
        head_tag = self._t("success")

        elements = []

        # Task metadata element
        task_desc_text = (
            f"\n**{self._t('task_description')}：** {self.desc}" if self.desc else ""
        )
        duration_text = (
            f"\n**{self._t('execution_duration')}：** {self.duration}"
            if self.duration
            else ""
        )
        elements.append(
            md(
                f"**{self._t('task_name')}：** {self.task_name}\n**{self._t('completion_time')}：** {task_time}{task_desc_text}{duration_text}\n**{self._t('execution_status')}：** {task_status}",
                text_align="left",
                text_size="normal",
                margin="0px 0px 0px 0px",
            )
        )

        # Storage information if provided
        if self.group or self.prefix:
            elements.append(
                colset(
                    [
                        col(
                            [
                                md(
                                    f"**{self._t('group')}**\n{self.group or ''}",
                                    text_align="center",
                                    text_size="normal_v2",
                                    margin="0px 4px 0px 4px",
                                )
                            ],
                            width="auto",
                            vertical_spacing="8px",
                            horizontal_align="left",
                            vertical_align="top",
                        ),
                        col(
                            [
                                md(
                                    f"**{self._t('storage_prefix')}**\n{self.prefix or ''}",
                                    text_align="center",
                                    text_size="normal_v2",
                                )
                            ],
                            width="weighted",
                            vertical_spacing="8px",
                            horizontal_align="left",
                            vertical_align="top",
                            weight=1,
                        ),
                    ],
                    background_style="grey-100",
                    horizontal_spacing="12px",
                    horizontal_align="left",
                    margin="0px 0px 0px 0px",
                )
            )

        # Result summary (collapsible panel)
        if self.msg:
            elements.append(
                panel(
                    f"**<font color='grey-800'>{self._t('result_overview')}</font>**",
                    [
                        md(
                            f"{self.msg}",
                            text_align="left",
                            text_size="normal_v2",
                            margin="0px 0px 0px 0px",
                        )
                    ],
                    expanded=False,
                )
            )

        # Use custom title or default
        card_title = (
            self.title if self.title else f"{self._t('task_completion_notification')}"
        )

        hdr = make_header(
            title=card_title,
            subtitle="",
            text_tag_list=[text_tag(head_tag, color)],
            template=color,
            padding="12px 8px 12px 8px",
        )
        cfg = config_textsize_normal_v2()
        return make_card(elements=elements, header=hdr, schema="2.0", config=cfg)


class ReportFailureTaskTemplate(LarkTemplate):
    """Template for task failure notifications.

    This template is used to notify about failed tasks.
    It always displays in failure mode (red color, failure status).
    """

    def __init__(
        self,
        task_name: str,
        status: int = 0,
        group: Optional[str] = None,
        prefix: Optional[str] = None,
        desc: Optional[str] = None,
        msg: Optional[str] = None,
        duration: Optional[str] = None,
        title: Optional[str] = None,
        language: LanguageCode = "zh",
    ):
        """Initialize task failure template.

        Args:
            task_name: Name of the failed task
            status: Task status code (default: 0, used for display)
            group: Storage group identifier for task results
            prefix: Storage path prefix for task results
            desc: Human-readable task description
            msg: Custom failure message
            duration: Task execution duration
            title: Custom card title (default: uses translation key)
            language: Display language code (default: "zh")
        """
        super().__init__(language)
        self.task_name = task_name
        self.status = status
        self.group = group
        self.prefix = prefix
        self.desc = desc
        self.duration = duration
        self.msg = msg
        self.title = title

    def generate(self) -> CardContent:
        """Generate task failure notification card."""
        task_time = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Always use failure styling
        task_status = (
            f"<font color='red'> :CrossMark: {self._t('failed')}: {self.status}</font>"
        )
        color = "red"
        head_tag = self._t("failure")

        elements = []

        # Task metadata element
        task_desc_text = (
            f"\n**{self._t('task_description')}：** {self.desc}" if self.desc else ""
        )
        duration_text = (
            f"\n**{self._t('execution_duration')}：** {self.duration}"
            if self.duration
            else ""
        )
        elements.append(
            md(
                f"**{self._t('task_name')}：** {self.task_name}\n**{self._t('completion_time')}：** {task_time}{task_desc_text}{duration_text}\n**{self._t('execution_status')}：** {task_status}",
                text_align="left",
                text_size="normal",
                margin="0px 0px 0px 0px",
            )
        )

        # Storage information if provided
        if self.group or self.prefix:
            elements.append(
                colset(
                    [
                        col(
                            [
                                md(
                                    f"**{self._t('group')}**\n{self.group or ''}",
                                    text_align="center",
                                    text_size="normal_v2",
                                    margin="0px 4px 0px 4px",
                                )
                            ],
                            width="auto",
                            vertical_spacing="8px",
                            horizontal_align="left",
                            vertical_align="top",
                        ),
                        col(
                            [
                                md(
                                    f"**{self._t('storage_prefix')}**\n{self.prefix or ''}",
                                    text_align="center",
                                    text_size="normal_v2",
                                )
                            ],
                            width="weighted",
                            vertical_spacing="8px",
                            horizontal_align="left",
                            vertical_align="top",
                            weight=1,
                        ),
                    ],
                    background_style="grey-100",
                    horizontal_spacing="12px",
                    horizontal_align="left",
                    margin="0px 0px 0px 0px",
                )
            )

        # Result summary (collapsible panel)
        if self.msg:
            elements.append(
                panel(
                    f"**<font color='grey-800'>{self._t('result_overview')}</font>**",
                    [
                        md(
                            f"{self.msg}",
                            text_align="left",
                            text_size="normal_v2",
                            margin="0px 0px 0px 0px",
                        )
                    ],
                    expanded=False,
                )
            )

        # Use custom title or default
        card_title = (
            self.title if self.title else f"{self._t('task_failure_notification')}"
        )

        hdr = make_header(
            title=card_title,
            subtitle="",
            text_tag_list=[text_tag(head_tag, color)],
            template=color,
            padding="12px 8px 12px 8px",
        )
        cfg = config_textsize_normal_v2()
        return make_card(elements=elements, header=hdr, schema="2.0", config=cfg)


class SimpleMessageTemplate(LarkTemplate):
    """Simple text message template for basic notifications.

    This template provides a clean, minimal notification format suitable for
    general purpose messaging without complex UI elements.
    """

    def __init__(
        self,
        title: str,
        content: str,
        color: ColorTheme = "blue",
        language: LanguageCode = "zh",
    ):
        """Initialize simple message template.

        Args:
            title: Message title displayed in the header
            content: Main message content (supports markdown)
            color: Theme color for the card header
            language: Display language code (default: "zh")
        """
        super().__init__(language)
        self.title = title
        self.content = content
        self.color = color

    def generate(self) -> CardContent:
        """Generate simple message card."""
        return make_card(
            elements=[md(self.content, text_align="left", text_size="normal")],
            header=make_header(title=self.title, template=self.color),
            schema="2.0",
        )


class AlertTemplate(LarkTemplate):
    """Alert template for urgent and status notifications.

    This template provides severity-based styling and iconography to clearly
    communicate the importance and type of alert being sent.
    """

    def __init__(
        self,
        alert_title: str,
        alert_message: str,
        severity: SeverityLevel = "warning",
        timestamp: Optional[str] = None,
        language: LanguageCode = "zh",
    ):
        """Initialize alert template.

        Args:
            alert_title: Title of the alert notification
            alert_message: Detailed alert message content
            severity: Alert severity level (info, warning, error, critical)
            timestamp: Custom timestamp string (defaults to current time)
            language: Display language code (default: "zh")

        Raises:
            ValueError: If severity is not one of the supported values
        """
        super().__init__(language)
        self.alert_title = alert_title
        self.alert_message = alert_message
        self.severity = severity
        self.timestamp = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Validate severity
        valid_severities = {"info", "warning", "error", "critical"}
        if severity not in valid_severities:
            raise ValueError(
                f"Invalid severity '{severity}'. Must be one of: {', '.join(valid_severities)}"
            )

    def generate(self) -> CardContent:
        """Generate alert notification card."""
        # Mapping severity levels to colors and icons
        color_map: Dict[SeverityLevel, ColorTheme] = {
            "info": "blue",
            "warning": "orange",
            "error": "red",
            "critical": "red",
        }

        icon_map: Dict[SeverityLevel, str] = {
            "info": ":InfoCircle:",
            "warning": ":WarningTriangle:",
            "error": ":CrossMark:",
            "critical": ":Fire:",
        }

        color = color_map[self.severity]
        icon = icon_map[self.severity]

        return make_card(
            elements=[
                md(
                    f"{icon} **{self.alert_message}**\n\n**{self._t('timestamp')}：** {self.timestamp}",
                    text_align="left",
                    text_size="normal",
                )
            ],
            header=make_header(
                title=self.alert_title,
                subtitle=self.severity.upper(),
                template=color,
                text_tag_list=[text_tag(self.severity.upper(), color)],
            ),
            schema="2.0",
        )


class RawContentTemplate(LarkTemplate):
    """Template for passing raw card content directly.

    This template allows you to pass pre-built Lark card content directly
    without any modification. Useful when you have custom card structures
    or when integrating with existing card generation logic.
    """

    def __init__(self, card_content: CardContent, language: LanguageCode = "zh"):
        """Initialize raw content template.

        Args:
            card_content: Pre-built Lark card content dictionary
            language: Display language code (default: "zh")
        """
        super().__init__(language)
        self.card_content = card_content

    def generate(self) -> CardContent:
        """Generate raw card content (passthrough)."""
        return self.card_content


class GenericCardTemplate(LarkTemplate):
    """Generic template built using CardBuilder.

    This template wraps card content generated by the CardBuilder,
    providing a flexible way to create custom card layouts.
    """

    def __init__(
        self,
        header_config: Optional[Dict[str, Any]] = None,
        elements: Optional[list] = None,
        language: LanguageCode = "zh",
    ):
        """Initialize generic card template.

        Args:
            header_config: Dictionary containing header configuration
            elements: List of card elements/blocks
            language: Display language code (default: "zh")
        """
        super().__init__(language)
        self.header_config = header_config
        self.elements = elements or []

    def generate(self) -> CardContent:
        """Generate card from builder configuration."""
        hdr = None
        if self.header_config:
            hdr = make_header(**self.header_config)

        cfg = config_textsize_normal_v2()
        return make_card(elements=self.elements, header=hdr, schema="2.0", config=cfg)


class CardBuilder:
    """Flexible, fluent builder for creating Lark card templates.

    The CardBuilder provides a chainable API for constructing card templates
    with multiple blocks of any type. It supports both high-level convenience
    methods and low-level block control for maximum flexibility.

    Example usage:
        >>> builder = (
        ...     CardBuilder()
        ...     .header("Task Results", status="success", color="green")
        ...     .metadata("Task Name", task_name)
        ...     .metadata("Duration", duration)
        ...     .columns()
        ...         .column("Group", group, width="auto")
        ...         .column("Prefix", prefix, width="weighted")
        ...         .end_columns()
        ...     .collapsible("Details", details_text, expanded=False)
        ...     .collapsible("Logs", log_text, expanded=False)
        ... )
        >>> template = builder.build()
    """

    def __init__(self, language: LanguageCode = "zh"):
        """Initialize card builder.

        Args:
            language: Display language code (default: "zh")
        """
        self._header_config: Optional[Dict[str, Any]] = None
        self._elements: list = []
        self._column_stack: list = []
        self._language = language

    def _t(self, key: str) -> str:
        """Get translation for the current builder language.

        Args:
            key: Translation key

        Returns:
            Translated string
        """
        return get_translation(key, self._language)

    def language(self, lang: LanguageCode) -> "CardBuilder":
        """Set the language for the builder.

        Args:
            lang: Language code ("zh" or "en")

        Returns:
            Self for chaining
        """
        self._language = lang
        return self

    def header(
        self,
        title: str,
        status: Optional[str] = None,
        color: Optional[ColorTheme] = None,
        subtitle: Optional[str] = None,
    ) -> "CardBuilder":
        """Set the card header (only one header per card).

        Args:
            title: Header title text
            status: Status tag text (e.g., "running", "success", "failed")
            color: Header color theme
            subtitle: Optional subtitle text

        Returns:
            Self for chaining

        Example:
            >>> builder.header("Task Complete", status="success", color="green")
        """
        text_tag_list = None
        if status:
            if color is None:
                # Auto-detect color from status
                status_color_map = {
                    "running": "wathet",
                    "success": "green",
                    "submitted": "wathet",
                    "completed": "green",
                    "failed": "red",
                    "error": "red",
                    "warning": "orange",
                    "info": "blue",
                }
                color = status_color_map.get(status.lower(), "blue")
            text_tag_list = [text_tag(status, color)]

        template_color = color or "blue"

        self._header_config = {
            "title": title,
            "subtitle": subtitle or "",
            "text_tag_list": text_tag_list,
            "template": template_color,
            "padding": "12px 8px 12px 8px",
        }
        return self

    def metadata(
        self, label: str, value: Any, translate_label: bool = False
    ) -> "CardBuilder":
        """Add a metadata row (can be called multiple times).

        Args:
            label: Metadata label/key
            value: Metadata value (will be converted to string)
            translate_label: If True, translate the label using _t()

        Returns:
            Self for chaining

        Example:
            >>> builder.metadata("Task Name", "my-task")
            >>> builder.metadata("Duration", "5 minutes")
        """
        display_label = self._t(label) if translate_label else label
        self._elements.append(
            md(
                f"**{display_label}:** {value}",
                text_align="left",
                text_size="normal",
                margin="0px 0px 0px 0px",
            )
        )
        return self

    def metadata_block(self, **kwargs) -> "CardBuilder":
        """Add multiple metadata fields as a single formatted block.

        Args:
            **kwargs: Key-value pairs for metadata fields

        Returns:
            Self for chaining

        Example:
            >>> builder.metadata_block(
            ...     task_name="my-task",
            ...     duration="5 minutes",
            ...     status="completed"
            ... )
        """
        lines = []
        for key, value in kwargs.items():
            # Convert snake_case to Title Case for display
            display_key = key.replace("_", " ").title()
            lines.append(f"**{display_key}:** {value}")

        self._elements.append(
            md(
                "\n".join(lines),
                text_align="left",
                text_size="normal",
                margin="0px 0px 0px 0px",
            )
        )
        return self

    def columns(self) -> "CardBuilder":
        """Start a column set context.

        After calling this, use .column() to add columns, then .end_columns()
        to finalize the column set.

        Returns:
            Self for chaining

        Example:
            >>> builder.columns()
            ...     .column("Left", "value1")
            ...     .column("Right", "value2")
            ...     .end_columns()
        """
        self._column_stack.append([])
        return self

    def column(
        self,
        label: str,
        value: Any = None,
        width: str = "auto",
        weight: int = 1,
    ) -> "CardBuilder":
        """Add a column to the current column set.

        Must be called after .columns() and before .end_columns().

        Args:
            label: Column header/label
            value: Column content (optional, uses label if not provided)
            width: Column width ("auto" or "weighted")
            weight: Weight for "weighted" columns (default: 1)

        Returns:
            Self for chaining

        Raises:
            ValueError: If called without an active column set context
        """
        if not self._column_stack:
            raise ValueError(
                "Call .columns() before .column(). Example: builder.columns().column(...).end_columns()"
            )

        if value is not None:
            col_content = md(
                f"**{label}**\n{value}",
                text_align="center",
                text_size="normal_v2",
                margin="0px 4px 0px 4px" if width == "auto" else "0px 0px 0px 0px",
            )
        else:
            col_content = md(
                label,
                text_align="center",
                text_size="normal_v2",
                margin="0px 4px 0px 4px" if width == "auto" else "0px 0px 0px 0px",
            )

        column_block = col(
            [col_content],
            width=width,
            vertical_spacing="8px",
            horizontal_align="left",
            vertical_align="top",
            weight=weight if width == "weighted" else None,
        )

        self._column_stack[-1].append(column_block)
        return self

    def end_columns(
        self,
        background_style: str = "grey-100",
        horizontal_spacing: str = "12px",
    ) -> "CardBuilder":
        """End the current column set context and add it to elements.

        Args:
            background_style: Background color for the column set
            horizontal_spacing: Space between columns

        Returns:
            Self for chaining

        Raises:
            ValueError: If no column set context is active
        """
        if not self._column_stack:
            raise ValueError("No column context to end. Use .columns() first.")

        cols = self._column_stack.pop()
        self._elements.append(
            colset(
                cols,
                background_style=background_style,
                horizontal_spacing=horizontal_spacing,
                horizontal_align="left",
                margin="0px 0px 0px 0px",
            )
        )
        return self

    def collapsible(
        self,
        title: str,
        content: str,
        expanded: bool = False,
        title_color: str = "grey-800",
    ) -> "CardBuilder":
        """Add a collapsible panel (can be called multiple times).

        Args:
            title: Panel title text
            content: Panel content (supports markdown)
            expanded: Whether panel is initially expanded (default: False)
            title_color: Color for the title text (default: "grey-800")

        Returns:
            Self for chaining

        Example:
            >>> builder.collapsible("Details", details_text, expanded=False)
            >>> builder.collapsible("Logs", log_text, expanded=True)
        """
        self._elements.append(
            panel(
                f"**<font color='{title_color}'>{title}</font>**",
                [
                    md(
                        content,
                        text_align="left",
                        text_size="normal_v2",
                        margin="0px 0px 0px 0px",
                    )
                ],
                expanded=expanded,
            )
        )
        return self

    def markdown(
        self,
        content: str,
        text_align: str = "left",
        text_size: str = "normal",
    ) -> "CardBuilder":
        """Add a markdown block (can be called multiple times).

        Args:
            content: Markdown content text
            text_align: Text alignment ("left", "center", "right")
            text_size: Text size ("normal", "normal_v2", etc.)

        Returns:
            Self for chaining

        Example:
            >>> builder.markdown("## Section Title")
            >>> builder.markdown("Some content here")
        """
        self._elements.append(
            md(
                content,
                text_align=text_align,
                text_size=text_size,
                margin="0px 0px 0px 0px",
            )
        )
        return self

    def divider(self) -> "CardBuilder":
        """Add a visual divider/separator line.

        Returns:
            Self for chaining
        """
        self._elements.append(md("---", text_align="left", text_size="normal"))
        return self

    def add_block(self, block: Dict[str, Any]) -> "CardBuilder":
        """Add a raw block for maximum flexibility.

        This allows you to add any custom block that you've built
        using the blocks module functions directly.

        Args:
            block: Raw block dictionary from blocks module

        Returns:
            Self for chaining

        Example:
            >>> from lark_webhook_notify.blocks import markdown, column_set
            >>> builder.add_block(markdown("Custom block"))
            >>> builder.add_block(column_set([...]))
        """
        self._elements.append(block)
        return self

    def build(self) -> GenericCardTemplate:
        """Build and return the final template.

        Returns:
            GenericCardTemplate instance ready to be sent

        Raises:
            ValueError: If column context is still open (forgot end_columns())
        """
        if self._column_stack:
            raise ValueError(
                f"Unclosed column context! You have {len(self._column_stack)} "
                "open column set(s). Call .end_columns() to close them."
            )

        return GenericCardTemplate(
            header_config=self._header_config,
            elements=self._elements,
            language=self._language,
        )
