from contextvars import ContextVar
from functools import wraps
import io
from time import sleep
import zipfile

from httpx import RequestError, Response
from pydantic import BaseModel

from ..config.config import get_config, logger
from ..utils.utils import (
    check_date_range_limit,
    split_date_range as split_date_range_util,
)

max_days_limit_ctx: ContextVar[int] = ContextVar("max_days_limit")
offset_increment_ctx: ContextVar[int] = ContextVar("offset_increment")


class AcknowledgementDocumentError(Exception):
    """Raised when the API returns an acknowledgement document indicating an error."""

    pass


class ServiceUnavailableError(Exception):
    """Raised when the ENTSO-E API returns a 503 Service Unavailable status."""

    pass


class UnexpectedError(Exception):
    """Raised when the ENTSO-E API returns an unexpected error."""

    pass


def unzip(func):
    """
    Decorator that handles ZIP responses from the ENTSO-E API.

    Wraps query functions to automatically extract ZIP content when the API
    returns application/zip content-type. Each file in the ZIP archive is
    extracted and converted to a separate Response object, preserving the
    original response metadata.

    Returns:
        List of Response objects - one for each file found in the ZIP archive,
        or the original response list if the content is not a ZIP file.
    """

    @wraps(func)
    def unzip_wrapper(*args, **kwargs) -> list[Response]:
        logger.trace("unzip_wrapper: Enter")
        # Call the original function to get the list of responses
        response_list = func(*args, **kwargs)

        # Since query_core returns a list, get the first (and typically only) response
        response = response_list[0]

        # Check if response is ZIP format
        if response.headers.get("Content-Type") == "application/zip":
            logger.debug("Response is ZIP format, extracting XML content")
            # Create a BytesIO object from the response content
            zip_buffer = io.BytesIO(response.content)

            # Open the ZIP file and extract XML files
            with zipfile.ZipFile(zip_buffer, "r") as zip_file:
                file_names = zip_file.namelist()

                logger.debug(f"Found {len(file_names)} files in ZIP: {file_names}")

                responses: list[Response] = []

                for file_name in file_names:
                    logger.trace(f"Extracting file from ZIP: {file_name}")
                    with zip_file.open(file_name) as xml_file:
                        xml_content = xml_file.read().decode("utf-8")

                    # Create a copy of the original response for each file
                    # Create a new Response object with the required attributes
                    new_response = Response(
                        status_code=response.status_code,
                        headers={
                            **response.headers,
                            "Content-Type": "text/xml; charset=utf-8",
                        },
                        content=xml_content.encode("utf-8"),
                        request=response.request,
                    )
                    responses.append(new_response)
                    logger.trace(
                        f"Created Response object for {file_name} ({len(xml_content)} characters)"
                    )

                logger.trace(f"unzip_wrapper: Exit with {len(responses)} responses")
                return responses

        logger.trace("unzip_wrapper: Exit with single response")
        return response_list

    return unzip_wrapper


def split_date_range(func):
    """
    Decorator that automatically splits large date ranges into smaller chunks.

    When a date range exceeds the specified limit (default 365 days), this decorator
    splits the requested period into two halves, makes recursive calls for each half,
    and combines the results into a single list of BaseModel instances.

    For outages endpoints (when periodStartUpdate/periodEndUpdate are present):
    - The 1-year limit applies to periodStartUpdate/periodEndUpdate
    - periodStart/periodEnd can exceed 1 year

    Returns:
        List of BaseModel instances from all time periods combined.
    """

    @wraps(func)
    def range_wrapper(params, *args, **kwargs):
        logger.trace("split_date_range wrapper: Enter")
        # Get max_days_limit from context
        max_days_limit = max_days_limit_ctx.get()

        # Determine which parameters to use for range checking
        period_start_update = params.get("periodStartUpdate")
        period_end_update = params.get("periodEndUpdate")
        period_start = params.get("periodStart")
        period_end = params.get("periodEnd")

        # For outages endpoints: if update parameters are present, use them
        if period_start_update is not None and period_end_update is not None:
            check_start, check_end = period_start_update, period_end_update
            split_param_start, split_param_end = "periodStartUpdate", "periodEndUpdate"
        # Otherwise, use regular period parameters
        elif period_start is not None and period_end is not None:
            check_start, check_end = period_start, period_end
            split_param_start, split_param_end = "periodStart", "periodEnd"
        else:
            # No valid date range to check, proceed with the call
            logger.trace("split_date_range wrapper: No date range to check")
            return func(params, *args, **kwargs)

        # Check if the range exceeds the limit
        if check_date_range_limit(check_start, check_end, max_days=max_days_limit):
            logger.info(
                f"Date range {check_start} to {check_end} exceeds {max_days_limit} day limit, splitting query"
            )

            # Split the range and make recursive calls
            pivot_date = split_date_range_util(
                check_start, check_end, max_days=max_days_limit
            )
            logger.debug(f"Split at pivot date: {pivot_date}")

            # Create new params for the first half
            params1 = params.copy()
            params1[split_param_end] = pivot_date
            logger.trace(
                f"First half: {params1[split_param_start]} to {params1[split_param_end]}"
            )

            # Create new params for the second half
            params2 = params.copy()
            params2[split_param_start] = pivot_date
            logger.trace(
                f"Second half: {params2[split_param_start]} to {params2[split_param_end]}"
            )

            # Recursively call for both halves
            result1 = range_wrapper(params1, *args, **kwargs)
            result2 = range_wrapper(params2, *args, **kwargs)

            logger.debug(
                f"Merged results from split range: {len(result1)} + {len(result2)} = {len(result1) + len(result2)} results"
            )
            logger.trace("split_date_range wrapper: Exit after merge")
            return [*result1, *result2]

        # Range is within limit, make the API call
        logger.trace("split_date_range wrapper: Exit without split")
        return func(params, *args, **kwargs)

    return range_wrapper


