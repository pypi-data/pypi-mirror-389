"""Tests for mediacatch.speech module."""

import os
import sys
from http import HTTPStatus
from unittest.mock import Mock, patch

import pytest

from mediacatch.speech import upload
from mediacatch.speech.result import wait_for_result
from mediacatch.utils import (
    MediacatchTimeoutError,
    MediacatchUploadError,
)

# Get the actual upload module (not the function)
upload_module = sys.modules['mediacatch.speech.upload']


class TestSpeechUpload:
    """Test speech upload functionality."""

    @patch.object(upload_module, 'requests')
    @patch.object(upload_module, 'make_request')
    def test_upload_success(
        self, mock_make_request, mock_requests, sample_audio_file, mock_file_id, mock_api_key
    ):
        """Test successful audio file upload."""
        # Mock initiate upload response
        init_response = Mock()
        init_response.json.return_value = {'file_id': mock_file_id}

        # Mock signed URL response
        signed_url_response = Mock()
        signed_url_response.json.return_value = {
            'url': 'https://s3.example.com/presigned-url'
        }

        # Mock complete upload response
        complete_response = Mock()
        complete_response.json.return_value = {'estimated_processing_time': '00:05:00'}

        mock_make_request.side_effect = [init_response, signed_url_response, complete_response]

        # Mock S3 PUT response
        put_response = Mock()
        put_response.headers = {'ETag': 'test-etag-123'}
        mock_requests.put = Mock(return_value=put_response)

        # Execute upload
        result = upload(sample_audio_file, api_key=mock_api_key, verbose=False)

        assert result == mock_file_id
        assert mock_make_request.call_count == 3
        mock_requests.put.assert_called_once()

    def test_upload_file_not_found(self, mock_api_key):
        """Test upload with non-existent file."""
        with pytest.raises(MediacatchUploadError, match='does not exist'):
            upload('/nonexistent/file.wav', api_key=mock_api_key)

    def test_upload_missing_api_key(self, sample_audio_file):
        """Test upload without API key."""
        # Temporarily remove API key from environment
        with patch.dict(os.environ, {'MEDIACATCH_API_KEY': ''}, clear=False):
            with pytest.raises(MediacatchUploadError, match='API key is required'):
                upload(sample_audio_file, api_key=None)

    @patch.object(upload_module, 'requests')
    @patch.object(upload_module, 'make_request')
    def test_upload_with_env_api_key(
        self, mock_make_request, mock_requests, sample_audio_file
    ):
        """Test upload using API key from environment.

        Note: API key is set by setup_test_env fixture in conftest.py
        """

        # Setup mocks
        init_response = Mock()
        init_response.json.return_value = {'file_id': 'test-file-id'}

        signed_url_response = Mock()
        signed_url_response.json.return_value = {'url': 'https://s3.example.com/url'}

        complete_response = Mock()
        complete_response.json.return_value = {'estimated_processing_time': '00:05:00'}

        mock_make_request.side_effect = [init_response, signed_url_response, complete_response]

        put_response = Mock()
        put_response.headers = {'ETag': 'test-etag'}
        mock_requests.put = Mock(return_value=put_response)

        result = upload(sample_audio_file, api_key=None, verbose=False)

        assert result == 'test-file-id'
        # API key is automatically loaded from environment via setup_test_env fixture

    @patch.object(upload_module, 'requests')
    @patch.object(upload_module, 'make_request')
    @patch.object(upload_module, 'compress_to_ogg')
    @patch.object(upload_module, 'check_ffmpeg')
    @patch.object(upload_module, 'tempfile')
    def test_upload_with_compression(
        self,
        mock_tempfile,
        mock_check_ffmpeg,
        mock_compress,
        mock_make_request,
        mock_requests,
        sample_audio_file,
        mock_api_key,
        mock_file_id,
        temp_dir,
    ):
        """Test upload with audio compression enabled."""
        # Mock temp file creation
        temp_ogg = temp_dir / 'temp.ogg'
        temp_ogg.write_bytes(b'fake ogg data')
        mock_temp_file = Mock()
        mock_temp_file.name = str(temp_ogg)
        mock_tempfile.NamedTemporaryFile.return_value.__enter__.return_value = mock_temp_file

        # Setup mocks
        init_response = Mock()
        init_response.json.return_value = {'file_id': mock_file_id}

        signed_url_response = Mock()
        signed_url_response.json.return_value = {'url': 'https://s3.example.com/url'}

        complete_response = Mock()
        complete_response.json.return_value = {'estimated_processing_time': '00:05:00'}

        mock_make_request.side_effect = [init_response, signed_url_response, complete_response]

        put_response = Mock()
        put_response.headers = {'ETag': 'etag'}
        mock_requests.put = Mock(return_value=put_response)

        result = upload(
            sample_audio_file,
            api_key=mock_api_key,
            compress_input=True,
            sample_rate=16000,
            verbose=False,
        )

        assert result == mock_file_id
        mock_check_ffmpeg.assert_called_once()
        mock_compress.assert_called_once()

    @patch.object(upload_module, 'requests')
    @patch.object(upload_module, 'make_request')
    def test_upload_with_optional_parameters(
        self, mock_make_request, mock_requests, sample_audio_file, mock_api_key, mock_file_id
    ):
        """Test upload with optional parameters."""
        init_response = Mock()
        init_response.json.return_value = {'file_id': mock_file_id}

        signed_url_response = Mock()
        signed_url_response.json.return_value = {'url': 'https://s3.example.com/url'}

        complete_response = Mock()
        complete_response.json.return_value = {'estimated_processing_time': '00:05:00'}

        mock_make_request.side_effect = [init_response, signed_url_response, complete_response]

        put_response = Mock()
        put_response.headers = {'ETag': 'etag'}
        mock_requests.put = Mock(return_value=put_response)

        result = upload(
            sample_audio_file,
            api_key=mock_api_key,
            quota='test-quota',
            fallback_language='en',
            output_languages='da,de',
            topics=['politics', 'sports'],
            summary=True,
            verbose=False,
        )

        assert result == mock_file_id

        # Verify the initiate upload call included optional parameters
        init_call_kwargs = mock_make_request.call_args_list[0][1]
        assert init_call_kwargs['json']['quota'] == 'test-quota'
        assert init_call_kwargs['json']['fallback_language'] == 'en'
        assert init_call_kwargs['json']['output_languages'] == 'da,de'
        assert init_call_kwargs['json']['topics'] == ['politics', 'sports']
        assert init_call_kwargs['json']['summary'] is True


