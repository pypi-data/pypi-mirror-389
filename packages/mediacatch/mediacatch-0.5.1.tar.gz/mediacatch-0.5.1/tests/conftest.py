"""Pytest configuration and shared fixtures for mediacatch tests."""

import json
import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Automatically set test environment variables for all tests."""
    monkeypatch.setenv("MEDIACATCH_API_KEY", "test_api_key_12345")
    monkeypatch.setenv("TEST_FILE_ID", "file_abc123def456")


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_audio_file(temp_dir: Path) -> Path:
    """Create a sample audio file for testing."""
    audio_path = temp_dir / 'test_audio.wav'
    # Create a minimal valid WAV file (44 bytes header + some data)
    wav_header = (
        b'RIFF'
        + (100).to_bytes(4, 'little')  # File size - 8
        + b'WAVE'
        + b'fmt '
        + (16).to_bytes(4, 'little')  # fmt chunk size
        + (1).to_bytes(2, 'little')  # audio format (PCM)
        + (1).to_bytes(2, 'little')  # num channels
        + (16000).to_bytes(4, 'little')  # sample rate
        + (32000).to_bytes(4, 'little')  # byte rate
        + (2).to_bytes(2, 'little')  # block align
        + (16).to_bytes(2, 'little')  # bits per sample
        + b'data'
        + (64).to_bytes(4, 'little')  # data chunk size
    )
    audio_path.write_bytes(wav_header + b'\x00' * 64)
    return audio_path


@pytest.fixture
def sample_video_file(temp_dir: Path) -> Path:
    """Create a sample video file for testing."""
    video_path = temp_dir / 'test_video.mp4'
    # Create a minimal file (not a valid MP4, but enough for path testing)
    video_path.write_bytes(b'fake video content')
    return video_path


@pytest.fixture
def sample_json_file(temp_dir: Path) -> Path:
    """Create a sample JSON file for testing."""
    json_path = temp_dir / 'test_data.json'
    test_data = {'test_key': 'test_value', 'nested': {'data': [1, 2, 3]}}
    json_path.write_text(json.dumps(test_data))
    return json_path


@pytest.fixture
def mock_speech_result() -> dict:
    """Mock speech API result structure based on actual API format."""
    return {
        'result': {
            'utterances': [
                {
                    'start': 0.0,
                    'end': 2.5,
                    'text': 'Hello world',
                    'raw_text': 'hello world',
                    'words': [
                        {'word': 'Hello', 'start': 0.0, 'end': 0.5},
                        {'word': 'world', 'start': 0.6, 'end': 1.2},
                    ],
                    'meta': {
                        'speaker': 'speaker_1',
                        'language': {'label': 'en', 'confidence': 0.99},
                        'gender': {'label': 'male', 'confidence': 0.92},
                    },
                },
                {
                    'start': 3.0,
                    'end': 5.0,
                    'text': 'Test audio',
                    'raw_text': 'test audio',
                    'words': [
                        {'word': 'Test', 'start': 3.0, 'end': 3.5},
                        {'word': 'audio', 'start': 3.6, 'end': 4.2},
                    ],
                    'meta': {
                        'speaker': 'speaker_2',
                        'language': {'label': 'en', 'confidence': 0.98},
                        'gender': {'label': 'female', 'confidence': 0.91},
                    },
                },
            ]
        }
    }


@pytest.fixture
def mock_vision_ocr_result() -> list:
    """Mock vision OCR API result structure."""
    return [
        {
            'text': 'Sample Text',
            'confidence': 0.95,
            'start_frame_idx': 0,
            'end_frame_idx': 100,
            'bbox': [100, 200, 300, 50],
            'frame': 50,
        },
        {
            'text': 'Another Text',
            'confidence': 0.88,
            'start_frame_idx': 120,
            'end_frame_idx': 200,
            'bbox': [150, 250, 250, 40],
            'frame': 160,
        },
    ]


@pytest.fixture
def mock_vision_face_result() -> list:
    """Mock vision face detection API result structure."""
    return [
        {
            'frame': 0,
            'bbox': [0.5, 0.5, 0.2, 0.3],
            'gender': 'male',
            'age': 30,
            'expression': 'happy',
            'ethnicity': 'caucasian',
        },
        {
            'frame': 30,
            'bbox': [0.3, 0.4, 0.25, 0.35],
            'gender': 'female',
            'age': 25,
            'expression': 'neutral',
            'ethnicity': 'asian',
        },
    ]


@pytest.fixture
def mock_vision_detect_result() -> list:
    """Mock vision object detection API result structure."""
    return [
        {'frame': 0, 'label': 'person', 'conf': 0.95, 'bbox': [0.1, 0.2, 0.5, 0.8]},
        {'frame': 0, 'label': 'car', 'conf': 0.88, 'bbox': [0.6, 0.7, 0.9, 0.9]},
        {'frame': 30, 'label': 'person', 'conf': 0.92, 'bbox': [0.2, 0.3, 0.6, 0.9]},
    ]


@pytest.fixture
def mock_api_key() -> str:
    """Get API key from test environment (set by setup_test_env fixture)."""
    return os.getenv('MEDIACATCH_API_KEY', 'test_api_key_12345')


@pytest.fixture
def mock_file_id() -> str:
    """Mock file ID returned by upload API (set by setup_test_env fixture)."""
    return os.getenv('TEST_FILE_ID', 'file_abc123def456')


@pytest.fixture
def mock_upload_response(mock_file_id: str) -> dict:
    """Mock upload initiation response."""
    return {
        'file_id': mock_file_id,
        'presigned_url': 'https://s3.example.com/upload',
        'fields': {'key': 'test-key', 'policy': 'test-policy'},
    }


@pytest.fixture
def mock_signed_url_response() -> dict:
    """Mock signed URL response for chunk upload."""
    return {'url': 'https://s3.example.com/presigned-upload-url'}


@pytest.fixture
def mock_complete_upload_response() -> dict:
    """Mock complete upload response."""
    return {'estimated_processing_time': '00:05:00', 'status': 'processing'}
