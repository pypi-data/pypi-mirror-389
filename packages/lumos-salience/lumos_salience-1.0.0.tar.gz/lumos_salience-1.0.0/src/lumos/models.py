"""
Module 1: LLM Model Runner
Supports local models and online APIs (OpenRouter)
"""

import os
import sys
import torch
from PIL import Image
from typing import Optional, Dict, Any, List
import requests
import json


class BaseLLMModel:
    """Base class for LLM models"""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
    
    def process_image(self, image_path: str, prompt: str) -> str:
        """
        Process image and return model output
        
        Args:
            image_path: Path to image file
            prompt: Prompt text
            
        Returns:
            str: Model output text
        """
        raise NotImplementedError("Subclass must implement process_image method")


class OpenRouterModel(BaseLLMModel):
    """OpenRouter API model"""
    
    def __init__(self, model_name: str, api_key: Optional[str] = None):
        """
        Initialize OpenRouter model
        
        Args:
            model_name: Model name (e.g., "anthropic/claude-3-opus")
            api_key: OpenRouter API key (if None, read from environment variable)
        """
        super().__init__(model_name)
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OpenRouter API key not provided. Set OPENROUTER_API_KEY environment variable or pass api_key parameter.")
        
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
    
    def process_image(self, image_path: str, prompt: str) -> str:
        """Process image using OpenRouter API"""
        import base64
        
        # Read and encode image
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        # Get image MIME type
        ext = os.path.splitext(image_path)[1].lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp'
        }
        mime_type = mime_types.get(ext, 'image/jpeg')
        
        # Build request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_data}"
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            "max_tokens": 256
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        except Exception as e:
            return f"Error: {str(e)}"


class DeepSeekVLModel(BaseLLMModel):
    """DeepSeek-VL local model"""
    
    def __init__(self, model_path: str = "deepseek-ai/deepseek-vl-7b-chat"):
        """
        Initialize DeepSeek-VL model
        
        Args:
            model_path: Model path or HuggingFace model ID
        """
        super().__init__(model_path)
        
        # Dynamically import DeepSeek modules
        try:
            from deepseek_vl.models import VLChatProcessor, MultiModalityCausalLM
            from deepseek_vl.utils.io import load_pil_images
        except ImportError:
            raise ImportError(
                "DeepSeek-VL not installed. Install with: "
                "git clone https://github.com/deepseek-ai/DeepSeek-VL.git && pip install -e ./DeepSeek-VL"
            )
        
        print(f"Loading DeepSeek-VL model: {model_path}")
        self.processor = VLChatProcessor.from_pretrained(model_path)
        self.tokenizer = self.processor.tokenizer
        self.model = MultiModalityCausalLM.from_pretrained(model_path, trust_remote_code=True)
        
        # Move to GPU
        if torch.cuda.is_available():
            self.model = self.model.to(torch.bfloat16).cuda().eval()
        else:
            self.model = self.model.eval()
        
        print(f"Model loaded on: {'CUDA' if torch.cuda.is_available() else 'CPU'}")
    
    def process_image(self, image_path: str, prompt: str) -> str:
        """Process image using DeepSeek-VL"""
        from deepseek_vl.utils.io import load_pil_images
        
        try:
            # Prepare conversation
            conversation = [
                {
                    "role": "User",
                    "content": f"<image_placeholder>{prompt}",
                    "images": [image_path]
                },
                {"role": "Assistant", "content": ""}
            ]
            
            # Load images
            pil_images = load_pil_images(conversation)
            if not pil_images:
                pil_images = [Image.open(image_path).convert("RGB")]
            
            # Prepare inputs
            prepare_inputs = self.processor(
                conversations=conversation,
                images=pil_images,
                force_batchify=True
            ).to(self.model.device)
            
            # Generate output
            inputs_embeds = self.model.prepare_inputs_embeds(**prepare_inputs)
            outputs = self.model.language_model.generate(
                inputs_embeds=inputs_embeds,
                attention_mask=prepare_inputs.attention_mask,
                pad_token_id=self.tokenizer.eos_token_id,
                bos_token_id=self.tokenizer.bos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                max_new_tokens=256,
                do_sample=False,
                use_cache=True
            )
            
            # Decode
            answer = self.tokenizer.decode(outputs[0].cpu().tolist(), skip_special_tokens=True)
            return answer.strip()
            
        except Exception as e:
            return f"Error: {str(e)}"


