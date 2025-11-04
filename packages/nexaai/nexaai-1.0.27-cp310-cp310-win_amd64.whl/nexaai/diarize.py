from typing import List, Optional, Sequence, Union
from abc import abstractmethod
from dataclasses import dataclass

from nexaai.base import BaseModel
from nexaai.common import PluginID, ModelConfig


@dataclass
class DiarizeConfig:
    """Configuration for speaker diarization."""

    min_speakers: int = 0  # Minimum number of speakers (0 = auto-detect)
    max_speakers: int = 0  # Maximum number of speakers (0 = no limit)


@dataclass
class SpeechSegment:
    """Speech segment with speaker label and timestamps."""

    start_time: float  # Segment start time in seconds
    end_time: float  # Segment end time in seconds
    speaker_label: str  # Speaker label (e.g., "SPEAKER_00")


@dataclass
class DiarizeResult:
    """Result from speaker diarization."""

    segments: Sequence[SpeechSegment]  # Array of speech segments
    segment_count: int  # Number of segments
    num_speakers: int  # Total unique speakers detected
    duration: float  # Total audio duration in seconds


class Diarize(BaseModel):
    """Abstract base class for speaker diarization models."""

    def __init__(self, m_cfg: ModelConfig = ModelConfig()):
        """Initialize base Diarize class."""
        self._m_cfg = m_cfg

    @classmethod
    def _load_from(
        cls,
        model_path: str,
        model_name: Optional[str] = None,
        m_cfg: ModelConfig = ModelConfig(),
        plugin_id: Union[PluginID, str] = PluginID.LLAMA_CPP,
        device_id: Optional[str] = None,
        **kwargs
    ) -> "Diarize":
        """Load diarization model from local path using PyBind backend."""
        from nexaai.diarize_impl.pybind_diarize_impl import PyBindDiarizeImpl

        # There is no MLX implementation for diarization as of now.
        return PyBindDiarizeImpl._load_from(
            model_path, model_name, m_cfg, plugin_id, device_id
        )

    @abstractmethod
    def infer(
        self,
        audio_path: str,
        config: Optional[DiarizeConfig] = None,
    ) -> DiarizeResult:
        """
        Perform speaker diarization on audio file.

        Determines "who spoke when" in the audio recording, producing time-stamped segments
        with speaker labels. Segments are time-ordered and non-overlapping.

        Args:
            audio_path: Path to audio file
            config: Optional diarization configuration

        Returns:
            DiarizeResult with segments, speaker count, and duration
        """
        pass
