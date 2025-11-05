"""
Basic Usage Examples for LUMOS Package

This script demonstrates the main functionalities of the LUMOS package.
"""

import os
from lumos import create_model, extract_saliency, segment_with_sam, evaluate_saliency


def example_1_openrouter_api():
    """Example 1: Using OpenRouter API"""
    print("\n" + "="*60)
    print("Example 1: OpenRouter API")
    print("="*60)
    
    # Set API key (or use environment variable OPENROUTER_API_KEY)
    api_key = os.environ.get("OPENROUTER_API_KEY", "your-api-key-here")
    
    # Create model
    model = create_model(
        "openrouter",
        model_name="anthropic/claude-3-opus",
        api_key=api_key
    )
    
    # Extract saliency bounding boxes
    extract_saliency(
        model=model,
        images_folder="images/",
        output_csv="bbox_results_openrouter.csv",
        limit=10  # Process first 10 images
    )
    
    print("✓ Bounding boxes extracted to bbox_results_openrouter.csv")


def example_2_local_model():
    """Example 2: Using local DeepSeek-VL model"""
    print("\n" + "="*60)
    print("Example 2: Local DeepSeek-VL Model")
    print("="*60)
    
    # Create local model
    model = create_model("deepseek-vl", model_path="deepseek-ai/deepseek-vl-7b-chat")
    
    # Extract saliency
    extract_saliency(
        model=model,
        images_folder="images/",
        output_csv="bbox_results_deepseek.csv",
        limit=10
    )
    
    print("✓ Bounding boxes extracted to bbox_results_deepseek.csv")


def example_3_sam_segmentation():
    """Example 3: Generate masks with SAM"""
    print("\n" + "="*60)
    print("Example 3: SAM Segmentation")
    print("="*60)
    
    # Generate fine-grained masks from bounding boxes
    segment_with_sam(
        csv_path="bbox_results_openrouter.csv",
        images_root="images/",
        output_dir="sam_outputs",
        model_type="vit_h",  # Use vit_l or vit_b for faster processing
        save_overlay=True    # Save visualization overlays
    )
    
    print("✓ Masks saved to sam_outputs/")


def example_4_evaluation():
    """Example 4: Evaluate against ground truth"""
    print("\n" + "="*60)
    print("Example 4: Evaluation")
    print("="*60)
    
    # Evaluate bounding boxes
    results_bbox = evaluate_saliency(
        csv_path="bbox_results_openrouter.csv",
        validation_dir="validations/DUTS-TR-Mask",
        output_csv="evaluation_bbox.csv",
        mode="bbox"
    )
    
    print("\nBounding Box Evaluation:")
    print(f"  Average IoU:       {results_bbox['iou'].mean():.4f}")
    print(f"  Average MAE:       {results_bbox['mae'].mean():.4f}")
    print(f"  Average S-measure: {results_bbox['s_measure'].mean():.4f}")
    print(f"  Average E-measure: {results_bbox['e_measure'].mean():.4f}")
    
    # Evaluate SAM masks
    results_mask = evaluate_saliency(
        csv_path="sam_outputs/sam_results.csv",
        validation_dir="validations/DUTS-TR-Mask",
        output_csv="evaluation_mask.csv",
        mode="mask"
    )
    
    print("\nSAM Mask Evaluation:")
    print(f"  Average IoU:       {results_mask['iou'].mean():.4f}")
    print(f"  Average MAE:       {results_mask['mae'].mean():.4f}")
    print(f"  Average S-measure: {results_mask['s_measure'].mean():.4f}")
    print(f"  Average E-measure: {results_mask['e_measure'].mean():.4f}")


def example_5_custom_prompt():
    """Example 5: Using custom prompt"""
    print("\n" + "="*60)
    print("Example 5: Custom Prompt")
    print("="*60)
    
    custom_prompt = """
    Look at this image carefully. 
    Identify the most visually salient object or region.
    Provide a bounding box in the format [x_min, y_min, x_max, y_max].
    Use pixel coordinates.
    Only return the coordinates, nothing else.
    """
    
    model = create_model("openrouter", model_name="anthropic/claude-3-opus")
    
    extract_saliency(
        model=model,
        images_folder="images/",
        output_csv="bbox_results_custom.csv",
        prompt=custom_prompt,
        limit=5
    )
    
    print("✓ Custom prompt results saved to bbox_results_custom.csv")