class QwenVLModel(BaseLLMModel):
    """Qwen2.5-VL local model"""
    
    def __init__(self, model_path: str = "Qwen/Qwen2.5-VL-7B-Instruct"):
        """
        Initialize Qwen-VL model
        
        Args:
            model_path: Model path or HuggingFace model ID
        """
        super().__init__(model_path)
        
        from transformers import pipeline
        
        print(f"Loading Qwen-VL model: {model_path}")
        self.pipeline = pipeline("image-text-to-text", model=model_path)
        print("Model loaded successfully")
    
    def process_image(self, image_path: str, prompt: str) -> str:
        """Process image using Qwen-VL"""
        try:
            image = Image.open(image_path).convert("RGB")
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": image},
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
            
            result = self.pipeline(messages, max_new_tokens=256)
            
            # Parse result
            if isinstance(result, list) and len(result) > 0:
                first_item = result[0]
                if isinstance(first_item, dict) and 'generated_text' in first_item:
                    generated = first_item['generated_text']
                    if isinstance(generated, list):
                        for msg in generated:
                            if isinstance(msg, dict) and msg.get('role') == 'assistant':
                                return msg.get('content', '')
                    elif isinstance(generated, str):
                        return generated
            
            return str(result)
            
        except Exception as e:
            return f"Error: {str(e)}"


class MiniCPMModel(BaseLLMModel):
    """MiniCPM-V local model"""
    
    def __init__(self, model_path: str = "openbmb/MiniCPM-V-4_5"):
        """
        Initialize MiniCPM model
        
        Args:
            model_path: Model path or HuggingFace model ID
        """
        super().__init__(model_path)
        
        from transformers import AutoModel, AutoTokenizer
        
        print(f"Loading MiniCPM model: {model_path}")
        self.model = AutoModel.from_pretrained(
            model_path, 
            trust_remote_code=True, 
            torch_dtype=torch.bfloat16
        )
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        
        if torch.cuda.is_available():
            self.model = self.model.cuda()
        
        print(f"Model loaded on: {'CUDA' if torch.cuda.is_available() else 'CPU'}")
    
    def process_image(self, image_path: str, prompt: str) -> str:
        """Process image using MiniCPM"""
        try:
            image = Image.open(image_path).convert("RGB")
            msgs = [{'role': 'user', 'content': [image, prompt]}]
            
            with torch.inference_mode():
                response = self.model.chat(
                    image=None,
                    msgs=msgs,
                    tokenizer=self.tokenizer,
                    sampling=False,
                    max_new_tokens=256
                )
            
            return response.strip()
            
        except Exception as e:
            return f"Error: {str(e)}"


def create_model(model_type: str, **kwargs) -> BaseLLMModel:
    """
    Factory function: Create model instance
    
    Args:
        model_type: Model type ("openrouter", "deepseek-vl", "qwen-vl", "minicpm")
        **kwargs: Model-specific parameters
        
    Returns:
        BaseLLMModel: Model instance
        
    Examples:
        >>> # OpenRouter API
        >>> model = create_model("openrouter", model_name="anthropic/claude-3-opus", api_key="sk-...")
        >>> 
        >>> # Local models
        >>> model = create_model("deepseek-vl", model_path="deepseek-ai/deepseek-vl-7b-chat")
        >>> model = create_model("qwen-vl", model_path="Qwen/Qwen2.5-VL-7B-Instruct")
        >>> model = create_model("minicpm", model_path="openbmb/MiniCPM-V-4_5")
    """
    model_type = model_type.lower()
    
    if model_type == "openrouter":
        return OpenRouterModel(**kwargs)
    elif model_type == "deepseek-vl":
        return DeepSeekVLModel(**kwargs)
    elif model_type == "qwen-vl":
        return QwenVLModel(**kwargs)
    elif model_type == "minicpm":
        return MiniCPMModel(**kwargs)
    else:
        raise ValueError(
            f"Unknown model type: {model_type}. "
            f"Supported types: openrouter, deepseek-vl, qwen-vl, minicpm"
        )
