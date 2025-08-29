from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from PIL import Image, ImageDraw
import requests
from io import BytesIO
import os
import base64
import warnings
warnings.filterwarnings('ignore')

# 移除cairosvg依赖，使用svglib作为唯一的SVG处理库
try:
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPM
    SVGLIB_AVAILABLE = True
except ImportError:
    SVGLIB_AVAILABLE = False
    print("Warning: SVG processing libraries not installed, SVG conversion will not be available")

from openai import OpenAI
import re
import math
# 导入面料纹理模块
from fabric_texture import apply_fabric_texture
import uuid
import json
# 导入并行处理库
import concurrent.futures
import time
import threading
import random
from datetime import datetime
from functools import wraps
# 导入阿里云DashScope文生图API
from http import HTTPStatus
from urllib.parse import urlparse, unquote
from pathlib import PurePosixPath
try:
    from dashscope import ImageSynthesis
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False
    print("Warning: DashScope not installed, will use OpenAI DALL-E as fallback")

# API配置信息 - 多个API密钥用于增强并发能力
# DALL-E API密钥（目前未使用，保留备用）
API_KEYS = [
    "sk-lNVAREVHjj386FDCd9McOL7k66DZCUkTp6IbV0u9970qqdlg",
    "sk-y8x6LH0zdtyQncT0aYdUW7eJZ7v7cuKTp90L7TiK3rPu3fAg", 
    "sk-Kp59pIj8PfqzLzYaAABh2jKsQLB0cUKU3n8l7TIK3rpU61QG",
    "sk-KACPocnavR6poutXUaj7HxsqUrxvcV808S2bv0U9974Ec83g",
    "sk-YknuN0pb6fKBOP6xFOqAdeeqhoYkd1cEl9380vC5HHeC2B30"
]
BASE_URL = "https://api.deepbricks.ai/v1/"

# GPT-4o-mini API配置 - 多个密钥用于高并发
GPT4O_MINI_API_KEYS = [
    "sk-lNVAREVHjj386FDCd9McOL7k66DZCUkTp6IbV0u9970qqdlg",
    "sk-y8x6LH0zdtyQncT0aYdUW7eJZ7v7cuKTp90L7TiK3rPu3fAg",
    "sk-Kp59pIj8PfqzLzYaAABh2jKsQLB0cUKU3n8l7TIK3rpU61QG", 
    "sk-KACPocnavR6poutXUaj7HxsqUrxvcV808S2bv0U9974Ec83g",
    "sk-YknuN0pb6fKBOP6xFOqAdeeqhoYkd1cEl9380vC5HHeC2B30",
    "sk-qgTzuaTw8LA8aaMuKHGNKTzklfILd2O4f3J80Vc1e716UNRG",
    "sk-NomBvwwNzPxLsQJYPrDhCUMoxe5hD2O4f4380VC3ibspPV50",
    "sk-J1STQi1Z7MVWZCkCXMhUTDtgYvuED2O4F4j80vc1E716uNt0",
    "sk-TB2wg0E6NAUfs3cxuuO7MmB1xHtrd2O4f5380vc3ibSPPv8G",
    "sk-JnAylOqL4tRKkdoNqNuUyzOGsqt8d2O4f5380vc3IBsPPv9G",
    "sk-b21I1MNl27hobxJ4B0ZFzCokwVF2d2O4f5B80VC1e716unVG",
    "sk-fMFkcOX0Pee9ecGWa73fdHU6tSjPD2o4F5J80Vc1e716uO10",
    "sk-BxN7ncNBMmyoy9FiRhgNkRrAegELD2O4F5r80vC3ibSpPvDG",
    "sk-Eun0GvNO0xUWm7EfprCGPukeTSHJD2O4F6380VC1E716Uo2g",
    "sk-c4rdtdCaZ4XZt92zKF8WiqGuf95Gd2o4F6B80vc3iBsPpVfg",
    "sk-QMCiQzJW0iMr3z3vr7FPxTWvfuQwd2o4hJr80vC1e716v060",
    "sk-b5eYKA5L5FPtoHFY3IhoJcE9cxwid2o4HgJ80vC3iBsPq7d0",
    "sk-OwECm6sctSh4lc8ZjMazIgKbW369D2O4hgb80vC3ibSPQ7bg",
    "sk-2G1gAKU00wK7Rt9cxJdErScYkNtSd2o4Hgb80vc3IBspQ7Ag",
    "sk-j3KSILShr68o3W9HOJPKBBzzmtjWd2oipAj4pp5CU06a44E0"
]
GPT4O_MINI_BASE_URL = "https://api.deepbricks.ai/v1/"

# 阿里云DashScope API配置 - 多个密钥用于增强并发能力
DASHSCOPE_API_KEYS = [
    "sk-1a19e43ed59443ae86c39041a194c17c",
    "sk-787d18eec7c2403ca5bcf4595cfff038", 
    "sk-51a3e204ed83484db3b44e12d81c143e",
    "sk-3f579673c4724c06a680f80246c2c90e",
    "sk-4ff1a99e019d4a25bef0762e716a55d5",
    "sk-4f82c6e2097440f8adb2ef688c7c7551",
    "sk-0d467c953af4433aa8bda24d5f4cc855",
    "sk-88a12822ab324befb510b4182cf84940",
    "sk-fc2dc196273342829029226faf8a6e64",
    "sk-6c561648158845498bd79405450ebcd1",
    "sk-b02c07bd5ba54037999d2f0980d4042a",
    "sk-7d8815e45a164bc09ed8f2a346ed00e1",
    "sk-39e94c32f421425b9221eae1b7f68918",
    "sk-551f4ccb2ad647a6834865732d42edcb",
    "sk-cdbe9b620dc04666aaf50fd44d8a756e",
    "sk-413b21a29e824d52ba3c59ae14ba7788",
    "sk-aebba67427b7494fa2e4f6c411dac362",
    "sk-b894e6b45ab14f63b578157f869b8bb4",
    "sk-dc84e80f08a84114a1e97a2e755c43d6",
    "sk-4ae00d04248d48d581f4ce316837fe87"
]

# API密钥轮询计数器
_api_key_counter = 0
_gpt4o_api_key_counter = 0
_dashscope_api_key_counter = 0
_api_lock = threading.Lock()

# 全局AI调用记录统计
_ai_call_records = []
_call_records_lock = threading.Lock()

# DashScope调用限流控制 - 2次/秒限制
_dashscope_call_times = []
_dashscope_rate_lock = threading.Lock()
_dashscope_wait_times = []  # 记录等待时间统计
DASHSCOPE_MAX_CALLS_PER_SECOND = 2
DASHSCOPE_TIME_WINDOW = 1.0  # 1秒时间窗口

def wait_for_dashscope_rate_limit():
    """DashScope调用限流控制 - 确保每秒不超过2次调用"""
    with _dashscope_rate_lock:
        current_time = time.time()
        
        # 清理超过时间窗口的调用记录
        _dashscope_call_times[:] = [t for t in _dashscope_call_times if current_time - t < DASHSCOPE_TIME_WINDOW]
        
        # 如果当前时间窗口内的调用数已达上限
        if len(_dashscope_call_times) >= DASHSCOPE_MAX_CALLS_PER_SECOND:
            # 计算需要等待的时间
            oldest_call = min(_dashscope_call_times)
            wait_time = DASHSCOPE_TIME_WINDOW - (current_time - oldest_call)
            
            if wait_time > 0:
                log(f"DashScope限流等待 wait_time={wait_time:.3f}s current_calls={len(_dashscope_call_times)}")
                _dashscope_wait_times.append(wait_time)  # 记录等待时间
                time.sleep(wait_time)
                
                # 重新获取当前时间并清理记录
                current_time = time.time()
                _dashscope_call_times[:] = [t for t in _dashscope_call_times if current_time - t < DASHSCOPE_TIME_WINDOW]
        
        # 记录当前调用时间
        _dashscope_call_times.append(current_time)
        log(f"DashScope调用许可 current_calls_in_window={len(_dashscope_call_times)}")
        return current_time

