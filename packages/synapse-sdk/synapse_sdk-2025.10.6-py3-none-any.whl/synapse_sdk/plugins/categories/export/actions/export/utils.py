from abc import ABC, abstractmethod
from typing import Any, Optional
import time

from pydantic_core import PydanticCustomError

from synapse_sdk.clients.exceptions import ClientError
from synapse_sdk.i18n import gettext as _
from synapse_sdk.shared.enums import Context


class ExportTargetHandler(ABC):
    """
    Abstract base class for handling export targets.

    This class defines the blueprint for export target handlers, requiring the implementation
    of methods to validate filters, retrieve results, and process collections of results.
    """

    # TODO: This is a temporary workaround and needs improvement in the future
    def _get_results_chunked(self, list_method, filters, chunk_size=100, max_retries=3, retry_delay=1, run=None):
        """
        Retrieve results in chunks to avoid memory and response size limits.

        Args:
            list_method: The client method to call (e.g., client.list_assignments)
            filters (dict): The filter criteria to apply
            chunk_size (int): Number of items to fetch per chunk
            max_retries (int): Maximum number of retries for failed requests
            retry_delay (int): Delay in seconds between retries

        Returns:
            tuple: A tuple containing the results generator and the total count
        """
        filters = filters.copy()
        filters['page_size'] = chunk_size

        page = 1
        results = []
        total_count = 0

        try:
            while True:
                filters['page'] = page

                # Retry logic for handling temporary server issues
                for attempt in range(max_retries + 1):
                    try:
                        response = list_method(params=filters, list_all=False)
                        break
                    except ClientError as e:
                        error_msg = str(e)

                        # Use log_dev_event for better debugging and monitoring
                        if run:
                            run.log_dev_event(
                                'Chunked data retrieval error',
                                {
                                    'page': page,
                                    'attempt': attempt + 1,
                                    'error_message': error_msg,
                                    'chunk_size': chunk_size,
                                },
                                level=Context.WARNING,
                            )

                        # Check for JSON decode errors specifically
                        if 'Expecting value' in error_msg or 'JSONDecodeError' in error_msg:
                            if run:
                                run.log_dev_event(
                                    'JSON parsing error - skipping page',
                                    {'page': page, 'error_type': 'JSON_DECODE_ERROR', 'error_details': error_msg},
                                    level=Context.DANGER,
                                )
                            # Skip this page and continue with next
                            page += 1
                            break
                        elif attempt < max_retries and ('503' in error_msg or 'connection' in error_msg.lower()):
                            retry_delay_seconds = retry_delay * (2**attempt)
                            if run:
                                run.log_dev_event(
                                    'Server issue - retrying with backoff',
                                    {
                                        'page': page,
                                        'retry_attempt': attempt + 1,
                                        'max_retries': max_retries,
                                        'retry_delay_seconds': retry_delay_seconds,
                                        'error_type': 'SERVER_ISSUE',
                                    },
                                    level=Context.INFO,
                                )
                            time.sleep(retry_delay_seconds)  # Exponential backoff
                            continue
                        else:
                            raise

                if page == 1:
                    total_count = response['count']

                current_results = response.get('results', [])
                results.extend(current_results)

                # Check if we've got all results or if there are no more results
                if len(current_results) < chunk_size or not response.get('next'):
                    break

                page += 1

                # Small delay between pages to avoid overwhelming the server
                time.sleep(0.1)

            return results, total_count
        except Exception:
            # Re-raise the exception to be handled by the calling method
            raise

    @abstractmethod
    def validate_filter(self, value: dict, client: Any):
        """
        Validate filter query params to request original data from api.

        Args:
            value (dict): The filter criteria to validate.
            client (Any): The client used to validate the filter.

        Raises:
            PydanticCustomError: If the filter criteria are invalid.

        Returns:
            dict: The validated filter criteria.
        """
        pass

    @abstractmethod
    def get_results(self, client: Any, filters: dict, run=None):
        """
        Retrieve original data from target sources.

        Args:
            client (Any): The client used to retrieve the results.
            filters (dict): The filter criteria to apply.
            run: Optional ExportRun instance for logging.

        Returns:
            tuple: A tuple containing the results and the total count of results.
        """
        pass

    @abstractmethod
    def get_export_item(self, results):
        """
        Providing elements to build export data.

        Args:
            results (list): The results to process.

        Yields:
            generator: A generator that yields processed data items.
        """
        pass


