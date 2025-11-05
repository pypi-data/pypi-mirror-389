"""
模块3: SAM 分割
使用 Segment Anything Model 从 bounding box 生成精细 mask
"""

import os
import csv
import ast
import json
import numpy as np
import cv2
import torch
from typing import List, Tuple, Optional, Dict
from tqdm import tqdm
import pandas as pd
from PIL import Image


class SAMSegmenter:
    """SAM (Segment Anything) 分割器"""
    
    def __init__(
        self, 
        model_type: str = "vit_h",
        checkpoint_path: Optional[str] = None,
        device: Optional[str] = None
    ):
        """
        初始化 SAM 分割器
        
        Args:
            model_type: SAM 模型类型 ("vit_h", "vit_l", "vit_b")
            checkpoint_path: 模型 checkpoint 路径（如果为 None，自动下载）
            device: 设备 ("cuda" 或 "cpu"，如果为 None 自动选择）
        """
        try:
            from segment_anything import sam_model_registry, SamPredictor
        except ImportError:
            raise ImportError(
                "segment-anything not installed. Install with: "
                "pip install git+https://github.com/facebookresearch/segment-anything.git"
            )
        
        self.model_type = model_type
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        
        # 自动下载 checkpoint
        if checkpoint_path is None:
            checkpoint_path = self._download_checkpoint(model_type)
        
        print(f"Loading SAM model ({model_type}) from {checkpoint_path}")
        sam = sam_model_registry[model_type](checkpoint=checkpoint_path)
        sam = sam.to(self.device)
        
        self.predictor = SamPredictor(sam)
        
        # 启用优化
        if self.device == "cuda":
            torch.backends.cudnn.benchmark = True
        
        print(f"SAM model loaded on {self.device}")
    
    def _download_checkpoint(self, model_type: str) -> str:
        """自动下载 SAM checkpoint"""
        import urllib.request
        
        checkpoint_urls = {
            "vit_h": "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth",
            "vit_l": "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_l_0b3195.pth",
            "vit_b": "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth"
        }
        
        if model_type not in checkpoint_urls:
            raise ValueError(f"Unknown model type: {model_type}")
        
        url = checkpoint_urls[model_type]
        filename = os.path.basename(url)
        checkpoint_path = os.path.join(os.path.expanduser("~"), ".lumos_cache", filename)
        
        os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
        
        if not os.path.exists(checkpoint_path):
            print(f"Downloading {model_type} checkpoint...")
            urllib.request.urlretrieve(url, checkpoint_path)
            print(f"Downloaded to {checkpoint_path}")
        else:
            print(f"Using cached checkpoint: {checkpoint_path}")
        
        return checkpoint_path
    
    def segment_from_bbox(
        self, 
        image: np.ndarray, 
        bbox: List[float]
    ) -> np.ndarray:
        """
        从单个 bounding box 生成 mask
        
        Args:
            image: 图像数组 (RGB, H x W x 3)
            bbox: Bounding box [x_min, y_min, x_max, y_max]
            
        Returns:
            np.ndarray: Binary mask (H x W, 0/255)
        """
        # 设置图像（只需要对每张图像调用一次）
        self.predictor.set_image(image)
        
        # 准备 bbox (xyxy 格式)
        x_min, y_min, x_max, y_max = bbox
        H, W = image.shape[:2]
        
        # 确保坐标在范围内
        x_min = max(0, min(x_min, W - 1))
        y_min = max(0, min(y_min, H - 1))
        x_max = max(0, min(x_max, W - 1))
        y_max = max(0, min(y_max, H - 1))
        
        # 转换为 SAM 输入格式
        bbox_array = np.array([[x_min, y_min, x_max, y_max]], dtype=np.float32)
        boxes_torch = torch.tensor(bbox_array, device=self.device)
        
        # Transform boxes
        boxes_transformed = self.predictor.transform.apply_boxes_torch(
            boxes_torch, 
            (H, W)
        )
        
        # 预测
        with torch.no_grad():
            if self.device == "cuda":
                with torch.cuda.amp.autocast():
                    masks, scores, _ = self.predictor.predict_torch(
                        point_coords=None,
                        point_labels=None,
                        boxes=boxes_transformed,
                        multimask_output=False
                    )
            else:
                masks, scores, _ = self.predictor.predict_torch(
                    point_coords=None,
                    point_labels=None,
                    boxes=boxes_transformed,
                    multimask_output=False
                )
        
        # 转换为 numpy (0/255)
        mask = (masks.squeeze(1).cpu().numpy()[0] > 0).astype(np.uint8) * 255
        
        return mask
    
    def segment_from_bboxes(
        self,
        image: np.ndarray,
        bboxes: List[List[float]]
    ) -> List[np.ndarray]:
        """
        从多个 bounding boxes 生成 masks
        
        Args:
            image: 图像数组 (RGB, H x W x 3)
            bboxes: Bounding boxes [[x_min, y_min, x_max, y_max], ...]
            
        Returns:
            List[np.ndarray]: Binary masks
        """
        if not bboxes:
            return []
        
        # 设置图像（一次性）
        self.predictor.set_image(image)
        
        H, W = image.shape[:2]
        
        # 准备所有 boxes
        valid_bboxes = []
        for bbox in bboxes:
            x_min, y_min, x_max, y_max = bbox
            x_min = max(0, min(x_min, W - 1))
            y_min = max(0, min(y_min, H - 1))
            x_max = max(0, min(x_max, W - 1))
            y_max = max(0, min(y_max, H - 1))
            valid_bboxes.append([x_min, y_min, x_max, y_max])
        
        boxes_array = np.array(valid_bboxes, dtype=np.float32)
        boxes_torch = torch.tensor(boxes_array, device=self.device)
        
        # Transform boxes
        boxes_transformed = self.predictor.transform.apply_boxes_torch(
            boxes_torch,
            (H, W)
        )
        
        # 批量预测
        with torch.no_grad():
            if self.device == "cuda":
                with torch.cuda.amp.autocast():
                    masks, scores, _ = self.predictor.predict_torch(
                        point_coords=None,
                        point_labels=None,
                        boxes=boxes_transformed,
                        multimask_output=False
                    )
            else:
                masks, scores, _ = self.predictor.predict_torch(
                    point_coords=None,
                    point_labels=None,
                    boxes=boxes_transformed,
                    multimask_output=False
                )
        
        # 转换为 numpy list
        masks_np = (masks.squeeze(1).cpu().numpy() > 0).astype(np.uint8) * 255
        
        return [masks_np[i] for i in range(len(masks_np))]
    
    def process_csv(
        self,
        csv_path: str,
        images_root: str = "",
        output_dir: str = "sam_outputs",
        save_overlay: bool = False
    ) -> str:
        """
        处理 CSV 文件中的所有 bounding boxes
        
        Args:
            csv_path: 输入 CSV 文件路径（包含 image_path 和 output_result 列）
            images_root: 图像根目录（如果 CSV 中是相对路径）
            output_dir: 输出目录
            save_overlay: 是否保存 overlay 预览图
            
        Returns:
            str: 输出结果 CSV 路径
        """
        # 读取 CSV
        df = pd.read_csv(csv_path)
        print(f"Loaded {len(df)} records from {csv_path}")
        
        # 创建输出目录
        masks_dir = os.path.join(output_dir, "masks")
        os.makedirs(masks_dir, exist_ok=True)
        
        if save_overlay:
            overlays_dir = os.path.join(output_dir, "overlays")
            os.makedirs(overlays_dir, exist_ok=True)
        
        # 解析 bboxes
        def parse_bboxes(output_result):
            """解析 output_result 列"""
            try:
                # 尝试 JSON
                data = json.loads(output_result)
                if isinstance(data, list):
                    if data and isinstance(data[0], list) and len(data[0]) == 4:
                        return data
                    elif len(data) == 4:
                        return [data]
            except:
                pass
            
            try:
                # 尝试 ast.literal_eval
                data = ast.literal_eval(str(output_result))
                if isinstance(data, list):
                    if data and isinstance(data[0], (list, tuple)) and len(data[0]) == 4:
                        return [list(bbox) for bbox in data]
                    elif len(data) == 4:
                        return [list(data)]
            except:
                pass
            
            return []
        
        # 按图像分组
        grouped = df.groupby("image_path")
        results = []
        
        for image_path, group in tqdm(grouped, total=grouped.ngroups, desc="Segmenting images"):
            # 构建完整路径
            if os.path.isabs(image_path):
                full_path = image_path
            else:
                full_path = os.path.join(images_root, image_path)
            
            if not os.path.exists(full_path):
                print(f"Warning: Image not found: {full_path}")
                continue
            
            # 加载图像
            image_bgr = cv2.imread(full_path)
            if image_bgr is None:
                print(f"Warning: Failed to read: {full_path}")
                continue
            
            image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
            
            # 收集该图像的所有 bboxes
            all_bboxes = []
            for _, row in group.iterrows():
                bboxes = parse_bboxes(row['output_result'])
                all_bboxes.extend(bboxes)
            
            if not all_bboxes:
                print(f"Warning: No valid bboxes for {image_path}")
                continue
            
            # 批量分割
            masks = self.segment_from_bboxes(image_rgb, all_bboxes)
            
            # 保存 masks
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            
            for i, mask in enumerate(masks):
                mask_name = f"{base_name}_box{i:03d}.png"
                mask_path = os.path.join(masks_dir, mask_name)
                cv2.imwrite(mask_path, mask, [cv2.IMWRITE_PNG_COMPRESSION, 1])
                
                # 保存 overlay（可选）
                overlay_path = None
                if save_overlay:
                    overlay = self._create_overlay(image_rgb, mask, alpha=0.45)
                    overlay_bgr = cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR)
                    overlay_name = f"{base_name}_box{i:03d}_overlay.png"
                    overlay_path = os.path.join(overlays_dir, overlay_name)
                    cv2.imwrite(overlay_path, overlay_bgr)
                
                results.append({
                    "image_path": image_path,
                    "bbox_index": i,
                    "bbox": all_bboxes[i],
                    "mask_path": mask_path,
                    "overlay_path": overlay_path
                })
        
        # 保存结果 CSV
        results_df = pd.DataFrame(results)
        results_csv = os.path.join(output_dir, "sam_results.csv")
        results_df.to_csv(results_csv, index=False)
        
        print(f"\nSegmentation complete! Results saved to {results_csv}")
        print(f"Masks saved to {masks_dir}")
        if save_overlay:
            print(f"Overlays saved to {overlays_dir}")
        
        return results_csv
    
    def _create_overlay(
        self, 
        image_rgb: np.ndarray, 
        mask: np.ndarray, 
        alpha: float = 0.5
    ) -> np.ndarray:
        """创建 mask overlay"""
        color = np.zeros_like(image_rgb)
        color[..., 1] = 255  # green
        mask_bool = mask > 0
        overlay = image_rgb.copy()
        overlay[mask_bool] = (
            alpha * color[mask_bool] + (1 - alpha) * overlay[mask_bool]
        ).astype(np.uint8)
        return overlay


def segment_with_sam(
    csv_path: str,
    images_root: str = "",
    output_dir: str = "sam_outputs",
    model_type: str = "vit_h",
    checkpoint_path: Optional[str] = None,
    save_overlay: bool = False
) -> str:
    """
    便捷函数：使用 SAM 从 CSV 中的 bboxes 生成 masks
    
    Args:
        csv_path: 输入 CSV 文件路径
        images_root: 图像根目录
        output_dir: 输出目录
        model_type: SAM 模型类型 ("vit_h", "vit_l", "vit_b")
        checkpoint_path: 自定义 checkpoint 路径
        save_overlay: 是否保存预览图
        
    Returns:
        str: 输出结果 CSV 路径
        
    Example:
        >>> from lumos.segmentation import segment_with_sam
        >>> 
        >>> segment_with_sam(
        ...     csv_path="bbox_results.csv",
        ...     images_root="images/",
        ...     output_dir="sam_outputs",
        ...     model_type="vit_h"
        ... )
    """
    segmenter = SAMSegmenter(
        model_type=model_type,
        checkpoint_path=checkpoint_path
    )
    
    return segmenter.process_csv(
        csv_path=csv_path,
        images_root=images_root,
        output_dir=output_dir,
        save_overlay=save_overlay
    )
