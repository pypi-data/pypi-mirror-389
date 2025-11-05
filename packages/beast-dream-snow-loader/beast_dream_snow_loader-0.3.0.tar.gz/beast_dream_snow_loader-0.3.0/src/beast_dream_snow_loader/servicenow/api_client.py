"""ServiceNow REST API client for CMDB operations."""

import os
import shutil
import subprocess
import time
from collections.abc import Callable
from typing import Any

import requests  # type: ignore

# Cluster-wide rule: Never create .env files in project directories.
# Execution context detection & graceful degradation:
# - Beast node: Has access to beast services (1Password, etc.) or they are provisionable
# - OSS user: No beast services required - this is the public-facing default for this repo
# Code detects available services (1Password CLI, etc.) and uses them if present.
# Code gracefully degrades when beast services aren't available (OSS user case).
# Code reads from os.getenv() which automatically uses the executing user's system environment.


def _is_instance_hibernating(response: requests.Response) -> bool:
    """Check if ServiceNow instance is hibernating based on response.

    Args:
        response: HTTP response from ServiceNow API

    Returns:
        True if instance appears to be hibernating, False otherwise
    """
    if response.status_code != 200:
        return False

    content_type = response.headers.get("Content-Type", "").lower()
    if "application/json" in content_type:
        return False

    # Check for hibernation indicators in HTML response
    if "text/html" in content_type:
        text_lower = response.text.lower()
        hibernation_indicators = [
            "instance hibernating",
            "instance hibernating page",
            "hibernating",
            "dev.do#!/home?wu=true",  # Wake-up redirect
        ]
        return any(indicator in text_lower for indicator in hibernation_indicators)

    return False


def _wait_with_pacifier(
    message: str,
    delay_seconds: float,
    max_dots: int = 3,
) -> None:
    """Display a cute pacifier while waiting.

    Uses Streamlit spinner if we're in a Streamlit app context (checks env vars first),
    otherwise falls back to terminal dots. No Streamlit import unless we're actually in Streamlit!

    Args:
        message: Message to display
        delay_seconds: How long to wait
        max_dots: Maximum number of dots in the animation (terminal only)
    """
    # Check if we're in Streamlit context BEFORE importing (avoids initialization warnings)
    # Streamlit sets these env vars when running via `streamlit run`
    if os.getenv("STREAMLIT_SERVER_PORT") or os.getenv("STREAMLIT_SERVER_ADDRESS"):
        try:
            import streamlit as st

            # Verify we can actually use Streamlit (double-check context)
            try:
                _ = st.session_state
                # We're in Streamlit - use the spinner widget!
                with st.spinner(f"😴 {message}"):
                    time.sleep(delay_seconds)
                return
            except (AttributeError, RuntimeError):
                # Streamlit imported but not in usable context, fall through to terminal
                pass
        except ImportError:
            # Streamlit not installed, fall through to terminal
            pass

    # Terminal fallback: clean single-line animation with progress
    dot_interval = 0.5  # Update every 0.5 seconds
    elapsed = 0.0
    spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    start_time = time.time()

    while elapsed < delay_seconds:
        remaining = max(0, delay_seconds - elapsed)
        spinner = spinner_frames[int(elapsed * 2) % len(spinner_frames)]
        dots = "." * ((int(elapsed * 2) % max_dots) + 1)

        # Single clean line: spinner, message, dots, remaining time
        # Use \r to return to start of line, then pad with spaces to clear old content
        line = f"{spinner} {message}{dots} ({remaining:.1f}s)"
        print(f"\r{line:<79}", end="", flush=True)

        time.sleep(min(dot_interval, delay_seconds - elapsed))
        elapsed = time.time() - start_time

    # Clear the line when done (move to start, clear to end, move to start again)
    print("\r\033[K", end="", flush=True)


