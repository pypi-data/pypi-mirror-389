"""Unit tests for DetailService."""

import json
from unittest.mock import Mock

import pytest

from check_msdefender.core.exceptions import ValidationError
from check_msdefender.services.detail_service import DetailService


class TestDetailService:
    """Unit tests for DetailService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.service = DetailService(self.mock_client)

    def test_init(self):
        """Test service initialization."""
        assert self.service.defender == self.mock_client
        assert hasattr(self.service, "logger")

    def test_get_result_by_machine_id_success(self):
        """Test successful retrieval by machine ID."""
        # Mock the API response
        mock_machine_data = {
            "id": "test-machine-123",
            "computerDnsName": "test.domain.com",
            "osPlatform": "Windows10",
            "lastSeen": "2024-01-15T10:30:00Z",
        }
        self.mock_client.get_machine_by_id.return_value = mock_machine_data

        result = self.service.get_result(machine_id="test-machine-123")

        # Should return 1 for found
        assert result["value"] == 1

        # Should call the client with correct machine ID
        self.mock_client.get_machine_by_id.assert_called_once_with("test-machine-123")

        # Should store the machine details
        assert hasattr(self.service, "_machine_details")
        assert self.service._machine_details == mock_machine_data

    def test_get_result_by_dns_name_success(self):
        """Test successful retrieval by DNS name."""
        # Mock DNS lookup response
        mock_dns_response = {"value": [{"id": "test-machine-456"}]}
        mock_machine_data = {
            "id": "test-machine-456",
            "computerDnsName": "test.domain.com",
        }

        self.mock_client.get_machine_by_dns_name.return_value = mock_dns_response
        self.mock_client.get_machine_by_id.return_value = mock_machine_data

        result = self.service.get_result(dns_name="test.domain.com")

        # Should return 1 for found
        assert result["value"] == 1

        # Should call both DNS lookup and machine ID retrieval
        self.mock_client.get_machine_by_dns_name.assert_called_once_with(
            "test.domain.com"
        )
        self.mock_client.get_machine_by_id.assert_called_once_with("test-machine-456")

    def test_get_result_by_dns_name_not_found(self):
        """Test DNS name not found."""
        # Mock empty DNS response
        mock_dns_response = {"value": []}
        self.mock_client.get_machine_by_dns_name.return_value = mock_dns_response

        result = self.service.get_result(dns_name="nonexistent.domain.com")

        # Should return 0 for not found
        assert result["value"] == 0

        # Should not call get_machine_by_id since DNS lookup failed
        self.mock_client.get_machine_by_dns_name.assert_called_once_with(
            "nonexistent.domain.com"
        )
        self.mock_client.get_machine_by_id.assert_not_called()

    def test_get_result_no_parameters(self):
        """Test error when no parameters provided."""
        with pytest.raises(
            ValidationError, match="Either machine_id or dns_name must be provided"
        ):
            self.service.get_result()

        # Should not make any API calls
        self.mock_client.get_machine_by_id.assert_not_called()
        self.mock_client.get_machine_by_dns_name.assert_not_called()

    def test_get_result_api_exception_propagation(self):
        """Test that API exceptions are propagated."""
        # Mock an exception from the client
        self.mock_client.get_machine_by_id.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            self.service.get_result(machine_id="test-machine")

    def test_get_machine_details_json_success(self):
        """Test JSON formatting of machine details."""
        # Set up machine details
        mock_data = {
            "id": "test-machine",
            "computerDnsName": "test.domain.com",
            "osPlatform": "Windows10",
        }
        self.service._machine_details = mock_data

        result = self.service.get_machine_details_json()

        # Should return formatted JSON
        assert result is not None
        parsed = json.loads(result)
        assert parsed == mock_data

        # Should be pretty-printed with indentation
        assert "\n" in result
        assert "  " in result  # 2-space indentation

    def test_get_machine_details_json_no_data(self):
        """Test JSON formatting when no data available."""
        result = self.service.get_machine_details_json()
        assert result is None

    def test_logging_calls(self):
        """Test that logging methods are called appropriately."""
        # Mock successful response
        mock_machine_data = {"id": "test-machine", "computerDnsName": "test.domain.com"}
        self.mock_client.get_machine_by_id.return_value = mock_machine_data

        # Mock the logger
        self.service.logger = Mock()

        self.service.get_result(machine_id="test-machine")

        # Verify logging calls
        self.service.logger.method_entry.assert_called_once_with(
            "get_result", machine_id="test-machine", dns_name=None
        )
        # get_result returns a dict, so method_exit gets the dict
        assert self.service.logger.method_exit.call_count == 1
        exit_call_args = self.service.logger.method_exit.call_args[0]
        assert exit_call_args[0] == "get_result"
        assert exit_call_args[1]["value"] == 1

    def test_dns_name_with_machine_id_precedence(self):
        """Test that DNS name resolution works when both parameters are provided."""
        # Mock responses
        mock_dns_response = {"value": [{"id": "dns-resolved-machine"}]}
        mock_machine_data = {"id": "dns-resolved-machine"}

        self.mock_client.get_machine_by_dns_name.return_value = mock_dns_response
        self.mock_client.get_machine_by_id.return_value = mock_machine_data

        # Call with both parameters - DNS name should be used first
        result = self.service.get_result(
            machine_id="direct-machine", dns_name="test.domain.com"
        )

        assert result["value"] == 1
        # Should resolve via DNS first
        self.mock_client.get_machine_by_dns_name.assert_called_once_with(
            "test.domain.com"
        )
        self.mock_client.get_machine_by_id.assert_called_once_with(
            "dns-resolved-machine"
        )
