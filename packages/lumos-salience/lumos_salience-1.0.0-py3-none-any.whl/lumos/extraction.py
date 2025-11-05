"""
Module 2: Saliency Extraction
Extract bounding boxes from LLM output and save as CSV
"""

import os
import csv
import json
import ast
import re
from typing import List, Dict, Tuple, Optional, Any
from PIL import Image
from tqdm import tqdm

from .models import BaseLLMModel


class BoundingBoxExtractor:
    """Bounding Box Extractor"""
    
    def __init__(self, model: BaseLLMModel, output_format: str = "pixel"):
        """
        Initialize extractor
        
        Args:
            model: LLM model instance
            output_format: Output format ("pixel" or "normalized")
        """
        self.model = model
        self.output_format = output_format
        self.image_dimensions_cache = {}
    
    def get_image_dimensions(self, image_path: str) -> Tuple[int, int]:
        """Get image dimensions (width, height)"""
        if image_path in self.image_dimensions_cache:
            return self.image_dimensions_cache[image_path]
        
        try:
            img = Image.open(image_path)
            width, height = img.size
            self.image_dimensions_cache[image_path] = (width, height)
            return width, height
        except Exception as e:
            print(f"Warning: Cannot load image {image_path}: {e}")
            return 400, 300  # Default dimensions
    
    def parse_bbox_from_text(self, text: str, image_path: str) -> List[List[float]]:
        """
        Parse bounding box from model output text
        
        Supported formats:
        1. [x1, y1, x2, y2]
        2. [[x1, y1, x2, y2], [x1, y1, x2, y2], ...]
        3. [{"bbox_2d": [x1, y1, x2, y2], "label": "..."}, ...]
        4. Coordinates in natural language description
        
        Args:
            text: Model output text
            image_path: Image path (for coordinate normalization/denormalization)
            
        Returns:
            List[List[float]]: bbox list [[x1, y1, x2, y2], ...]
        """
        bbox_list = []
        
        # Clean text
        text = text.strip()
        
        # Remove markdown code block markers
        if text.startswith("```json") or text.startswith("```"):
            lines = text.split('\n')
            text = '\n'.join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        
        # Method 1: Try parsing as JSON
        try:
            data = json.loads(text)
            if isinstance(data, list):
                # Format: [[x1, y1, x2, y2], ...]
                if data and isinstance(data[0], (list, tuple)) and len(data[0]) == 4:
                    bbox_list = [list(map(float, bbox)) for bbox in data]
                # Format: [x1, y1, x2, y2]
                elif len(data) == 4 and all(isinstance(x, (int, float)) for x in data):
                    bbox_list = [list(map(float, data))]
                # Format: [{"bbox_2d": [...], "label": "..."}, ...]
                elif data and isinstance(data[0], dict) and "bbox_2d" in data[0]:
                    bbox_list = [list(map(float, item["bbox_2d"])) for item in data if "bbox_2d" in item]
        except (json.JSONDecodeError, ValueError, KeyError):
            pass
        
        # Method 2: Try using ast.literal_eval
        if not bbox_list:
            try:
                data = ast.literal_eval(text)
                if isinstance(data, list):
                    if data and isinstance(data[0], (list, tuple)) and len(data[0]) == 4:
                        bbox_list = [list(map(float, bbox)) for bbox in data]
                    elif len(data) == 4 and all(isinstance(x, (int, float)) for x in data):
                        bbox_list = [list(map(float, data))]
            except (ValueError, SyntaxError):
                pass
        
        # Method 3: Regular expression to extract coordinates
        if not bbox_list:
            # Match [number, number, number, number] pattern
            pattern = r'\[(\d+(?:\.\d+)?),\s*(\d+(?:\.\d+)?),\s*(\d+(?:\.\d+)?),\s*(\d+(?:\.\d+)?)\]'
            matches = re.findall(pattern, text)
            if matches:
                bbox_list = [[float(x) for x in match] for match in matches]
        
        # Check if coordinates are normalized (0-1 range)
        if bbox_list:
            width, height = self.get_image_dimensions(image_path)
            normalized_list = []
            
            for bbox in bbox_list:
                x1, y1, x2, y2 = bbox
                
                # Check if normalized coordinates
                is_normalized = all(0 <= c <= 1 for c in bbox)
                
                if is_normalized and self.output_format == "pixel":
                    # Convert to pixel coordinates
                    x1 = int(x1 * width)
                    y1 = int(y1 * height)
                    x2 = int(x2 * width)
                    y2 = int(y2 * height)
                elif not is_normalized and self.output_format == "normalized":
                    # Convert to normalized coordinates
                    x1 = x1 / width
                    y1 = y1 / height
                    x2 = x2 / width
                    y2 = y2 / height
                
                normalized_list.append([x1, y1, x2, y2])
            
            bbox_list = normalized_list
        
        return bbox_list
    
    def process_single_image(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """
        Process single image
        
        Args:
            image_path: Image path
            prompt: Prompt text
            
        Returns:
            Dict: {"image_path": str, "raw_output": str, "bboxes": List}
        """
        # Call model
        raw_output = self.model.process_image(image_path, prompt)
        
        # Parse bbox
        bboxes = self.parse_bbox_from_text(raw_output, image_path)
        
        return {
            "image_path": image_path,
            "raw_output": raw_output,
            "bboxes": bboxes
        }
    
    def process_folder(
        self, 
        images_folder: str, 
        prompt: str,
        output_csv: str = "bbox_results.csv",
        limit: Optional[int] = None,
        recursive: bool = True
    ) -> str:
        """
        Batch process images in folder
        
        Args:
            images_folder: Image folder path
            prompt: Prompt text
            output_csv: Output CSV file path
            limit: Limit number of images to process
            recursive: Whether to recursively process subfolders
            
        Returns:
            str: Output CSV file path
        """
        # Collect image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        image_files = []
        
        if recursive:
            for root, _, files in os.walk(images_folder):
                for file in files:
                    if os.path.splitext(file)[1].lower() in image_extensions:
                        image_files.append(os.path.join(root, file))
        else:
            for file in os.listdir(images_folder):
                if os.path.splitext(file)[1].lower() in image_extensions:
                    image_files.append(os.path.join(images_folder, file))
        
        if not image_files:
            print(f"No images found in {images_folder}")
            return output_csv
        
        image_files.sort()
        
        # Limit number
        if limit:
            image_files = image_files[:limit]
        
        print(f"Found {len(image_files)} images to process")
        
        # Process images and save to CSV
        with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['image_path', 'output_result'])
            
            for image_path in tqdm(image_files, desc="Processing images"):
                result = self.process_single_image(image_path, prompt)
                
                # Save raw output and parsed bbox
                # Format: use bboxes if parsing succeeds, otherwise save raw output
                output_value = str(result['bboxes']) if result['bboxes'] else result['raw_output']
                
                # Use relative path
                relative_path = os.path.relpath(image_path, start=os.path.dirname(images_folder))
                writer.writerow([relative_path, output_value])
        
        print(f"\nResults saved to: {output_csv}")
        return output_csv


