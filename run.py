#!/usr/bin/env python3
"""
Local development runner for the Flask T-shirt design app
"""

if __name__ == '__main__':
    from flask_app import app
    app.run(debug=True, host='0.0.0.0', port=5000)