class AssignmentExportTargetHandler(ExportTargetHandler):
    """Handler for assignment target exports.

    Implements ExportTargetHandler interface for assignment-specific
    export operations including validation, data retrieval, and processing.
    """

    def validate_filter(self, value: dict, client: Any):
        if 'project' not in value:
            raise PydanticCustomError('missing_field', _('Project is required for Assignment.'))
        try:
            client.list_assignments(params=value)
        except ClientError:
            raise PydanticCustomError('client_error', _('Unable to get Assignment.'))
        return value

    def get_results(self, client: Any, filters: dict, run=None):
        return self._get_results_chunked(client.list_assignments, filters, run=run)

    def get_export_item(self, results):
        for result in results:
            yield {
                'data': result['data'],
                'files': result['file'],
                'id': result['id'],
            }


class GroundTruthExportTargetHandler(ExportTargetHandler):
    """Handler for ground truth target exports.

    Implements ExportTargetHandler interface for ground truth dataset
    export operations including validation, data retrieval, and processing.
    """

    def validate_filter(self, value: dict, client: Any):
        if 'ground_truth_dataset_version' not in value:
            raise PydanticCustomError('missing_field', _('Ground Truth dataset version is required.'))
        try:
            client.get_ground_truth_version(value['ground_truth_dataset_version'])
        except ClientError:
            raise PydanticCustomError('client_error', _('Unable to get Ground Truth dataset version.'))
        return value

    def get_results(self, client: Any, filters: dict, run=None):
        filters['ground_truth_dataset_versions'] = filters.pop('ground_truth_dataset_version')
        return self._get_results_chunked(client.list_ground_truth_events, filters, run=run)

    def get_export_item(self, results):
        for result in results:
            files_key = next(iter(result['data_unit']['files']))
            yield {
                'data': result['data'],
                'files': result['data_unit']['files'][files_key],
                'id': result['id'],
            }


class TaskExportTargetHandler(ExportTargetHandler):
    """Handler for task target exports.

    Implements ExportTargetHandler interface for task-specific
    export operations including validation, data retrieval, and processing.
    """

    def validate_filter(self, value: dict, client: Any):
        if 'project' not in value:
            raise PydanticCustomError('missing_field', _('Project is required for Task.'))
        try:
            client.list_tasks(params=value)
        except ClientError:
            raise PydanticCustomError('client_error', _('Unable to get Task.'))
        return value

    def get_results(self, client: Any, filters: dict, run=None):
        filters['expand'] = ['data_unit', 'assignment', 'workshop']
        return self._get_results_chunked(client.list_tasks, filters, run=run)

    def get_export_item(self, results):
        for result in results:
            files_key = next(iter(result['data_unit']['files']))
            yield {
                'data': result['data'],
                'files': result['data_unit']['files'][files_key],
                'id': result['id'],
            }


class TargetHandlerFactory:
    """Factory class for creating export target handlers.

    Provides a centralized way to create appropriate target handlers
    based on the target type. Supports assignment, ground_truth, and task targets.

    Example:
        >>> handler = TargetHandlerFactory.get_handler('assignment')
        >>> isinstance(handler, AssignmentExportTargetHandler)
        True
    """

    @staticmethod
    def get_handler(target: str) -> ExportTargetHandler:
        """Get the appropriate target handler for the given target type.

        Args:
            target (str): The target type ('assignment', 'ground_truth', 'task')

        Returns:
            ExportTargetHandler: The appropriate handler instance

        Raises:
            ValueError: If the target type is not supported

        Example:
            >>> handler = TargetHandlerFactory.get_handler('assignment')
            >>> handler.validate_filter({'project': 123}, client)
        """
        if target == 'assignment':
            return AssignmentExportTargetHandler()
        elif target == 'ground_truth':
            return GroundTruthExportTargetHandler()
        elif target == 'task':
            return TaskExportTargetHandler()
        else:
            raise ValueError(f'Unknown target: {target}')