def _execute_with_hibernation_retry(
    operation: Callable[[], requests.Response],
    operation_name: str = "API call",
    max_attempts: int = 8,
    base_delay_seconds: float = 2.0,
    max_delay_seconds: float = 60.0,
    exponential_base: float = 1.5,
) -> requests.Response:
    """Execute an API operation with hibernation detection and exponential backoff.

    If the instance is hibernating, retries with exponential backoff and a cute pacifier.

    Args:
        operation: Function that returns a requests.Response
        operation_name: Name of the operation for logging
        max_attempts: Maximum number of retry attempts
        base_delay_seconds: Initial delay between retries
        max_delay_seconds: Maximum delay between retries
        exponential_base: Base for exponential backoff calculation

    Returns:
        Response from successful API call

    Raises:
        requests.HTTPError: If instance doesn't wake up after max_attempts
    """
    last_response = None

    for attempt in range(1, max_attempts + 1):
        response = operation()

        # Check if instance is hibernating
        if not _is_instance_hibernating(response):
            # Success! Instance is awake
            if attempt > 1:
                print(f"✓ Instance woke up after {attempt} attempt(s)")
            return response

        # Instance is hibernating
        last_response = response

        if attempt == max_attempts:
            # Last attempt - give up
            print(
                f"\n❌ Instance still hibernating after {max_attempts} attempts.\n"
                f"   Please log in via web UI to wake it up:\n"
                f"   https://{response.url.split('/')[2] if hasattr(response, 'url') else 'your-instance.service-now.com'}\n"
            )
            raise requests.HTTPError(
                f"ServiceNow instance is hibernating. "
                f"Please log in via web UI to wake it up. "
                f"Attempted {max_attempts} times."
            )

        # Calculate exponential backoff delay
        delay = min(
            base_delay_seconds * (exponential_base ** (attempt - 1)),
            max_delay_seconds,
        )

        # Show cute pacifier with progress info
        instance_url = (
            response.url.split("/")[2]
            if hasattr(response, "url") and response.url
            else "instance"
        )
        _wait_with_pacifier(
            f"😴 {instance_url} hibernating [attempt {attempt}/{max_attempts}]",
            delay,
        )

    # Should never reach here, but just in case
    if last_response:
        raise requests.HTTPError("Failed to wake up ServiceNow instance")
    raise RuntimeError("No response received")


def _is_1password_available() -> bool:
    """Check if 1Password CLI is installed and available.

    Returns:
        True if 1Password CLI is installed, False otherwise
    """
    return shutil.which("op") is not None


def _is_1password_signed_in() -> bool:
    """Check if user is signed in to 1Password CLI.

    Checks sign-in status silently without prompting for sign-in.
    Returns False if not signed in (does not attempt to sign in).

    Returns:
        True if already signed in, False otherwise (including if CLI not available)

    Note:
        This checks status only - does not attempt to sign in.
        If user is not signed in, returns False silently.
    """
    if not _is_1password_available():
        return False

    try:
        # Check sign-in status silently (no prompting)
        # Use 'op whoami' which checks status without prompting
        result = subprocess.run(
            ["op", "whoami"],
            capture_output=True,
            text=True,
            timeout=5,
            # Don't capture stderr to avoid prompts
        )
        # If command succeeds and returns user info, user is signed in
        # If not signed in, command fails with non-zero exit code
        return result.returncode == 0 and result.stdout.strip() != ""
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        return False