def extract_saliency(
    model: BaseLLMModel,
    images_folder: str,
    output_csv: str = "bbox_results.csv",
    prompt: Optional[str] = None,
    limit: Optional[int] = None,
    output_format: str = "pixel"
) -> str:
    """
    Convenience function: Extract salience bounding boxes
    
    Args:
        model: LLM model instance
        images_folder: Image folder path
        output_csv: Output CSV file path
        prompt: Prompt text (if None, use default prompt)
        limit: Limit number of images to process
        output_format: Output format ("pixel" or "normalized")
        
    Returns:
        str: Output CSV file path
        
    Example:
        >>> from lumos.models import create_model
        >>> from lumos.extraction import extract_saliency
        >>> 
        >>> model = create_model("openrouter", model_name="anthropic/claude-3-opus", api_key="sk-...")
        >>> extract_saliency(
        ...     model=model,
        ...     images_folder="images/",
        ...     output_csv="results.csv",
        ...     limit=100
        ... )
    """
    if prompt is None:
        prompt = (
            "Analyze the image and use a Bounding Box format to indicate the important region. "
            "Output one Bounding Box in the format of [x_min, y_min, x_max, y_max]. "
            "Format the final output with clear 4 coordinates. "
            "Do not output text or anything else"
        )
    
    extractor = BoundingBoxExtractor(model, output_format=output_format)
    return extractor.process_folder(
        images_folder=images_folder,
        prompt=prompt,
        output_csv=output_csv,
        limit=limit
    )
