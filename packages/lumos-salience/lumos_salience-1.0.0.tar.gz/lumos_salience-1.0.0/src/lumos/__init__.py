"""
LUMOS — LLM-based Universal Measure Of Salience

A package for testing Large Language Models' ability to capture salience in images

Modules:
    - models: LLM model runners (local and online API)
    - extraction: Saliency extraction (extract bounding boxes from LLM output)
    - segmentation: SAM segmentation (generate fine-grained masks from bboxes)
    - evaluation: Evaluation metrics (IoU, MAE, S-measure, E-measure)

Quick Start:
    >>> from lumos import create_model, extract_saliency, segment_with_sam, evaluate_saliency
    >>> 
    >>> # 1. Create model
    >>> model = create_model("openrouter", model_name="anthropic/claude-3-opus", api_key="sk-...")
    >>> 
    >>> # 2. Extract salience bounding boxes
    >>> extract_saliency(model, "images/", "bbox_results.csv", limit=100)
    >>> 
    >>> # 3. Generate fine-grained masks with SAM
    >>> segment_with_sam("bbox_results.csv", "images/", "sam_outputs/")
    >>> 
    >>> # 4. Evaluate results
    >>> evaluate_saliency("sam_outputs/sam_results.csv", "validations/", mode="mask")
"""

__version__ = "1.0.0"
__author__ = "Cantay Caliskan, Zhizhuang Chen"
__email__ = "ccaliska@ur.rochester.edu, zchen141@u.rochester.edu"

# Import main functionalities
from .models import (
    BaseLLMModel,
    OpenRouterModel,
    DeepSeekVLModel,
    QwenVLModel,
    MiniCPMModel,
    create_model
)

from .extraction import (
    BoundingBoxExtractor,
    extract_saliency
)

from .segmentation import (
    SAMSegmenter,
    segment_with_sam
)

from .evaluation import (
    SaliencyEvaluator,
    evaluate_saliency,
    calculate_iou,
    calculate_mae,
    calculate_s_measure,
    calculate_e_measure
)

__all__ = [
    # Module 1: Models
    "BaseLLMModel",
    "OpenRouterModel",
    "DeepSeekVLModel",
    "QwenVLModel",
    "MiniCPMModel",
    "create_model",
    
    # Module 2: Extraction
    "BoundingBoxExtractor",
    "extract_saliency",
    
    # Module 3: Segmentation
    "SAMSegmenter",
    "segment_with_sam",
    
    # Module 4: Evaluation
    "SaliencyEvaluator",
    "evaluate_saliency",
    "calculate_iou",
    "calculate_mae",
    "calculate_s_measure",
    "calculate_e_measure",
]