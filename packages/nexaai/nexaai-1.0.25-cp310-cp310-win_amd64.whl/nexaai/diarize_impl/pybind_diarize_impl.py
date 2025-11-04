from typing import Any, Optional, Union

from nexaai.common import PluginID, ModelConfig
from nexaai.diarize import Diarize, DiarizeConfig, DiarizeResult, SpeechSegment
from nexaai.binds import diarize_bind, common_bind
from nexaai.runtime import _ensure_runtime


class PyBindDiarizeImpl(Diarize):
    def __init__(self, handle: Any, m_cfg: ModelConfig = ModelConfig()):
        """Private constructor, should not be called directly."""
        super().__init__(m_cfg)
        self._handle = handle  # This is a py::capsule
        self._model_config = None

    @classmethod
    def _load_from(
        cls,
        model_path: str,
        model_name: Optional[str] = None,
        m_cfg: ModelConfig = ModelConfig(),
        plugin_id: Union[PluginID, str] = PluginID.LLAMA_CPP,
        device_id: Optional[str] = None,
    ) -> "PyBindDiarizeImpl":
        """Load diarization model from local path using PyBind backend."""
        _ensure_runtime()

        # Create model config
        config = common_bind.ModelConfig()

        config.n_ctx = m_cfg.n_ctx
        if m_cfg.n_threads is not None:
            config.n_threads = m_cfg.n_threads
        if m_cfg.n_threads_batch is not None:
            config.n_threads_batch = m_cfg.n_threads_batch
        if m_cfg.n_batch is not None:
            config.n_batch = m_cfg.n_batch
        if m_cfg.n_ubatch is not None:
            config.n_ubatch = m_cfg.n_ubatch
        if m_cfg.n_seq_max is not None:
            config.n_seq_max = m_cfg.n_seq_max
        config.n_gpu_layers = m_cfg.n_gpu_layers

        # handle chat template strings (if needed for diarization)
        if m_cfg.chat_template_path:
            config.chat_template_path = m_cfg.chat_template_path

        if m_cfg.chat_template_content:
            config.chat_template_content = m_cfg.chat_template_content

        # Convert plugin_id to string
        plugin_id_str = (
            plugin_id.value if isinstance(plugin_id, PluginID) else str(plugin_id)
        )

        # Create Diarize handle using the binding
        handle = diarize_bind.ml_diarize_create(
            model_path=model_path,
            model_name=model_name,
            model_config=config,
            plugin_id=plugin_id_str,
            device_id=device_id,
            license_id=None,  # Optional
            license_key=None,  # Optional
        )

        return cls(handle, m_cfg)

    def eject(self):
        """Release the model from memory."""
        # py::capsule handles cleanup automatically
        if hasattr(self, "_handle") and self._handle is not None:
            del self._handle
            self._handle = None

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
        if self._handle is None:
            raise RuntimeError("Diarization model not loaded. Call _load_from first.")

        # Convert DiarizeConfig to binding format if provided
        diarize_config = None
        if config:
            diarize_config = diarize_bind.DiarizeConfig()
            diarize_config.min_speakers = config.min_speakers
            diarize_config.max_speakers = config.max_speakers

        # Perform diarization using the binding
        result_dict = diarize_bind.ml_diarize_infer(
            handle=self._handle, audio_path=audio_path, config=diarize_config
        )

        # Convert result to DiarizeResult
        segments = []
        for segment_dict in result_dict.get("segments", []):
            segments.append(
                SpeechSegment(
                    start_time=float(segment_dict["start_time"]),
                    end_time=float(segment_dict["end_time"]),
                    speaker_label=segment_dict["speaker_label"],
                )
            )

        return DiarizeResult(
            segments=segments,
            segment_count=result_dict.get("segment_count", 0),
            num_speakers=result_dict.get("num_speakers", 0),
            duration=result_dict.get("duration", 0.0),
        )
