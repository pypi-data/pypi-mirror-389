"""Tests for mediacatch.utils module."""

import subprocess
from http import HTTPStatus
from unittest.mock import Mock, patch

import pytest

from mediacatch.utils import (
    MediacatchAPIError,
    MediacatchError,
    MediacatchTimeoutError,
    MediacatchUploadError,
)
from mediacatch.utils.general import (
    check_ffmpeg,
    compress_to_ogg,
    get_assets_data,
    get_data_from_url,
    load_data_from_json,
    make_request,
    read_file_in_chunks,
)


class TestExceptions:
    """Test custom exception classes."""

    def test_mediacatch_error(self):
        """Test MediacatchError exception."""
        error = MediacatchError('Test error message')
        assert error.message == 'Test error message'
        assert str(error) == 'Test error message'

    def test_mediacatch_api_error(self):
        """Test MediacatchAPIError exception."""
        error = MediacatchAPIError(404, 'Not Found')
        assert error.status_code == 404
        assert error.reason == 'Not Found'
        assert 'API returned error status code: 404' in str(error)
        assert 'with reason: Not Found' in str(error)

    def test_mediacatch_timeout_error(self):
        """Test MediacatchTimeoutError exception."""
        error = MediacatchTimeoutError('Request timed out')
        assert error.message == 'Request timed out'
        assert str(error) == 'Request timed out'

    def test_mediacatch_upload_error(self):
        """Test MediacatchUploadError exception."""
        error = MediacatchUploadError('Upload failed')
        assert error.message == 'Upload failed'
        assert str(error) == 'Upload failed'


class TestGetDataFromUrl:
    """Test get_data_from_url function."""

    @patch('mediacatch.utils.general.requests.get')
    def test_get_data_from_url_success(self, mock_get):
        """Test successful data retrieval from URL."""
        mock_response = Mock()
        mock_response.status_code = HTTPStatus.OK
        mock_response.json.return_value = {'key': 'value'}
        mock_get.return_value = mock_response

        result = get_data_from_url('https://example.com/data')

        assert result == {'key': 'value'}
        mock_get.assert_called_once_with('https://example.com/data')

    @patch('mediacatch.utils.general.requests.get')
    def test_get_data_from_url_failure(self, mock_get):
        """Test failed data retrieval from URL."""
        mock_response = Mock()
        mock_response.status_code = HTTPStatus.NOT_FOUND
        mock_get.return_value = mock_response

        with pytest.raises(AssertionError):
            get_data_from_url('https://example.com/notfound')


class TestLoadDataFromJson:
    """Test load_data_from_json function."""

    def test_load_data_from_json_success(self, sample_json_file):
        """Test successful JSON data loading."""
        result = load_data_from_json(str(sample_json_file))

        assert result == {'test_key': 'test_value', 'nested': {'data': [1, 2, 3]}}

    def test_load_data_from_json_file_not_found(self):
        """Test JSON loading with non-existent file."""
        with pytest.raises(AssertionError):
            load_data_from_json('/nonexistent/file.json')


class TestGetAssetsData:
    """Test get_assets_data function."""

    def test_get_assets_data_existing_file(self):
        """Test retrieving existing asset file."""
        # The assets folder should contain font files
        result = get_assets_data('Arial.ttf')
        assert isinstance(result, str)
        assert 'Arial.ttf' in result

    def test_get_assets_data_nonexistent_file(self):
        """Test retrieving non-existent asset file."""
        with pytest.raises(AssertionError):
            get_assets_data('nonexistent_file.txt')


class TestMakeRequest:
    """Test make_request function."""

    @patch('mediacatch.utils.general.requests.get')
    def test_make_request_success(self, mock_get):
        """Test successful request."""
        mock_response = Mock()
        mock_response.status_code = HTTPStatus.OK
        mock_get.return_value = mock_response

        result = make_request('get', 'https://example.com', {})

        assert result == mock_response
        mock_get.assert_called_once()

    @patch('mediacatch.utils.general.requests.post')
    def test_make_request_post_error(self, mock_post):
        """Test POST request with error status."""
        mock_response = Mock()
        mock_response.status_code = HTTPStatus.BAD_REQUEST
        mock_response.json.return_value = {'detail': 'Bad request'}
        mock_post.return_value = mock_response

        with pytest.raises(RuntimeError, match='Error during request'):
            make_request('post', 'https://example.com', {})

    @patch('mediacatch.utils.general.requests.get')
    @patch('mediacatch.utils.general.time.sleep')
    def test_make_request_retry_logic(self, mock_sleep, mock_get):
        """Test request retry logic."""
        # First two attempts fail, third succeeds
        mock_response_fail = Mock()
        mock_response_fail.status_code = HTTPStatus.SERVICE_UNAVAILABLE

        mock_response_success = Mock()
        mock_response_success.status_code = HTTPStatus.OK

        mock_get.side_effect = [mock_response_fail, mock_response_fail, mock_response_success]

        result = make_request('get', 'https://example.com', {}, max_retries=3)

        assert result == mock_response_success
        assert mock_get.call_count == 3
        assert mock_sleep.call_count == 2

    @patch('mediacatch.utils.general.requests.get')
    @patch('mediacatch.utils.general.time.sleep')
    def test_make_request_max_retries_exceeded(self, mock_sleep, mock_get):
        """Test request when max retries is exceeded."""
        mock_response = Mock()
        mock_response.status_code = HTTPStatus.SERVICE_UNAVAILABLE
        mock_get.return_value = mock_response

        with pytest.raises(RuntimeError, match='Maximum retry limit reached'):
            make_request('get', 'https://example.com', {}, max_retries=2)

        assert mock_get.call_count == 2