def _get_1password_credential(
    item_name: str,
    field: str,
    vault: str = "Beastmaster",
    prompt_if_needed: bool = False,
) -> str | None:
    """Get credential from 1Password CLI.

    Only retrieves credential if user is already signed in.
    Optionally prompts for sign-in if not signed in and prompt_if_needed=True.

    Args:
        item_name: 1Password item name (e.g., "ServiceNow Dev Account")
        field: Field name (e.g., "username", "api_key", "password")
        vault: Vault name (default: "Beastmaster")
        prompt_if_needed: If True, prompt for sign-in if not signed in (default: False)

    Returns:
        Credential value as string, or None if:
        - 1Password CLI not installed
        - User not signed in (and prompt_if_needed=False)
        - Item/field not found
        - Command fails for any reason

    Note:
        By default, this is a silent check - does not prompt for sign-in.
        Set prompt_if_needed=True to prompt for sign-in if not signed in.
    """
    # Check if already signed in
    if not _is_1password_signed_in():
        if prompt_if_needed and _is_1password_available():
            # Prompt for sign-in (unusual initialization scenario)
            print(
                "\n⚠️  1Password CLI available but not signed in.\n"
                "   Credentials not found in environment variables.\n"
                "   To sign in: run 'op signin'\n"
            )
        return None

    try:
        op_url = f"op://{vault}/{item_name}/{field}"
        result = subprocess.run(
            ["op", "read", op_url],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        return result.stdout.strip()
    except (
        subprocess.TimeoutExpired,
        subprocess.CalledProcessError,
        FileNotFoundError,
    ):
        return None


class ServiceNowAPIClient:
    """ServiceNow REST API client with authentication and basic operations.

    Supports multiple authentication methods (in order of preference):
    1. API key (Basic Auth with API key as password) - recommended for production
       - Use with service account user (named user, no UI login)
    2. OAuth 2.0 token (Bearer token) - optional, can tie to service account
    3. Basic Auth (username/password) - development/testing only

    Production Pattern: Named service account user with API key (no UI login).
    See docs/servicenow_constraints.md for assumptions.
    """

    def __init__(
        self,
        instance: str | None = None,
        username: str | None = None,
        password: str | None = None,
        api_key: str | None = None,
        oauth_token: str | None = None,
    ):
        """Initialize ServiceNow API client.

        Args:
            instance: ServiceNow instance URL (e.g., 'dev12345.service-now.com')
            username: ServiceNow username (for Basic Auth or API key)
            password: ServiceNow password (for Basic Auth, fallback only)
            api_key: ServiceNow API key (preferred, used as password in Basic Auth)
            oauth_token: OAuth 2.0 access token (most secure, Bearer token)

        Authentication Priority:
        1. API key (SERVICENOW_API_KEY + SERVICENOW_USERNAME) - Recommended for production
           - Use service account user (named user, no UI login)
        2. OAuth token (SERVICENOW_OAUTH_TOKEN env var) - Optional, Bearer token
        3. Username/password (SERVICENOW_USERNAME/SERVICENOW_PASSWORD) - Development/testing only

        Credentials are loaded from (in priority order):
        1. Function arguments (highest priority)
        2. Environment variables
        3. 1Password CLI (if available AND signed in)
        """
        # Get instance URL (priority: arg → env → 1Password)
        # Detect unusual initialization: no env vars AND 1Password available but not signed in
        env_instance = os.getenv("SERVICENOW_INSTANCE", "")
        has_env_vars = bool(env_instance)

        if instance:
            self.instance = instance
        elif env_instance:
            self.instance = env_instance
        else:
            # No env vars - check if we should prompt for 1Password sign-in
            should_prompt = (
                not has_env_vars
                and _is_1password_available()
                and not _is_1password_signed_in()
            )
            # Try 1Password (prompt if unusual initialization scenario)
            op_instance = _get_1password_credential(
                "ServiceNow Dev Account", "instance", prompt_if_needed=should_prompt
            )
            self.instance = op_instance or ""

        if not self.instance:
            raise ValueError("ServiceNow instance URL is required")

        # Ensure instance URL is clean (no https:// prefix)
        self.instance = (
            self.instance.replace("https://", "").replace("http://", "").rstrip("/")
        )

        self.base_url = f"https://{self.instance}/api/now"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

        # Authentication: Priority 1 - API Key (Recommended for production)
        # Use service account user (named user, no UI login) with API key
        # Try: function arg → env var → 1Password
        env_api_key = os.getenv("SERVICENOW_API_KEY", "")
        env_username = os.getenv("SERVICENOW_USERNAME", "")
        has_env_auth = bool(env_api_key and env_username)

        if api_key:
            api_key_value = api_key
        elif env_api_key:
            api_key_value = env_api_key
        else:
            # No env vars - check if we should prompt for 1Password sign-in
            should_prompt = (
                not has_env_auth
                and _is_1password_available()
                and not _is_1password_signed_in()
            )
            api_key_value = (
                _get_1password_credential(
                    "ServiceNow Dev Account", "api_key", prompt_if_needed=should_prompt
                )
                or ""
            )

        if username:
            username_value = username
        elif env_username:
            username_value = env_username
        else:
            # No env vars - check if we should prompt for 1Password sign-in
            should_prompt = (
                not has_env_auth
                and _is_1password_available()
                and not _is_1password_signed_in()
            )
            username_value = (
                _get_1password_credential(
                    "ServiceNow Dev Account", "username", prompt_if_needed=should_prompt
                )
                or ""
            )

        if api_key_value and username_value:
            self.session.auth = (username_value, api_key_value)
            return

        # Authentication: Priority 2 - OAuth Token (Optional)
        # Try: function arg → env var → 1Password
        env_oauth_token = os.getenv("SERVICENOW_OAUTH_TOKEN", "")
        has_env_oauth = bool(env_oauth_token)

        if oauth_token:
            oauth_token_value = oauth_token
        elif env_oauth_token:
            oauth_token_value = env_oauth_token
        else:
            # No env vars - check if we should prompt for 1Password sign-in
            should_prompt = (
                not has_env_oauth
                and _is_1password_available()
                and not _is_1password_signed_in()
            )
            oauth_token_value = (
                _get_1password_credential(
                    "ServiceNow Dev Account",
                    "oauth_token",
                    prompt_if_needed=should_prompt,
                )
                or ""
            )

        if oauth_token_value:
            self.session.headers["Authorization"] = f"Bearer {oauth_token_value}"
            return

        # Authentication: Priority 3 - Basic Auth (username/password) - Development/testing only
        # NOT recommended for production - use service account with API key instead
        # Try: function arg → env var → 1Password
        env_password = os.getenv("SERVICENOW_PASSWORD", "")
        has_env_password = bool(env_password and env_username)

        if password:
            password_value = password
        elif env_password:
            password_value = env_password
        else:
            # No env vars - check if we should prompt for 1Password sign-in
            should_prompt = (
                not has_env_password
                and _is_1password_available()
                and not _is_1password_signed_in()
            )
            password_value = (
                _get_1password_credential(
                    "ServiceNow Dev Account", "password", prompt_if_needed=should_prompt
                )
                or ""
            )

        if username_value and password_value:
            self.session.auth = (username_value, password_value)
            return

        # No valid authentication found
        raise ValueError(
            "ServiceNow authentication required. Recommended for production:\n"
            "  - API key: SERVICENOW_API_KEY + SERVICENOW_USERNAME env vars\n"
            "    (Use service account user - named user, no UI login)\n"
            "  - OAuth token: SERVICENOW_OAUTH_TOKEN env var (optional)\n"
            "  - Username/password: SERVICENOW_USERNAME + SERVICENOW_PASSWORD env vars\n"
            "    (Development/testing only - NOT recommended for production)"
        )

    def create_record(self, table: str, data: dict[str, Any]) -> dict[str, Any]:
        """Create a record in a ServiceNow table.

        Args:
            table: ServiceNow table name (e.g., 'cmdb_ci_network_gateway')
            data: Record data as dictionary

        Returns:
            Created record data from ServiceNow

        Raises:
            requests.HTTPError: If API request fails
        """
        url = f"{self.base_url}/table/{table}"

        def _create() -> requests.Response:
            return self.session.post(url, json=data)

        response = _execute_with_hibernation_retry(
            _create, operation_name=f"create_record({table})"
        )
        if response.status_code == 401:
            # Provide more detail on auth failure
            error_detail = response.text
            raise requests.HTTPError(
                f"401 Unauthorized - Authentication failed.\n"
                f"Instance: {self.instance}\n"
                f"URL: {url}\n"
                f"Response: {error_detail}\n"
                f"Please verify username and password are correct."
            )
        if response.status_code == 400:
            # Provide more detail on bad request
            error_detail = response.text
            try:
                error_json = response.json()
                error_detail = error_json
            except Exception:
                pass
            raise requests.HTTPError(
                f"400 Bad Request - Invalid request.\n"
                f"Instance: {self.instance}\n"
                f"URL: {url}\n"
                f"Data: {data}\n"
                f"Response: {error_detail}\n"
                f"This may indicate missing required fields, invalid table name, or validation errors."
            )
        response.raise_for_status()
        return response.json().get("result", {})  # type: ignore

    def get_record(self, table: str, sys_id: str) -> dict[str, Any] | None:
        """Get a record from a ServiceNow table by sys_id.

        Args:
            table: ServiceNow table name
            sys_id: Record sys_id

        Returns:
            Record data or None if not found

        Raises:
            requests.HTTPError: If API request fails
        """
        url = f"{self.base_url}/table/{table}/{sys_id}"

        def _get() -> requests.Response:
            return self.session.get(url)

        response = _execute_with_hibernation_retry(
            _get, operation_name=f"get_record({table})"
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json().get("result", {})  # type: ignore

    def update_record(
        self, table: str, sys_id: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update a record in a ServiceNow table.

        Args:
            table: ServiceNow table name
            sys_id: Record sys_id
            data: Updated record data

        Returns:
            Updated record data from ServiceNow

        Raises:
            requests.HTTPError: If API request fails
        """
        url = f"{self.base_url}/table/{table}/{sys_id}"

        def _update() -> requests.Response:
            return self.session.put(url, json=data)

        response = _execute_with_hibernation_retry(
            _update, operation_name=f"update_record({table})"
        )
        response.raise_for_status()
        return response.json().get("result", {})  # type: ignore

    def query_records(
        self, table: str, query: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Query records from a ServiceNow table.

        Args:
            table: ServiceNow table name
            query: ServiceNow encoded query string (e.g., 'name=test')
            limit: Maximum number of records to return

        Returns:
            List of record data dictionaries

        Raises:
            requests.HTTPError: If API request fails
        """
        url = f"{self.base_url}/table/{table}"
        params: dict[str, Any] = {"sysparm_limit": limit}
        if query:
            params["sysparm_query"] = query

        def _query() -> requests.Response:
            return self.session.get(url, params=params)

        response = _execute_with_hibernation_retry(
            _query, operation_name=f"query_records({table})"
        )
        response.raise_for_status()
        return response.json().get("result", [])  # type: ignore

    def table_exists(self, table_name: str) -> bool:
        """Check if a ServiceNow table exists and is accessible.

        Args:
            table_name: ServiceNow table name to check

        Returns:
            True if table exists and is accessible, False otherwise
        """
        try:
            # Try to query the table with a minimal query (limit 1)
            self.query_records(table_name, query=None, limit=1)
            return True
        except Exception:
            return False

    def get_table_info(self, table_name: str) -> dict[str, Any] | None:
        """Get table metadata from sys_db_object table.

        Args:
            table_name: ServiceNow table name

        Returns:
            Dictionary with table metadata (name, label, scope, etc.) or None if not found
        """
        try:
            # Query sys_db_object to get table metadata
            results = self.query_records(
                "sys_db_object",
                query=f"name={table_name}",
                limit=1,
            )
            if results:
                # Filter to what we care about
                return {
                    "name": results[0].get("name"),
                    "label": results[0].get("label"),
                    "sys_class_name": results[0].get("sys_class_name"),
                    "super_class": results[0].get("super_class"),
                    "scope": results[0].get("scope"),
                }
            return None
        except Exception:
            return None

    def create_change_request(
        self,
        short_description: str,
        type: str = "standard",  # "standard", "normal", "emergency"
        description: str | None = None,
    ) -> dict[str, Any]:
        """Create a Change Request in ServiceNow.

        Note: Change Requests are for workflow/audit. For schema/data changes,
        we may need to use changesets instead (see create_changeset).

        Args:
            short_description: Short description of the change
            type: Change type - "standard" (pre-approved), "normal" (needs approval), "emergency"
            description: Detailed description (optional)

        Returns:
            Created Change Request data with sys_id

        Raises:
            requests.HTTPError: If API request fails
        """
        url = f"{self.base_url}/table/change_request"
        data: dict[str, Any] = {
            "short_description": short_description,
            "type": type,
        }
        if description:
            data["description"] = description

        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json().get("result", {})  # type: ignore

    def create_changeset(
        self, name: str, description: str | None = None
    ) -> dict[str, Any]:
        """Create a changeset for schema/data changes (CMDB modifications).

        Changesets are used for schema changes - grouping related data modifications
        together. This is different from Change Requests (workflow/audit).

        Args:
            name: Changeset name
            description: Changeset description (optional)

        Returns:
            Created changeset data with sys_id

        Raises:
            requests.HTTPError: If API request fails
        """
        # TODO: Investigate ServiceNow changeset API endpoint
        # Changesets are typically for schema/data changes (CMDB modifications)
        # This might be:
        # - /api/now/changeset
        # - /api/sn_cmdb/changeset
        # - Or part of a different API
        # Need to verify the correct endpoint and structure
        raise NotImplementedError(
            "Changeset creation not yet implemented - need to investigate ServiceNow changeset API"
        )

    def get_current_changeset(self) -> dict[str, Any] | None:
        """Get current changeset context if we're in one.

        Changesets can include both schema changes (table structure, fields) and
        data changes (records in those tables). This is useful for CMDB modifications
        where we want transactional behavior - all schema and data changes together.

        This is different from Change Requests (workflow/audit for operations).

        Note: This may not be directly supported by ServiceNow API.
        We might need to track changeset context manually or use headers.

        Returns:
            Current changeset data if in a changeset context, None otherwise
        """
        # TODO: Investigate ServiceNow API for detecting changeset context
        # Changesets can include both schema AND data changes (CMDB modifications)
        # This might require:
        # - Session headers (X-Changeset-ID?)
        # - API endpoint for current changeset context
        # - Manual tracking of changeset association
        return None

    def associate_with_change_request(
        self, table: str, record_sys_id: str, change_request_sys_id: str
    ) -> dict[str, Any]:
        """Associate a record with a Change Request.

        Args:
            table: Table name of the record
            record_sys_id: sys_id of the record to associate
            change_request_sys_id: sys_id of the Change Request

        Returns:
            Updated record data

        Raises:
            requests.HTTPError: If API request fails
        """
        url = f"{self.base_url}/table/{table}/{record_sys_id}"
        data = {"change_request": change_request_sys_id}
        response = self.session.put(url, json=data)
        response.raise_for_status()
        return response.json().get("result", {})  # type: ignore
