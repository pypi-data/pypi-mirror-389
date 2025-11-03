import os
import logging
from typing import Dict, Optional, Any
from reasonchain.llm_models.fine_tune import fine_tune_model
from reasonchain.llm_models.provider_registry import LLMProviderRegistry
from reasonchain.llm_models.base_provider import BaseLLMProvider


class LLMIntegration:
    """
    Enhanced LLM Integration that uses ReasonChain's provider registry system.
    Supports any LLM provider through the registry pattern.
    """
    
    def __init__(self, provider: str, model: str, api_key: Optional[str] = None, **kwargs):
        """
        Initialize LLM Integration with flexible provider support.
        
        Args:
            provider: LLM provider name (openai, groq, ollama, anthropic, etc.)
            model: Model name for the provider
            api_key: API key for the provider (if required)
            **kwargs: Additional provider-specific parameters
        """
        self.provider = provider
        self.model = model
        self.kwargs = kwargs
        
        # Get provider from registry
        try:
            self.llm_provider = LLMProviderRegistry.get_provider(
                provider, 
                model, 
                api_key=api_key or os.getenv(f"{provider.upper()}_API_KEY"),
                **kwargs
            )
        except Exception as e:
            # Fallback to available providers if specific provider not found
            available_providers = LLMProviderRegistry.list_providers()
            raise ValueError(
                f"Provider '{provider}' not available. Available providers: {available_providers}. "
                f"Error: {str(e)}"
            )
        
        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(f"{self.provider}-{self.model}")
        
        self.logger.info(f"Initialized LLM Integration with provider: {provider}, model: {model}")
    
    @classmethod
    def register_custom_provider(cls, provider_name: str, provider_class: type) -> None:
        """
        Register a custom LLM provider.
        
        Args:
            provider_name: Name of the provider
            provider_class: Provider class that inherits from BaseLLMProvider
        """
        LLMProviderRegistry.register(provider_name, provider_class)
        logging.info(f"Registered custom provider: {provider_name}")
    
    @classmethod
    def list_available_providers(cls) -> list:
        """Get list of all available LLM providers."""
        return LLMProviderRegistry.list_providers()
        
    def execute(self, prompt: str, **kwargs) -> Dict:
        """Generate a response using the ReasonChain provider system."""
        try:
            self.logger.info(f"Executing prompt with {self.provider}:{self.model}")
            
            # Use ReasonChain's provider system
            if hasattr(self.llm_provider, 'generate_chat_response'):
                # For chat-based providers
                messages = [{"role": "user", "content": prompt}]
                response = self.llm_provider.generate_chat_response(messages, **kwargs)
            else:
                # For completion-based providers
                response = self.llm_provider.generate_response(prompt, **kwargs)
            
            return {
                "status": "success",
                "output": response,
                "metadata": {
                    "provider": self.provider,
                    "model": self.model,
                    "provider_type": type(self.llm_provider).__name__
                }
            }
        except Exception as e:
            self.logger.error(f"Error executing prompt: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "metadata": {
                    "provider": self.provider,
                    "model": self.model,
                    "provider_type": type(self.llm_provider).__name__ if hasattr(self, 'llm_provider') else None
                }
            }
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the current provider."""
        return {
            "provider": self.provider,
            "model": self.model,
            "provider_class": type(self.llm_provider).__name__,
            "available_methods": [method for method in dir(self.llm_provider) if not method.startswith('_')]
        }
    
    @staticmethod
    def download_model(model_name, save_path="models"):
        """
        Download a model from Hugging Face and save it locally.
        :param model_name: Name of the model on Hugging Face (e.g., 'distilgpt2').
        :param save_path: Directory to save the model.
        """
        import transformers
        os.makedirs(save_path, exist_ok=True)
        model_path = os.path.join(save_path, model_name.replace("/", "_"))

        try:
            print(f"Downloading model: {model_name}")
            model = transformers.AutoModelForCausalLM.from_pretrained(model_name)
            tokenizer = transformers.AutoTokenizer.from_pretrained(model_name)

            # Save the model and tokenizer
            model.save_pretrained(model_path)
            tokenizer.save_pretrained(model_path)

            print(f"Model downloaded and saved to: {model_path}")
            return model_path
        except Exception as e:
            print(f"Error downloading model: {e}")
            return None
    
    def _generate_response(self, prompt: str, model: Optional[str] = None, **kwargs) -> str:
        """
        Legacy method - now delegates to ReasonChain provider system.
        Kept for backward compatibility.
        """
        self.logger.warning("_generate_response is deprecated. Use execute() method instead.")
        
        try:
            result = self.execute(prompt, **kwargs)
            if result["status"] == "success":
                return result["output"]
            else:
                raise Exception(result["message"])
        except Exception as e:
            self.logger.error(f"Error in LLM generation: {e}")
            raise e
    
    @classmethod
    def add_provider(cls, provider_name: str, provider_class: type):
        """
        Add a new provider using ReasonChain's registry system.
        :param provider_name: Name of the new provider.
        :param provider_class: Provider class that inherits from BaseLLMProvider.
        """
        cls.register_custom_provider(provider_name, provider_class)
        logging.info(f"Added new provider: {provider_name}")