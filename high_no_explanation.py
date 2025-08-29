import streamlit as st
from PIL import Image, ImageDraw
import requests
from io import BytesIO
import os  # 确保os模块在这里导入
# 移除cairosvg依赖，使用svglib作为唯一的SVG处理库
try:
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPM
    SVGLIB_AVAILABLE = True
except ImportError:
    SVGLIB_AVAILABLE = False
    st.warning("SVG processing libraries not installed, SVG conversion will not be available")
from openai import OpenAI
from streamlit_image_coordinates import streamlit_image_coordinates
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
# 导入阿里云DashScope文生图API
from http import HTTPStatus
from urllib.parse import urlparse, unquote
from pathlib import PurePosixPath
try:
    from dashscope import ImageSynthesis
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False
    st.warning("DashScope not installed, will use OpenAI DALL-E as fallback")

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
                print(f"DashScope限流等待 wait_time={wait_time:.3f}s current_calls={len(_dashscope_call_times)}")
                _dashscope_wait_times.append(wait_time)  # 记录等待时间
                time.sleep(wait_time)
                
                # 重新获取当前时间并清理记录
                current_time = time.time()
                _dashscope_call_times[:] = [t for t in _dashscope_call_times if current_time - t < DASHSCOPE_TIME_WINDOW]
        
        # 记录当前调用时间
        _dashscope_call_times.append(current_time)
        print(f"DashScope调用许可 current_calls_in_window={len(_dashscope_call_times)}")
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

def _mask_key(key: str) -> str:
    """掩码显示API密钥"""
    try:
        if not key:
            return "None"
        if len(key) <= 10:
            return key[:2] + "***" + key[-2:]
        else:
            return key[:6] + "***" + key[-4:]
    except:
        return "Invalid"

def print_ai_call_summary():
    """打印AI调用汇总报告"""
    with _call_records_lock:
        if not _ai_call_records:
            print("AI调用汇总：无调用记录")
            return
        
        print("=" * 80)
        print("🚀 AI调用汇总报告")
        print("=" * 80)
        
        # 按API类型分组统计
        gpt4o_calls = [r for r in _ai_call_records if r['api_type'] == 'GPT-4o-mini']
        dashscope_calls = [r for r in _ai_call_records if r['api_type'] == 'DashScope']
        
        # GPT-4o-mini统计
        if gpt4o_calls:
            print(f"📊 GPT-4o-mini调用统计 (共{len(gpt4o_calls)}次):")
            success_count = len([r for r in gpt4o_calls if r['status'] == 'success'])
            failed_count = len([r for r in gpt4o_calls if r['status'] == 'failed'])
            retry_count = len([r for r in gpt4o_calls if r['status'] == 'retry'])
            total_duration = sum(r['duration_ms'] for r in gpt4o_calls)
            avg_duration = total_duration / len(gpt4o_calls) if gpt4o_calls else 0
            
            print(f"  ✅ 成功: {success_count}次 | ❌ 失败: {failed_count}次 | 🔄 重试: {retry_count}次")
            print(f"  ⏱️  总耗时: {total_duration:.1f}ms | 平均: {avg_duration:.1f}ms")
            
            # 失败原因统计
            failure_reasons = {}
            for record in gpt4o_calls:
                if record['status'] in ['failed', 'retry'] and record['reason']:
                    failure_reasons[record['reason']] = failure_reasons.get(record['reason'], 0) + 1
            
            if failure_reasons:
                print(f"  🚨 失败原因分布: {failure_reasons}")
            
            # 详细调用记录
            for i, record in enumerate(gpt4o_calls, 1):
                status_icon = "✅" if record['status'] == 'success' else "❌" if record['status'] == 'failed' else "🔄"
                reason_text = f" ({record['reason']})" if record['reason'] else ""
                print(f"    {i:2d}. {status_icon} key={record['api_key']} 发送={record['start_time_str']} 接收={record['end_time_str']} duration={record['duration_ms']:.1f}ms attempt={record['attempt']}{reason_text}")
        
        # DashScope统计
        if dashscope_calls:
            print(f"\n📊 DashScope调用统计 (共{len(dashscope_calls)}次):")
            success_count = len([r for r in dashscope_calls if r['status'] == 'success'])
            failed_count = len([r for r in dashscope_calls if r['status'] == 'failed'])
            retry_count = len([r for r in dashscope_calls if r['status'] == 'retry'])
            total_duration = sum(r['duration_ms'] for r in dashscope_calls)
            avg_duration = total_duration / len(dashscope_calls) if dashscope_calls else 0
            
            print(f"  ✅ 成功: {success_count}次 | ❌ 失败: {failed_count}次 | 🔄 重试: {retry_count}次")
            print(f"  ⏱️  总耗时: {total_duration:.1f}ms | 平均: {avg_duration:.1f}ms")
            
            # 限流统计
            if _dashscope_wait_times:
                total_wait_time = sum(_dashscope_wait_times)
                avg_wait_time = total_wait_time / len(_dashscope_wait_times)
                max_wait_time = max(_dashscope_wait_times)
                print(f"  🚦 限流统计: 等待{len(_dashscope_wait_times)}次 | 总等待: {total_wait_time:.3f}s | 平均: {avg_wait_time:.3f}s | 最长: {max_wait_time:.3f}s")
            else:
                print(f"  🚦 限流统计: 无等待 (调用频率在限制范围内)")
            
            # 失败原因统计
            failure_reasons = {}
            for record in dashscope_calls:
                if record['status'] in ['failed', 'retry'] and record['reason']:
                    failure_reasons[record['reason']] = failure_reasons.get(record['reason'], 0) + 1
            
            if failure_reasons:
                print(f"  🚨 失败原因分布: {failure_reasons}")
            
            # 详细调用记录
            for i, record in enumerate(dashscope_calls, 1):
                status_icon = "✅" if record['status'] == 'success' else "❌" if record['status'] == 'failed' else "🔄"
                reason_text = f" ({record['reason']})" if record['reason'] else ""
                print(f"    {i:2d}. {status_icon} key={record['api_key']} 发送={record['start_time_str']} 接收={record['end_time_str']} duration={record['duration_ms']:.1f}ms attempt={record['attempt']}{reason_text}")
        
        # 总体统计
        total_calls = len(_ai_call_records)
        total_success = len([r for r in _ai_call_records if r['status'] == 'success'])
        total_failed = len([r for r in _ai_call_records if r['status'] == 'failed'])
        total_retry = len([r for r in _ai_call_records if r['status'] == 'retry'])
        overall_duration = sum(r['duration_ms'] for r in _ai_call_records)
        success_rate = (total_success / total_calls * 100) if total_calls > 0 else 0
        
        print(f"\n📈 总体统计:")
        print(f"  🎯 总调用: {total_calls}次 | 成功率: {success_rate:.1f}%")
        print(f"  ✅ 成功: {total_success}次 | ❌ 失败: {total_failed}次 | 🔄 重试: {total_retry}次")
        print(f"  ⏱️  总耗时: {overall_duration:.1f}ms")
        
        print("=" * 80)