def add_ai_call_record(api_type, model, api_key, start_time, end_time, status, reason=None, attempt=1):
    """添加AI调用记录"""
    with _call_records_lock:
        record = {
            'api_type': api_type,  # 'GPT-4o-mini' 或 'DashScope'
            'model': model,
            'api_key': _mask_key(api_key),
            'start_time': start_time,
            'end_time': end_time,
            'start_time_str': time.strftime('%H:%M:%S', time.localtime(start_time)) + f'.{int((start_time % 1) * 1000):03d}',
            'end_time_str': time.strftime('%H:%M:%S', time.localtime(end_time)) + f'.{int((end_time % 1) * 1000):03d}',
            'duration_ms': (end_time - start_time) * 1000,
            'status': status,  # 'success', 'failed', 'retry'
            'reason': reason,  # 失败或重试原因
            'attempt': attempt
        }
        _ai_call_records.append(record)

def print_ai_call_summary():
    """打印AI调用汇总报告"""
    with _call_records_lock:
        if not _ai_call_records:
            log("AI调用汇总：无调用记录")
            return
        
        log("=" * 80)
        log("🚀 AI调用汇总报告")
        log("=" * 80)
        
        # 按API类型分组统计
        gpt4o_calls = [r for r in _ai_call_records if r['api_type'] == 'GPT-4o-mini']
        dashscope_calls = [r for r in _ai_call_records if r['api_type'] == 'DashScope']
        
        # GPT-4o-mini统计
        if gpt4o_calls:
            log(f"📊 GPT-4o-mini调用统计 (共{len(gpt4o_calls)}次):")
            success_count = len([r for r in gpt4o_calls if r['status'] == 'success'])
            failed_count = len([r for r in gpt4o_calls if r['status'] == 'failed'])
            retry_count = len([r for r in gpt4o_calls if r['status'] == 'retry'])
            total_duration = sum(r['duration_ms'] for r in gpt4o_calls)
            avg_duration = total_duration / len(gpt4o_calls) if gpt4o_calls else 0
            
            log(f"  ✅ 成功: {success_count}次 | ❌ 失败: {failed_count}次 | 🔄 重试: {retry_count}次")
            log(f"  ⏱️  总耗时: {total_duration:.1f}ms | 平均: {avg_duration:.1f}ms")
            
            # 失败原因统计
            failure_reasons = {}
            for record in gpt4o_calls:
                if record['status'] in ['failed', 'retry'] and record['reason']:
                    failure_reasons[record['reason']] = failure_reasons.get(record['reason'], 0) + 1
            
            if failure_reasons:
                log(f"  🚨 失败原因分布: {failure_reasons}")
            
            # 详细调用记录
            for i, record in enumerate(gpt4o_calls, 1):
                status_icon = "✅" if record['status'] == 'success' else "❌" if record['status'] == 'failed' else "🔄"
                reason_text = f" ({record['reason']})" if record['reason'] else ""
                log(f"    {i:2d}. {status_icon} key={record['api_key']} 发送={record['start_time_str']} 接收={record['end_time_str']} duration={record['duration_ms']:.1f}ms attempt={record['attempt']}{reason_text}")
        
        # DashScope统计
        if dashscope_calls:
            log(f"\n📊 DashScope调用统计 (共{len(dashscope_calls)}次):")
            success_count = len([r for r in dashscope_calls if r['status'] == 'success'])
            failed_count = len([r for r in dashscope_calls if r['status'] == 'failed'])
            retry_count = len([r for r in dashscope_calls if r['status'] == 'retry'])
            total_duration = sum(r['duration_ms'] for r in dashscope_calls)
            avg_duration = total_duration / len(dashscope_calls) if dashscope_calls else 0
            
            log(f"  ✅ 成功: {success_count}次 | ❌ 失败: {failed_count}次 | 🔄 重试: {retry_count}次")
            log(f"  ⏱️  总耗时: {total_duration:.1f}ms | 平均: {avg_duration:.1f}ms")
            
            # 限流统计
            if _dashscope_wait_times:
                total_wait_time = sum(_dashscope_wait_times)
                avg_wait_time = total_wait_time / len(_dashscope_wait_times)
                max_wait_time = max(_dashscope_wait_times)
                log(f"  🚦 限流统计: 等待{len(_dashscope_wait_times)}次 | 总等待: {total_wait_time:.3f}s | 平均: {avg_wait_time:.3f}s | 最长: {max_wait_time:.3f}s")
            else:
                log(f"  🚦 限流统计: 无等待 (调用频率在限制范围内)")
            
            # 失败原因统计
            failure_reasons = {}
            for record in dashscope_calls:
                if record['status'] in ['failed', 'retry'] and record['reason']:
                    failure_reasons[record['reason']] = failure_reasons.get(record['reason'], 0) + 1
            
            if failure_reasons:
                log(f"  🚨 失败原因分布: {failure_reasons}")
            
            # 详细调用记录
            for i, record in enumerate(dashscope_calls, 1):
                status_icon = "✅" if record['status'] == 'success' else "❌" if record['status'] == 'failed' else "🔄"
                reason_text = f" ({record['reason']})" if record['reason'] else ""
                log(f"    {i:2d}. {status_icon} key={record['api_key']} 发送={record['start_time_str']} 接收={record['end_time_str']} duration={record['duration_ms']:.1f}ms attempt={record['attempt']}{reason_text}")
        
        # 总体统计
        total_calls = len(_ai_call_records)
        total_success = len([r for r in _ai_call_records if r['status'] == 'success'])
        total_failed = len([r for r in _ai_call_records if r['status'] == 'failed'])
        total_retry = len([r for r in _ai_call_records if r['status'] == 'retry'])
        overall_duration = sum(r['duration_ms'] for r in _ai_call_records)
        success_rate = (total_success / total_calls * 100) if total_calls > 0 else 0
        
        log(f"\n📈 总体统计:")
        log(f"  🎯 总调用: {total_calls}次 | 成功率: {success_rate:.1f}%")
        log(f"  ✅ 成功: {total_success}次 | ❌ 失败: {total_failed}次 | 🔄 重试: {total_retry}次")
        log(f"  ⏱️  总耗时: {overall_duration:.1f}ms")
        
        log("=" * 80)

def clear_ai_call_records():
    """清空AI调用记录"""
    with _call_records_lock:
        _ai_call_records.clear()
    # 同时清空限流统计
    with _dashscope_rate_lock:
        _dashscope_wait_times.clear()

# 设置默认生成的设计数量
DEFAULT_DESIGN_COUNT = 15

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # 在生产环境中使用更安全的密钥