class TestReadFileInChunks:
    """Test read_file_in_chunks function."""

    def test_read_file_in_chunks(self, temp_dir):
        """Test reading file in chunks."""
        # Create a test file with known content
        test_file = temp_dir / 'test.bin'
        test_content = b'x' * 1024 * 1024  # 1MB of data
        test_file.write_bytes(test_content)

        # Read in 512KB chunks
        chunk_size = 512 * 1024
        chunks = []

        with test_file.open('rb') as f:
            for chunk in read_file_in_chunks(f, chunk_size=chunk_size):
                chunks.append(chunk)

        # Should have 2 chunks
        assert len(chunks) == 2
        assert len(chunks[0]) == chunk_size
        assert len(chunks[1]) == chunk_size

        # Verify content
        assert b''.join(chunks) == test_content

    def test_read_file_in_chunks_small_file(self, temp_dir):
        """Test reading small file in chunks."""
        test_file = temp_dir / 'small.bin'
        test_content = b'small content'
        test_file.write_bytes(test_content)

        with test_file.open('rb') as f:
            chunks = list(read_file_in_chunks(f, chunk_size=1024))

        assert len(chunks) == 1
        assert chunks[0] == test_content


class TestCheckFfmpeg:
    """Test check_ffmpeg function."""

    @patch('mediacatch.utils.general.subprocess.run')
    def test_check_ffmpeg_installed(self, mock_run):
        """Test when ffmpeg is installed."""
        mock_run.return_value = Mock(returncode=0)

        # Should not raise exception
        check_ffmpeg()

        mock_run.assert_called_once()
        assert 'ffmpeg' in mock_run.call_args[0][0]

    @patch('mediacatch.utils.general.subprocess.run')
    def test_check_ffmpeg_not_installed(self, mock_run):
        """Test when ffmpeg is not installed."""
        mock_run.side_effect = FileNotFoundError()

        with pytest.raises(MediacatchUploadError, match='FFMPEG is not installed'):
            check_ffmpeg()


class TestCompressToOgg:
    """Test compress_to_ogg function."""

    @patch('mediacatch.utils.general.subprocess.run')
    def test_compress_to_ogg_success(self, mock_run, temp_dir):
        """Test successful compression to OGG format."""
        input_path = str(temp_dir / 'input.wav')
        output_path = str(temp_dir / 'output.ogg')
        mock_run.return_value = Mock(returncode=0)

        compress_to_ogg(input_path, output_path, sample_rate=16000)

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert 'ffmpeg' in call_args
        assert input_path in call_args
        assert output_path in call_args
        assert '16000' in call_args
        assert 'libvorbis' in call_args

    @patch('mediacatch.utils.general.subprocess.run')
    def test_compress_to_ogg_failure(self, mock_run, temp_dir):
        """Test failed compression to OGG format."""
        input_path = str(temp_dir / 'input.wav')
        output_path = str(temp_dir / 'output.ogg')

        error = subprocess.CalledProcessError(1, 'ffmpeg')
        error.stderr = 'FFmpeg error message'
        mock_run.side_effect = error

        with pytest.raises(MediacatchUploadError, match='Failed to compress file to OGG format'):
            compress_to_ogg(input_path, output_path)

    @patch('mediacatch.utils.general.subprocess.run')
    def test_compress_to_ogg_custom_sample_rate(self, mock_run, temp_dir):
        """Test compression with custom sample rate."""
        input_path = str(temp_dir / 'input.wav')
        output_path = str(temp_dir / 'output.ogg')
        mock_run.return_value = Mock(returncode=0)

        compress_to_ogg(input_path, output_path, sample_rate=48000)

        call_args = mock_run.call_args[0][0]
        assert '48000' in call_args
