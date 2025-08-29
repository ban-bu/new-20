#!/usr/bin/env python3
"""
Railway部署专用启动脚本
用于确保在Railway环境中正确启动Flask应用
"""

import os
import sys
import logging
from flask_app import app

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """主启动函数"""
    # Railway环境检测
    is_railway = bool(os.environ.get('RAILWAY_ENVIRONMENT'))
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0'
    
    logger.info("=" * 60)
    logger.info("🚀 AI T-shirt Design Generator Starting")
    logger.info("=" * 60)
    logger.info(f"Platform: {'Railway' if is_railway else 'Local'}")
    logger.info(f"Host: {host}")
    logger.info(f"Port: {port}")
    logger.info(f"Python: {sys.version}")
    logger.info("=" * 60)
    
    try:
        # 启动Flask应用
        app.run(
            host=host,
            port=port,
            debug=False,
            threaded=True,
            use_reloader=False  # 避免Railway上的重载问题
        )
    except Exception as e:
        logger.error(f"❌ Server startup failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()