# 配置CORS以支持Railway部署和跨域请求
CORS(app, 
     origins=["*"],  # 在生产环境中应该限制为具体域名
     methods=["GET", "POST", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"],
     supports_credentials=True)

# 统一日志工具：带毫秒时间戳与线程名
def _mask_key(key: str) -> str:
    try:
        if not key:
            return "<none>"
        return f"{key[:6]}...{key[-4:]}"
    except Exception:
        return "<hidden>"

def log(message: str) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    thread_name = threading.current_thread().name
    print(f"[{now}] [thread={thread_name}] {message}", flush=True)

def log_step(name: str = None):
    def decorator(func):
        step_name = name or func.__name__
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            log(f"{step_name} START")
            try:
                result = func(*args, **kwargs)
                elapsed_ms = (time.time() - start) * 1000
                log(f"{step_name} END {elapsed_ms:.1f}ms")
                return result
            except Exception as e:
                elapsed_ms = (time.time() - start) * 1000
                log(f"{step_name} ERROR {elapsed_ms:.1f}ms: {e}")
                raise
        return wrapper
    return decorator

def get_next_api_key():
    """获取下一个DALL-E API密钥（轮询方式）"""
    global _api_key_counter
    with _api_lock:
        key = API_KEYS[_api_key_counter % len(API_KEYS)]
        _api_key_counter += 1
        return key

def get_next_gpt4o_api_key():
    """获取下一个GPT-4o-mini API密钥（轮询方式）"""
    global _gpt4o_api_key_counter
    with _api_lock:
        key = GPT4O_MINI_API_KEYS[_gpt4o_api_key_counter % len(GPT4O_MINI_API_KEYS)]
        _gpt4o_api_key_counter += 1
        return key

def get_next_dashscope_api_key():
    """获取下一个DashScope API密钥（轮询方式）"""
    global _dashscope_api_key_counter
    with _api_lock:
        key = DASHSCOPE_API_KEYS[_dashscope_api_key_counter % len(DASHSCOPE_API_KEYS)]
        _dashscope_api_key_counter += 1
        return key

def make_background_transparent(image, threshold=100):
    """
    将图像的白色/浅色背景转换为透明背景
    
    Args:
        image: PIL图像对象，RGBA模式
        threshold: 背景色识别阈值，数值越大识别的背景范围越大
    
    Returns:
        处理后的PIL图像对象，透明背景
    """
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # 获取图像数据
    data = image.getdata()
    new_data = []
    
    # 分析四个角落的颜色来确定背景色
    width, height = image.size
    corner_pixels = [
        image.getpixel((0, 0)),           # 左上角
        image.getpixel((width-1, 0)),     # 右上角
        image.getpixel((0, height-1)),    # 左下角
        image.getpixel((width-1, height-1)) # 右下角
    ]
    
    # 计算平均背景颜色（假设四个角都是背景）
    bg_r = sum(p[0] for p in corner_pixels) // 4
    bg_g = sum(p[1] for p in corner_pixels) // 4
    bg_b = sum(p[2] for p in corner_pixels) // 4
    
    log(f"检测到的背景颜色: RGB({bg_r}, {bg_g}, {bg_b})")
    
    # 遍历所有像素
    transparent_count = 0
    for item in data:
        r, g, b, a = item
        
        # 计算当前像素与背景色的差异
        diff = abs(r - bg_r) + abs(g - bg_g) + abs(b - bg_b)
        
        # 另外检查是否是浅色（可能是背景）
        brightness = (r + g + b) / 3
        is_light = brightness > 180  # 亮度大于180认为是浅色
        
        # 检查是否接近灰白色
        gray_similarity = abs(r - g) + abs(g - b) + abs(r - b)
        is_grayish = gray_similarity < 30  # 颜色差异小说明是灰色系
        
        # 如果差异小于阈值或者是浅色灰白色，认为是背景，设为透明
        if diff < threshold or (is_light and is_grayish):
            new_data.append((r, g, b, 0))  # 完全透明
            transparent_count += 1
        else:
            # 否则保持原像素
            new_data.append((r, g, b, a))
    
    log(f"透明化了 {transparent_count} 个像素，占总像素的 {transparent_count/(image.size[0]*image.size[1])*100:.1f}%")
    
    # 创建新图像
    transparent_image = Image.new('RGBA', image.size)
    transparent_image.putdata(new_data)
    
    return transparent_image

def calculate_color_brightness(rgb_color):
    """计算RGB颜色的感知亮度 (0-255)
    使用标准感知亮度公式：0.299*R + 0.587*G + 0.114*B
    """
    if isinstance(rgb_color, str):
        # 处理十六进制颜色
        rgb_color = rgb_color.lstrip('#')
        r = int(rgb_color[0:2], 16)
        g = int(rgb_color[2:4], 16)
        b = int(rgb_color[4:6], 16)
    elif isinstance(rgb_color, (tuple, list)):
        r, g, b = rgb_color[:3]
    else:
        return 128  # 默认中等亮度
    
    # 使用感知亮度公式
    brightness = 0.299 * r + 0.587 * g + 0.114 * b
    return brightness

def calculate_contrast_ratio(color1, color2):
    """计算两个颜色之间的对比度比率 (WCAG标准)
    返回值范围：1.0 (无对比度) 到 21.0 (最大对比度)
    """
    # 计算相对亮度 (0.0 - 1.0)
    def relative_luminance(rgb):
        if isinstance(rgb, str):
            rgb = rgb.lstrip('#')
            r = int(rgb[0:2], 16) / 255.0
            g = int(rgb[2:4], 16) / 255.0
            b = int(rgb[4:6], 16) / 255.0
        else:
            r, g, b = [c/255.0 for c in rgb[:3]]
        
        # 应用gamma校正
        def gamma_correct(c):
            if c <= 0.03928:
                return c / 12.92
            else:
                return pow((c + 0.055) / 1.055, 2.4)
        
        return 0.2126 * gamma_correct(r) + 0.7152 * gamma_correct(g) + 0.0722 * gamma_correct(b)
    
    lum1 = relative_luminance(color1)
    lum2 = relative_luminance(color2)
    
    # 确保较亮的颜色作为分子
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    
    # 对比度公式
    contrast = (lighter + 0.05) / (darker + 0.05)
    return contrast

def is_dark_color(color):
    """判断颜色是否为深色 (亮度 < 128)"""
    brightness = calculate_color_brightness(color)
    return brightness < 128

def get_contrasting_color_description(shirt_color, min_contrast_ratio=4.5):
    """根据T恤颜色生成对比色描述，用于logo生成提示词
    
    Args:
        shirt_color: T恤颜色 (hex或rgb)
        min_contrast_ratio: 最小对比度要求 (默认4.5符合WCAG AA标准)
    
    Returns:
        dict: 包含颜色描述和具体颜色建议的字典
    """
    shirt_brightness = calculate_color_brightness(shirt_color)
    is_dark_shirt = shirt_brightness < 128
    
    log(f"T恤颜色分析 color={shirt_color} brightness={shirt_brightness:.1f} is_dark={is_dark_shirt}")
    
    if is_dark_shirt:
        # 深色T恤 - 使用亮色logo
        return {
            "color_description": "bright, light-colored, high-contrast white or light colors",
            "specific_colors": "white, light gray, bright yellow, light blue, or cream",
            "avoid_colors": "dark colors, black, navy, dark gray",
            "contrast_type": "light_on_dark",
            "additional_effects": "add subtle white outline or glow effect for extra visibility"
        }
    else:
        # 浅色T恤 - 使用深色logo
        return {
            "color_description": "dark, bold-colored, high-contrast black or dark colors", 
            "specific_colors": "black, dark gray, navy blue, dark green, or deep purple",
            "avoid_colors": "light colors, white, light gray, pale colors",
            "contrast_type": "dark_on_light",
            "additional_effects": "use solid, bold colors with clean edges"
        }

def convert_svg_to_png(svg_content):
    """
    将SVG内容转换为PNG格式的PIL图像对象
    使用svglib库来处理，不再依赖cairosvg
    """
    try:
        if SVGLIB_AVAILABLE:
            # 使用svglib将SVG内容转换为PNG
            from io import BytesIO
            svg_bytes = BytesIO(svg_content)
            drawing = svg2rlg(svg_bytes)
            png_bytes = BytesIO()
            renderPM.drawToFile(drawing, png_bytes, fmt="PNG")
            png_bytes.seek(0)
            return Image.open(png_bytes).convert("RGBA")
        else:
            log("Error: SVG conversion libraries not available. Please install svglib and reportlab.")
            return None
    except Exception as e:
        log(f"Error converting SVG to PNG: {str(e)}")
        return None

@log_step("load_original_tshirt_image")
def load_original_tshirt_image():
    """并发可调用：查找并加载白色T恤底图为RGBA。找不到则抛出异常。"""
    original_image_path = "white_shirt.png"
    possible_paths = [
        "white_shirt.png",
        "./white_shirt.png",
        "../white_shirt.png",
        "images/white_shirt.png",
    ]
    found = False
    for path in possible_paths:
        if os.path.exists(path):
            original_image_path = path
            found = True
            break
    if not found:
        raise FileNotFoundError("Could not find base T-shirt image")
    img = Image.open(original_image_path).convert("RGBA")
    log(f"加载T恤底图: {original_image_path} size={img.size}")
    return img

@log_step("get_ai_design_suggestions")
def get_ai_design_suggestions(user_preferences=None, max_retries=3):
    """Get design suggestions from GPT-4o-mini with more personalized features
    
    使用轮询机制从20个GPT-4o API密钥中选择，支持最高并发设计建议生成
    当遇到401错误时自动重试下一个密钥
    """
    # Default prompt if no user preferences provided
    if not user_preferences:
        user_preferences = "casual fashion t-shirt design"
    
    # Construct the prompt
    prompt = f"""
    As a design consultant, please provide personalized design suggestions for a "{user_preferences}" style.
    
    Please provide the following design suggestions in JSON format:

    1. Color: Select the most suitable color for this style (provide name and hex code)
    2. Fabric: Select the most suitable fabric type (Cotton, Polyester, Cotton-Polyester Blend, Jersey, Linen, or Bamboo)
    3. Text: A suitable phrase or slogan that matches the style (keep it concise and impactful)
    4. Logo: A brief description of a logo element that would complement the design

    Return your response as a valid JSON object with the following structure:
    {{
        "color": {{
            "name": "Color name",
            "hex": "#XXXXXX"
        }},
        "fabric": "Fabric type",
        "text": "Suggested text or slogan",
        "logo": "Logo/graphic description"
    }}
    """
    
    # 重试统计
    retry_reasons = []
    start_time = time.time()
    
    # 重试机制：尝试多个API密钥
    for attempt in range(max_retries):
        api_key = get_next_gpt4o_api_key()
        api_start = time.time()
        try:
            log(f"AI建议请求 attempt={attempt+1} key={_mask_key(api_key)}")
            client = OpenAI(api_key=api_key, base_url=GPT4O_MINI_BASE_URL)
            
            # 调用GPT-4o-mini
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a professional design consultant. Provide design suggestions in JSON format exactly as requested."},
                    {"role": "user", "content": prompt}
                ]
            )
            api_end = time.time()
            api_duration = (api_end - api_start) * 1000
            log(f"AI建议响应 duration={api_duration:.1f}ms")
            
            # 返回建议内容
            if response.choices and len(response.choices) > 0:
                suggestion_text = response.choices[0].message.content
                log(f"AI建议解析 length={len(suggestion_text) if suggestion_text else 0}字符")
                
                # 尝试解析JSON
                try:
                    # 查找JSON格式的内容
                    json_match = re.search(r'```json\s*(.*?)\s*```', suggestion_text, re.DOTALL)
                    if json_match:
                        suggestion_json = json.loads(json_match.group(1))
                    else:
                        # 尝试直接解析整个内容
                        suggestion_json = json.loads(suggestion_text)
                    
                    # 记录成功调用
                    add_ai_call_record('GPT-4o-mini', 'gpt-4o-mini', api_key, api_start, api_end, 'success', attempt=attempt+1)
                    
                    total_duration = (time.time() - start_time) * 1000
                    if retry_reasons:
                        log(f"AI建议成功 总耗时={total_duration:.1f}ms 重试={len(retry_reasons)}次 原因={retry_reasons}")
                    else:
                        log(f"AI建议成功 耗时={total_duration:.1f}ms 无重试")
                    return suggestion_json
                except Exception as e:
                    log(f"JSON解析失败: {e}")
                    return {"error": f"Failed to parse design suggestions: {str(e)}"}
            else:
                return {"error": "Failed to get AI design suggestions. Please try again later."}
                
        except Exception as e:
            error_str = str(e)
            api_end = time.time()
            retry_time = (time.time() - start_time) * 1000
            
            # 检查是否是401错误（无效API密钥）
            if "401" in error_str or "invalid api key" in error_str.lower() or "invalid_api_key" in error_str:
                reason = "401无效密钥"
                retry_reasons.append(f"{reason}@{retry_time:.0f}ms")
                log(f"AI建议重试 attempt={attempt+1}/{max_retries} reason={reason} time={retry_time:.1f}ms")
                
                # 记录重试调用
                if attempt < max_retries - 1:
                    add_ai_call_record('GPT-4o-mini', 'gpt-4o-mini', api_key, api_start, api_end, 'retry', reason, attempt+1)
                    continue  # 尝试下一个密钥
                else:
                    # 记录最终失败调用
                    add_ai_call_record('GPT-4o-mini', 'gpt-4o-mini', api_key, api_start, api_end, 'failed', reason, attempt+1)
                    log(f"AI建议失败 重试汇总={retry_reasons}")
                    return {"error": f"所有GPT-4o API密钥都无效，请检查密钥配置: {error_str}"}
            else:
                # 其他错误，直接返回
                reason = "其他错误"
                retry_reasons.append(f"{reason}@{retry_time:.0f}ms")
                # 记录失败调用
                add_ai_call_record('GPT-4o-mini', 'gpt-4o-mini', api_key, api_start, api_end, 'failed', reason, attempt+1)
                log(f"AI建议失败 重试汇总={retry_reasons} 最终错误={error_str}")
                return {"error": f"Error getting AI design suggestions: {error_str}"}
    
    # 如果所有重试都失败
    total_duration = (time.time() - start_time) * 1000
    log(f"AI建议彻底失败 总耗时={total_duration:.1f}ms 重试汇总={retry_reasons}")
    return {"error": "Failed to get AI design suggestions after multiple retries"}

