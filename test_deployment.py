#!/usr/bin/env python3
"""
Test script to validate the Flask app deployment readiness
"""

import sys
import importlib
import os

def test_imports():
    """Test if all required modules can be imported"""
    required_modules = [
        'flask', 'PIL', 'requests', 'openai', 
        'numpy', 'dashscope', 'fabric_texture'
    ]
    
    print("Testing imports...")
    for module in required_modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            return False
    return True

def test_files():
    """Test if all required files exist"""
    required_files = [
        'flask_app.py',
        'fabric_texture.py', 
        'white_shirt.png',
        'templates/index.html',
        'static/css/style.css',
        'requirements.txt',
        'Procfile'
    ]
    
    print("\nTesting files...")
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - missing")
            return False
    return True

def test_flask_app():
    """Test if Flask app can be imported and initialized"""
    print("\nTesting Flask app...")
    try:
        from flask_app import app
        print("✅ Flask app imported successfully")
        
        # Test if app has required routes
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        required_routes = ['/', '/generate']
        
        for route in required_routes:
            if route in routes:
                print(f"✅ Route {route} exists")
            else:
                print(f"❌ Route {route} missing")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Flask app test failed: {e}")
        return False

def test_deployment_config():
    """Test Railway deployment configuration"""
    print("\nTesting deployment config...")
    
    # Check Procfile
    if os.path.exists('Procfile'):
        with open('Procfile', 'r') as f:
            content = f.read()
            if 'python flask_app.py' in content:
                print("✅ Procfile configured correctly")
            else:
                print("❌ Procfile misconfigured")
                return False
    
    # Check requirements.txt
    if os.path.exists('requirements.txt'):
        with open('requirements.txt', 'r') as f:
            content = f.read()
            if 'Flask' in content and 'streamlit' not in content:
                print("✅ requirements.txt configured correctly")
            else:
                print("❌ requirements.txt still contains Streamlit or missing Flask")
                return False
    
    return True

def main():
    """Run all tests"""
    print("🚀 Testing Flask T-shirt Design App Deployment Readiness\n")
    
    tests = [
        ("Import Test", test_imports),
        ("File Test", test_files), 
        ("Flask App Test", test_flask_app),
        ("Deployment Config Test", test_deployment_config)
    ]
    
    all_passed = True
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running {test_name}")
        print('='*50)
        
        if not test_func():
            all_passed = False
    
    print(f"\n{'='*50}")
    if all_passed:
        print("🎉 All tests passed! The app is ready for deployment.")
        print("\nTo deploy to Railway:")
        print("1. Push code to GitHub")
        print("2. Connect GitHub repo to Railway")  
        print("3. Railway will auto-deploy using Procfile")
        print("\nTo test locally:")
        print("python flask_app.py")
    else:
        print("❌ Some tests failed. Please fix the issues before deployment.")
        sys.exit(1)
    print('='*50)

if __name__ == '__main__':
    main()
