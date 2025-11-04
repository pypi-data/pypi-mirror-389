"""
UptimeRobot API v2 Client

A comprehensive Python client for UptimeRobot API v2.
"""

import requests
from typing import Optional, Dict, Any, List, Union
import time


class UptimeRobotClient:
    """
    UptimeRobot API v2 client.

    Provides methods for all UptimeRobot API endpoints.
    """

    BASE_URL = "https://api.uptimerobot.com/v2/"

    def __init__(self, api_key: str):
        """
        Initialize the UptimeRobot client.

        Args:
            api_key: Your UptimeRobot API key
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'UptimeRobot-API-Python/0.1.0'
        })

    def _make_request(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a POST request to the UptimeRobot API.

        Args:
            endpoint: API endpoint (e.g., 'getMonitors')
            data: Request data (optional)

        Returns:
            API response

        Raises:
            requests.RequestException: For HTTP errors
            ValueError: For API errors
        """
        url = self.BASE_URL + endpoint

        # Prepare request data
        request_data = {"api_key": self.api_key}
        if data:
            request_data.update(data)

        # Make request
        response = self.session.post(url, json=request_data)
        response.raise_for_status()

        result = response.json()

        # Check for API errors
        if result.get("stat") != "ok":
            error = result.get("error", {})
            raise ValueError(f"API Error: {error.get('type', 'unknown')} - {error.get('message', 'unknown error')}")

        return result

    # Monitor Methods
    def get_monitors(self, monitors: Optional[str] = None, types: Optional[str] = None,
                    statuses: Optional[str] = None, keyword: Optional[str] = None,
                    alert_contacts: Optional[int] = None, logs: Optional[int] = None,
                    logs_limit: Optional[int] = None, response_times: Optional[int] = None,
                    response_times_limit: Optional[int] = None, response_times_average: Optional[int] = None,
                    response_times_start_date: Optional[int] = None, response_times_end_date: Optional[int] = None,
                    offset: Optional[int] = None, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Get monitors with optional filtering and detailed information.

        Args:
            monitors: Comma-separated monitor IDs
            types: Comma-separated monitor types
            statuses: Comma-separated monitor statuses
            keyword: Search keyword
            alert_contacts: Include alert contacts (1=yes, 0=no)
            logs: Include logs (1=yes, 0=no)
            logs_limit: Number of logs to include
            response_times: Include response times (1=yes, 0=no)
            response_times_limit: Number of response time entries
            response_times_average: Include average response time (1=yes, 0=no)
            response_times_start_date: Start date for response times (Unix timestamp)
            response_times_end_date: End date for response times (Unix timestamp)
            offset: Pagination offset
            limit: Pagination limit (max 50)

        Returns:
            Monitors data
        """
        data = {}
        if monitors is not None:
            data["monitors"] = monitors
        if types is not None:
            data["types"] = types
        if statuses is not None:
            data["statuses"] = statuses
        if keyword is not None:
            data["keyword"] = keyword
        if alert_contacts is not None:
            data["alert_contacts"] = alert_contacts
        if logs is not None:
            data["logs"] = logs
        if logs_limit is not None:
            data["logs_limit"] = logs_limit
        if response_times is not None:
            data["response_times"] = response_times
        if response_times_limit is not None:
            data["response_times_limit"] = response_times_limit
        if response_times_average is not None:
            data["response_times_average"] = response_times_average
        if response_times_start_date is not None:
            data["response_times_start_date"] = response_times_start_date
        if response_times_end_date is not None:
            data["response_times_end_date"] = response_times_end_date
        if offset is not None:
            data["offset"] = offset
        if limit is not None:
            data["limit"] = limit

        return self._make_request("getMonitors", data)

    def new_monitor(self, friendly_name: str, url: str, type: int,
                   sub_type: Optional[int] = None, port: Optional[int] = None,
                   keyword_type: Optional[int] = None, keyword_value: Optional[str] = None,
                   interval: Optional[int] = None, timeout: Optional[int] = None,
                   alert_contacts: Optional[str] = None, monitor_group_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Create a new monitor.

        Args:
            friendly_name: Monitor display name
            url: URL/IP to monitor
            type: Monitor type (1=HTTP, 2=Keyword, 3=Ping, 4=Port, 5=Heartbeat)
            sub_type: Subtype for port monitors
            port: Port number for port monitors
            keyword_type: Keyword monitoring type
            keyword_value: Keyword to monitor
            interval: Check interval in seconds
            timeout: Timeout in seconds
            alert_contacts: Comma-separated alert contact IDs
            monitor_group_id: Group ID to assign monitor to

        Returns:
            Creation result
        """
        data = {
            "friendly_name": friendly_name,
            "url": url,
            "type": type
        }

        optional_fields = {
            "sub_type": sub_type,
            "port": port,
            "keyword_type": keyword_type,
            "keyword_value": keyword_value,
            "interval": interval,
            "timeout": timeout,
            "alert_contacts": alert_contacts,
            "monitor_group_id": monitor_group_id
        }

        for field, value in optional_fields.items():
            if value is not None:
                data[field] = value

        return self._make_request("newMonitor", data)

    def edit_monitor(self, id: int, friendly_name: Optional[str] = None, url: Optional[str] = None,
                    type: Optional[int] = None, interval: Optional[int] = None,
                    timeout: Optional[int] = None, alert_contacts: Optional[str] = None) -> Dict[str, Any]:
        """
        Update an existing monitor.

        Args:
            id: Monitor ID to update
            friendly_name: New display name
            url: New URL/IP
            type: New monitor type
            interval: New check interval
            timeout: New timeout
            alert_contacts: New alert contact IDs

        Returns:
            Update result
        """
        data = {"id": id}

        optional_fields = {
            "friendly_name": friendly_name,
            "url": url,
            "type": type,
            "interval": interval,
            "timeout": timeout,
            "alert_contacts": alert_contacts
        }

        for field, value in optional_fields.items():
            if value is not None:
                data[field] = value

        return self._make_request("editMonitor", data)

    def delete_monitor(self, id: int) -> Dict[str, Any]:
        """
        Delete a monitor.

        Args:
            id: Monitor ID to delete

        Returns:
            Deletion result
        """
        return self._make_request("deleteMonitor", {"id": id})

    def reset_monitor(self, id: int) -> Dict[str, Any]:
        """
        Reset monitor statistics.

        Args:
            id: Monitor ID to reset

        Returns:
            Reset result
        """
        return self._make_request("resetMonitor", {"id": id})

    # Alert Contact Methods
    def get_alert_contacts(self, alert_contacts: Optional[str] = None) -> Dict[str, Any]:
        """
        Get alert contacts.

        Args:
            alert_contacts: Comma-separated contact IDs

        Returns:
            Alert contacts data
        """
        data = {}
        if alert_contacts:
            data["alert_contacts"] = alert_contacts

        return self._make_request("getAlertContacts", data)

    def new_alert_contact(self, friendly_name: str, type: int, value: str) -> Dict[str, Any]:
        """
        Create a new alert contact.

        Args:
            friendly_name: Contact display name
            type: Contact type (1=Email, 2=SMS, etc.)
            value: Contact value (email, phone, webhook URL)

        Returns:
            Creation result
        """
        data = {
            "friendly_name": friendly_name,
            "type": type,
            "value": value
        }

        return self._make_request("newAlertContact", data)

    def edit_alert_contact(self, id: int, friendly_name: Optional[str] = None,
                          type: Optional[int] = None, value: Optional[str] = None) -> Dict[str, Any]:
        """
        Update an alert contact.

        Args:
            id: Contact ID to update
            friendly_name: New display name
            type: New contact type
            value: New contact value

        Returns:
            Update result
        """
        data = {"id": id}

        if friendly_name is not None:
            data["friendly_name"] = friendly_name
        if type is not None:
            data["type"] = type
        if value is not None:
            data["value"] = value

        return self._make_request("editAlertContact", data)

    def delete_alert_contact(self, id: int) -> Dict[str, Any]:
        """
        Delete an alert contact.

        Args:
            id: Contact ID to delete

        Returns:
            Deletion result
        """
        return self._make_request("deleteAlertContact", {"id": id})

    # Maintenance Window Methods
    def get_maintenance_windows(self, maintenance_windows: Optional[str] = None) -> Dict[str, Any]:
        """
        Get maintenance windows.

        Args:
            maintenance_windows: Comma-separated window IDs

        Returns:
            Maintenance windows data
        """
        data = {}
        if maintenance_windows:
            data["maintenance_windows"] = maintenance_windows

        return self._make_request("getMaintenanceWindows", data)

    def new_maintenance_window(self, friendly_name: str, type: int, value: str,
                             duration: int, start_time: Optional[str] = None,
                             status: Optional[int] = None) -> Dict[str, Any]:
        """
        Create a new maintenance window.

        Args:
            friendly_name: Window display name
            type: Window type (1=once, 2=weekly, 3=monthly)
            value: Window timing expression
            duration: Duration in minutes
            start_time: Start time (optional)
            status: Status (optional)

        Returns:
            Creation result
        """
        data = {
            "friendly_name": friendly_name,
            "type": type,
            "value": value,
            "duration": duration
        }

        if start_time:
            data["start_time"] = start_time
        if status is not None:
            data["status"] = status

        return self._make_request("newMaintenanceWindow", data)

    def edit_maintenance_window(self, id: int, friendly_name: Optional[str] = None,
                               type: Optional[int] = None, value: Optional[str] = None,
                               duration: Optional[int] = None) -> Dict[str, Any]:
        """
        Update a maintenance window.

        Args:
            id: Window ID to update
            friendly_name: New display name
            type: New window type
            value: New timing expression
            duration: New duration

        Returns:
            Update result
        """
        data = {"id": id}

        if friendly_name:
            data["friendly_name"] = friendly_name
        if type is not None:
            data["type"] = type
        if value:
            data["value"] = value
        if duration is not None:
            data["duration"] = duration

        return self._make_request("editMaintenanceWindow", data)

    def delete_maintenance_window(self, id: int) -> Dict[str, Any]:
        """
        Delete a maintenance window.

        Args:
            id: Window ID to delete

        Returns:
            Deletion result
        """
        return self._make_request("deleteMaintenanceWindow", {"id": id})

    # Status Page Methods
    def get_status_pages(self, status_pages: Optional[str] = None) -> Dict[str, Any]:
        """
        Get status pages.

        Args:
            status_pages: Comma-separated page IDs

        Returns:
            Status pages data
        """
        data = {}
        if status_pages:
            data["status_pages"] = status_pages

        return self._make_request("getStatusPages", data)

    def new_status_page(self, friendly_name: str, monitors: str) -> Dict[str, Any]:
        """
        Create a new status page.

        Args:
            friendly_name: Page display name
            monitors: Comma-separated monitor IDs

        Returns:
            Creation result
        """
        data = {
            "friendly_name": friendly_name,
            "monitors": monitors
        }

        return self._make_request("newStatusPage", data)

    def edit_status_page(self, id: int, friendly_name: Optional[str] = None,
                        monitors: Optional[str] = None, status_page_password: Optional[str] = None) -> Dict[str, Any]:
        """
        Update a status page.

        Args:
            id: Page ID to update
            friendly_name: New display name
            monitors: New monitor IDs
            status_page_password: New password

        Returns:
            Update result
        """
        data = {"id": id}

        if friendly_name:
            data["friendly_name"] = friendly_name
        if monitors:
            data["monitors"] = monitors
        if status_page_password:
            data["status_page_password"] = status_page_password

        return self._make_request("editStatusPage", data)

    def delete_status_page(self, id: int) -> Dict[str, Any]:
        """
        Delete a status page.

        Args:
            id: Page ID to delete

        Returns:
            Deletion result
        """
        return self._make_request("deleteStatusPage", {"id": id})

    # Account Methods
    def get_account_details(self) -> Dict[str, Any]:
        """
        Get account details.

        Returns:
            Account information
        """
        return self._make_request("getAccountDetails")

    def get_api_key_details(self) -> Dict[str, Any]:
        """
        Get API key details.

        Returns:
            API key information
        """
        return self._make_request("getApiKeyDetails")

    def close(self):
        """Close the session."""
        self.session.close()
