"""Tests for mediacatch.viz module."""

from unittest.mock import patch

import pytest

from mediacatch.viz.speech import SpeechViz
from mediacatch.viz.annotator import Annotator


class TestSpeechViz:
    """Test SpeechViz visualization class."""

    def test_speech_viz_init(self, sample_video_file, mock_speech_result, temp_dir):
        """Test SpeechViz initialization."""
        output_path = temp_dir / 'output.mp4'

        viz = SpeechViz(
            file_path=sample_video_file,
            results=mock_speech_result,
            output_path=output_path,
            subtitles=True,
            meta=True,
        )

        assert viz.file_path == sample_video_file
        assert viz.results == mock_speech_result
        assert viz.output_path == output_path
        assert viz.subtitles is True
        assert viz.meta is True

    def test_speech_viz_init_file_not_found(self, mock_speech_result, temp_dir):
        """Test SpeechViz initialization with non-existent file."""
        with pytest.raises(AssertionError, match='File not found'):
            SpeechViz(
                file_path='/nonexistent/file.mp4',
                results=mock_speech_result,
                output_path=temp_dir / 'output.mp4',
            )

    def test_speech_viz_init_empty_results(self, sample_video_file, temp_dir):
        """Test SpeechViz initialization with empty results."""
        with pytest.raises(AssertionError):
            SpeechViz(
                file_path=sample_video_file,
                results=None,
                output_path=temp_dir / 'output.mp4',
            )

    def test_create_text_subtitle(self, sample_video_file, mock_speech_result, temp_dir):
        """Test text subtitle generation."""
        output_path = temp_dir / 'output.mp4'

        viz = SpeechViz(
            file_path=sample_video_file,
            results=mock_speech_result,
            output_path=output_path,
        )

        utterances = mock_speech_result['result']['utterances']
        subtitles = viz.create_text_subtitle(utterances)

        # Should generate SRT format
        assert isinstance(subtitles, str)
        assert 'Hello' in subtitles
        assert 'world' in subtitles
        assert 'Test' in subtitles
        assert 'audio' in subtitles

    def test_create_meta_subtitle(self, sample_video_file, mock_speech_result, temp_dir):
        """Test meta subtitle generation."""
        output_path = temp_dir / 'output.mp4'

        viz = SpeechViz(
            file_path=sample_video_file,
            results=mock_speech_result,
            output_path=output_path,
        )

        utterances = mock_speech_result['result']['utterances']
        subtitles = viz.create_meta_subtitle(utterances)

        # Should generate SRT format with metadata
        assert isinstance(subtitles, str)
        assert 'Speaker_1' in subtitles or 'speaker_1' in subtitles
        assert 'Male' in subtitles or 'male' in subtitles

    def test_should_end_subtitle_max_length(self, sample_video_file, mock_speech_result, temp_dir):
        """Test subtitle end condition based on max length."""
        output_path = temp_dir / 'output.mp4'

        viz = SpeechViz(
            file_path=sample_video_file,
            results=mock_speech_result,
            output_path=output_path,
            max_subtitle_length=5,
        )

        # Subtitle exceeds max length
        should_end = viz._should_end_subtitle(['word1', 'word2'], start=0.0, end=6.0, last_word='word2')
        assert should_end is True

        # Subtitle within max length
        should_end = viz._should_end_subtitle(['word1', 'word2'], start=0.0, end=4.0, last_word='word2')
        assert should_end is False

    def test_should_end_subtitle_max_chars(self, sample_video_file, mock_speech_result, temp_dir):
        """Test subtitle end condition based on max characters."""
        output_path = temp_dir / 'output.mp4'

        viz = SpeechViz(
            file_path=sample_video_file,
            results=mock_speech_result,
            output_path=output_path,
            max_chars_in_subtitle=20,
        )

        # Subtitle exceeds max chars
        long_words = ['verylongword'] * 5
        should_end = viz._should_end_subtitle(long_words, start=0.0, end=5.0, last_word='verylongword')
        assert should_end is True

    def test_should_end_subtitle_punctuation(self, sample_video_file, mock_speech_result, temp_dir):
        """Test subtitle end condition based on punctuation."""
        output_path = temp_dir / 'output.mp4'

        viz = SpeechViz(
            file_path=sample_video_file,
            results=mock_speech_result,
            output_path=output_path,
        )

        # Last word ends with period
        should_end = viz._should_end_subtitle(['Hello', 'world.'], start=0.0, end=2.0, last_word='world.')
        assert should_end is True

        # Last word ends with question mark
        should_end = viz._should_end_subtitle(['Hello', 'there?'], start=0.0, end=2.0, last_word='there?')
        assert should_end is True

        # Last word ends with exclamation
        should_end = viz._should_end_subtitle(['Hello', 'world!'], start=0.0, end=2.0, last_word='world!')
        assert should_end is True

    def test_write_srt_file(self, temp_dir):
        """Test writing SRT file."""
        input_path = temp_dir / 'input.mp4'
        input_path.touch()

        subtitles = """1
00:00:00,000 --> 00:00:02,500
Hello world

"""

        output_path = SpeechViz.write_srt_file(str(input_path), '.test.srt', subtitles)

        assert output_path.exists()
        assert output_path.suffix == '.srt'
        assert output_path.read_text() == subtitles

    @patch('mediacatch.viz.speech.subprocess.run')
    def test_burn_subtitles_text_only(
        self, mock_subprocess, sample_video_file, mock_speech_result, temp_dir
    ):
        """Test burning text subtitles only."""
        output_path = temp_dir / 'output.mp4'

        viz = SpeechViz(
            file_path=sample_video_file,
            results=mock_speech_result,
            output_path=output_path,
        )

        text_srt = temp_dir / 'text.srt'
        text_srt.write_text('1\n00:00:00,000 --> 00:00:02,500\nHello world\n')

        viz.burn_subtitles(text_srt, None)

        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        assert 'ffmpeg' in call_args
        assert str(text_srt) in call_args

    @patch('mediacatch.viz.speech.subprocess.run')
    def test_burn_subtitles_text_and_meta(
        self, mock_subprocess, sample_video_file, mock_speech_result, temp_dir
    ):
        """Test burning text and meta subtitles."""
        output_path = temp_dir / 'output.mp4'

        viz = SpeechViz(
            file_path=sample_video_file,
            results=mock_speech_result,
            output_path=output_path,
        )

        text_srt = temp_dir / 'text.srt'
        text_srt.write_text('1\n00:00:00,000 --> 00:00:02,500\nHello world\n')

        meta_srt = temp_dir / 'meta.srt'
        meta_srt.write_text('1\n00:00:00,000 --> 00:00:02,500\nSpeaker 1\n')

        # Create the tmp file that will be created during the process
        tmp_file = output_path.with_name('tmp.mkv')
        tmp_file.touch()

        viz.burn_subtitles(text_srt, meta_srt)

        # Should be called twice: once for text, once for meta
        assert mock_subprocess.call_count == 2