def clear_ai_call_records():
    """清空AI调用记录"""
    with _call_records_lock:
        _ai_call_records.clear()
    # 同时清空限流统计
    with _dashscope_rate_lock:
        _dashscope_wait_times.clear()

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
    
    print(f"检测到的背景颜色: RGB({bg_r}, {bg_g}, {bg_b})")
    
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
    
    print(f"透明化了 {transparent_count} 个像素，占总像素的 {transparent_count/(image.size[0]*image.size[1])*100:.1f}%")
    
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
    
    print(f"T恤颜色分析 color={shirt_color} brightness={shirt_brightness:.1f} is_dark={is_dark_shirt}")
    
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

# 自定义SVG转PNG函数，不依赖外部库
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
            st.error("SVG conversion libraries not available. Please install svglib and reportlab.")
            return None
    except Exception as e:
        st.error(f"Error converting SVG to PNG: {str(e)}")
        return None

# 设置默认生成的设计数量，取代UI上的选择按钮
DEFAULT_DESIGN_COUNT = 20  # 可以设置为1, 3, 5, 15, 20，分别对应原来的low, medium, high, ultra-high

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
            print(f"AI建议请求 attempt={attempt+1} key={api_key[:6]}...{api_key[-4:]}")
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
            print(f"AI建议响应 duration={api_duration:.1f}ms")
            
            # 返回建议内容
            if response.choices and len(response.choices) > 0:
                suggestion_text = response.choices[0].message.content
                print(f"AI建议解析 length={len(suggestion_text) if suggestion_text else 0}字符")
                
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
                        print(f"AI建议成功 总耗时={total_duration:.1f}ms 重试={len(retry_reasons)}次 原因={retry_reasons}")
                    else:
                        print(f"AI建议成功 耗时={total_duration:.1f}ms 无重试")
                    return suggestion_json
                except Exception as e:
                    print(f"JSON解析失败: {e}")
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
                print(f"AI建议重试 attempt={attempt+1}/{max_retries} reason={reason} time={retry_time:.1f}ms")
                
                # 记录重试调用
                if attempt < max_retries - 1:
                    add_ai_call_record('GPT-4o-mini', 'gpt-4o-mini', api_key, api_start, api_end, 'retry', reason, attempt+1)
                    continue  # 尝试下一个密钥
                else:
                    # 记录最终失败调用
                    add_ai_call_record('GPT-4o-mini', 'gpt-4o-mini', api_key, api_start, api_end, 'failed', reason, attempt+1)
                    print(f"AI建议失败 重试汇总={retry_reasons}")
                    return {"error": f"所有GPT-4o API密钥都无效，请检查密钥配置: {error_str}"}
            else:
                # 其他错误，直接返回
                reason = "其他错误"
                retry_reasons.append(f"{reason}@{retry_time:.0f}ms")
                # 记录失败调用
                add_ai_call_record('GPT-4o-mini', 'gpt-4o-mini', api_key, api_start, api_end, 'failed', reason, attempt+1)
                print(f"AI建议失败 重试汇总={retry_reasons} 最终错误={error_str}")
                return {"error": f"Error getting AI design suggestions: {error_str}"}
    
    # 如果所有重试都失败
    total_duration = (time.time() - start_time) * 1000
    print(f"AI建议彻底失败 总耗时={total_duration:.1f}ms 重试汇总={retry_reasons}")
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
        
        # 如果单一颜色占比超过阈值，认为是无效logo
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
        print(f"Logo对比色适配 shirt_color={shirt_color} contrast_type={contrast_info['contrast_type']}")
        
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
        st.error("DashScope API不可用，无法生成logo。请确保已正确安装dashscope库。")
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
            
            print(f'Logo生成请求 attempt={attempt+1} key={current_api_key[:6]}...{current_api_key[-4:]}')
            
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
            print(f'Logo生成响应 duration={api_duration:.1f}ms status={rsp.status_code}')
            
            if rsp.status_code == HTTPStatus.OK:
                # 下载生成的图像
                for result in rsp.output.results:
                    download_start = time.time()
                    image_resp = requests.get(result.url)
                    if image_resp.status_code == 200:
                        # 加载图像并转换为RGBA模式
                        img = Image.open(BytesIO(image_resp.content)).convert("RGBA")
                        download_duration = (time.time() - download_start) * 1000
                        print(f"Logo下载完成 size={img.size} duration={download_duration:.1f}ms")
                        
                        # 后处理：将白色背景转换为透明（使用适中的阈值）
                        process_start = time.time()
                        img_processed = make_background_transparent(img, threshold=80)
                        process_duration = (time.time() - process_start) * 1000
                        print(f"背景透明化完成 duration={process_duration:.1f}ms")
                        
                        # 验证生成的logo是否有效
                        if is_valid_logo(img_processed):
                            # 记录成功调用
                            add_ai_call_record('DashScope', 'wanx2.0-t2i-turbo', current_api_key, api_start, api_end, 'success', attempt=attempt+1)
                            
                            total_duration = (time.time() - start_time) * 1000
                            if retry_reasons:
                                print(f"Logo生成成功 总耗时={total_duration:.1f}ms 重试={len(retry_reasons)}次 原因={retry_reasons}")
                            else:
                                print(f"Logo生成成功 耗时={total_duration:.1f}ms 无重试")
                            return img_processed
                        else:
                            reason = "验证失败"
                            retry_time = (time.time() - start_time) * 1000
                            retry_reasons.append(f"{reason}@{retry_time:.0f}ms")
                            print(f"Logo生成重试 attempt={attempt+1}/{max_retries} reason={reason} time={retry_time:.1f}ms")
                            if attempt < max_retries - 1:
                                # 记录重试调用
                                add_ai_call_record('DashScope', 'wanx2.0-t2i-turbo', current_api_key, api_start, api_end, 'retry', reason, attempt+1)
                                time.sleep(3)  # 增加等待时间，适应Railway环境
                                continue
                            else:
                                # 记录最终失败但仍返回结果的调用
                                add_ai_call_record('DashScope', 'wanx2.0-t2i-turbo', current_api_key, api_start, api_end, 'failed', reason, attempt+1)
                                print(f"Logo验证失败但返回 重试汇总={retry_reasons}")
                                return img_processed  # 即使验证失败，也返回最后的结果
                    else:
                        reason = f"下载失败{image_resp.status_code}"
                        retry_time = (time.time() - start_time) * 1000
                        retry_reasons.append(f"{reason}@{retry_time:.0f}ms")
                        print(f"Logo生成重试 attempt={attempt+1}/{max_retries} reason={reason} time={retry_time:.1f}ms")
                        
                        if attempt < max_retries - 1:
                            # 记录重试调用
                            add_ai_call_record('DashScope', 'wanx2.0-t2i-turbo', current_api_key, api_start, api_end, 'retry', reason, attempt+1)
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
                print(f"Logo生成重试 attempt={attempt+1}/{max_retries} reason={reason} time={retry_time:.1f}ms")
                
                if attempt < max_retries - 1:
                    # 记录重试调用
                    add_ai_call_record('DashScope', 'wanx2.0-t2i-turbo', current_api_key, api_start, api_end, 'retry', reason, attempt+1)
                    time.sleep(5)  # 增加等待时间，适应Railway环境
                    continue
                else:
                    # 记录最终失败调用
                    add_ai_call_record('DashScope', 'wanx2.0-t2i-turbo', current_api_key, api_start, api_end, 'failed', reason, attempt+1)
                    print(f"Logo生成失败 重试汇总={retry_reasons}")
                    st.error(f"DashScope API调用失败: {rsp.message}")
                
        except Exception as e:
            error_str = str(e)
            api_end = time.time()
            retry_time = (time.time() - start_time) * 1000
            
            # 针对429错误（限流）增加更长延迟
            if "429" in error_str or "Throttling.RateQuota" in error_str:
                reason = "429限流"
                retry_delay = 8 + attempt * 4  # 8s, 12s, 16s递增延迟
                retry_reasons.append(f"{reason}@{retry_time:.0f}ms")
                print(f"Logo生成重试 attempt={attempt+1}/{max_retries} reason={reason} delay={retry_delay}s time={retry_time:.1f}ms")
                
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
                print(f"Logo生成重试 attempt={attempt+1}/{max_retries} reason={reason} error={error_str} time={retry_time:.1f}ms")
                
                if attempt < max_retries - 1:
                    # 记录重试调用
                    add_ai_call_record('DashScope', 'wanx2.0-t2i-turbo', current_api_key, api_start, api_end, 'retry', reason, attempt+1)
                    time.sleep(5)  # 增加等待时间，适应Railway环境
                    continue
                else:
                    # 记录最终失败调用
                    add_ai_call_record('DashScope', 'wanx2.0-t2i-turbo', current_api_key, api_start, api_end, 'failed', reason, attempt+1)
            
            if attempt == max_retries - 1:
                print(f"Logo生成失败 重试汇总={retry_reasons}")
                st.error(f"DashScope API调用错误: {e}")
    
    # 所有重试都失败
    total_duration = (time.time() - start_time) * 1000
    print(f"Logo生成彻底失败 总耗时={total_duration:.1f}ms 重试汇总={retry_reasons}")
    st.error("Logo生成失败，请检查网络连接或稍后重试。")
    return None

