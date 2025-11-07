"""Tests for mediacatch.vision module."""

import os
from http import HTTPStatus
from unittest.mock import Mock, patch

import pytest

from mediacatch.vision.upload import upload
from mediacatch.vision.result import wait_for_result
from mediacatch.utils import (
    MediacatchTimeoutError,
    MediacatchUploadError,
)


class TestVisionUpload:
    """Test vision upload functionality."""

    @patch('builtins.open', create=True)
    @patch('requests.post')
    @patch('requests.Session')
    def test_upload_ocr_success(
        self, mock_session_class, mock_post, mock_open, sample_video_file, mock_api_key
    ):
        """Test successful OCR video upload."""
        # Mock presigned URL response
        presigned_response = Mock()
        presigned_response.status_code = HTTPStatus.CREATED
        presigned_response.json.return_value = {
            'file_id': 'test-file-id',
            'url': 'https://s3.example.com/upload',
            'fields': {'key': 'test-key', 'policy': 'test-policy'},
        }

        # Mock complete upload response
        complete_response = Mock()
        complete_response.status_code = HTTPStatus.OK

        mock_post.side_effect = [presigned_response, complete_response]

        # Mock S3 upload response
        mock_session = Mock()
        s3_response = Mock()
        s3_response.status_code = HTTPStatus.NO_CONTENT
        mock_session.post.return_value = s3_response
        mock_session_class.return_value = mock_session

        # Mock file open
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file

        result = upload(str(sample_video_file), type='ocr', api_key=mock_api_key, verbose=False)

        assert result == 'test-file-id'
        assert mock_post.call_count == 2

    @patch('builtins.open', create=True)
    @patch('requests.post')
    @patch('requests.Session')
    def test_upload_face_success(
        self, mock_session_class, mock_post, mock_open, sample_video_file, mock_api_key
    ):
        """Test successful face detection video upload."""
        presigned_response = Mock()
        presigned_response.status_code = HTTPStatus.CREATED
        presigned_response.json.return_value = {
            'file_id': 'face-file-id',
            'url': 'https://s3.example.com/upload',
            'fields': {'key': 'test-key'},
        }

        complete_response = Mock()
        complete_response.status_code = HTTPStatus.OK

        mock_post.side_effect = [presigned_response, complete_response]

        mock_session = Mock()
        s3_response = Mock()
        s3_response.status_code = HTTPStatus.NO_CONTENT
        mock_session.post.return_value = s3_response
        mock_session_class.return_value = mock_session

        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file

        result = upload(
            str(sample_video_file),
            type='face',
            api_key=mock_api_key,
            face_recognition=True,
            face_age=True,
            face_gender=True,
            verbose=False,
        )

        assert result == 'face-file-id'

    def test_upload_missing_api_key(self, sample_video_file):
        """Test upload without API key."""
        # Temporarily remove API key from environment
        with patch.dict(os.environ, {'MEDIACATCH_API_KEY': ''}, clear=False):
            with pytest.raises(MediacatchUploadError, match='API key is required'):
                upload(str(sample_video_file), type='ocr', api_key=None)

    @patch('requests.post')
    def test_upload_presigned_url_failure(self, mock_post, sample_video_file, mock_api_key):
        """Test upload when presigned URL request fails."""
        mock_response = Mock()
        mock_response.status_code = HTTPStatus.BAD_REQUEST
        mock_post.return_value = mock_response

        with pytest.raises(MediacatchUploadError, match='Failed to get presigned URL'):
            upload(str(sample_video_file), type='ocr', api_key=mock_api_key, verbose=False)

    @patch('builtins.open', create=True)
    @patch('time.sleep')
    @patch('requests.post')
    @patch('requests.Session')
    def test_upload_s3_retry_logic(
        self,
        mock_session_class,
        mock_post,
        mock_sleep,
        mock_open,
        sample_video_file,
        mock_api_key,
    ):
        """Test S3 upload retry logic."""
        presigned_response = Mock()
        presigned_response.status_code = HTTPStatus.CREATED
        presigned_response.json.return_value = {
            'file_id': 'test-file-id',
            'url': 'https://s3.example.com/upload',
            'fields': {'key': 'test-key'},
        }

        complete_response = Mock()
        complete_response.status_code = HTTPStatus.OK

        mock_post.side_effect = [presigned_response, complete_response]

        # First two S3 attempts fail, third succeeds
        mock_session = Mock()
        s3_fail_response = Mock()
        s3_fail_response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR

        s3_success_response = Mock()
        s3_success_response.status_code = HTTPStatus.NO_CONTENT

        mock_session.post.side_effect = [
            s3_fail_response,
            s3_fail_response,
            s3_success_response,
        ]
        mock_session_class.return_value = mock_session

        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file

        result = upload(
            str(sample_video_file),
            type='ocr',
            api_key=mock_api_key,
            max_retries=3,
            delay=0.1,
            verbose=False,
        )

        assert result == 'test-file-id'
        assert mock_session.post.call_count == 3
        assert mock_sleep.call_count == 2

    @patch('builtins.open', create=True)
    @patch('time.sleep')
    @patch('requests.post')
    @patch('requests.Session')
    def test_upload_s3_max_retries_exceeded(
        self,
        mock_session_class,
        mock_post,
        mock_sleep,
        mock_open,
        sample_video_file,
        mock_api_key,
    ):
        """Test S3 upload when max retries is exceeded."""
        presigned_response = Mock()
        presigned_response.status_code = HTTPStatus.CREATED
        presigned_response.json.return_value = {
            'file_id': 'test-file-id',
            'url': 'https://s3.example.com/upload',
            'fields': {'key': 'test-key'},
        }

        mock_post.return_value = presigned_response

        mock_session = Mock()
        s3_response = Mock()
        s3_response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
        mock_session.post.return_value = s3_response
        mock_session_class.return_value = mock_session

        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file

        with pytest.raises(MediacatchUploadError, match='Failed to upload to S3'):
            upload(
                str(sample_video_file),
                type='ocr',
                api_key=mock_api_key,
                max_retries=2,
                delay=0.1,
                verbose=False,
            )

    @patch('builtins.open', create=True)
    @patch('requests.post')
    @patch('requests.Session')
    def test_upload_with_ocr_parameters(
        self, mock_session_class, mock_post, mock_open, sample_video_file, mock_api_key
    ):
        """Test upload with OCR-specific parameters."""
        presigned_response = Mock()
        presigned_response.status_code = HTTPStatus.CREATED
        presigned_response.json.return_value = {
            'file_id': 'ocr-file-id',
            'url': 'https://s3.example.com/upload',
            'fields': {'key': 'test-key'},
        }

        complete_response = Mock()
        complete_response.status_code = HTTPStatus.OK

        mock_post.side_effect = [presigned_response, complete_response]

        mock_session = Mock()
        s3_response = Mock()
        s3_response.status_code = HTTPStatus.NO_CONTENT
        mock_session.post.return_value = s3_response
        mock_session_class.return_value = mock_session

        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file

        result = upload(
            str(sample_video_file),
            type='ocr',
            api_key=mock_api_key,
            fps=2,
            tolerance=15,
            min_bbox_iou=0.6,
            min_levenshtein_ratio=0.8,
            max_text_length=5,
            min_text_confidence=0.6,
            max_text_confidence=0.9,
            get_frame_index=True,
            get_bbox=True,
            verbose=False,
        )

        assert result == 'ocr-file-id'

        # Verify parameters were included in the request
        init_call_args = mock_post.call_args_list[0]
        import json

        request_data = json.loads(init_call_args[1]['data'])
        extra = request_data['extra']
        assert extra['fps'] == 2
        assert extra['tolerance'] == 15
        assert extra['min_bbox_iou'] == 0.6
        assert extra['min_levenshtein_ratio'] == 0.8