class TestAnnotator:
    """Test Annotator class."""

    def test_annotator_init(self):
        """Test Annotator initialization."""
        import numpy as np

        im = np.zeros((100, 100, 3), dtype=np.uint8)
        annotator = Annotator(im, line_width=5, font_size=25)

        assert annotator.line_width == 5
        assert annotator.font is not None

    def test_annotator_bbox_label(self):
        """Test drawing bounding box with label."""
        import numpy as np

        im = np.zeros((200, 200, 3), dtype=np.uint8)
        annotator = Annotator(im)

        # Draw a bounding box with label
        bbox = [50, 50, 150, 150]
        annotator.bbox_label(bbox, label='Test Label', color=(255, 0, 0))

        # Convert back to array to verify changes were made
        result = annotator.asarray()
        assert isinstance(result, np.ndarray)
        assert result.shape == im.shape

        # Image should have been modified (not all zeros)
        assert not np.all(result == 0)

    def test_annotator_asarray(self):
        """Test converting annotated image to array."""
        import numpy as np

        im = np.zeros((100, 100, 3), dtype=np.uint8)
        annotator = Annotator(im)

        result = annotator.asarray()
        assert isinstance(result, np.ndarray)
        assert result.shape == (100, 100, 3)

    @patch('mediacatch.viz.annotator.get_assets_data')
    def test_annotator_custom_font(self, mock_get_assets):
        """Test annotator with custom font."""
        import numpy as np

        mock_get_assets.return_value = '/path/to/font.ttf'

        im = np.zeros((100, 100, 3), dtype=np.uint8)
        # Initialize annotator with custom font
        Annotator(im, font='CustomFont.ttf')

        mock_get_assets.assert_called_once_with('CustomFont.ttf')


class TestVizIntegration:
    """Integration tests for visualization functionality."""

    @patch('mediacatch.viz.speech.subprocess.run')
    def test_speech_viz_full_workflow(
        self, mock_subprocess, sample_video_file, mock_speech_result, temp_dir
    ):
        """Test complete SpeechViz workflow."""
        output_path = temp_dir / 'output.mp4'

        viz = SpeechViz(
            file_path=sample_video_file,
            results=mock_speech_result,
            output_path=output_path,
            subtitles=True,
            meta=True,
        )

        # Create tmp file before calling create_viz
        tmp_file = output_path.with_name('tmp.mkv')
        tmp_file.touch()

        viz.create_viz()

        # Should have called subprocess for burning subtitles
        assert mock_subprocess.called

        # SRT files should have been created
        text_srt = output_path.with_suffix('.text.srt')
        meta_srt = output_path.with_suffix('.meta.srt')
        assert text_srt.exists()
        assert meta_srt.exists()

    def test_speech_viz_subtitles_only(
        self, sample_video_file, mock_speech_result, temp_dir
    ):
        """Test SpeechViz with subtitles only (no meta)."""
        output_path = temp_dir / 'output.mp4'

        viz = SpeechViz(
            file_path=sample_video_file,
            results=mock_speech_result,
            output_path=output_path,
            subtitles=True,
            meta=False,
        )

        with patch('mediacatch.viz.speech.subprocess.run'):
            viz.create_viz()

        # Only text SRT should exist
        text_srt = output_path.with_suffix('.text.srt')
        meta_srt = output_path.with_suffix('.meta.srt')
        assert text_srt.exists()
        assert not meta_srt.exists()

    def test_speech_viz_meta_only(self, sample_video_file, mock_speech_result, temp_dir):
        """Test SpeechViz with meta only (no subtitles)."""
        output_path = temp_dir / 'output.mp4'

        viz = SpeechViz(
            file_path=sample_video_file,
            results=mock_speech_result,
            output_path=output_path,
            subtitles=False,
            meta=True,
        )

        with patch('mediacatch.viz.speech.subprocess.run'):
            viz.create_viz()

        # Only meta SRT should exist
        text_srt = output_path.with_suffix('.text.srt')
        meta_srt = output_path.with_suffix('.meta.srt')
        assert not text_srt.exists()
        assert meta_srt.exists()