def is_valid_logo(image, min_colors=2, min_non_transparent_pixels=300, max_dominant_ratio=0.985):
    """检查生成的logo是否有效（不是纯色或空白图像）"""
    if image is None:
        return False
    
    try:
        # 转换为RGBA模式以便分析
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # 获取所有像素数据
        pixels = list(image.getdata())
        
        # 统计非透明像素
        non_transparent_pixels = [p for p in pixels if len(p) >= 4 and p[3] > 50]  # alpha > 50
        
        # 检查是否有足够的非透明像素
        if len(non_transparent_pixels) < min_non_transparent_pixels:
            print(f"Logo验证失败：非透明像素数量不足 ({len(non_transparent_pixels)} < {min_non_transparent_pixels})")
            return False
        
        # 统计颜色数量（忽略透明像素）
        unique_colors = set()
        for pixel in non_transparent_pixels:
            # 只考虑RGB值，忽略alpha
            rgb = (pixel[0], pixel[1], pixel[2])
            unique_colors.add(rgb)
        
        # 检查颜色多样性
        if len(unique_colors) < min_colors:
            print(f"Logo验证失败：颜色数量不足 ({len(unique_colors)} < {min_colors})")
            return False
        
        # 检查是否为纯色图像（所有非透明像素颜色相似）
        if len(unique_colors) == 1:
            print("Logo验证失败：图像为纯色")
            return False
        
        # 检查颜色分布是否过于单一（主要颜色占比过高）
        color_counts = {}
        for pixel in non_transparent_pixels:
            rgb = (pixel[0], pixel[1], pixel[2])
            color_counts[rgb] = color_counts.get(rgb, 0) + 1
        
        # 找到最常见的颜色
        most_common_color_count = max(color_counts.values())
        dominant_color_ratio = most_common_color_count / len(non_transparent_pixels)
        
        # 如果单一颜色占比超过95%，认为是无效logo
        if dominant_color_ratio > max_dominant_ratio:
            print(f"Logo验证失败：主要颜色占比过高 ({dominant_color_ratio:.2%} > {max_dominant_ratio:.2%})")
            return False
        
        print(f"Logo验证通过：{len(unique_colors)}种颜色，{len(non_transparent_pixels)}个非透明像素，主要颜色占比{dominant_color_ratio:.2%}")
        return True
        
    except Exception as e:
        print(f"Logo验证过程中出错: {e}")
        return False

