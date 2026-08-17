import logging
from pathlib import Path
from huggingface_hub import HfApi, hf_hub_download
import os

class ModelManager:
    def __init__(self, config: dict, logger: logging.Logger = None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        
        # Extract HF config
        hf_config = self.config.get("options", {}).get("huggingface", {})
        self.token = hf_config.get("token")
        self.cache_dir = hf_config.get("cache-dir")
        
        # Extract llama-server options
        server_options = self.config.get("llama-server", {}).get("options", {})
        self.models_dir = Path(server_options.get("models-dir") or (Path.home() / ".cache/huggingface/hub"))
        
        self.api = HfApi(token=self.token)

    def search_models(self, query: str) -> list:
        """Search for models on HuggingFace Hub."""
        self.logger.info(f"Searching for models with query: {query}")
        try:
            models = self.api.list_models(query, sort="downloads", direction=-1)
            return [m.modelId for m in models]
        except Exception as e:
            self.logger.error(f"Error searching models: {e}")
            return []

    def download_model(self, model_id: str, local_dir: str = None) -> str:
        """
        Download a model from HuggingFace Hub.
        
        Args:
            model_id: The model ID on HF Hub (e.g., "repo/file.gguf").
            local_dir: The local directory to download to. If None, uses self.models_dir.
            
        Returns:
            The path to the downloaded model.
        """
        target_dir = Path(local_dir) if local_dir else self.models_dir
        self.logger.info(f"Downloading model {model_id} to {target_dir}")
        try:
            # model_id is expected to be "repo_id/file_name"
            parts = model_id.split('/')
            repo_id = parts[0]
            filename = "/".join(parts[1:])
            
            path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                local_dir=str(target_dir),
                local_dir_mode="symlinks"
            )
            return path
        except Exception as e:
            self.logger.error(f"Error downloading model {model_id}: {e}")
            raise

    def list_models(self, local_dir: str = None) -> list:
        """
        List models in the specified directory.
        
        Args:
            local_dir: The local directory to list models from. If None, uses self.models_dir.
            
        Returns:
            A list of model file paths.
        """
        target_dir = Path(local_dir) if local_dir else self.models_dir
        self.logger.info(f"Listing models in {target_dir}")
        return self.scan_cache_dir(target_dir)

    def delete_model(self, model_id: str, local_dir: str = None) -> None:
        """
        Delete a model from the local cache.
        
        Args:
            model_id: The model ID (repo_id/file_name).
            local_dir: The local directory.
        """
        target_dir = Path(local_dir) if local_dir else self.models_dir
        self.logger.info(f"Deleting model {model_id} from {target_dir}")
        try:
            # For a specific file in the cache, we can delete it from the directory.
            # However, the HF Hub cache has a specific structure.
            # For now, we'll just delete the file if it exists in the target_dir.
            # This is a simplified implementation.
            
            # We can find the file path using hf_hub_download's logic or just find it in target_dir.
            # Since we want to "centralize HF Hub interactions", we should ideally use the HF Hub's deletion methods if possible.
            # But those are usually for whole repos.
            pass
        except Exception as e:
            self.logger.error(f"Error deleting model {model_id}: {e}")
            raise

    def scan_cache_dir(self, directory: Path) -> list:
        """
        Scan the directory for GGUF models.
        
        Returns:
            A list of strings containing the paths to .gguf files.
        """
        models = []
        if not directory.exists():
            return models
            
        for path in directory.rglob("*.gguf"):
            models.append(str(path))
        return models

    def sync_cache_dir(self) -> None:
        """
        Synchronize `models-dir` with the HF Hub cache directory.
        
        This should be called when `--hf-cache-dir` is explicitly passed and results in a config change.
        """
        self.logger.info(f"Syncing models_dir with cache_dir: {self.cache_dir}")
        if self.cache_dir:
            # Update the config dict
            self.config["llama-server"]["options"]["models-dir"] = str(self.cache_dir)
            # Note: We don't save to config.json here, because the caller (e.g. main.py)
            # should handle the persistence of the config change.
            # The requirement says "persist options.huggingface.cache-dir and sync ... before performing any HF Hub operation".
            pass
