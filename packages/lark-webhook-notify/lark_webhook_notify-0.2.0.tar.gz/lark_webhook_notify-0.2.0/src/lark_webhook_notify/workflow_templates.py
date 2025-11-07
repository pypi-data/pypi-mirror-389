"""Workflow-specific template factories for common use cases.

This module provides pre-configured template factories for different workflow stages,
making it easy to create consistent notifications across a multi-stage workflow.
Each factory function returns a configured CardBuilder or completed template.
"""

import json
from datetime import datetime
from typing import Optional, Dict, Any
from .templates import CardBuilder, GenericCardTemplate, LanguageCode, get_translation


class WorkflowTemplates:
    """Factory class for creating workflow-specific notification templates.

    This class provides static methods for creating templates for common workflow
    stages like network submission, task execution, result collection, etc.
    """

    @staticmethod
    def _t(key: str, language: LanguageCode = "zh") -> str:
        """Get translation for a given key and language.

        Args:
            key: Translation key
            language: Language code (default: "zh")

        Returns:
            Translated string
        """
        return get_translation(key, language)

    @staticmethod
    def network_submission_start(
        network_set_name: str,
        network_type: str,
        group: Optional[str] = None,
        prefix: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        language: LanguageCode = "zh",
    ) -> GenericCardTemplate:
        """Create template for network submission start notification.

        Uses wathet (light blue) color for start phase.

        Args:
            network_set_name: Name of the network set being created
            network_type: Type of networks being submitted
            group: Storage group identifier
            prefix: Storage path prefix
            metadata: Additional metadata to display
            language: Display language code

        Returns:
            GenericCardTemplate ready to be sent
        """

        def _t(k: str) -> str:
            return WorkflowTemplates._t(k, language)

        builder = CardBuilder(language).header(
            _t("network_submission_started"), status=_t("running"), color="wathet"
        )
        metadata_lines = [
            f"**{_t('network_set_name')}:** {network_set_name}",
            f"**{_t('network_type')}:** {network_type}",
        ]

        builder.markdown(
            "\n".join(metadata_lines), text_align="left", text_size="normal"
        )

        if group or prefix:
            builder.columns().column(
                _t("group"), group or "*unknown*", width="auto"
            ).column(
                _t("storage_prefix"), prefix or "*N/A*", width="weighted"
            ).end_columns()

        if metadata:
            s = json.dumps(metadata, indent=2, ensure_ascii=False)
            msg = f"```json\n{s}\n```"
            builder.collapsible(_t("metadata_overview"), msg, expanded=False)

        return builder.build()

    @staticmethod
    def network_submission_complete(
        network_set_name: str,
        submitted_count: Optional[int] = None,
        group: Optional[str] = None,
        prefix: Optional[str] = None,
        duration: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        language: LanguageCode = "zh",
    ) -> GenericCardTemplate:
        """Create template for network submission completion notification.

        Uses green color for success phase.

        Args:
            network_set_name: Name of the completed network set
            submitted_count: Number of networks successfully submitted
            group: Storage group identifier
            prefix: Storage path prefix
            duration: Time taken to submit networks
            language: Display language code

        Returns:
            GenericCardTemplate ready to be sent
        """

        def _t(k: str) -> str:
            return WorkflowTemplates._t(k, language)

        builder = CardBuilder(language).header(
            _t("network_submission_complete"), status=_t("success"), color="green"
        )
        metadata_lines = [
            f"**{_t('network_set_name')}:** {network_set_name}",
        ]
        if submitted_count is not None:
            metadata_lines.append(f"**{_t('submitted_count')}:** {submitted_count}")

        if duration:
            metadata_lines.append(f"**{_t('duration')}:** {duration}")
        builder.markdown(
            "\n".join(metadata_lines), text_align="left", text_size="normal"
        )

        if group or prefix:
            builder.columns().column(
                _t("group"), group or "*unknown*", width="auto"
            ).column(
                _t("storage_prefix"), prefix or "*N/A*", width="weighted"
            ).end_columns()
        if metadata:
            s = json.dumps(metadata, indent=2, ensure_ascii=False)
            msg = f"```json\n{s}\n```"
            builder.collapsible(_t("metadata_overview"), msg, expanded=False)

        return builder.build()

    @staticmethod
    def network_submission_failure(
        network_set_name: str,
        error_message: str,
        submitted_count: Optional[int] = None,
        group: Optional[str] = None,
        language: LanguageCode = "zh",
    ) -> GenericCardTemplate:
        """Create template for network submission failure notification.

        Uses red color for failure phase.

        Args:
            network_set_name: Name of the failed network set
            error_message: Error message describing the failure
            submitted_count: Number of networks submitted before failure
            group: Storage group identifier
            language: Display language code

        Returns:
            GenericCardTemplate ready to be sent
        """

        def _t(k: str) -> str:
            return WorkflowTemplates._t(k, language)

        metadata_lines = [
            f"**{_t('network_set_name')}:** {network_set_name}",
            f"**{_t('group')}:** {group or '*unknown*'}",
        ]
        if submitted_count is not None:
            metadata_lines.append(f"**{_t('submitted_count')}:** {submitted_count}")

        return (
            CardBuilder(language)
            .header(_t("network_submission_failed"), status=_t("failed"), color="red")
            .markdown("\n".join(metadata_lines), text_align="left", text_size="normal")
            .collapsible(_t("error_details"), error_message, expanded=False)
            .build()
        )

    @staticmethod
    def config_upload_complete(
        config_name: str,
        file_count: int,
        labels: Optional[list[str]] = None,
        desc: Optional[str] = None,
        language: LanguageCode = "zh",
    ) -> GenericCardTemplate:
        """Create template for configuration upload notification.

        Uses green color for success phase.

        Args:
            config_name: Name of the uploaded configuration
            file_count: Number of files uploaded
            labels: The labels of uploaded files
            desc: Configuration description
            language: Display language code

        Returns:
            GenericCardTemplate ready to be sent
        """

        def _t(k: str) -> str:
            return WorkflowTemplates._t(k, language)

        builder = CardBuilder(language).header(
            _t("config_uploaded"), status=_t("success"), color="green"
        )
        metadata_lines = [
            f"**{_t('config_name')}:** {config_name}",
            f"**{_t('files_uploaded')}:** {file_count}",
        ]

        if desc:
            metadata_lines.append(f"**{_t('description')}:** {desc}")
        builder.markdown(
            "\n".join(metadata_lines), text_align="left", text_size="normal"
        )

        if labels and len(labels) > 0:
            msg = ",".join(labels)
            builder.collapsible(_t("uploaded_files"), msg, expanded=False)

        return builder.build()

    @staticmethod
    def job_submission_start(
        job_title: str,
        desc: Optional[str] = None,
        group: Optional[str] = None,
        prefix: Optional[str] = None,
        msg: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        language: LanguageCode = "zh",
    ) -> GenericCardTemplate:
        """Create template for task submission start notification.

        Similar in style to StartTaskTemplate with consistent structure.

        Args:
            job_title: Name of this job being created
            desc: Human-readable task description
            group: Storage group identifier
            prefix: Storage path prefix
            msg: Additional runtime overview message
            metadata: Additional metadata to display
            language: Display language code

        Returns:
            GenericCardTemplate ready to be sent
        """

        def _t(k: str) -> str:
            return WorkflowTemplates._t(k, language)

        start_time = datetime.now().strftime("%Y-%m-%d %H:%M")

        builder = CardBuilder(language).header(
            _t("task_submission_started"), status=_t("running"), color="wathet"
        )

        # Build main metadata block similar to StartTaskTemplate
        metadata_lines = [
            f"**{_t('task_name')}:** {job_title}",
            f"**{_t('start_time')}:** {start_time}",
        ]

        if desc:
            metadata_lines.append(f"**{_t('task_description')}:** {desc}")

        # Add status with wathet icon (similar to StartTaskTemplate)
        metadata_lines.append(
            f"**{_t('execution_status')}:** <font color='wathet-400'> :StatusInFlight: {_t('running')}</font>"
        )

        builder.markdown(
            "\n".join(metadata_lines), text_align="left", text_size="normal"
        )

        # Storage information if provided (similar to StartTaskTemplate)
        if group or prefix:
            builder.columns().column(
                _t("result_storage"), group or "*unknown*", width="auto"
            ).column(
                _t("storage_prefix"), prefix or "*N/A*", width="weighted"
            ).end_columns()

        # Submission overview (collapsible panel similar to StartTaskTemplate)
        if msg:
            builder.collapsible(_t("running_overview"), msg, expanded=False)
        if metadata:
            s = json.dumps(metadata, indent=2, ensure_ascii=False)
            msg = f"```json\n{s}\n```"
            builder.collapsible(_t("metadata_overview"), msg, expanded=False)

        return builder.build()

    @staticmethod
    def job_submission_complete(
        job_title: str,
        submitted_count: int,
        desc: Optional[str] = None,
        group: Optional[str] = None,
        prefix: Optional[str] = None,
        duration: Optional[str] = None,
        msg: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        language: LanguageCode = "zh",
    ) -> GenericCardTemplate:
        """Create template for task submission completion notification.

        Matches the exact structure of StartTaskTemplate but for submission completion.
        Uses purple color to distinguish from start (wathet) and final success (green) phases.
        Built using CardBuilder chain-build style for consistency.

        Args:
            job_title: Name of this job
            submitted_count: Number of tasks successfully submitted
            desc: Human-readable description of the task set
            group: Storage group identifier
            prefix: Storage path prefix
            duration: Time taken to complete submission
            msg: Custom completion message or summary
            metadata: Additional metadata to display
            language: Display language code

        Returns:
            GenericCardTemplate ready to be sent
        """

        def _t(k: str) -> str:
            return WorkflowTemplates._t(k, language)

        completion_time = datetime.now().strftime("%Y-%m-%d %H:%M")

        builder = CardBuilder(language).header(
            _t("task_submission_complete"), status=_t("submitted"), color="wathet"
        )

        metadata_lines = [
            f"**{_t('task_name')}:** {job_title}",
            f"**{_t('completion_time')}:** {completion_time}",
            f"**{_t('submitted_count')}:** {submitted_count}",
        ]
        if desc:
            metadata_lines.append(f"**{_t('task_description')}:** {desc}")

        if duration:
            metadata_lines.append(f"**{_t('execution_duration')}:** {duration}")
        metadata_lines.append(
            f"**{_t('execution_status')}:** <font color='wathet-400'> :StatusInFlight: {_t('task_submission_complete')}, {_t('running')}</font>"
        )
        builder.markdown(
            "\n".join(metadata_lines), text_align="left", text_size="normal"
        )

        # Add storage columns if provided (matching StartTaskTemplate structure)
        if group or prefix:
            builder.columns().column(
                _t("result_storage"), group or "*unknown*", width="auto"
            ).column(
                _t("storage_prefix"), prefix or "*N/A*", width="weighted"
            ).end_columns()

        # Submission overview (collapsible panel similar to StartTaskTemplate)
        if msg:
            builder.collapsible(_t("running_overview"), msg, expanded=False)
        if metadata:
            s = json.dumps(metadata, indent=2, ensure_ascii=False)
            msg = f"```json\n{s}\n```"
            builder.collapsible(_t("metadata_overview"), msg, expanded=False)

        return builder.build()

    @staticmethod
    def job_submission_failure(
        job_title: str,
        error_message: str,
        submitted_count: Optional[int] = None,
        group: Optional[str] = None,
        language: LanguageCode = "zh",
    ) -> GenericCardTemplate:
        """Create template for None task submission failure notification.s red color for failure phase.

        Args:
            job_title: Name of this job
            error_message: Error message describing the failure
            submitted_count: Number of tasks submitted before failure
            group: Storage group identifier
            language: Display language code

        Returns:
            GenericCardTemplate ready to be sent
        """

        def _t(k: str) -> str:
            return WorkflowTemplates._t(k, language)

        metadata_lines = [
            f"**{_t('task_name')}:** {job_title}",
            f"**{_t('group')}:** {group or '*unknown*'}",
        ]
        if submitted_count is not None:
            metadata_lines.append(
                f"**{_t('submitted_before_failure')}:** {submitted_count}",
            )

        return (
            CardBuilder(language)
            .header(_t("task_submission_failed"), status=_t("failed"), color="red")
            .markdown("\n".join(metadata_lines), text_align="left", text_size="normal")
            .collapsible(_t("error_details"), error_message, expanded=False)
            .build()
        )

    @staticmethod
    def job_complete(
        job_title: str,
        success: bool = True,
        status: int = 0,
        group: Optional[str] = None,
        prefix: Optional[str] = None,
        desc: Optional[str] = None,
        msg: Optional[str] = None,
        duration: Optional[str] = None,
        title: Optional[str] = None,
        language: LanguageCode = "zh",
    ) -> GenericCardTemplate:
        """Create template for task set completion notification.

        Similar in style to ReportTaskResultTemplate and ReportFailureTaskTemplate,
        with dynamic styling based on success/failure status.

        Args:
            job_title: Name of the completed job
            success: Whether the task set completed successfully (default: True)
            status: Task status code (used for display, typically 0 for success)
            group: Storage group identifier for task results
            prefix: Storage path prefix for task results
            desc: Human-readable task description
            msg: Custom result message or summary
            duration: Task execution duration
            title: Custom card title (overrides default)
            language: Display language code

        Returns:
            GenericCardTemplate ready to be sent
        """

        def _t(k: str) -> str:
            return WorkflowTemplates._t(k, language)

        completion_time = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Determine styling based on success parameter (matching ReportTaskResultTemplate and ReportFailureTaskTemplate)
        if success:
            task_status = f"<font color='green'> :CheckMark: {_t('completed')}</font>"
            color = "green"
            head_tag = _t("success")
            default_title = _t("task_completion_notification")
        else:
            task_status = (
                f"<font color='red'> :CrossMark: {_t('failed')}: {status}</font>"
            )
            color = "red"
            head_tag = _t("failure")
            default_title = _t("task_failure_notification")

        # Use custom title or default
        card_title = title if title else default_title

        builder = CardBuilder(language).header(card_title, status=head_tag, color=color)

        # Build main metadata block (matching ReportTaskResultTemplate structure exactly)
        metadata_lines = [
            f"**{_t('task_name')}：** {job_title}",
            f"**{_t('completion_time')}：** {completion_time}",
        ]

        if desc:
            metadata_lines.append(f"**{_t('task_description')}：** {desc}")

        if duration:
            metadata_lines.append(f"**{_t('execution_duration')}：** {duration}")

        metadata_lines.append(f"**{_t('execution_status')}：** {task_status}")

        builder.markdown(
            "\n".join(metadata_lines), text_align="left", text_size="normal"
        )

        # Storage information if provided (matching ReportTaskResultTemplate structure)
        if group or prefix:
            builder.columns().column(
                _t("group"), group or "*unknown*", width="auto"
            ).column(
                _t("storage_prefix"), prefix or "*N/A*", width="weighted"
            ).end_columns()

        # Result overview (collapsible panel matching ReportTaskResultTemplate)
        if msg:
            builder.collapsible(_t("result_overview"), msg, expanded=False)

        return builder.build()

    @staticmethod
    def task_set_progress(
        task_sets_progress: Dict[str, Dict[str, int]],
        overall_status: str = "running",
        language: LanguageCode = "zh",
    ) -> GenericCardTemplate:
        """Create template for multi-task-set progress notification.

        Uses blue (wathet) color for progress/info phase.

        Args:
            task_sets_progress: Dictionary mapping task set names to progress info
                Each progress info should have 'complete' and 'total' keys
            overall_status: Overall status ("running", "success", etc.)
            language: Display language code

        Returns:
            GenericCardTemplate ready to be sent
        """

        def _t(k: str) -> str:
            return WorkflowTemplates._t(k, language)

        builder = CardBuilder(language).header(
            _t("task_set_progress"), status=overall_status, color="blue"
        )

        # Build progress table
        table_lines = [
            f"| {_t('task_set_name')} | Progress | {_t('completed')} | Total |",
            "|:---|:---|---:|---:|",
        ]
        for task_set_name, progress in task_sets_progress.items():
            complete = progress.get("complete", 0)
            total = progress.get("total", 0)
            pct = (complete / total * 100) if total > 0 else 0
            table_lines.append(
                f"| {task_set_name} | {pct:.1f}% | {complete} | {total} |"
            )

        builder.collapsible(_t("task_sets"), "\n".join(table_lines), expanded=True)

        return builder.build()

    @staticmethod
    def result_collection_start(
        task_set_names: list[str],
        job_title: Optional[str] = None,
        group: Optional[str] = None,
        msg: Optional[str] = None,
        language: LanguageCode = "zh",
    ) -> GenericCardTemplate:
        """Create template for result collection start notification.

        Uses wathet (light blue) color for start phase.

        Args:
            task_set_names: List of task set names being collected
            job_title: Name of the completed job
            group: Storage group identifier
            msg: Custom result message or summary
            language: Display language code

        Returns:
            GenericCardTemplate ready to be sent
        """

        def _t(k: str) -> str:
            return WorkflowTemplates._t(k, language)

        builder = CardBuilder(language).header(
            _t("result_collection_started"), status=_t("running"), color="purple"
        )
        if job_title is None:
            if len(task_set_names) == 1:
                job_title = task_set_names[0]
            else:
                job_title = f"Collection of {len(task_set_names)} Task Sets"
        metadata_lines = [
            f"**{_t('task_name')}：** {job_title}",
            f"**{_t('task_set_count')}:** {len(task_set_names)}",
        ]

        if group:
            metadata_lines.append(f"**{_t('group')}:** {group}")

        builder.markdown(
            "\n".join(metadata_lines), text_align="left", text_size="normal"
        )
        if msg:
            builder.collapsible(_t("running_overview"), msg, expanded=False)

        return builder.build()

    @staticmethod
    def result_collection_complete(
        task_set_names: list[str],
        job_title: Optional[str] = None,
        group: Optional[str] = None,
        prefix: Optional[str] = None,
        msg: Optional[str] = None,
        language: LanguageCode = "zh",
    ) -> GenericCardTemplate:
        """Create template for result collection completion notification.

        Uses blue color for data collection phase (distinct from task completion).

        Args:
            task_set_name: Name of the task set with collected results
            job_title: Name of the completed job
            group: Storage group identifier
            prefix: Storage path prefix
            msg: Custom result message or summary
            language: Display language code

        Returns:
            GenericCardTemplate ready to be sent
        """

        def _t(k: str) -> str:
            return WorkflowTemplates._t(k, language)

        builder = CardBuilder(language).header(
            _t("result_collection_complete"), status=_t("success"), color="purple"
        )
        if job_title is None:
            if len(task_set_names) == 1:
                job_title = task_set_names[0]
            else:
                job_title = f"Collection of {len(task_set_names)} Task Sets"
        metadata_lines = [
            f"**{_t('task_name')}：** {job_title}",
            f"**{_t('task_set_count')}:** {len(task_set_names)}",
        ]

        if group:
            metadata_lines.append(f"**{_t('group')}:** {group}")

        builder.markdown(
            "\n".join(metadata_lines), text_align="left", text_size="normal"
        )
        if group or prefix:
            builder.columns().column(
                _t("group"), group or "*unknown*", width="auto"
            ).column(
                _t("storage_prefix"), prefix or "*N/A*", width="weighted"
            ).end_columns()

        if msg:
            builder.collapsible(_t("state_overview"), msg, expanded=False)
        return builder.build()

    @staticmethod
    def comparison_complete(
        comparison_name: str,
        task_set_count: int,
        result_rows: int,
        result_columns: int,
        comparison_table: Optional[str] = None,
        language: LanguageCode = "zh",
    ) -> GenericCardTemplate:
        """Create template for comparison completion notification.

        Uses orange color for analysis/comparison phase (distinct from task completion).

        Args:
            comparison_name: Name of the comparison
            task_set_count: Number of task sets compared
            result_rows: Number of rows in comparison result
            result_columns: Number of columns in comparison result
            comparison_table: Markdown table with comparison results
            language: Display language code

        Returns:
            GenericCardTemplate ready to be sent
        """

        def _t(k: str) -> str:
            return WorkflowTemplates._t(k, language)

        metadata_lines = [
            f"**{_t('comparison_name')}:** {comparison_name}",
            f"**{_t('task_sets_compared')}:** {task_set_count}",
        ]

        builder = (
            CardBuilder(language)
            .header(_t("comparison_complete"), status=_t("success"), color="orange")
            .markdown("\n".join(metadata_lines), text_align="left", text_size="normal")
            .columns()
            .column(_t("result_rows"), result_rows, width="weighted")
            .column(_t("result_columns"), result_columns, width="weighted")
            .end_columns()
        )

        if comparison_table:
            builder.collapsible(
                _t("comparison_results"), comparison_table, expanded=False
            )

        return builder.build()


# Convenience function for creating custom templates
def create_custom_template(language: LanguageCode = "zh") -> CardBuilder:
    """Create a new CardBuilder for custom template creation.

    Args:
        language: Display language code

    Returns:
        New CardBuilder instance

    Example:
        >>> template = (
        ...     create_custom_template()
        ...     .header("My Custom Card", status="info")
        ...     .metadata("Key", "Value")
        ...     .collapsible("Details", "More info here")
        ...     .build()
        ... )
    """
    return CardBuilder(language)