class TestVisionResult:
    """Test vision result retrieval functionality."""

    @patch('mediacatch.vision.result.requests.get')
    @patch('mediacatch.vision.result.time.sleep')
    def test_wait_for_result_success(
        self, mock_sleep, mock_get, mock_file_id, mock_vision_ocr_result
    ):
        """Test successful result retrieval."""
        response_processing = Mock()
        response_processing.status_code = HTTPStatus.PROCESSING

        response_success = Mock()
        response_success.status_code = HTTPStatus.OK
        response_success.json.return_value = mock_vision_ocr_result

        mock_get.side_effect = [response_processing, response_success]

        result = wait_for_result(mock_file_id, verbose=False, delay=1)

        assert result == mock_vision_ocr_result
        assert mock_get.call_count == 2
        mock_sleep.assert_called_once_with(1)

    @patch('mediacatch.vision.result.requests.get')
    @patch('mediacatch.vision.result.time.sleep')
    def test_wait_for_result_accepted_status(
        self, mock_sleep, mock_get, mock_file_id, mock_vision_face_result
    ):
        """Test result retrieval with 202 Accepted status."""
        response_accepted = Mock()
        response_accepted.status_code = HTTPStatus.ACCEPTED

        response_success = Mock()
        response_success.status_code = HTTPStatus.OK
        response_success.json.return_value = mock_vision_face_result

        mock_get.side_effect = [response_accepted, response_success]

        result = wait_for_result(mock_file_id, verbose=False, delay=1)

        assert result == mock_vision_face_result
        mock_sleep.assert_called_once()

    @patch('mediacatch.vision.result.requests.get')
    @patch('mediacatch.vision.result.time.sleep')
    def test_wait_for_result_no_content(self, mock_sleep, mock_get, mock_file_id):
        """Test result retrieval with 204 No Content."""
        response = Mock()
        response.status_code = HTTPStatus.NO_CONTENT
        mock_get.return_value = response

        result = wait_for_result(mock_file_id, verbose=False)

        assert result == {}

    @patch('mediacatch.vision.result.requests.get')
    @patch('mediacatch.vision.result.time.sleep')
    def test_wait_for_result_gateway_timeout_retry(
        self, mock_sleep, mock_get, mock_file_id, mock_vision_ocr_result
    ):
        """Test result retrieval with 504 Gateway Timeout."""
        response_timeout = Mock()
        response_timeout.status_code = HTTPStatus.GATEWAY_TIMEOUT

        response_success = Mock()
        response_success.status_code = HTTPStatus.OK
        response_success.json.return_value = mock_vision_ocr_result

        mock_get.side_effect = [response_timeout, response_success]

        result = wait_for_result(mock_file_id, verbose=False, delay=1)

        assert result == mock_vision_ocr_result
        mock_sleep.assert_called_once()

    @patch('mediacatch.vision.result.requests.get')
    def test_wait_for_result_not_found(self, mock_get, mock_file_id):
        """Test result retrieval with 404 Not Found."""
        response = Mock()
        response.status_code = HTTPStatus.NOT_FOUND
        mock_get.return_value = response

        with pytest.raises(Exception) as exc_info:
            wait_for_result(mock_file_id, verbose=False)

        assert 'File not found' in str(exc_info.value) or '404' in str(exc_info.value)

    @patch('mediacatch.vision.result.requests.get')
    def test_wait_for_result_too_many_requests(self, mock_get, mock_file_id):
        """Test result retrieval with 429 Too Many Requests."""
        response = Mock()
        response.status_code = HTTPStatus.TOO_MANY_REQUESTS
        mock_get.return_value = response

        with pytest.raises(Exception) as exc_info:
            wait_for_result(mock_file_id, verbose=False)

        assert 'Too many requests' in str(exc_info.value) or '429' in str(exc_info.value)

    @patch('mediacatch.vision.result.requests.get')
    def test_wait_for_result_internal_server_error(self, mock_get, mock_file_id):
        """Test result retrieval with 500 Internal Server Error."""
        response = Mock()
        response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
        mock_get.return_value = response

        with pytest.raises(Exception) as exc_info:
            wait_for_result(mock_file_id, verbose=False)

        assert 'Internal server error' in str(exc_info.value) or '500' in str(exc_info.value)

    @patch('mediacatch.vision.result.requests.get')
    @patch('mediacatch.vision.result.time.sleep')
    @patch('mediacatch.vision.result.time.time')
    def test_wait_for_result_timeout(self, mock_time, mock_sleep, mock_get, mock_file_id):
        """Test result retrieval timeout."""
        mock_time.side_effect = [0, 10, 20, 30, 40]

        response = Mock()
        response.status_code = HTTPStatus.PROCESSING
        mock_get.return_value = response

        with pytest.raises(MediacatchTimeoutError, match='Timeout waiting for result'):
            wait_for_result(mock_file_id, timeout=30, delay=10, verbose=False)

    @patch('mediacatch.vision.result.requests.get')
    def test_wait_for_result_custom_url(self, mock_get, mock_file_id, mock_vision_ocr_result):
        """Test result retrieval with custom URL."""
        response = Mock()
        response.status_code = HTTPStatus.OK
        response.json.return_value = mock_vision_ocr_result
        mock_get.return_value = response

        custom_url = 'https://custom.vision.api.example.com'
        result = wait_for_result(mock_file_id, url=custom_url, verbose=False)

        assert result == mock_vision_ocr_result
        mock_get.assert_called_once()
        assert custom_url in mock_get.call_args[0][0]
