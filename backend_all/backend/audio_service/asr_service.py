import json
from datetime import datetime
import whisper
import tempfile
import os
import torch
import psutil
import logging
from typing import Optional, Dict, Any
from functools import lru_cache

logger = logging.getLogger(__name__)


class WhisperASR:
    """优化的Whisper语音识别服务"""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, model_size: str = "small", device: str = "auto", cache_dir: str = "./asr_cache"):
        """
        初始化Whisper模型

        Args:
            model_size: tiny, base, small, medium, large
            device: "cpu", "cuda" or "auto"
            cache_dir: 缓存目录
        """
        # 避免重复初始化
        if hasattr(self, 'initialized') and self.initialized:
            return

        self.model_size = self._get_optimal_model_size(model_size)
        self.device = self._get_optimal_device(device)
        self.cache_dir = cache_dir

        # 创建缓存目录
        os.makedirs(self.cache_dir, exist_ok=True)

        logger.info(f"初始化WhisperASR: model={self.model_size}, device={self.device}")

        try:
            self.model = whisper.load_model(self.model_size, device=self.device)
            self.initialized = True
            logger.info("Whisper模型加载成功")
        except Exception as e:
            logger.error(f"Whisper模型加载失败: {str(e)}")
            raise

    def _get_optimal_model_size(self, model_size: str) -> str:
        """根据系统内存自动选择模型大小"""
        if model_size != "auto":
            return model_size

        memory_gb = psutil.virtual_memory().total / (1024 ** 3)

        if memory_gb < 2:
            return "tiny"
        elif memory_gb < 4:
            return "base"
        elif memory_gb < 8:
            return "small"
        elif memory_gb < 16:
            return "medium"
        else:
            return "large"

    def _get_optimal_device(self, device: str) -> str:
        """自动选择最佳计算设备"""
        if device != "auto":
            return device

        if torch.cuda.is_available():
            # 检查CUDA内存
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
            if gpu_memory > 4:  # 至少有4GB显存
                return "cuda"

        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return "mps"

        return "cpu"

    @lru_cache(maxsize=128)
    def transcribe(self, audio_path: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        语音转文字（带缓存）

        Args:
            audio_path: 音频文件路径
            language: 语言代码 (zh, en, ja等)，None为自动检测

        Returns:
            {"text": str, "language": str, "confidence": float}
        """
        # 生成缓存键
        cache_key = self._generate_cache_key(audio_path, language)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")

        # 检查缓存
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_result = json.load(f)
                logger.debug(f"使用缓存结果: {cache_key}")
                return cached_result
            except Exception as e:
                logger.warning(f"缓存读取失败: {str(e)}")

        try:
            # 设置解码参数
            decode_options = {
                "language": language,
                "task": "transcribe",
                "fp16": self.device != "cpu",
                "temperature": 0.0,
                "best_of": 3,  # 减少以提高速度
                "beam_size": 3,
                "patience": 1.0,
                "length_penalty": 1.0,
                "without_timestamps": True,
                "initial_prompt": "这是一段中文语音。" if language == "zh" else None,
            }

            # 移除空参数
            decode_options = {k: v for k, v in decode_options.items() if v is not None}

            # 执行识别
            result = self.model.transcribe(audio_path, **decode_options)

            # 处理结果
            processed_result = {
                "text": result["text"].strip(),
                "language": result.get("language", language or "auto"),
                "confidence": self._calculate_confidence(result.get("segments", [])),
                "model": self.model_size,
                "processing_time": result.get("processing_time", 0),
                "timestamp": datetime.now().isoformat()
            }

            # 保存缓存
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(processed_result, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.warning(f"缓存保存失败: {str(e)}")

            logger.info(f"语音识别完成: lang={processed_result['language']}, "
                        f"confidence={processed_result['confidence']:.2f}")

            return processed_result

        except Exception as e:
            logger.error(f"语音识别失败: {str(e)}", exc_info=True)
            raise

    def transcribe_bytes(self, audio_bytes: bytes, language: Optional[str] = None) -> Dict[str, Any]:
        """
        从字节流进行语音识别

        Args:
            audio_bytes: 音频字节流
            language: 语言代码

        Returns:
            识别结果
        """
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            tmp_file.write(audio_bytes)
            temp_path = tmp_file.name

        try:
            return self.transcribe(temp_path, language)
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"临时文件清理失败: {str(e)}")

    def _calculate_confidence(self, segments: list) -> float:
        """计算整体置信度"""
        if not segments:
            return 0.0

        confidences = [seg.get("confidence", 0.0) for seg in segments]
        return sum(confidences) / len(confidences) if confidences else 0.0

    def _generate_cache_key(self, audio_path: str, language: Optional[str]) -> str:
        """生成缓存键"""
        import hashlib

        # 基于文件内容和语言参数生成哈希
        with open(audio_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()

        lang_suffix = language or "auto"
        return f"{file_hash}_{lang_suffix}_{self.model_size}"

    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            "model": self.model_size,
            "device": self.device,
            "cache_dir": self.cache_dir,
            "initialized": self.initialized if hasattr(self, 'initialized') else False
        }


# 全局单例实例
_asr_instance = None


def get_asr_instance(**kwargs) -> WhisperASR:
    """获取ASR单例实例"""
    global _asr_instance
    if _asr_instance is None:
        _asr_instance = WhisperASR(**kwargs)
    return _asr_instance


def init_asr_service(**kwargs):
    """初始化ASR服务"""
    global _asr_instance
    if _asr_instance is None:
        try:
            _asr_instance = WhisperASR(**kwargs)
            logger.info("ASR服务初始化完成")
        except Exception as e:
            logger.error(f"ASR服务初始化失败: {str(e)}")
            raise
    return _asr_instance