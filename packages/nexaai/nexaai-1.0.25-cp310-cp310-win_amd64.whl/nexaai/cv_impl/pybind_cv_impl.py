from typing import Optional, Union, List
import os

from nexaai.common import PluginID, ModelConfig
from nexaai.cv import CVModel, CVModelConfig, CVResults, CVResult, BoundingBox, CVCapabilities
from nexaai.binds import cv_bind, common_bind
from nexaai.runtime import _ensure_runtime


class PyBindCVImpl(CVModel):
    def __init__(self, handle: any, m_cfg: ModelConfig = ModelConfig()):
        """Private constructor, should not be called directly."""
        super().__init__()
        self._handle = handle  # This is a py::capsule
        self._model_config = None

    @classmethod
    def _load_from(cls,
                   local_path: str,  # This is the local path after auto_download_model processing
                   model_name: Optional[str] = None,
                   m_cfg: CVModelConfig = CVModelConfig(CVCapabilities.OCR),
                   plugin_id: Union[PluginID, str] = PluginID.LLAMA_CPP,
                   device_id: Optional[str] = None,
                   **kwargs
                   ) -> 'PyBindCVImpl':
        """Load CV model from configuration using PyBind backend."""
        _ensure_runtime()

        config = cv_bind.CVModelConfig()
        config.capabilities = cv_bind.CVCapabilities(m_cfg.capabilities)
        if m_cfg.det_model_path is not None:
            config.det_model_path = m_cfg.det_model_path
        else:
            config.det_model_path = local_path

        print("local_path: ", local_path)
        print("m_cfg.rec_model_path: ", m_cfg.rec_model_path)
        if m_cfg.rec_model_path is not None:
            config.rec_model_path = m_cfg.rec_model_path
        else:
            config.rec_model_path = local_path
        print("config.rec_model_path: ", config.rec_model_path)
        
        if m_cfg.char_dict_path is not None:
            config.char_dict_path = m_cfg.char_dict_path

        if m_cfg.model_path is not None:
            config.model_path = m_cfg.model_path

        if m_cfg.system_library_path is not None:
            config.system_library_path = m_cfg.system_library_path

        plugin_id_str = plugin_id.value if isinstance(
            plugin_id, PluginID) else str(plugin_id)

        model_name_to_use = model_name if model_name else local_path
        handle = cv_bind.ml_cv_create(
            model_name=model_name_to_use,
            config=config,
            plugin_id=plugin_id_str,
            device_id=device_id,
            license_id=None,
            license_key=None
        )

        return cls(handle, m_cfg)

    def eject(self):
        """Release the model from memory."""
        # py::capsule handles cleanup automatically
        if hasattr(self, '_handle') and self._handle is not None:
            del self._handle
            self._handle = None

    def infer(self, input_image_path: str) -> CVResults:
        """Perform inference on image."""
        if self._handle is None:
            raise RuntimeError("CV model not loaded. Call _load_from first.")

        if not os.path.exists(input_image_path):
            raise FileNotFoundError(
                f"Input image not found: {input_image_path}")

        try:
            # Perform inference using the binding
            result_dict = cv_bind.ml_cv_infer(
                handle=self._handle,
                input_image_path=input_image_path
            )

            # Convert result dictionary to CVResults
            results = []
            for result_data in result_dict["results"]:
                # Create bounding box if present
                bbox = None
                if "bbox" in result_data and result_data["bbox"] is not None:
                    bbox_data = result_data["bbox"]
                    bbox = BoundingBox(
                        x=bbox_data["x"],
                        y=bbox_data["y"],
                        width=bbox_data["width"],
                        height=bbox_data["height"]
                    )

                # Create CV result
                cv_result = CVResult(
                    image_paths=result_data.get("image_paths"),
                    image_count=result_data.get("image_count", 0),
                    class_id=result_data.get("class_id", 0),
                    confidence=result_data.get("confidence", 0.0),
                    bbox=bbox,
                    text=result_data.get("text"),
                    embedding=result_data.get("embedding"),
                    embedding_dim=result_data.get("embedding_dim", 0)
                )
                results.append(cv_result)

            return CVResults(
                results=results,
                result_count=result_dict["result_count"]
            )

        except Exception as e:
            raise RuntimeError(f"CV inference failed: {str(e)}")