def change_shirt_color(image, color_hex, apply_texture=False, fabric_type=None):
    """Change T-shirt color with optional fabric texture"""
    start_time = time.time()
    
    # 转换十六进制颜色为RGB
    color_rgb = tuple(int(color_hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
    print(f"T恤改色开始 color={color_hex} size={image.size}")
    
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
    print(f"T恤改色完成 duration={duration:.1f}ms changed={changed_pixels}/{pixel_count}({change_ratio:.1f}%)")
    
    # 如果需要应用纹理
    if apply_texture and fabric_type:
        texture_start = time.time()
        result = apply_fabric_texture(colored_image, fabric_type)
        texture_duration = (time.time() - texture_start) * 1000
        print(f"纹理应用完成 fabric={fabric_type} duration={texture_duration:.1f}ms")
        return result
    
    return colored_image

def apply_text_to_shirt(image, text, color_hex="#FFFFFF", font_size=80):
    """Apply text to T-shirt image"""
    if not text:
        return image
    
    # 创建副本避免修改原图
    result_image = image.copy().convert("RGBA")
    img_width, img_height = result_image.size
    
    # 创建透明的文本图层
    text_layer = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_layer)
    
    # 尝试加载字体
    from PIL import ImageFont
    import platform
    
    font = None
    try:
        system = platform.system()
        
        # 根据不同系统尝试不同的字体路径
        if system == 'Windows':
            font_paths = [
                "C:/Windows/Fonts/arial.ttf",
                "C:/Windows/Fonts/ARIAL.TTF",
                "C:/Windows/Fonts/calibri.ttf",
            ]
        elif system == 'Darwin':  # macOS
            font_paths = [
                "/Library/Fonts/Arial.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
            ]
        else:  # Linux或其他
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            ]
        
        # 尝试加载每个字体
        for font_path in font_paths:
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, font_size)
                break
    except Exception as e:
        print(f"Error loading font: {e}")
    
    # 如果加载失败，使用默认字体
    if font is None:
        try:
            font = ImageFont.load_default()
        except:
            print("Could not load default font")
            return result_image
    
    # 将十六进制颜色转换为RGB
    color_rgb = tuple(int(color_hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
    text_color = color_rgb + (255,)  # 添加不透明度
    
    # 计算文本位置 (居中)
    text_bbox = text_draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    text_x = (img_width - text_width) // 2
    text_y = (img_height // 3) - (text_height // 2)  # 放在T恤上部位置
    
    # 绘制文本
    text_draw.text((text_x, text_y), text, fill=text_color, font=font)
    
    # 组合图像
    result_image = Image.alpha_composite(result_image, text_layer)
    
    return result_image

def apply_logo_to_shirt(shirt_image, logo_image, position="center", size_percent=60, background_color=None):
    """Apply logo to T-shirt image with better blending to reduce shadows"""
    start_time = time.time()
    
    if logo_image is None:
        print("Logo应用跳过：Logo为空")
        return shirt_image
    
    # 验证logo是否有效
    if not is_valid_logo(logo_image):
        print("Logo应用跳过：Logo验证失败")
        return shirt_image
    
    print(f"Logo应用开始 shirt_size={shirt_image.size} logo_size={logo_image.size} position={position}")
    
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
    print(f"Logo调整大小 from={logo_with_bg.size} to={logo_resized.size} duration={resize_duration:.1f}ms")
    
    # 根据位置确定坐标
    position = position.lower() if isinstance(position, str) else "center"
    
    if position == "top-center":
        logo_x, logo_y = chest_left + (chest_width - logo_width) // 2, chest_top + 10
    elif position == "center":
        logo_x, logo_y = chest_left + (chest_width - logo_width) // 2, chest_top + (chest_height - logo_height) // 2 + 30  # 略微偏下
    else:  # 默认中间
        logo_x, logo_y = chest_left + (chest_width - logo_width) // 2, chest_top + (chest_height - logo_height) // 2 + 30
    
    # 对于透明背景的logo，直接使用alpha通道作为蒙版
    if logo_resized.mode == 'RGBA':
        # 使用alpha通道作为蒙版
        logo_mask = logo_resized.split()[-1]  # 获取alpha通道
        print(f"使用RGBA模式logo的alpha通道作为蒙版")
    else:
        # 如果不是RGBA模式，创建传统的基于颜色差异的蒙版
        logo_mask = Image.new("L", logo_resized.size, 0)  # 创建一个黑色蒙版（透明）
        
        # 如果提供了背景颜色，使用它来判断什么是背景
        if background_color:
            bg_color_rgb = tuple(int(background_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        else:
            # 默认假设白色是背景
            bg_color_rgb = (255, 255, 255)
        
        # 遍历像素，创建蒙版
        for y in range(logo_resized.height):
            for x in range(logo_resized.width):
                pixel = logo_resized.getpixel((x, y))
                if len(pixel) >= 3:  # 至少有RGB值
                    # 计算与背景颜色的差异
                    r_diff = abs(pixel[0] - bg_color_rgb[0])
                    g_diff = abs(pixel[1] - bg_color_rgb[1])
                    b_diff = abs(pixel[2] - bg_color_rgb[2])
                    diff = r_diff + g_diff + b_diff
                    
                    # 如果差异大于阈值，则认为是前景
                    if diff > 60:  # 可以调整阈值
                        # 根据差异程度设置不同的透明度
                        transparency = min(255, diff)
                        logo_mask.putpixel((x, y), transparency)
    
    # 对于透明背景的logo，使用PIL的alpha合成功能
    blend_start = time.time()
    if logo_resized.mode == 'RGBA':
        # 检查logo是否真的有透明像素
        has_transparency = False
        for pixel in logo_resized.getdata():
            if len(pixel) == 4 and pixel[3] < 255:  # 有alpha通道且不完全不透明
                has_transparency = True
                break
        
        print(f"Logo透明度检查 mode={logo_resized.mode} has_transparency={has_transparency}")
        
        if has_transparency:
            # 直接使用PIL的alpha合成，这样处理透明背景更准确
            result_image.paste(logo_resized, (logo_x, logo_y), logo_resized)
        else:
            # 如果没有透明像素，先处理背景透明化
            print("Logo背景透明化处理")
            transparent_logo = make_background_transparent(logo_resized, threshold=120)
            result_image.paste(transparent_logo, (logo_x, logo_y), transparent_logo)
    else:
        # 对于非透明背景的logo，使用传统的像素级混合方法
        shirt_region = result_image.crop((logo_x, logo_y, logo_x + logo_width, logo_y + logo_height))
        
        # 合成logo和T恤区域，使用蒙版确保只有logo的非背景部分被使用
        for y in range(logo_height):
            for x in range(logo_width):
                mask_value = logo_mask.getpixel((x, y))
                if mask_value > 20:  # 有一定的不透明度
                    # 获取logo像素
                    logo_pixel = logo_resized.getpixel((x, y))
                    # 获取T恤对应位置的像素
                    shirt_pixel = shirt_region.getpixel((x, y))
                    
                    # 根据透明度混合像素
                    alpha = mask_value / 255.0
                    blended_pixel = (
                        int(logo_pixel[0] * alpha + shirt_pixel[0] * (1 - alpha)),
                        int(logo_pixel[1] * alpha + shirt_pixel[1] * (1 - alpha)),
                        int(logo_pixel[2] * alpha + shirt_pixel[2] * (1 - alpha)),
                        255  # 完全不透明
                    )
                    
                    # 更新T恤区域的像素
                    shirt_region.putpixel((x, y), blended_pixel)
        
        # 将修改后的区域粘贴回T恤
        result_image.paste(shirt_region, (logo_x, logo_y))
    
    blend_duration = (time.time() - blend_start) * 1000
    total_duration = (time.time() - start_time) * 1000
    print(f"Logo应用完成 position=({logo_x},{logo_y}) blend={blend_duration:.1f}ms total={total_duration:.1f}ms")
    
    return result_image

def generate_complete_design(design_prompt, variation_id=None):
    """Generate complete T-shirt design based on prompt"""
    if not design_prompt:
        return None, {"error": "Please enter a design prompt"}
    
    # 获取AI设计建议
    design_suggestions = get_ai_design_suggestions(design_prompt)
    
    if "error" in design_suggestions:
        return None, design_suggestions
    
    # 加载原始T恤图像
    try:
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
            return None, {"error": "Could not find base T-shirt image"}
        
        # 加载原始白色T恤图像
        original_image = Image.open(original_image_path).convert("RGBA")
    except Exception as e:
        return None, {"error": f"Error loading T-shirt image: {str(e)}"}
    
    try:
        # 使用AI建议的颜色和面料
        color_hex = design_suggestions.get("color", {}).get("hex", "#FFFFFF")
        color_name = design_suggestions.get("color", {}).get("name", "Custom Color")
        fabric_type = design_suggestions.get("fabric", "Cotton")
        
        # 1. 应用颜色和纹理
        colored_shirt = change_shirt_color(
            original_image,
            color_hex,
            apply_texture=True,
            fabric_type=fabric_type
        )
        
        # 2. 生成Logo
        logo_description = design_suggestions.get("logo", "")
        logo_image = None
        
        if logo_description:
            # 修改Logo提示词，生成透明背景的矢量图logo
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
            
            # 生成透明背景的矢量logo，带有重试机制
            print(f"开始生成logo: {logo_description}")
            logo_image = generate_vector_image(logo_prompt, max_retries=3, shirt_color=color_hex)
            
            if logo_image is None:
                print(f"Logo生成失败，将继续生成不带logo的设计")
            else:
                print(f"Logo生成成功")
        
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
        return None, {"error": f"Error generating design: {str(e)}\n{traceback_str}"}

def generate_single_design(design_index):
    try:
        # 添加小的固定延迟，避免所有线程同时发起API请求
        time.sleep(0.2)
        
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
        design, info = generate_complete_design(varied_prompt)
        
        # 添加设计索引到信息中以便排序
        if info and isinstance(info, dict):
            info["design_index"] = design_index
        
        return design, info
    except Exception as e:
        print(f"Error generating design {design_index}: {e}")
        return None, {"error": f"Failed to generate design {design_index}"}

def generate_multiple_designs(design_prompt, count=1):
    """Generate multiple T-shirt designs in parallel - independent designs rather than variations"""
    if count <= 1:
        # 如果只需要一个设计，直接生成不需要并行
        base_design, base_info = generate_complete_design(design_prompt)
        if base_design:
            return [(base_design, base_info)]
        else:
            return []
    
    designs = []
    
    # 创建线程池，现在支持最高并发（20个线程）
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(count, 20)) as executor:
        # 提交所有任务
        future_to_id = {executor.submit(generate_single_design, i): i for i in range(count)}
        
        # 收集结果
        for future in concurrent.futures.as_completed(future_to_id):
            design_id = future_to_id[future]
            try:
                design, info = future.result()
                if design:
                    designs.append((design, info))
            except Exception as e:
                print(f"Design {design_id} generated an exception: {e}")
    
    # 按照设计索引排序
    designs.sort(key=lambda x: x[1].get("design_index", 0) if x[1] and "design_index" in x[1] else 0)
    
    return designs

def show_high_recommendation_without_explanation():
    st.title("👕 AI Recommendation Experiment Platform")
    st.markdown("### Study1-Let AI Design Your T-shirt")
    
    # Display experiment group and design count information
    st.info(f"You are currently in Study1, and AI will generate {DEFAULT_DESIGN_COUNT} T-shirt design options for you")
    
    # 初始化会话状态变量
    if 'user_prompt' not in st.session_state:
        st.session_state.user_prompt = ""
    if 'final_design' not in st.session_state:
        st.session_state.final_design = None
    if 'design_info' not in st.session_state:
        st.session_state.design_info = None
    if 'is_generating' not in st.session_state:
        st.session_state.is_generating = False
    if 'should_generate' not in st.session_state:
        st.session_state.should_generate = False
    if 'recommendation_level' not in st.session_state:
        # 设置固定推荐级别，不再允许用户选择
        if DEFAULT_DESIGN_COUNT == 1:
            st.session_state.recommendation_level = "low"
        elif DEFAULT_DESIGN_COUNT == 3:
            st.session_state.recommendation_level = "medium"
        elif DEFAULT_DESIGN_COUNT == 5:
            st.session_state.recommendation_level = "high"
        elif DEFAULT_DESIGN_COUNT == 15:
            st.session_state.recommendation_level = "ultra-high"
        else:  # 20或其他值
            st.session_state.recommendation_level = "maximum"
    if 'generated_designs' not in st.session_state:
        st.session_state.generated_designs = []
    if 'selected_design_index' not in st.session_state:
        st.session_state.selected_design_index = 0
    if 'original_tshirt' not in st.session_state:
        # 加载原始白色T恤图像
        try:
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
            
            if found:
                st.session_state.original_tshirt = Image.open(original_image_path).convert("RGBA")
            else:
                st.error("Could not find base T-shirt image")
                st.session_state.original_tshirt = None
        except Exception as e:
            st.error(f"Error loading T-shirt image: {str(e)}")
            st.session_state.original_tshirt = None
    
    # Create two-column layout
    design_col, options_col = st.columns([3, 2])
    
    with design_col:
        # Create placeholder area for T-shirt design display
        design_area = st.empty()
        
        # Display current T-shirt design state
        if len(st.session_state.generated_designs) > 0:
            with design_area.container():
                st.markdown("### Your Custom T-shirt Design")
                
                # Display the selected design
                selected_design, selected_info = st.session_state.generated_designs[st.session_state.selected_design_index]
                st.image(selected_design, use_column_width=True)
                
                # Add design number indicator
                current_design = st.session_state.selected_design_index + 1
                total_designs = len(st.session_state.generated_designs)
                st.markdown(f"**Design {current_design} of {total_designs}**")
        else:
            # Display original blank T-shirt
            with design_area.container():
                st.markdown("### T-shirt Design Preview")
                
                if st.session_state.original_tshirt is not None:
                    st.image(st.session_state.original_tshirt, use_column_width=True)
                    st.info("🎨 Your custom design will appear here")
                else:
                    st.error("Could not load original T-shirt image, please refresh the page")
    
    with options_col:
        # Design options and control area
        st.markdown("### Design Options")
        
        # Show design selector if designs are generated
        if len(st.session_state.generated_designs) > 0:
            st.markdown("#### Choose Your Favorite Design")
            
            design_options = [f"Design {i+1}" for i in range(len(st.session_state.generated_designs))]
            selected_option = st.selectbox(
                "Select a design to view:",
                options=design_options,
                index=st.session_state.selected_design_index,
                key="design_selector"
            )
            
            # Update selected design index
            new_index = design_options.index(selected_option)
            if new_index != st.session_state.selected_design_index:
                st.session_state.selected_design_index = new_index
                st.rerun()
            
            st.markdown("---")
        
        # Design prompt input area
        st.markdown("#### Describe your desired T-shirt design:")
        
        # Add brief description
        st.markdown(f"""
        Enter three keywords to describe your ideal T-shirt design. Our AI will combine these features to create {DEFAULT_DESIGN_COUNT} unique design options for you.
        """)
        
        # Initialize keywords state
        if 'keywords' not in st.session_state:
            st.session_state.keywords = ""
        
        # Keywords input box
        keywords = st.text_input(
            "Enter keywords for your design", 
            value=st.session_state.keywords, 
            placeholder="e.g., casual, nature, blue", 
            key="input_keywords"
        )
        
        # Generate design button
        generate_col = st.empty()
        with generate_col:
            generate_button = st.button("🎨 Generate T-shirt Design", key="generate_design")
        
        # Create progress and message areas below input box
        progress_area = st.empty()
        message_area = st.empty()
        
        # Generate new designs button
        if len(st.session_state.generated_designs) > 0:
            st.markdown("---")
            if st.button("🔄 Generate New Designs", key="regenerate_design"):
                st.session_state.generated_designs = []
                st.session_state.selected_design_index = 0
                st.rerun()
        
        # Generate design button event handling
        if generate_button:
            # Save user input keywords
            st.session_state.keywords = keywords
            
            # Check if keywords were entered
            if not keywords:
                st.error("Please enter at least one keyword")
            else:
                # Use user input keywords directly as prompt
                user_prompt = keywords
                
                # Save user input
                st.session_state.user_prompt = user_prompt
                
                # Use fixed design count
                design_count = DEFAULT_DESIGN_COUNT
                
                # Clear previous designs
                st.session_state.final_design = None
                st.session_state.generated_designs = []
                st.session_state.selected_design_index = 0
                
                try:
                    # Clear previous AI call records
                    clear_ai_call_records()
                    
                    # Show generation progress
                    with design_area.container():
                        st.markdown("### Generating T-shirt Designs")
                        if st.session_state.original_tshirt is not None:
                            st.image(st.session_state.original_tshirt, use_column_width=True)
                    
                    # Create progress bar and status message below input box
                    progress_bar = progress_area.progress(0)
                    message_area.info(f"AI is generating {design_count} unique design options for you. This may take about 1-3 minutes. Please do not refresh the page or close the browser. Thank you for your patience!")
                    # Record start time
                    start_time = time.time()
                    
                    # Collect generated designs
                    designs = []
                    
                    # Safe function for generating single design
                    def generate_single_safely(design_index):
                        try:
                            return generate_complete_design(user_prompt, design_index)
                        except Exception as e:
                            message_area.error(f"Error generating design: {str(e)}")
                            return None, {"error": f"Failed to generate design: {str(e)}"}
                    
                    # For single design, generate directly
                    if design_count == 1:
                        design, info = generate_single_safely(0)
                        if design:
                            designs.append((design, info))
                        progress_bar.progress(100)
                        message_area.success("Design generation complete!")
                    else:
                        # Use parallel processing for multiple designs
                        completed_count = 0
                        
                        # Progress update function
                        def update_progress():
                            nonlocal completed_count
                            completed_count += 1
                            progress = int(100 * completed_count / design_count)
                            progress_bar.progress(progress)
                            message_area.info(f"Generated {completed_count}/{design_count} designs...")
                        
                        # Use thread pool for parallel generation with maximum concurrency
                        max_workers = min(design_count, 20)  # Increased max threads to 20, utilizing more API keys
                        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                            # Submit all tasks
                            future_to_id = {executor.submit(generate_single_safely, i): i for i in range(design_count)}
                            
                            # Collect results
                            for future in concurrent.futures.as_completed(future_to_id):
                                design_id = future_to_id[future]
                                try:
                                    design, info = future.result()
                                    if design:
                                        designs.append((design, info))
                                except Exception as e:
                                    message_area.error(f"Design {design_id+1} generation failed: {str(e)}")
                                
                                # Update progress
                                update_progress()
                        
                        # Sort designs by ID
                        designs.sort(key=lambda x: x[1].get("design_index", 0) if x[1] and "design_index" in x[1] else 0)
                    
                    # Record end time
                    end_time = time.time()
                    generation_time = end_time - start_time
                    
                    # Print AI call summary report
                    print_ai_call_summary()
                    
                    # Store generated designs
                    if designs:
                        st.session_state.generated_designs = designs
                        st.session_state.selected_design_index = 0
                        message_area.success(f"Generated {len(designs)} designs in {generation_time:.1f} seconds!")
                    else:
                        message_area.error("Could not generate any designs. Please try again.")
                    
                    # Re-render design area to show newly generated designs
                    st.rerun()
                except Exception as e:
                    import traceback
                    # Print AI call summary report even if error occurs
                    print_ai_call_summary()
                    message_area.error(f"An error occurred: {str(e)}")
                    st.error(traceback.format_exc())
    