def generate_vector_image(prompt, background_color=None, max_retries=3, shirt_color=None):
    """Generate a vector-style logo with transparent background using DashScope API with validation and retry
    
    使用轮询机制从20个DashScope API密钥中选择，支持高并发并行生成提高效率
    
    Args:
        prompt: 基础logo描述
        background_color: 背景颜色（已弃用，保留兼容性）
        max_retries: 最大重试次数
        shirt_color: T恤颜色，用于智能对比度调整
    """
    
    # 获取对比色描述（如果提供了T恤颜色）
    contrast_info = None
    color_requirements = ""
    
    if shirt_color:
        contrast_info = get_contrasting_color_description(shirt_color)
        log(f"Logo对比色适配 shirt_color={shirt_color} contrast_type={contrast_info['contrast_type']}")
        
        # 根据T恤颜色调整颜色要求
        if contrast_info['contrast_type'] == 'light_on_dark':
            # 深色T恤 - 使用亮色logo
            color_requirements = f"""
    颜色要求（深色T恤适配）：
    - 主色调必须使用亮色：{contrast_info['specific_colors']}
    - 严格避免：{contrast_info['avoid_colors']}
    - 添加白色或浅色描边增强对比度
    - 使用高饱和度亮色确保可见性
    - 可适当添加发光效果或白边轮廓"""
        else:
            # 浅色T恤 - 使用深色logo
            color_requirements = f"""
    颜色要求（浅色T恤适配）：
    - 主色调必须使用深色：{contrast_info['specific_colors']}
    - 严格避免：{contrast_info['avoid_colors']}
    - 使用深色粗描边增强轮廓
    - 颜色饱和度高，对比强烈
    - 实心色块设计，避免浅色填充"""
    else:
        # 默认通用颜色要求
        color_requirements = """
    通用颜色要求：
    - 极高对比度，颜色饱和鲜明
    - 深色轮廓+亮色填充，确保在任何背景都清晰
    - 颜色至少三种，包含深色边框"""
    
    # 构建智能颜色适配的矢量图logo专用提示词
    vector_style_prompt = f"""创建一个矢量风格的logo设计: {prompt}
    
    基础要求:
    1. 简洁的矢量图风格，线条清晰、闭合、边缘净
    2. 必须是透明背景(透明PNG)，无背板、无渐变底、无阴影
    3. 专业的logo设计，适合印刷到T恤，避免过多细碎噪点
    4. 几何形状简洁，不要过于复杂，中心构图
    5. 不要包含文字或字母
    6. 不要显示T恤或服装模型
    7. 纯粹的图形标志设计
    8. 矢量插画风格，扁平化设计，实心色块
    9. 背景必须完全透明，不要留边缘白边/灰边
    10. 输出PNG透明背景图标，尺寸768x768
    11. 图标应独立，无任何背景元素，不要样机/预览
    {color_requirements}"""
    
    # 如果DashScope不可用，直接返回None
    if not DASHSCOPE_AVAILABLE:
        print("Error: DashScope API不可用，无法生成logo。请确保已正确安装dashscope库。")
        return None
    
    # 重试统计
    retry_reasons = []
    start_time = time.time()
    
    # 尝试生成logo，最多重试max_retries次
    for attempt in range(max_retries):
        # 获取下一个DashScope API密钥用于当前请求
        current_api_key = get_next_dashscope_api_key()
        api_start = time.time()
        try:
            # 为重试添加随机性，避免生成相同的图像
            if attempt > 0:
                retry_prompt = f"{vector_style_prompt}\n\n变化要求: 请生成与之前不同的设计风格，尝试{['更加几何化', '更加有机化', '更加现代化'][attempt % 3]}的设计"
            else:
                retry_prompt = vector_style_prompt
            
            log(f'Logo生成请求 attempt={attempt+1} key={_mask_key(current_api_key)}')
            
            # DashScope调用限流控制 - 确保每秒不超过2次调用
            rate_limit_start = wait_for_dashscope_rate_limit()
            
            rsp = ImageSynthesis.call(
                api_key=current_api_key,
                model="wanx2.0-t2i-turbo",
                prompt=retry_prompt,
                n=1,
                size='768*768'
            )
            api_end = time.time()
            api_duration = (api_end - api_start) * 1000
            log(f'Logo生成响应 duration={api_duration:.1f}ms status={rsp.status_code}')
            
            if rsp.status_code == HTTPStatus.OK:
                # 下载生成的图像
                for result in rsp.output.results:
                    download_start = time.time()
                    image_resp = requests.get(result.url)
                    if image_resp.status_code == 200:
                        # 加载图像并转换为RGBA模式
                        img = Image.open(BytesIO(image_resp.content)).convert("RGBA")
                        download_duration = (time.time() - download_start) * 1000
                        log(f"Logo下载完成 size={img.size} duration={download_duration:.1f}ms")
                        
                        # 后处理：将白色背景转换为透明（使用适中的阈值）
                        process_start = time.time()
                        img_processed = make_background_transparent(img, threshold=80)
                        process_duration = (time.time() - process_start) * 1000
                        log(f"背景透明化完成 duration={process_duration:.1f}ms")
                        
                        # 验证生成的logo是否有效
                        if is_valid_logo(img_processed):
                            # 记录成功调用
                            add_ai_call_record('DashScope', 'wanx2.0-t2i-turbo', current_api_key, api_start, api_end, 'success', attempt=attempt+1)
                            
                            total_duration = (time.time() - start_time) * 1000
                            if retry_reasons:
                                log(f"Logo生成成功 总耗时={total_duration:.1f}ms 重试={len(retry_reasons)}次 原因={retry_reasons}")
                            else:
                                log(f"Logo生成成功 耗时={total_duration:.1f}ms 无重试")
                            return img_processed
                        else:
                            reason = "验证失败"
                            retry_time = (time.time() - start_time) * 1000
                            retry_reasons.append(f"{reason}@{retry_time:.0f}ms")
                            log(f"Logo生成重试 attempt={attempt+1}/{max_retries} reason={reason} time={retry_time:.1f}ms")
                            
                            if attempt < max_retries - 1:
                                # 记录重试调用
                                add_ai_call_record('DashScope', 'wanx2.0-t2i-turbo', current_api_key, api_start, api_end, 'retry', reason, attempt+1)
                                time.sleep(0.2)
                                continue
                            else:
                                # 记录最终失败但仍返回结果的调用
                                add_ai_call_record('DashScope', 'wanx2.0-t2i-turbo', current_api_key, api_start, api_end, 'failed', reason, attempt+1)
                                log(f"Logo验证失败但返回 重试汇总={retry_reasons}")
                                return img_processed  # 即使验证失败，也返回最后的结果
                    else:
                        reason = f"下载失败{image_resp.status_code}"
                        retry_time = (time.time() - start_time) * 1000
                        retry_reasons.append(f"{reason}@{retry_time:.0f}ms")
                        log(f"Logo生成重试 attempt={attempt+1}/{max_retries} reason={reason} time={retry_time:.1f}ms")
                        
                        if attempt < max_retries - 1:
                            # 记录重试调用
                            add_ai_call_record('DashScope', 'wanx2.0-t2i-turbo', current_api_key, api_start, api_end, 'retry', reason, attempt+1)
                            time.sleep(1)
                            continue
                        else:
                            # 记录最终失败调用
                            add_ai_call_record('DashScope', 'wanx2.0-t2i-turbo', current_api_key, api_start, api_end, 'failed', reason, attempt+1)
            else:
                reason = f"API失败{rsp.status_code}"
                if hasattr(rsp, 'message'):
                    reason += f"({rsp.message})"
                retry_time = (time.time() - start_time) * 1000
                retry_reasons.append(f"{reason}@{retry_time:.0f}ms")
                log(f"Logo生成重试 attempt={attempt+1}/{max_retries} reason={reason} time={retry_time:.1f}ms")
                
                if attempt < max_retries - 1:
                    # 记录重试调用
                    add_ai_call_record('DashScope', 'wanx2.0-t2i-turbo', current_api_key, api_start, api_end, 'retry', reason, attempt+1)
                    time.sleep(1)
                    continue
                else:
                    # 记录最终失败调用
                    add_ai_call_record('DashScope', 'wanx2.0-t2i-turbo', current_api_key, api_start, api_end, 'failed', reason, attempt+1)
                    log(f"Logo生成失败 重试汇总={retry_reasons}")
                
        except Exception as e:
            error_str = str(e)
            api_end = time.time()
            retry_time = (time.time() - start_time) * 1000
            
            # 针对429错误（限流）增加更长延迟
            if "429" in error_str or "Throttling.RateQuota" in error_str:
                reason = "429限流"
                retry_delay = 5 + attempt * 3  # 5s, 8s, 11s递增延迟
                retry_reasons.append(f"{reason}@{retry_time:.0f}ms")
                log(f"Logo生成重试 attempt={attempt+1}/{max_retries} reason={reason} delay={retry_delay}s time={retry_time:.1f}ms")
                
                if attempt < max_retries - 1:
                    # 记录重试调用
                    add_ai_call_record('DashScope', 'wanx2.0-t2i-turbo', current_api_key, api_start, api_end, 'retry', reason, attempt+1)
                    time.sleep(retry_delay)
                    continue
                else:
                    # 记录最终失败调用
                    add_ai_call_record('DashScope', 'wanx2.0-t2i-turbo', current_api_key, api_start, api_end, 'failed', reason, attempt+1)
            else:
                reason = "异常错误"
                retry_reasons.append(f"{reason}@{retry_time:.0f}ms")
                log(f"Logo生成重试 attempt={attempt+1}/{max_retries} reason={reason} error={error_str} time={retry_time:.1f}ms")
                
                if attempt < max_retries - 1:
                    # 记录重试调用
                    add_ai_call_record('DashScope', 'wanx2.0-t2i-turbo', current_api_key, api_start, api_end, 'retry', reason, attempt+1)
                    time.sleep(1)
                    continue
                else:
                    # 记录最终失败调用
                    add_ai_call_record('DashScope', 'wanx2.0-t2i-turbo', current_api_key, api_start, api_end, 'failed', reason, attempt+1)
            
            if attempt == max_retries - 1:
                log(f"Logo生成失败 重试汇总={retry_reasons}")
    
    # 所有重试都失败
    total_duration = (time.time() - start_time) * 1000
    log(f"Logo生成彻底失败 总耗时={total_duration:.1f}ms 重试汇总={retry_reasons}")
    return None

