from flask import Flask, render_template, request, jsonify, session
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
    "sk-d5XpJF2NMWWdq7ZEJQLyP0AojgNkRrAegELD2o4F5j80VC3ibSPPVC0",
    "sk-fMFkcOX0Pee9ecGWa73fdHU6tSjPD2o4F5J80Vc1e716uO10",
    "sk-BxN7ncNBMmyoy9FiRhgNkRrAegELD2O4F5r80vC3ibSpPvDG",
    "sk-Eun0GvNO0xUWm7EfprCGPukeTSHJD2O4F6380VC1E716Uo2g",
    "sk-c4rdtdCaZ4XZt92zKF8WiqGuf95Gd2o4F6B80vc3iBsPpVfg",
    "sk-QMCiQzJW0iMr3z3vr7FPxTWvfuQwd2o4hJr80vC1e716v060",
    "sk-b5eYKA5L5FPtoHFY3IhoJcE9cxwid2o4HgJ80vC3iBsPq7d0",
    "sk-OwECm6sctSh4lc8ZjMazIgKbW369D2O4hgb80vC3ibSPQ7bg",
    "sk-2G1gAKU00wK7Rt9cxJdErScYkNtSd2o4Hgb80vc3IBspQ7Ag"
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
    "sk-cdbe9b620dc04666aaf50fd44d8a756e"
]

# API密钥轮询计数器
_api_key_counter = 0
_gpt4o_api_key_counter = 0
_dashscope_api_key_counter = 0
_api_lock = threading.Lock()

# 设置默认生成的设计数量
DEFAULT_DESIGN_COUNT = 5

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # 在生产环境中使用更安全的密钥

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

@log_step("get_ai_design_suggestions")
def get_ai_design_suggestions(user_preferences=None):
    """Get design suggestions from GPT-4o-mini with more personalized features
    
    使用轮询机制从20个GPT-4o API密钥中选择，支持最高并发设计建议生成
    """
    api_key = get_next_gpt4o_api_key()
    log(f"GPT-4o-mini client init with key={_mask_key(api_key)} base_url={GPT4O_MINI_BASE_URL}")
    client = OpenAI(api_key=api_key, base_url=GPT4O_MINI_BASE_URL)
    
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
    
    try:
        # 调用GPT-4o-mini
        log("GPT-4o-mini chat.completions.create SUBMIT")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional design consultant. Provide design suggestions in JSON format exactly as requested."},
                {"role": "user", "content": prompt}
            ]
        )
        log("GPT-4o-mini chat.completions.create RESPONSE")
        
        # 返回建议内容
        if response.choices and len(response.choices) > 0:
            suggestion_text = response.choices[0].message.content
            log(f"GPT-4o-mini suggestion received length={len(suggestion_text) if suggestion_text else 0}")
            
            # 尝试解析JSON
            try:
                # 查找JSON格式的内容
                json_match = re.search(r'```json\s*(.*?)\s*```', suggestion_text, re.DOTALL)
                if json_match:
                    suggestion_json = json.loads(json_match.group(1))
                else:
                    # 尝试直接解析整个内容
                    suggestion_json = json.loads(suggestion_text)
                
                return suggestion_json
            except Exception as e:
                log(f"Error parsing JSON: {e}")
                return {"error": f"Failed to parse design suggestions: {str(e)}"}
        else:
            return {"error": "Failed to get AI design suggestions. Please try again later."}
    except Exception as e:
        return {"error": f"Error getting AI design suggestions: {str(e)}"}

def is_valid_logo(image, min_colors=3, min_non_transparent_pixels=1000):
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
        if dominant_color_ratio > 0.95:
            print(f"Logo验证失败：主要颜色占比过高 ({dominant_color_ratio:.2%})")
            return False
        
        print(f"Logo验证通过：{len(unique_colors)}种颜色，{len(non_transparent_pixels)}个非透明像素，主要颜色占比{dominant_color_ratio:.2%}")
        return True
        
    except Exception as e:
        print(f"Logo验证过程中出错: {e}")
        return False

