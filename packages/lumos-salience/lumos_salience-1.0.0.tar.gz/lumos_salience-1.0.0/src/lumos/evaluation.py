"""
模块4: 评估指标
计算 IoU, MAE, S-measure, E-measure
"""

import os
import numpy as np
import cv2
import pandas as pd
import json
import ast
from typing import List, Tuple, Optional, Dict
from tqdm import tqdm


def load_mask(mask_path: str) -> np.ndarray:
    """
    加载 mask 并二值化
    
    Args:
        mask_path: Mask 文件路径
        
    Returns:
        np.ndarray: 二值 mask (0/1)
    """
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    if mask is None:
        raise ValueError(f"Cannot load mask: {mask_path}")
    
    # 归一化到 0-1
    mask = (mask > 0).astype(np.float32)
    return mask


def calculate_iou(pred_mask: np.ndarray, gt_mask: np.ndarray) -> float:
    """
    计算 Intersection over Union (IoU)
    
    Args:
        pred_mask: 预测 mask (0/1)
        gt_mask: Ground truth mask (0/1)
        
    Returns:
        float: IoU 分数
    """
    pred_mask = (pred_mask > 0.5).astype(np.uint8)
    gt_mask = (gt_mask > 0.5).astype(np.uint8)
    
    intersection = np.logical_and(pred_mask, gt_mask).sum()
    union = np.logical_or(pred_mask, gt_mask).sum()
    
    if union == 0:
        return 1.0 if intersection == 0 else 0.0
    
    return float(intersection / union)


def calculate_mae(pred_mask: np.ndarray, gt_mask: np.ndarray) -> float:
    """
    计算 Mean Absolute Error (MAE)
    
    Args:
        pred_mask: 预测 mask (0-1)
        gt_mask: Ground truth mask (0-1)
        
    Returns:
        float: MAE 分数
    """
    pred_mask = np.clip(pred_mask, 0, 1).astype(np.float32)
    gt_mask = np.clip(gt_mask, 0, 1).astype(np.float32)
    
    mae = np.mean(np.abs(pred_mask - gt_mask))
    return float(mae)


def calculate_s_measure(pred_mask: np.ndarray, gt_mask: np.ndarray, alpha: float = 0.5) -> float:
    """
    计算 S-measure (Structure Measure)
    
    Reference: 
    "Structure-measure: A New Way to Evaluate Foreground Maps" (ICCV 2017)
    
    Args:
        pred_mask: 预测 mask (0-1)
        gt_mask: Ground truth mask (0-1)
        alpha: 平衡参数
        
    Returns:
        float: S-measure 分数
    """
    pred_mask = pred_mask.astype(np.float32)
    gt_mask = gt_mask.astype(np.float32)
    
    # Region similarity
    x = np.mean(gt_mask)
    
    if x == 0:  # GT 全为背景
        pred_fg = pred_mask
        gt_fg = gt_mask
        s_region = 1.0 - np.mean(pred_fg)
    elif x == 1:  # GT 全为前景
        s_region = np.mean(pred_mask)
    else:
        # 前景和背景的相似度
        gt_fg = gt_mask
        gt_bg = 1 - gt_mask
        
        pred_fg = pred_mask
        pred_bg = 1 - pred_mask
        
        # Similarity of foreground
        numerator_fg = np.sum(pred_fg * gt_fg)
        denominator_fg = np.sum(gt_fg) + np.sum(pred_fg) - numerator_fg + 1e-8
        s_fg = numerator_fg / denominator_fg
        
        # Similarity of background
        numerator_bg = np.sum(pred_bg * gt_bg)
        denominator_bg = np.sum(gt_bg) + np.sum(pred_bg) - numerator_bg + 1e-8
        s_bg = numerator_bg / denominator_bg
        
        s_region = x * s_fg + (1 - x) * s_bg
    
    # Object similarity
    def ssim(pred, gt):
        """简化的 SSIM"""
        mu_pred = np.mean(pred)
        mu_gt = np.mean(gt)
        
        sigma_pred = np.std(pred)
        sigma_gt = np.std(gt)
        sigma_pred_gt = np.mean((pred - mu_pred) * (gt - mu_gt))
        
        c1 = 0.01 ** 2
        c2 = 0.03 ** 2
        
        s = ((2 * mu_pred * mu_gt + c1) * (2 * sigma_pred_gt + c2)) / \
            ((mu_pred**2 + mu_gt**2 + c1) * (sigma_pred**2 + sigma_gt**2 + c2))
        
        return s
    
    s_object = ssim(pred_mask, gt_mask)
    
    # 综合
    s_measure = alpha * s_object + (1 - alpha) * s_region
    
    return float(np.clip(s_measure, 0, 1))


