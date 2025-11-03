from typing import Dict, Optional, List
import os
import logging
import threading
import json
from pathlib import Path
import keyring
from keyring.errors import KeyringError

class APIKeyManager:
    def __init__(self, service_name: str = "reasonflow", backup_file: str = "api_keys_backup.json"):
        self.service_name = service_name
        self.backup_file = Path(backup_file)
        self.cached_keys: Dict[str, str] = {}
        self.lock = threading.Lock()  # Thread safety
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(self.service_name)

    def set_api_key(self, provider: str, api_key: str, persist: bool = True, scope: str = "default") -> bool:
        """Set API key for a provider."""
        try:
            if not provider or not api_key:
                raise ValueError("Provider and API key must be non-empty.")
            
            key_id = f"{provider}:{scope}"
            
            with self.lock:
                # Cache the key in memory
                self.cached_keys[key_id] = api_key
                
            if persist:
                try:
                    # Store in system keyring
                    keyring.set_password(self.service_name, key_id, api_key)
                except KeyringError:
                    self.logger.warning("Keyring is unavailable; falling back to local backup.")
                    self._backup_to_file(key_id, api_key)
            
            # Set environment variable
            os.environ[f"{provider.upper()}_API_KEY"] = api_key
            self.logger.info(f"API key set for provider '{provider}' in scope '{scope}'.")
            return True
        except Exception as e:
            self.logger.error(f"Error setting API key: {str(e)}")
            return False

    def get_api_key(self, provider: str, scope: str = "default") -> Optional[str]:
        """Get API key for a provider."""
        try:
            key_id = f"{provider}:{scope}"
            
            with self.lock:
                # Check memory cache first
                if key_id in self.cached_keys:
                    return self.cached_keys[key_id]
            
            # Check environment variables
            env_key = os.getenv(f"{provider.upper()}_API_KEY")
            if env_key:
                with self.lock:
                    self.cached_keys[key_id] = env_key
                return env_key
            
            # Check system keyring
            try:
                stored_key = keyring.get_password(self.service_name, key_id)
                if stored_key:
                    with self.lock:
                        self.cached_keys[key_id] = stored_key
                    return stored_key
            except KeyringError:
                self.logger.warning("Keyring is unavailable; checking local backup.")
            
            # Check local backup
            return self._load_from_backup(key_id)
        except Exception as e:
            self.logger.error(f"Error getting API key: {str(e)}")
            return None

    def delete_api_key(self, provider: str, scope: str = "default") -> bool:
        """Delete API key for a provider."""
        try:
            key_id = f"{provider}:{scope}"
            
            with self.lock:
                # Remove from cache
                self.cached_keys.pop(key_id, None)
            
            # Remove from environment
            if f"{provider.upper()}_API_KEY" in os.environ:
                del os.environ[f"{provider.upper()}_API_KEY"]
            
            # Remove from system keyring
            try:
                keyring.delete_password(self.service_name, key_id)
            except KeyringError:
                self.logger.warning("Keyring is unavailable; removing from local backup.")
                self._remove_from_backup(key_id)
            
            self.logger.info(f"API key deleted for provider '{provider}' in scope '{scope}'.")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting API key: {str(e)}")
            return False

    def list_providers(self) -> List[str]:
        """List all providers with stored API keys."""
        try:
            with self.lock:
                providers = set(key.split(":")[0] for key in self.cached_keys.keys())
            
            # Add providers from environment variables
            for key in os.environ:
                if key.endswith('_API_KEY'):
                    providers.add(key.replace('_API_KEY', '').lower())
            
            self.logger.info("Providers listed successfully.")
            return sorted(list(providers))
        except Exception as e:
            self.logger.error(f"Error listing providers: {str(e)}")
            return []

    def _backup_to_file(self, key_id: str, api_key: str) -> None:
        """Backup API key to a local file."""
        try:
            if not self.backup_file.exists():
                self.backup_file.write_text(json.dumps({}))
            
            with self.backup_file.open("r+") as file:
                data = json.load(file)
                data[key_id] = api_key
                file.seek(0)
                json.dump(data, file, indent=4)
                file.truncate()
        except Exception as e:
            self.logger.error(f"Error backing up API key to file: {str(e)}")

    def _load_from_backup(self, key_id: str) -> Optional[str]:
        """Load API key from local backup."""
        try:
            if not self.backup_file.exists():
                return None
            
            with self.backup_file.open("r") as file:
                data = json.load(file)
                return data.get(key_id)
        except Exception as e:
            self.logger.error(f"Error loading API key from backup: {str(e)}")
            return None

    def _remove_from_backup(self, key_id: str) -> None:
        """Remove API key from local backup."""
        try:
            if not self.backup_file.exists():
                return
            
            with self.backup_file.open("r+") as file:
                data = json.load(file)
                if key_id in data:
                    del data[key_id]
                    file.seek(0)
                    json.dump(data, file, indent=4)
                    file.truncate()
        except Exception as e:
            self.logger.error(f"Error removing API key from backup: {str(e)}")