class TestSpeechResult:
    """Test speech result retrieval functionality."""

    @patch('mediacatch.speech.result.requests.get')
    @patch('mediacatch.speech.result.time.sleep')
    def test_wait_for_result_success(
        self, mock_sleep, mock_get, mock_file_id, mock_speech_result
    ):
        """Test successful result retrieval."""
        # First call returns 425 (Too Early), second returns 200 with result
        response_processing = Mock()
        response_processing.status_code = HTTPStatus.TOO_EARLY

        response_success = Mock()
        response_success.status_code = HTTPStatus.OK
        response_success.json.return_value = mock_speech_result

        mock_get.side_effect = [response_processing, response_success]

        result = wait_for_result(mock_file_id, verbose=False, delay=1)

        assert result == mock_speech_result
        assert mock_get.call_count == 2
        mock_sleep.assert_called_once_with(1)

    @patch('mediacatch.speech.result.requests.get')
    @patch('mediacatch.speech.result.time.sleep')
    def test_wait_for_result_accepted_status(
        self, mock_sleep, mock_get, mock_file_id, mock_speech_result
    ):
        """Test result retrieval with 202 Accepted status."""
        response_accepted = Mock()
        response_accepted.status_code = HTTPStatus.ACCEPTED

        response_success = Mock()
        response_success.status_code = HTTPStatus.OK
        response_success.json.return_value = mock_speech_result

        mock_get.side_effect = [response_accepted, response_success]

        result = wait_for_result(mock_file_id, verbose=False, delay=1)

        assert result == mock_speech_result
        mock_sleep.assert_called_once()

    @patch('mediacatch.speech.result.requests.get')
    def test_wait_for_result_not_found(self, mock_get, mock_file_id):
        """Test result retrieval with 404 Not Found."""
        response = Mock()
        response.status_code = HTTPStatus.NOT_FOUND
        mock_get.return_value = response

        # The function raises MediacatchAPIError which is caught and re-raised as MediacatchError
        with pytest.raises(Exception) as exc_info:
            wait_for_result(mock_file_id, verbose=False)

        # Check that error message contains the relevant information
        assert 'File not found' in str(exc_info.value) or '404' in str(exc_info.value)

    @patch('mediacatch.speech.result.requests.get')
    def test_wait_for_result_too_many_requests(self, mock_get, mock_file_id):
        """Test result retrieval with 429 Too Many Requests."""
        response = Mock()
        response.status_code = HTTPStatus.TOO_MANY_REQUESTS
        mock_get.return_value = response

        with pytest.raises(Exception) as exc_info:
            wait_for_result(mock_file_id, verbose=False)

        assert 'Too many requests' in str(exc_info.value) or '429' in str(exc_info.value)

    @patch('mediacatch.speech.result.requests.get')
    def test_wait_for_result_internal_server_error(self, mock_get, mock_file_id):
        """Test result retrieval with 500 Internal Server Error."""
        response = Mock()
        response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
        mock_get.return_value = response

        with pytest.raises(Exception) as exc_info:
            wait_for_result(mock_file_id, verbose=False)

        assert 'Internal server error' in str(exc_info.value) or '500' in str(exc_info.value)

    @patch('mediacatch.speech.result.requests.get')
    @patch('mediacatch.speech.result.time.sleep')
    @patch('mediacatch.speech.result.time.time')
    def test_wait_for_result_timeout(self, mock_time, mock_sleep, mock_get, mock_file_id):
        """Test result retrieval timeout."""
        # Simulate time passage
        mock_time.side_effect = [0, 10, 20, 30, 40]  # Each call adds 10 seconds

        response = Mock()
        response.status_code = HTTPStatus.TOO_EARLY
        mock_get.return_value = response

        with pytest.raises(MediacatchTimeoutError, match='Timeout waiting for result'):
            wait_for_result(mock_file_id, timeout=30, delay=10, verbose=False)

    @patch('mediacatch.speech.result.requests.get')
    def test_wait_for_result_request_exception(self, mock_get, mock_file_id):
        """Test result retrieval with request exception."""
        import requests

        mock_get.side_effect = requests.RequestException('Connection error')

        # Should handle exception and continue, then timeout
        with pytest.raises(MediacatchTimeoutError):
            wait_for_result(mock_file_id, timeout=1, delay=1, verbose=False)

    @patch('mediacatch.speech.result.requests.get')
    @patch('mediacatch.speech.result.time.sleep')
    def test_wait_for_result_json_decode_error(self, mock_sleep, mock_get, mock_file_id):
        """Test result retrieval with JSON decode error."""
        import json

        response = Mock()
        response.status_code = HTTPStatus.OK
        response.json.side_effect = json.JSONDecodeError('Invalid JSON', '', 0)
        mock_get.return_value = response

        # Should handle exception and continue, then timeout
        with pytest.raises(MediacatchTimeoutError):
            wait_for_result(mock_file_id, timeout=1, delay=1, verbose=False)

    @patch('mediacatch.speech.result.requests.get')
    def test_wait_for_result_custom_url(self, mock_get, mock_file_id, mock_speech_result):
        """Test result retrieval with custom URL."""
        response = Mock()
        response.status_code = HTTPStatus.OK
        response.json.return_value = mock_speech_result
        mock_get.return_value = response

        custom_url = 'https://custom.api.example.com/speech'
        result = wait_for_result(mock_file_id, url=custom_url, verbose=False)

        assert result == mock_speech_result
        mock_get.assert_called_once()
        assert custom_url in mock_get.call_args[0][0]