def calculate_e_measure(pred_mask: np.ndarray, gt_mask: np.ndarray) -> float:
    """
    计算 E-measure (Enhanced-alignment Measure)
    
    Reference:
    "Enhanced-alignment Measure for Binary Foreground Map Evaluation" (IJCAI 2018)
    
    Args:
        pred_mask: 预测 mask (0-1)
        gt_mask: Ground truth mask (0-1)
        
    Returns:
        float: E-measure 分数
    """
    pred_mask = pred_mask.astype(np.float32)
    gt_mask = gt_mask.astype(np.float32)
    
    # Enhanced alignment matrix
    align_matrix = 2 * pred_mask * gt_mask / (pred_mask**2 + gt_mask**2 + 1e-8)
    
    # Enhanced alignment score
    h, w = gt_mask.shape
    
    # 局部和全局统计
    gt_fg = gt_mask > 0.5
    gt_bg = gt_mask <= 0.5
    
    if np.sum(gt_fg) == 0:  # 无前景
        enhanced_score = 1.0 - np.mean(pred_mask)
    elif np.sum(gt_bg) == 0:  # 无背景
        enhanced_score = np.mean(pred_mask)
    else:
        # 前景和背景的 enhanced alignment
        align_fg = align_matrix[gt_fg]
        align_bg = align_matrix[gt_bg]
        
        # 计算均值
        mean_fg = np.mean(align_fg) if len(align_fg) > 0 else 0
        mean_bg = np.mean(align_bg) if len(align_bg) > 0 else 0
        
        # 权重
        w_fg = np.sum(gt_fg) / (h * w)
        w_bg = np.sum(gt_bg) / (h * w)
        
        enhanced_score = w_fg * mean_fg + w_bg * mean_bg
    
    return float(np.clip(enhanced_score, 0, 1))


def create_bbox_mask(image_shape: Tuple[int, int], bbox: List[float]) -> np.ndarray:
    """
    从 bounding box 创建 mask
    
    Args:
        image_shape: (height, width)
        bbox: [x_min, y_min, x_max, y_max]
        
    Returns:
        np.ndarray: Binary mask (0/1)
    """
    height, width = image_shape
    mask = np.zeros((height, width), dtype=np.float32)
    
    x_min, y_min, x_max, y_max = bbox
    
    # 确保坐标在范围内
    x_min = max(0, min(int(x_min), width - 1))
    y_min = max(0, min(int(y_min), height - 1))
    x_max = max(0, min(int(x_max), width - 1))
    y_max = max(0, min(int(y_max), height - 1))
    
    if x_max < x_min:
        x_min, x_max = x_max, x_min
    if y_max < y_min:
        y_min, y_max = y_max, y_min
    
    mask[y_min:y_max+1, x_min:x_max+1] = 1.0
    
    return mask


def create_multi_bbox_mask(image_shape: Tuple[int, int], bboxes: List[List[float]]) -> np.ndarray:
    """
    从多个 bounding boxes 创建 mask
    
    Args:
        image_shape: (height, width)
        bboxes: [[x_min, y_min, x_max, y_max], ...]
        
    Returns:
        np.ndarray: Binary mask (0/1)
    """
    mask = np.zeros(image_shape, dtype=np.float32)
    
    for bbox in bboxes:
        bbox_mask = create_bbox_mask(image_shape, bbox)
        mask = np.maximum(mask, bbox_mask)
    
    return mask


def parse_bboxes(output_result: str) -> List[List[float]]:
    """解析 bbox 字符串"""
    try:
        data = json.loads(output_result)
        if isinstance(data, list):
            if data and isinstance(data[0], list) and len(data[0]) == 4:
                return [[float(x) for x in bbox] for bbox in data]
            elif len(data) == 4:
                return [[float(x) for x in data]]
    except:
        pass
    
    try:
        data = ast.literal_eval(str(output_result))
        if isinstance(data, list):
            if data and isinstance(data[0], (list, tuple)) and len(data[0]) == 4:
                return [[float(x) for x in bbox] for bbox in data]
            elif len(data) == 4:
                return [[float(x) for x in data]]
    except:
        pass
    
    return []