def handle_acknowledgement(func):
    """
    Decorator that handles acknowledgement documents from the ENTSO-E API.

    Checks if the API response contains an acknowledgement document indicating
    an error or "No matching data found" condition. Returns None for "No matching
    data found" cases, raises UnexpectedError for transient server errors that
    should be retried, or raises AcknowledgementDocumentError for other error
    conditions.

    Returns:
        The original BaseModel instance, or None if no data was found.

    Raises:
        UnexpectedError: For transient "unexpected error occurred" messages (triggers retry)
        AcknowledgementDocumentError: For other acknowledgement documents containing errors
    """

    @wraps(func)
    def ack_wrapper(params, *args, **kwargs) -> BaseModel | None:
        logger.trace("handle_acknowledgement wrapper: Enter")
        xml_model = func(params, *args, **kwargs)
        name = type(xml_model).__name__

        if "acknowledgementmarketdocument" in name.lower():
            logger.debug(f"Response is acknowledgement document: {name}")
            reason = xml_model.reason[0].text

            if "No matching data found" in reason:
                logger.info("Acknowledgement: No matching data found")
                logger.trace("handle_acknowledgement wrapper: Exit with None")
                return None
            elif "Unexpected error occurred" in reason:
                logger.info(reason)
                raise UnexpectedError("Acknowledgement: Unexpected error occurred.")
            else:
                logger.error(f"Acknowledgement: {reason}")
                raise AcknowledgementDocumentError(reason)

        logger.trace("handle_acknowledgement wrapper: Exit with xml_model")
        return xml_model

    return ack_wrapper


def pagination(func):
    """
    Decorator that handles pagination for API requests with large result sets.

    When an 'offset' parameter is present, this decorator automatically
    makes multiple API calls with increasing offset values until all data
    is retrieved. The increment size is determined by the offset_increment
    parameter from context. Results from all pages are combined into a single list.

    Returns:
        List of BaseModel instances from all paginated results combined.
    """

    @wraps(func)
    def pagination_wrapper(params, *args, **kwargs):
        logger.trace("pagination wrapper: Enter")
        # Check if offset is in params (indicating pagination may be needed)
        if "offset" not in params:
            logger.trace("pagination wrapper: Exit, no offset parameter")
            return func(params, *args, **kwargs)

        # Get offset_increment from context, with default and warning if not set
        offset_increment = offset_increment_ctx.get()

        logger.info(f"Starting pagination with increment={offset_increment}")

        merged_result = []

        for offset in range(
            0, 4801, offset_increment
        ):  # 0 to 4800 in increments of offset_increment
            params["offset"] = offset
            logger.trace(f"Fetching page at offset {offset}")

            result = func(params, *args, **kwargs)

            if not result:
                logger.debug(f"Pagination complete at offset {offset}, no more results")
                break

            # Add results to accumulated list
            merged_result.extend(result)
            logger.trace(f"Retrieved {len(result)} results at offset {offset}")

        logger.debug(f"Pagination completed with {len(merged_result)} total results")
        logger.trace("pagination wrapper: Exit")
        return merged_result

    return pagination_wrapper


def check_service_unavailable(func):
    """
    Decorator that checks for 503 Service Unavailable responses from the ENTSO-E API.

    Inspects the HTTP response status code and raises a ServiceUnavailableError
    if a 503 status is detected, which triggers the retry mechanism.

    Returns:
        The original Response object if no 503 status is found.

    Raises:
        ServiceUnavailableError: When the response has a 503 Service Unavailable status
    """

    @wraps(func)
    def service_unavailable_wrapper(*args, **kwargs) -> Response:
        logger.trace("check_service_unavailable wrapper: Enter")
        response = func(*args, **kwargs)

        # Check response for 503 status
        if response.status_code == 503:
            logger.info("ENTSO-E API returned 503 Service Unavailable")
            raise ServiceUnavailableError("ENTSO-E API is unavailable (HTTP 503).")

        logger.trace("check_service_unavailable wrapper: Exit")
        return response

    return service_unavailable_wrapper


def retry(func):
    """
    Decorator that catches connection errors, service unavailable errors, waits and retries.

    Args:
        retry_count: Number of retry attempts (default: 3)
        retry_delay: Wait time between retries in seconds (default: 10)
    """

    @wraps(func)
    def retry_wrapper(*args, **kwargs):
        logger.trace("retry wrapper: Enter")
        config = get_config()
        last_exception = None

        for attempt in range(config.retries):
            logger.trace(f"Retry attempt {attempt + 1}/{config.retries}")
            try:
                result = func(*args, **kwargs)
                logger.trace(
                    f"retry wrapper: Exit successfully on attempt {attempt + 1}"
                )
                return result
            # Catch connection errors, socket errors, and service unavailable errors
            except (RequestError, ServiceUnavailableError, UnexpectedError) as e:
                last_exception = e
                if attempt < config.retries - 1:
                    logger.warning(
                        f"Attempt {attempt + 1}/{config.retries} failed: {e} "
                        f"Retrying in {config.retry_delay(attempt)}s..."
                    )
                    sleep(config.retry_delay(attempt))
                continue

        # If we've exhausted all retries, raise the last exception
        logger.error(
            f'All {config.retries} retry attempts failed. You may use entsoe.config.set_config(log_level="DEBUG") for more details.'
        )
        if last_exception:
            raise last_exception
        else:
            raise RuntimeError(
                'All retry attempts failed with unknown error. You may use entsoe.config.set_config(log_level="DEBUG") for more details.'
            )

    return retry_wrapper