@log_step("change_shirt_color")
def change_shirt_color(image, color_hex, apply_texture=False, fabric_type=None):
    """Change T-shirt color with optional fabric texture"""
    start_time = time.time()
    
    # 转换十六进制颜色为RGB
    color_rgb = tuple(int(color_hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
    log(f"T恤改色开始 color={color_hex} size={image.size}")
    
    # 创建副本避免修改原图
    colored_image = image.copy().convert("RGBA")
    
    # 获取图像数据
    data = colored_image.getdata()
    
    # 创建新数据
    new_data = []
    # 白色阈值 - 调整这个值可以控制哪些像素被视为白色/浅色并被改变
    threshold = 200
    
    pixel_count = 0
    changed_pixels = 0
    for item in data:
        pixel_count += 1
        # 判断是否是白色/浅色区域 (RGB值都很高)
        if item[0] > threshold and item[1] > threshold and item[2] > threshold and item[3] > 0:
            # 保持原透明度，改变颜色
            new_color = (color_rgb[0], color_rgb[1], color_rgb[2], item[3])
            new_data.append(new_color)
            changed_pixels += 1
        else:
            # 保持其他颜色不变
            new_data.append(item)
    
    # 更新图像数据
    colored_image.putdata(new_data)
    
    duration = (time.time() - start_time) * 1000
    change_ratio = (changed_pixels / pixel_count) * 100 if pixel_count > 0 else 0
    log(f"T恤改色完成 duration={duration:.1f}ms changed={changed_pixels}/{pixel_count}({change_ratio:.1f}%)")
    
    # 如果需要应用纹理
    # 纹理阶段已禁用
    
    return colored_image

def apply_logo_to_shirt(shirt_image, logo_image, position="center", size_percent=60, background_color=None):
    """Apply logo to T-shirt image with better blending to reduce shadows"""
    start_time = time.time()
    
    if logo_image is None:
        log("Logo应用跳过：Logo为空")
        return shirt_image
    
    # 验证logo是否有效
    if not is_valid_logo(logo_image):
        log("Logo应用跳过：Logo验证失败")
        return shirt_image
    
    log(f"Logo应用开始 shirt_size={shirt_image.size} logo_size={logo_image.size} position={position}")
    
    # 创建副本避免修改原图
    result_image = shirt_image.copy().convert("RGBA")
    img_width, img_height = result_image.size
    
    # 定义T恤前胸区域
    chest_width = int(img_width * 0.95)
    chest_height = int(img_height * 0.6)
    chest_left = (img_width - chest_width) // 2
    chest_top = int(img_height * 0.2)
    
    # 提取logo前景
    logo_with_bg = logo_image.copy().convert("RGBA")
    
    # 调整Logo大小
    resize_start = time.time()
    logo_size_factor = size_percent / 100
    logo_width = int(chest_width * logo_size_factor * 0.7)
    logo_height = int(logo_width * logo_with_bg.height / logo_with_bg.width)
    logo_resized = logo_with_bg.resize((logo_width, logo_height), Image.LANCZOS)
    resize_duration = (time.time() - resize_start) * 1000
    log(f"Logo调整大小 from={logo_with_bg.size} to={logo_resized.size} duration={resize_duration:.1f}ms")
    
    # 根据位置确定坐标
    position = position.lower() if isinstance(position, str) else "center"
    
    if position == "top-center":
        logo_x, logo_y = chest_left + (chest_width - logo_width) // 2, chest_top + 10
    elif position == "center":
        logo_x, logo_y = chest_left + (chest_width - logo_width) // 2, chest_top + (chest_height - logo_height) // 2 + 30  # 略微偏下
    else:  # 默认中间
        logo_x, logo_y = chest_left + (chest_width - logo_width) // 2, chest_top + (chest_height - logo_height) // 2 + 30
    
    # 对于透明背景的logo，直接使用alpha通道作为蒙版
    blend_start = time.time()
    if logo_resized.mode == 'RGBA':
        # 检查logo是否真的有透明像素
        has_transparency = False
        for pixel in logo_resized.getdata():
            if len(pixel) == 4 and pixel[3] < 255:  # 有alpha通道且不完全不透明
                has_transparency = True
                break
        
        log(f"Logo透明度检查 mode={logo_resized.mode} has_transparency={has_transparency}")
        
        if has_transparency:
            # 直接使用PIL的alpha合成，这样处理透明背景更准确
            result_image.paste(logo_resized, (logo_x, logo_y), logo_resized)
        else:
            # 如果没有透明像素，先处理背景透明化
            log("Logo背景透明化处理")
            transparent_logo = make_background_transparent(logo_resized, threshold=120)
            result_image.paste(transparent_logo, (logo_x, logo_y), transparent_logo)
    
    blend_duration = (time.time() - blend_start) * 1000
    total_duration = (time.time() - start_time) * 1000
    log(f"Logo应用完成 position=({logo_x},{logo_y}) blend={blend_duration:.1f}ms total={total_duration:.1f}ms")
    
    return result_image

def generate_complete_design(design_prompt, variation_id=None):
    """Generate complete T-shirt design based on prompt"""
    if not design_prompt:
        return None, {"error": "Please enter a design prompt"}
    
    # 并发：提前启动底图加载
    base_image = None
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=3) as local_executor:
        base_image_future = local_executor.submit(load_original_tshirt_image)
        
        # 同时获取AI设计建议
        design_suggestions = get_ai_design_suggestions(design_prompt)
        if "error" in design_suggestions:
            try:
                # 等待底图线程结束，避免僵尸线程
                _ = base_image_future.result(timeout=0.1)
            except Exception:
                pass
            return None, design_suggestions
        
        # 提取建议
        color_hex = design_suggestions.get("color", {}).get("hex", "#FFFFFF")
        color_name = design_suggestions.get("color", {}).get("name", "Custom Color")
        fabric_type = design_suggestions.get("fabric", "Cotton")
        logo_description = design_suggestions.get("logo", "")
        
        # 并发：拿到建议立刻触发logo生成
        logo_future = None
        if logo_description:
            logo_prompt = f"""Create a professional vector logo design: {logo_description}. 
            Requirements: 
            1. Simple professional design
            2. IMPORTANT: Transparent background (PNG format)
            3. Clear and distinct graphic with high contrast
            4. Vector-style illustration suitable for T-shirt printing
            5. Must not include any text, numbers or color name, only logo graphic
            6. IMPORTANT: Do NOT include any mockups or product previews
            7. IMPORTANT: Create ONLY the logo graphic itself
            8. NO META REFERENCES - do not show the logo applied to anything
            9. Design should be a standalone graphic symbol/icon only
            10. CRITICAL: Clean vector art style with crisp lines and solid colors
            11. Ensure rich details and multiple colors to avoid solid color designs"""
            log(f"开始生成logo: {logo_description}")
            logo_future = local_executor.submit(generate_vector_image, logo_prompt, None, 3, color_hex)
        
        # 等待底图加载完成
        try:
            base_image = base_image_future.result()
        except Exception as e:
            return None, {"error": f"Error loading T-shirt image: {str(e)}"}
        
        # 并发：开始改色与纹理
        log(f"应用颜色（纹理已禁用） color={color_hex}")
        shirt_future = local_executor.submit(change_shirt_color, base_image, color_hex, False, None)
        
        # 汇总结果
        colored_shirt = None
        logo_image = None
        try:
            colored_shirt = shirt_future.result()
        except Exception as e:
            import traceback
            traceback_str = traceback.format_exc()
            log(f"change_shirt_color 异常: {e}\n{traceback_str}")
            return None, {"error": f"Error changing shirt color: {str(e)}"}
        
        if logo_future is not None:
            try:
                logo_image = logo_future.result()
                if logo_image is None:
                    log("Logo生成失败，将继续生成不带logo的设计")
            except Exception as e:
                log(f"Logo生成异常: {e}")
                logo_image = None
    
    try:
        # 最终设计 - 不添加文字
        final_design = colored_shirt
        
        # 应用Logo (如果有)
        if logo_image:
            # 应用透明背景的logo到T恤
            final_design = apply_logo_to_shirt(colored_shirt, logo_image, "center", 60)
        
        return final_design, {
            "color": {"hex": color_hex, "name": color_name},
            "fabric": fabric_type,
            "logo": logo_description,
            "design_index": 0 if variation_id is None else variation_id  # 使用design_index替代variation_id
        }
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        log(f"generate_complete_design 合成阶段异常: {e}\n{traceback_str}")
        return None, {"error": f"Error assembling final design: {str(e)}\n{traceback_str}"}

def generate_single_design(design_index, design_prompt):
    try:
        # 添加随机延迟，避免所有线程同时发起API请求
        random_delay = 0.3 + (design_index * 0.2) + (random.random() * 0.5)
        time.sleep(random_delay)
        
        # 为每个设计添加轻微的提示词变化，确保设计多样性
        design_variations = [
            "",  # 原始提示词
            "modern and minimalist",
            "colorful and vibrant", 
            "vintage and retro",
            "elegant and simple",
            "bold and edgy",
            "soft and feminine",
            "urban streetwear",
            "artistic and creative",
            "sporty and athletic",
            "professional and classic",
            "playful and fun",
            "dark and mysterious",
            "bright and cheerful",
            "geometric and abstract",
            "nature-inspired",
            "tech and futuristic",
            "handcrafted and artisanal", 
            "luxury and premium",
            "casual everyday"
        ]
        
        # 选择合适的变化描述词
        variation_desc = ""
        if design_index < len(design_variations):
            variation_desc = design_variations[design_index]
        
        # 创建变化的提示词
        if variation_desc:
            # 将变化描述词添加到原始提示词
            varied_prompt = f"{design_prompt}, {variation_desc}"
        else:
            varied_prompt = design_prompt
        
        # 完整的独立流程 - 每个设计独立获取AI建议、生成图片，确保颜色一致性
        # 使用独立提示词生成完全不同的设计
        log(f"generate_single_design 调用 generate_complete_design index={design_index}")
        design, info = generate_complete_design(varied_prompt)
        
        # 添加设计索引到信息中以便排序
        if info and isinstance(info, dict):
            info["design_index"] = design_index
        
        return design, info
    except Exception as e:
        print(f"Error generating design {design_index}: {e}")
        return None, {"error": f"Failed to generate design {design_index}"}

def image_to_base64(image):
    """Convert PIL image to base64 string"""
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点，用于Railway部署验证"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'message': 'AI T-shirt Design Generator is running'
    })