def generate_vector_image(prompt, background_color=None, max_retries=3):
    """Generate a vector-style logo with transparent background using DashScope API with validation and retry
    
    使用轮询机制从15个DashScope API密钥中选择，支持高并发并行生成提高效率
    """
    
    # 构建矢量图logo专用的提示词
    vector_style_prompt = f"""创建一个矢量风格的logo设计: {prompt}
    要求:
    1. 简洁的矢量图风格，线条清晰
    2. 必须是透明背景，不能有任何白色或彩色背景
    3. 专业的logo设计，适合印刷到T恤上
    4. 高对比度，颜色鲜明
    5. 几何形状简洁，不要过于复杂
    6. 不要包含文字或字母
    7. 不要显示T恤或服装模型
    8. 纯粹的图形标志设计
    9. 矢量插画风格，扁平化设计
    10. 重要：背景必须完全透明，不能有任何颜色填充
    11. 请生成PNG格式的透明背景图标
    12. 图标应该是独立的，没有任何背景元素
    13. 确保logo有丰富的细节和多种颜色，避免纯色设计"""
    
    # 如果DashScope不可用，直接返回None
    if not DASHSCOPE_AVAILABLE:
        print("Error: DashScope API不可用，无法生成logo。请确保已正确安装dashscope库。")
        return None
    
    # 尝试生成logo，最多重试max_retries次
    for attempt in range(max_retries):
        try:
            print(f'----第{attempt + 1}次尝试使用DashScope生成矢量logo，提示词: {vector_style_prompt}----')
            
            # 为重试添加随机性，避免生成相同的图像
            if attempt > 0:
                retry_prompt = f"{vector_style_prompt}\n\n变化要求: 请生成与之前不同的设计风格，尝试{['更加几何化', '更加有机化', '更加现代化'][attempt % 3]}的设计"
            else:
                retry_prompt = vector_style_prompt
            
            # 获取下一个DashScope API密钥用于当前请求
            current_api_key = get_next_dashscope_api_key()
            print(f'使用DashScope API密钥: {current_api_key[:20]}...{current_api_key[-10:]}')
            
            rsp = ImageSynthesis.call(
                api_key=current_api_key,
                model="wanx2.0-t2i-turbo",
                prompt=retry_prompt,
                n=1,
                size='1024*1024'
            )
            print('DashScope响应: %s' % rsp)
            
            if rsp.status_code == HTTPStatus.OK:
                # 下载生成的图像
                for result in rsp.output.results:
                    image_resp = requests.get(result.url)
                    if image_resp.status_code == 200:
                        # 加载图像并转换为RGBA模式
                        img = Image.open(BytesIO(image_resp.content)).convert("RGBA")
                        print(f"DashScope生成的logo尺寸: {img.size}")
                        
                        # 后处理：将白色背景转换为透明（使用更高的阈值）
                        img_processed = make_background_transparent(img, threshold=120)
                        print(f"背景透明化处理完成")
                        
                        # 验证生成的logo是否有效
                        if is_valid_logo(img_processed):
                            print(f"Logo生成成功并通过验证（第{attempt + 1}次尝试）")
                            return img_processed
                        else:
                            print(f"第{attempt + 1}次生成的logo未通过验证，准备重试...")
                            if attempt < max_retries - 1:
                                time.sleep(3)  # 增加等待时间，适应Railway环境
                                continue
                            else:
                                print("所有重试都失败，返回最后一次生成的logo")
                                return img_processed  # 即使验证失败，也返回最后的结果
                    else:
                        print(f"下载图像失败, 状态码: {image_resp.status_code}")
                        if attempt < max_retries - 1:
                            continue
            else:
                print('DashScope调用失败, status_code: %s, code: %s, message: %s' %
                      (rsp.status_code, rsp.code, rsp.message))
                if attempt < max_retries - 1:
                    print(f"第{attempt + 1}次调用失败，准备重试...")
                    time.sleep(5)  # 增加等待时间，适应Railway环境
                    continue
                else:
                    print(f"Error: DashScope API调用失败: {rsp.message}")
                
        except Exception as e:
            print(f"第{attempt + 1}次DashScope调用出错: {e}")
            if attempt < max_retries - 1:
                print("准备重试...")
                time.sleep(5)  # 增加等待时间，适应Railway环境
                continue
            else:
                print(f"Error: DashScope API调用错误: {e}")
    
    # 所有重试都失败
    print(f"经过{max_retries}次尝试，logo生成失败")
    print("Error: Logo生成失败，请检查网络连接或稍后重试。")
    return None

