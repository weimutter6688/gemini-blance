# app/services/chat/stream_optimizer.py

import asyncio
import math
from typing import Any, AsyncGenerator, Callable, List

from app.config.config import settings
from app.core.constants import (
    DEFAULT_STREAM_CHUNK_SIZE,
    DEFAULT_STREAM_LONG_TEXT_THRESHOLD,
    DEFAULT_STREAM_MAX_DELAY,
    DEFAULT_STREAM_MIN_DELAY,
    DEFAULT_STREAM_SHORT_TEXT_THRESHOLD,
)
from app.log.logger import get_gemini_logger, get_openai_logger

logger_openai = get_openai_logger()
logger_gemini = get_gemini_logger()


class StreamOptimizer:
    """流式输出优化器

    提供流式输出优化功能，包括智能延迟调整和长文本分块输出。
    """

    def __init__(
        self,
        logger=None,
        min_delay: float = DEFAULT_STREAM_MIN_DELAY,
        max_delay: float = DEFAULT_STREAM_MAX_DELAY,
        short_text_threshold: int = DEFAULT_STREAM_SHORT_TEXT_THRESHOLD,
        long_text_threshold: int = DEFAULT_STREAM_LONG_TEXT_THRESHOLD,
        chunk_size: int = DEFAULT_STREAM_CHUNK_SIZE,
    ):
        """初始化流式输出优化器

        参数:
            logger: 日志记录器
            min_delay: 最小延迟时间（秒）
            max_delay: 最大延迟时间（秒）
            short_text_threshold: 短文本阈值（字符数）
            long_text_threshold: 长文本阈值（字符数）
            chunk_size: 长文本分块大小（字符数）
        """
        self.logger = logger
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.short_text_threshold = short_text_threshold
        self.long_text_threshold = long_text_threshold
        self.chunk_size = chunk_size

    def calculate_delay(self, text_length: int) -> float:
        """根据文本长度计算延迟时间

        参数:
            text_length: 文本长度

        返回:
            延迟时间（秒）
        """
        if text_length <= self.short_text_threshold:
            # 短文本使用较大延迟
            return self.max_delay
        elif text_length >= self.long_text_threshold:
            # 长文本使用较小延迟
            return self.min_delay
        else:
            # 中等长度文本使用线性插值计算延迟
            # 使用对数函数使延迟变化更平滑
            ratio = math.log(text_length / self.short_text_threshold) / math.log(
                self.long_text_threshold / self.short_text_threshold
            )
            return self.max_delay - ratio * (self.max_delay - self.min_delay)

    def split_text_into_chunks(self, text: str) -> List[str]:
        """将文本分割成小块

        参数:
            text: 要分割的文本

        返回:
            文本块列表
        """
        return [
            text[i : i + self.chunk_size] for i in range(0, len(text), self.chunk_size)
        ]

    async def optimize_stream_output(
        self,
        text: str,
        create_response_chunk: Callable[[str], Any],
        format_chunk: Callable[[Any], str],
    ) -> AsyncGenerator[str, None]:
        """优化流式输出

        参数:
            text: 要输出的文本
            create_response_chunk: 创建响应块的函数，接收文本，返回响应块
            format_chunk: 格式化响应块的函数，接收响应块，返回格式化后的字符串

        返回:
            异步生成器，生成格式化后的响应块
        """
        if not text:
            return

        # 计算智能延迟时间
        delay = self.calculate_delay(len(text))
        # if self.logger:
        #     self.logger.info(f"Text length: {len(text)}, delay: {delay:.4f}s")

        # 根据文本长度决定输出方式
        if len(text) >= self.long_text_threshold:
            # 长文本：分块输出
            chunks = self.split_text_into_chunks(text)
            # if self.logger:
            #     self.logger.info(f"Long text: splitting into {len(chunks)} chunks")
            for chunk_text in chunks:
                chunk_response = create_response_chunk(chunk_text)
                yield format_chunk(chunk_response)
                await asyncio.sleep(delay)
        else:
            # 短文本：逐字符输出
            for char in text:
                char_chunk = create_response_chunk(char)
                yield format_chunk(char_chunk)
                await asyncio.sleep(delay)


# 创建默认的优化器实例，可以直接导入使用
openai_optimizer = StreamOptimizer(
    logger=logger_openai,
    min_delay=settings.STREAM_MIN_DELAY,
    max_delay=settings.STREAM_MAX_DELAY,
    short_text_threshold=settings.STREAM_SHORT_TEXT_THRESHOLD,
    long_text_threshold=settings.STREAM_LONG_TEXT_THRESHOLD,
    chunk_size=settings.STREAM_CHUNK_SIZE,
)

gemini_optimizer = StreamOptimizer(
    logger=logger_gemini,
    min_delay=settings.STREAM_MIN_DELAY,
    max_delay=settings.STREAM_MAX_DELAY,
    short_text_threshold=settings.STREAM_SHORT_TEXT_THRESHOLD,
    long_text_threshold=settings.STREAM_LONG_TEXT_THRESHOLD,
    chunk_size=settings.STREAM_CHUNK_SIZE,
)
