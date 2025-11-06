import hashlib
import os
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests
from tqdm import tqdm


class ModelManager:
    """Manages model downloading and caching."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize the ModelManager.
        
        Args:
            cache_dir: Directory to cache models. Defaults to ~/.cache/your_package
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".cache" / "your_package"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def download_model(
        self,
        url: str,
        filename: Optional[str] = None,
        expected_hash: Optional[str] = None,
        hash_algorithm: str = "sha256",
        force_download: bool = False
    ) -> Path:
        """
        Download a model file from a URL with caching and verification.
        
        Args:
            url: URL to download the model from
            filename: Name to save the file as. If None, extracted from URL
            expected_hash: Expected hash of the file for verification
            hash_algorithm: Hash algorithm to use (sha256, md5, etc.)
            force_download: Force re-download even if file exists
            
        Returns:
            Path to the downloaded model file
            
        Raises:
            ValueError: If hash verification fails
            requests.RequestException: If download fails
        """
        if filename is None:
            filename = Path(urlparse(url).path).name
            if not filename:
                raise ValueError("Could not determine filename from URL. Please provide filename explicitly.")
        
        model_path = self.cache_dir / filename
        
        # Check if file exists and skip download if not forced
        if model_path.exists() and not force_download:
            print(f"Model already cached at {model_path}")
            if expected_hash:
                if self._verify_hash(model_path, expected_hash, hash_algorithm):
                    return model_path
                else:
                    print("Hash verification failed. Re-downloading...")
            else:
                return model_path
        
        print(f"Downloading model from {url}...")
        
        # Download with progress bar
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(model_path, 'wb') as f, tqdm(
            desc=filename,
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                size = f.write(chunk)
                pbar.update(size)
        
        # Verify hash if provided
        if expected_hash:
            if not self._verify_hash(model_path, expected_hash, hash_algorithm):
                model_path.unlink()  # Delete corrupted file
                raise ValueError(
                    f"Hash verification failed. Expected {expected_hash}, "
                    f"but got {self._compute_hash(model_path, hash_algorithm)}"
                )
            print("Hash verification successful!")
        
        print(f"Model downloaded to {model_path}")
        return model_path
    
    def _compute_hash(self, filepath: Path, algorithm: str = "sha256") -> str:
        """Compute hash of a file."""
        hash_func = hashlib.new(algorithm)
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    
    def _verify_hash(self, filepath: Path, expected_hash: str, algorithm: str = "sha256") -> bool:
        """Verify file hash matches expected hash."""
        actual_hash = self._compute_hash(filepath, algorithm)
        return actual_hash.lower() == expected_hash.lower()
    
    def clear_cache(self) -> None:
        """Remove all cached models."""
        import shutil
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            print(f"Cache cleared: {self.cache_dir}")
    
    def list_cached_models(self) -> list[Path]:
        """List all cached model files."""
        if not self.cache_dir.exists():
            return []
        return list(self.cache_dir.glob("*"))