@log_step("change_shirt_color")
def change_shirt_color(image, color_hex, apply_texture=False, fabric_type=None):
    """Change T-shirt color with optional fabric texture"""
    # 转换十六进制颜色为RGB
    color_rgb = tuple(int(color_hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
    
    # 创建副本避免修改原图
    colored_image = image.copy().convert("RGBA")
    
    # 获取图像数据
    data = colored_image.getdata()
    
    # 创建新数据
    new_data = []
    # 白色阈值 - 调整这个值可以控制哪些像素被视为白色/浅色并被改变
    threshold = 200
    
    for item in data:
        # 判断是否是白色/浅色区域 (RGB值都很高)
        if item[0] > threshold and item[1] > threshold and item[2] > threshold and item[3] > 0:
            # 保持原透明度，改变颜色
            new_color = (color_rgb[0], color_rgb[1], color_rgb[2], item[3])
            new_data.append(new_color)
        else:
            # 保持其他颜色不变
            new_data.append(item)
    
    # 更新图像数据
    colored_image.putdata(new_data)
    log("change_shirt_color recolor done")
    
    # 如果需要应用纹理
    if apply_texture and fabric_type:
        log(f"apply_fabric_texture START fabric={fabric_type}")
        textured = apply_fabric_texture(colored_image, fabric_type)
        log("apply_fabric_texture END")
        return textured
    
    return colored_image

def apply_logo_to_shirt(shirt_image, logo_image, position="center", size_percent=60, background_color=None):
    """Apply logo to T-shirt image with better blending to reduce shadows"""
    if logo_image is None:
        print("Logo为空，跳过logo应用")
        return shirt_image
    
    # 验证logo是否有效
    if not is_valid_logo(logo_image):
        print("Logo验证失败，跳过logo应用")
        return shirt_image
    
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
    logo_size_factor = size_percent / 100
    logo_width = int(chest_width * logo_size_factor * 0.7)
    logo_height = int(logo_width * logo_with_bg.height / logo_with_bg.width)
    logo_resized = logo_with_bg.resize((logo_width, logo_height), Image.LANCZOS)
    
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
        # 检查logo是否真的有透明像素
        has_transparency = False
        for pixel in logo_resized.getdata():
            if len(pixel) == 4 and pixel[3] < 255:  # 有alpha通道且不完全不透明
                has_transparency = True
                break
        
        print(f"Logo模式: {logo_resized.mode}, 有透明像素: {has_transparency}")
        
        if has_transparency:
            # 直接使用PIL的alpha合成，这样处理透明背景更准确
            print(f"将透明背景logo应用到T恤位置: ({logo_x}, {logo_y})")
            result_image.paste(logo_resized, (logo_x, logo_y), logo_resized)
        else:
            # 如果没有透明像素，先处理背景透明化
            print("Logo没有透明像素，进行背景透明化处理")
            transparent_logo = make_background_transparent(logo_resized, threshold=120)
            result_image.paste(transparent_logo, (logo_x, logo_y), transparent_logo)
    
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
            logo_image = generate_vector_image(logo_prompt, max_retries=3)
            
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
        log(f"generate_complete_design EXCEPTION: {e}\n{traceback_str}")
        return None, {"error": f"Error generating design: {str(e)}\n{traceback_str}"}

def generate_single_design(design_index, design_prompt):
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

@app.route('/generate', methods=['POST'])
def generate_designs():
    data = request.get_json()
    keywords = data.get('keywords', '')
    
    if not keywords:
        return jsonify({'error': 'Please enter at least one keyword'}), 400
    
    try:
        design_count = DEFAULT_DESIGN_COUNT
        designs = []
        
        # 生成多个设计并行处理
        if design_count == 1:
            design, info = generate_complete_design(keywords, 0)
            if design:
                designs.append({
                    'image': image_to_base64(design),
                    'info': info
                })
        else:
            # 使用线程池并行生成多个设计
            max_workers = min(design_count, 20)
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有任务
                future_to_id = {executor.submit(generate_single_design, i, keywords): i for i in range(design_count)}
                
                # 收集结果
                for future in concurrent.futures.as_completed(future_to_id):
                    design_id = future_to_id[future]
                    try:
                        design, info = future.result()
                        if design:
                            designs.append({
                                'image': image_to_base64(design),
                                'info': info,
                                'design_id': design_id
                            })
                    except Exception as e:
                        print(f"Design {design_id} generation failed: {str(e)}")
            
            # 按照ID排序设计
            designs.sort(key=lambda x: x.get('design_id', 0))
        
        return jsonify({
            'success': True,
            'designs': designs,
            'total': len(designs)
        })
    
    except Exception as e:
        import traceback
        error_msg = f"Error generating designs: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return jsonify({'error': error_msg}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