def example_6_complete_pipeline():
    """Example 6: Complete end-to-end pipeline"""
    print("\n" + "="*60)
    print("Example 6: Complete Pipeline")
    print("="*60)
    
    # Step 1: Create model
    print("\n[1/4] Creating model...")
    model = create_model("openrouter", model_name="anthropic/claude-3-opus")
    
    # Step 2: Extract bounding boxes
    print("\n[2/4] Extracting bounding boxes...")
    extract_saliency(
        model=model,
        images_folder="images/",
        output_csv="pipeline_bboxes.csv",
        limit=20
    )
    
    # Step 3: Generate masks
    print("\n[3/4] Generating masks with SAM...")
    segment_with_sam(
        csv_path="pipeline_bboxes.csv",
        images_root="images/",
        output_dir="pipeline_outputs",
        model_type="vit_h"
    )
    
    # Step 4: Evaluate
    print("\n[4/4] Evaluating results...")
    results = evaluate_saliency(
        csv_path="pipeline_outputs/sam_results.csv",
        validation_dir="validations/DUTS-TR-Mask",
        output_csv="pipeline_evaluation.csv",
        mode="mask"
    )
    
    print("\n" + "="*60)
    print("Pipeline Complete!")
    print("="*60)
    print(f"\nFinal Results (n={len(results)} images):")
    print(f"  IoU:       {results['iou'].mean():.4f} ± {results['iou'].std():.4f}")
    print(f"  MAE:       {results['mae'].mean():.4f} ± {results['mae'].std():.4f}")
    print(f"  S-measure: {results['s_measure'].mean():.4f} ± {results['s_measure'].std():.4f}")
    print(f"  E-measure: {results['e_measure'].mean():.4f} ± {results['e_measure'].std():.4f}")


def example_7_compare_models():
    """Example 7: Compare multiple models"""
    print("\n" + "="*60)
    print("Example 7: Model Comparison")
    print("="*60)
    
    models_to_test = [
        ("OpenRouter Claude", "openrouter", {"model_name": "anthropic/claude-3-opus"}),
        ("OpenRouter GPT-4", "openrouter", {"model_name": "openai/gpt-4-vision-preview"}),
    ]
    
    results_summary = []
    
    for model_name, model_type, kwargs in models_to_test:
        print(f"\n{'='*60}")
        print(f"Testing: {model_name}")
        print(f"{'='*60}")
        
        # Create model
        model = create_model(model_type, **kwargs)
        
        # Extract and evaluate
        csv_name = f"comparison_{model_name.replace(' ', '_').lower()}.csv"
        extract_saliency(model, "images/", csv_name, limit=10)
        
        results = evaluate_saliency(
            csv_path=csv_name,
            validation_dir="validations/DUTS-TR-Mask",
            mode="bbox"
        )
        
        results_summary.append({
            "model": model_name,
            "iou": results['iou'].mean(),
            "mae": results['mae'].mean(),
            "s_measure": results['s_measure'].mean(),
            "e_measure": results['e_measure'].mean()
        })
    
    # Print comparison
    print("\n" + "="*60)
    print("Model Comparison Summary")
    print("="*60)
    print(f"{'Model':<25} {'IoU':>10} {'MAE':>10} {'S-Mea':>10} {'E-Mea':>10}")
    print("-"*60)
    for r in results_summary:
        print(f"{r['model']:<25} {r['iou']:>10.4f} {r['mae']:>10.4f} "
              f"{r['s_measure']:>10.4f} {r['e_measure']:>10.4f}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("LUMOS Package - Basic Usage Examples")
    print("="*60)
    
    # Uncomment the example you want to run:
    
    # example_1_openrouter_api()
    # example_2_local_model()
    # example_3_sam_segmentation()
    # example_4_evaluation()
    # example_5_custom_prompt()
    # example_6_complete_pipeline()
    # example_7_compare_models()
    
    print("\n" + "="*60)
    print("To run an example, uncomment the desired function call in __main__")
    print("="*60 + "\n")
