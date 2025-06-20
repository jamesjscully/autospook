import os
import re
from flask import Flask, render_template, request, escape, jsonify
from markupsafe import Markup
from orchestrator import generate_report, Analysis
import logging
from flask_talisman import Talisman
from auth import require_auth, init_auth_routes, get_auth_status

app = Flask(__name__)

# Security headers
csp = {
    'default-src': "'self'",
    'script-src': "'self' 'unsafe-inline' https://unpkg.com https://cdn.tailwindcss.com",
    'style-src': "'self' 'unsafe-inline' https://cdn.tailwindcss.com",
    'img-src': "'self' data:",
    'connect-src': "'self'",
    'font-src': "'self'",
    'object-src': "'none'",
    'media-src': "'self'",
    'frame-src': "'none'",
}

# Disable HTTPS enforcement in development
if os.getenv('FLASK_ENV') != 'production':
    Talisman(app, content_security_policy=csp, force_https=False)
else:
    Talisman(app, content_security_policy=csp)

# Security Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Input validation
def validate_input(text, max_length=1000):
    """Validate and sanitize user input"""
    if not text or not isinstance(text, str):
        return None
    
    # Remove excessive whitespace and limit length
    text = text.strip()[:max_length]
    
    # Basic pattern validation - alphanumeric, spaces, basic punctuation
    if not re.match(r'^[a-zA-Z0-9\s\-_.,;:()@]+$', text):
        raise ValueError("Input contains invalid characters")
    
    return text

def sanitize_html(html_content):
    """Basic HTML sanitization for display"""
    if not html_content:
        return ""
    
    # Allow only safe HTML tags
    import bleach
    allowed_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'a']
    allowed_attributes = {'a': ['href', 'target', 'class']}
    
    return bleach.clean(html_content, tags=allowed_tags, attributes=allowed_attributes)

# Initialize authentication routes
init_auth_routes(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health_check():
    """Public health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'service': 'autospook',
        'version': '1.0.0'
    })

@app.route('/submit', methods=['POST'])
@require_auth
def submit_target():
    try:
        # Validate and sanitize inputs
        target_name = validate_input(request.form.get('target_name', ''), max_length=200)
        target_context = validate_input(request.form.get('target_context', ''), max_length=2000)
        
        if not target_name:
            raise ValueError("Target name is required")
        
        logger.info(f"Starting investigation for target: {target_name[:50]}... (User: {request.auth_user})")
        
        analysis: Analysis = generate_report(target_name, target_context)

        return f"""
        <div class="mt-4 p-4 bg-gray-700 border border-gray-600 rounded-lg">
            <div class="flex justify-between items-center mb-4">
                <h3 class="font-bold text-green-400">OSINT Analysis Complete</h3>
                <div class="flex items-center space-x-4">
                    <span class="font-semibold text-gray-300">Target:</span>
                    <span class="text-white">{escape(analysis.target_name)}</span>
                    <span class="font-semibold text-gray-300">Risk Level:</span>
                    <span class="px-2 py-1 rounded text-sm {get_risk_color(analysis.risk_level)}">
                        {escape(analysis.risk_level)}
                    </span>
                </div>
            </div>

            <div class="bg-gray-800 border border-gray-600 rounded-lg p-6 max-h-96 overflow-y-auto">
                <div class="prose prose-invert prose-sm max-w-none">
                    <style>
                        .prose h2 {{ color: #10b981; margin-top: 1.5rem; margin-bottom: 1rem; }}
                        .prose h3 {{ color: #34d399; margin-top: 1rem; margin-bottom: 0.5rem; }}
                        .prose p {{ margin-bottom: 1rem; line-height: 1.6; }}
                        .prose ul {{ margin-bottom: 1rem; }}
                        .prose li {{ margin-bottom: 0.5rem; }}
                        .prose strong {{ color: #fbbf24; }}
                    </style>
                    {Markup(sanitize_html(analysis.html_report))}
                </div>
            </div>
        </div>
        """

    except ValueError as e:
        logger.warning(f"Input validation error: {e}")
        return f"""
        <div class="mt-4 p-4 bg-red-900 border border-red-700 text-red-200 rounded-lg">
            <h3 class="font-bold">Invalid Input</h3>
            <p class="text-sm mt-2">Please check your input and try again.</p>
        </div>
        """
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)[:100]}...")  # Log full error server-side
        return f"""
        <div class="mt-4 p-4 bg-red-900 border border-red-700 text-red-200 rounded-lg">
            <h3 class="font-bold">Analysis Failed</h3>
            <p class="text-sm mt-2">An error occurred during analysis. Please try again.</p>
            <p class="text-sm mt-1">Ensure all required API keys are configured.</p>
        </div>
        """

def get_risk_color(risk_level):
    risk_colors = {
        'Low': 'bg-green-600 text-green-100',
        'Medium': 'bg-yellow-600 text-yellow-100', 
        'High': 'bg-red-600 text-red-100'
    }
    return risk_colors.get(risk_level, 'bg-gray-600 text-gray-100')

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)