@app.route('/generate', methods=['POST', 'OPTIONS'])
def generate_designs():
    # 处理OPTIONS预检请求
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
        
    data = request.get_json()
    keywords = data.get('keywords', '')
    
    if not keywords:
        return jsonify({'error': 'Please enter at least one keyword'}), 400
    
    try:
        # 清空之前的AI调用记录
        clear_ai_call_records()
        
        design_count = DEFAULT_DESIGN_COUNT
        log(f"HTTP /generate pipeline START design_count={design_count} keywords='{keywords}'")
        designs = []
        
        # 统一线程池：并发发出所有建议请求；建议返回即并发进行改色与logo生成
        from concurrent.futures import ThreadPoolExecutor, as_completed
        max_workers = min(design_count * 3 + 2, 60)
        variations = [
            "",
            "modern and minimalist",
            "colorful and vibrant",
            "vintage and retro",
            "elegant and simple",
            "bold and edgy",
            "soft and feminine",
            "urban streetwear",
            "artistic and creative",
            "sporty and athletic",
            "professional and classic",
            "playful and fun",
            "dark and mysterious",
            "bright and cheerful",
            "geometric and abstract",
            "nature-inspired",
            "tech and futuristic",
            "handcrafted and artisanal",
            "luxury and premium",
            "casual everyday"
        ]
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 预加载底图（与建议并发）
            base_image_future = executor.submit(load_original_tshirt_image)
            
            # 先把全部建议请求并发出去
            def suggestion_task(idx: int):
                desc = variations[idx] if idx < len(variations) else ""
                prompt = keywords if not desc else f"{keywords}, {desc}"
                log(f"建议请求 SUBMIT idx={idx} prompt='{prompt}'")
                return get_ai_design_suggestions(prompt)
            sugg_future_to_idx = {executor.submit(suggestion_task, i): i for i in range(design_count)}
            
            # 对每个返回的建议，立即并发改色和logo
            final_futures = []
            for sf in as_completed(sugg_future_to_idx):
                idx = sugg_future_to_idx[sf]
                try:
                    suggestion = sf.result()
                except Exception as e:
                    log(f"建议请求异常 idx={idx}: {e}")
                    continue
                if not suggestion or (isinstance(suggestion, dict) and 'error' in suggestion):
                    log(f"建议返回错误 idx={idx}: {suggestion}")
                    continue
                color_hex = suggestion.get('color', {}).get('hex', '#FFFFFF')
                color_name = suggestion.get('color', {}).get('name', 'Custom Color')
                fabric_type = suggestion.get('fabric', 'Cotton')
                logo_desc = suggestion.get('logo', '')
                log(f"建议已到达 idx={idx} color={color_hex} logo_desc_len={len(logo_desc) if logo_desc else 0}")
                
                # 改色任务（等待底图加载即可开始）
                def make_color_task(hx: str):
                    def _t():
                        base_img = base_image_future.result()
                        return change_shirt_color(base_img, hx, False, None)
                    return _t
                color_future = executor.submit(make_color_task(color_hex))
                
                # logo 任务（立即开始，DashScope API key 轮询分配）
                # 若建议没有logo描述，构造一个默认描述，确保始终生成
                if not logo_desc or not str(logo_desc).strip():
                    logo_desc = f"abstract geometric badge matching {color_name} ({color_hex}), clean edges, vector flat style, center composition"
                logo_prompt = f"""Create a professional vector logo design: {logo_desc}. 
                Requirements: 
                1. Simple professional design
                2. IMPORTANT: Transparent background (PNG format)
                3. Clear and distinct graphic with high contrast
                4. Vector-style illustration suitable for T-shirt printing
                5. Must not include any text, numbers or color name, only logo graphic
                6. IMPORTANT: Do NOT include any mockups or product previews
                7. IMPORTANT: Create ONLY the logo graphic itself
                8. NO META REFERENCES - do not show the logo applied to anything
                9. Design should be a standalone graphic symbol/icon only
                10. CRITICAL: Clean vector art style with crisp lines and solid colors
                11. Ensure rich details and multiple colors to avoid solid color designs"""
                log(f"logo 任务 SUBMIT idx={idx}")
                logo_future = executor.submit(generate_vector_image, logo_prompt, None, 3, color_hex)
                
                # 合成任务：等待改色与logo完成后输出最终图
                def make_compose_task(index: int, color_f, logo_f, cx: str, cn: str, fb: str, ld: str):
                    def _c():
                        shirt = color_f.result()
                        logo_img = logo_f.result() if logo_f is not None else None
                        # 若logo生成失败，进行一次回退生成
                        if logo_img is None:
                            try:
                                fallback_desc = f"minimal abstract icon with two-tone colors, clean vector silhouette, center composition, complements {cx}"
                                fallback_prompt = f"Create a professional vector logo design: {fallback_desc}. Requirements: Transparent background (PNG), high contrast, no text, no mockups, clean edges, flat style"
                                logo_img = generate_vector_image(fallback_prompt, None, 2, cx)
                                log(f"回退logo生成 idx={index} {'成功' if logo_img is not None else '失败'}")
                            except Exception as _:
                                logo_img = None
                        final_img = shirt
                        if logo_img is not None:
                            final_img = apply_logo_to_shirt(shirt, logo_img, "center", 60)
                        info = {
                            'color': {'hex': cx, 'name': cn},
                            'fabric': fb,
                            'logo': ld,
                            'design_index': index
                        }
                        return final_img, info, index
                    return _c
                final_futures.append(executor.submit(make_compose_task(idx, color_future, logo_future, color_hex, color_name, fabric_type, logo_desc)))
            
            # 收集最终结果
            for ff in as_completed(final_futures):
                try:
                    img, info, did = ff.result()
                    if img is not None:
                        designs.append({
                            'image': image_to_base64(img),
                            'info': info,
                            'design_id': did
                        })
                        log(f"设计完成 idx={did}")
                except Exception as e:
                    log(f"合成阶段异常: {e}")
        
        # 排序并返回
        designs.sort(key=lambda x: x.get('design_id', 0))
        log(f"HTTP /generate pipeline END total={len(designs)}")
        
        # 打印AI调用汇总报告
        print_ai_call_summary()
        
        return jsonify({
            'success': True,
            'designs': designs,
            'total': len(designs)
        })
    
    except Exception as e:
        import traceback
        error_msg = f"Error generating designs: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        
        # 即使发生错误也打印AI调用汇总报告
        print_ai_call_summary()
        
        return jsonify({'error': error_msg}), 500

if __name__ == '__main__':
    # Railway环境配置
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"🚀 Starting AI T-shirt Design Generator...")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Debug: {debug_mode}")
    print(f"   Environment: {'Railway' if os.environ.get('RAILWAY_ENVIRONMENT') else 'Local'}")
    print(f"   DashScope Available: {DASHSCOPE_AVAILABLE}")
    print(f"   CORS Enabled: True")
    
    try:
        app.run(host=host, port=port, debug=debug_mode, threaded=True)
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        raise