class SaliencyEvaluator:
    """Saliency 评估器"""
    
    def __init__(self, validation_dir: str):
        """
        初始化评估器
        
        Args:
            validation_dir: Ground truth masks 目录
        """
        self.validation_dir = validation_dir
    
    def get_gt_mask_path(self, image_path: str) -> str:
        """获取对应的 ground truth mask 路径"""
        filename = os.path.splitext(os.path.basename(image_path))[0]
        
        # 尝试常见的 mask 目录结构
        possible_paths = [
            os.path.join(self.validation_dir, f"{filename}.png"),
            os.path.join(self.validation_dir, "DUTS-TR-Mask", f"{filename}.png"),
            os.path.join(self.validation_dir, "masks", f"{filename}.png"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return possible_paths[0]  # 返回默认路径
    
    def evaluate_single_from_bbox(
        self,
        image_path: str,
        bboxes: List[List[float]],
        gt_mask_path: Optional[str] = None
    ) -> Dict[str, float]:
        """
        从 bounding boxes 评估单张图像
        
        Args:
            image_path: 图像路径
            bboxes: Bounding boxes
            gt_mask_path: Ground truth mask 路径（可选）
            
        Returns:
            Dict: 评估指标
        """
        if gt_mask_path is None:
            gt_mask_path = self.get_gt_mask_path(image_path)
        
        if not os.path.exists(gt_mask_path):
            return {
                "iou": 0.0,
                "mae": 1.0,
                "s_measure": 0.0,
                "e_measure": 0.0,
                "success": False
            }
        
        # 加载 GT mask
        gt_mask = load_mask(gt_mask_path)
        
        # 创建预测 mask
        if not bboxes:
            pred_mask = np.zeros_like(gt_mask)
        else:
            pred_mask = create_multi_bbox_mask(gt_mask.shape, bboxes)
        
        # 计算指标
        iou = calculate_iou(pred_mask, gt_mask)
        mae = calculate_mae(pred_mask, gt_mask)
        s_measure = calculate_s_measure(pred_mask, gt_mask)
        e_measure = calculate_e_measure(pred_mask, gt_mask)
        
        return {
            "iou": iou,
            "mae": mae,
            "s_measure": s_measure,
            "e_measure": e_measure,
            "success": True
        }
    
    def evaluate_single_from_mask(
        self,
        pred_mask_path: str,
        gt_mask_path: Optional[str] = None,
        image_path: Optional[str] = None
    ) -> Dict[str, float]:
        """
        从预测 mask 文件评估单张图像
        
        Args:
            pred_mask_path: 预测 mask 路径
            gt_mask_path: Ground truth mask 路径（可选）
            image_path: 图像路径（用于推断 GT mask 路径）
            
        Returns:
            Dict: 评估指标
        """
        if gt_mask_path is None:
            if image_path is None:
                # 从 mask 文件名推断
                image_path = os.path.basename(pred_mask_path)
            gt_mask_path = self.get_gt_mask_path(image_path)
        
        if not os.path.exists(gt_mask_path):
            return {
                "iou": 0.0,
                "mae": 1.0,
                "s_measure": 0.0,
                "e_measure": 0.0,
                "success": False
            }
        
        # 加载 masks
        pred_mask = load_mask(pred_mask_path)
        gt_mask = load_mask(gt_mask_path)
        
        # 调整尺寸
        if pred_mask.shape != gt_mask.shape:
            pred_mask = cv2.resize(pred_mask, (gt_mask.shape[1], gt_mask.shape[0]))
        
        # 计算指标
        iou = calculate_iou(pred_mask, gt_mask)
        mae = calculate_mae(pred_mask, gt_mask)
        s_measure = calculate_s_measure(pred_mask, gt_mask)
        e_measure = calculate_e_measure(pred_mask, gt_mask)
        
        return {
            "iou": iou,
            "mae": mae,
            "s_measure": s_measure,
            "e_measure": e_measure,
            "success": True
        }
    
    def evaluate_from_csv(
        self,
        csv_path: str,
        output_csv: Optional[str] = None,
        mode: str = "bbox"
    ) -> pd.DataFrame:
        """
        从 CSV 批量评估
        
        Args:
            csv_path: 输入 CSV 路径
            output_csv: 输出 CSV 路径（可选）
            mode: 评估模式 ("bbox" 或 "mask")
                - "bbox": CSV 包含 image_path 和 output_result (bboxes)
                - "mask": CSV 包含 image_path 和 mask_path
                
        Returns:
            pd.DataFrame: 评估结果
        """
        df = pd.read_csv(csv_path)
        print(f"Loaded {len(df)} records from {csv_path}")
        
        results = []
        
        if mode == "bbox":
            # 按图像分组
            grouped = df.groupby("image_path")
            
            for image_path, group in tqdm(grouped, desc="Evaluating"):
                # 解析所有 bboxes
                all_bboxes = []
                for _, row in group.iterrows():
                    bboxes = parse_bboxes(row['output_result'])
                    all_bboxes.extend(bboxes)
                
                # 评估
                metrics = self.evaluate_single_from_bbox(image_path, all_bboxes)
                metrics['image_path'] = image_path
                metrics['num_bboxes'] = len(all_bboxes)
                results.append(metrics)
        
        elif mode == "mask":
            for _, row in tqdm(df.iterrows(), total=len(df), desc="Evaluating"):
                mask_path = row['mask_path']
                image_path = row.get('image_path', None)
                
                metrics = self.evaluate_single_from_mask(mask_path, image_path=image_path)
                metrics['image_path'] = image_path
                metrics['mask_path'] = mask_path
                results.append(metrics)
        
        else:
            raise ValueError(f"Unknown mode: {mode}")
        
        # 创建结果 DataFrame
        results_df = pd.DataFrame(results)
        
        # 统计
        successful = results_df[results_df['success'] == True]
        
        if len(successful) > 0:
            print(f"\n{'='*70}")
            print(f"Evaluation Results")
            print(f"{'='*70}")
            print(f"Successful: {len(successful)}/{len(results_df)} images")
            print(f"\nMetrics (mean ± std):")
            print(f"  IoU       : {successful['iou'].mean():.4f} ± {successful['iou'].std():.4f}")
            print(f"  MAE       : {successful['mae'].mean():.4f} ± {successful['mae'].std():.4f}")
            print(f"  S-measure : {successful['s_measure'].mean():.4f} ± {successful['s_measure'].std():.4f}")
            print(f"  E-measure : {successful['e_measure'].mean():.4f} ± {successful['e_measure'].std():.4f}")
            print(f"{'='*70}\n")
        else:
            print("\nWarning: No successful evaluations!")
        
        # 保存结果
        if output_csv:
            results_df.to_csv(output_csv, index=False)
            print(f"Results saved to {output_csv}")
        
        return results_df


def evaluate_saliency(
    csv_path: str,
    validation_dir: str,
    output_csv: Optional[str] = None,
    mode: str = "bbox"
) -> pd.DataFrame:
    """
    便捷函数：评估 saliency 结果
    
    Args:
        csv_path: 输入 CSV 路径
        validation_dir: Ground truth masks 目录
        output_csv: 输出 CSV 路径
        mode: 评估模式 ("bbox" 或 "mask")
        
    Returns:
        pd.DataFrame: 评估结果
        
    Example:
        >>> from lumos.evaluation import evaluate_saliency
        >>> 
        >>> # 评估 bounding boxes
        >>> results = evaluate_saliency(
        ...     csv_path="bbox_results.csv",
        ...     validation_dir="validations/DUTS-TR-Mask",
        ...     output_csv="evaluation_results.csv",
        ...     mode="bbox"
        ... )
        >>> 
        >>> # 评估 SAM masks
        >>> results = evaluate_saliency(
        ...     csv_path="sam_results.csv",
        ...     validation_dir="validations/DUTS-TR-Mask",
        ...     output_csv="sam_evaluation_results.csv",
        ...     mode="mask"
        ... )
    """
    evaluator = SaliencyEvaluator(validation_dir)
    return evaluator.evaluate_from_csv(csv_path, output_csv, mode)
