"""
Session tracking service for managing user sessions.
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from flask import request, current_app
from flask_login import current_user
import requests
from user_agents import parse as parse_user_agent

from ..models import UserSession, User
from ..extensions import db

logger = logging.getLogger(__name__)


def get_client_ip() -> str:
    """
    Get the client's IP address from request.
    Handles X-Forwarded-For header for apps behind proxies.
    """
    if request.headers.get('X-Forwarded-For'):
        # X-Forwarded-For can contain multiple IPs, take the first one
        ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
        return ip
    return request.remote_addr or '0.0.0.0'


def parse_user_agent_string(user_agent_str: str) -> Dict[str, Optional[str]]:
    """
    Parse user agent string and extract browser/OS/device information.
    
    Returns:
        Dictionary with browser_name, browser_version, os_name, os_version, device_type
    """
    try:
        ua = parse_user_agent(user_agent_str)
        
        # Determine device type
        device_type = 'desktop'
        if ua.is_mobile:
            device_type = 'mobile'
        elif ua.is_tablet:
            device_type = 'tablet'
        
        return {
            'browser_name': ua.browser.family if ua.browser.family else None,
            'browser_version': '.'.join(str(v) for v in ua.browser.version[:2]) if ua.browser.version else None,
            'os_name': ua.os.family if ua.os.family else None,
            'os_version': '.'.join(str(v) for v in ua.os.version[:2]) if ua.os.version else None,
            'device_type': device_type
        }
    except Exception as e:
        logger.warning(f"Failed to parse user agent: {e}")
        return {
            'browser_name': None,
            'browser_version': None,
            'os_name': None,
            'os_version': None,
            'device_type': 'desktop'
        }


def get_ip_geolocation(ip_address: str) -> Dict[str, Optional[str]]:
    """
    Get geolocation information for an IP address using ipapi.co free tier.
    
    Returns:
        Dictionary with city, region, country
    """
    # Skip geolocation for localhost/private IPs
    if ip_address in ('127.0.0.1', 'localhost', '0.0.0.0') or ip_address.startswith('192.168.') or ip_address.startswith('10.'):
        return {
            'city': None,
            'region': None,
            'country': None
        }
    
    try:
        # Use ipapi.co free tier (no API key required, rate limited)
        url = f'https://ipapi.co/{ip_address}/json/'
        response = requests.get(url, timeout=3)
        
        if response.status_code == 200:
            data = response.json()
            
            # Map region code (e.g., "US", "EU") - use country code as region for simplicity
            region = data.get('country_code')
            
            return {
                'city': data.get('city'),
                'region': region,
                'country': data.get('country_code')
            }
        else:
            logger.warning(f"Geolocation API returned status {response.status_code} for IP {ip_address}")
            return {
                'city': None,
                'region': None,
                'country': None
            }
    except requests.exceptions.Timeout:
        logger.warning(f"Geolocation API timeout for IP {ip_address}")
        return {
            'city': None,
            'region': None,
            'country': None
        }
    except Exception as e:
        logger.warning(f"Failed to get geolocation for IP {ip_address}: {e}")
        return {
            'city': None,
            'region': None,
            'country': None
        }


def create_session(user: User, session_token: Optional[str] = None) -> UserSession:
    """
    Create a new session record for a user.
    
    Args:
        user: User instance
        session_token: Optional session token (will generate if not provided)
    
    Returns:
        UserSession instance
    """
    if session_token is None:
        session_token = str(uuid.uuid4())
    
    # Get request information
    ip_address = get_client_ip()
    user_agent_str = request.headers.get('User-Agent', 'Unknown')
    
    # Parse user agent
    ua_info = parse_user_agent_string(user_agent_str)
    
    # Get geolocation (non-blocking, don't fail if it doesn't work)
    geo_info = get_ip_geolocation(ip_address)
    
    # Mark all other sessions as not current
    UserSession.query.filter_by(user_id=user.id, is_current=True).update({'is_current': False})
    
    # Create session record
    session = UserSession(
        user_id=user.id,
        session_token=session_token,
        ip_address=ip_address,
        user_agent=user_agent_str,
        browser_name=ua_info['browser_name'],
        browser_version=ua_info['browser_version'],
        os_name=ua_info['os_name'],
        os_version=ua_info['os_version'],
        device_type=ua_info['device_type'],
        city=geo_info['city'],
        region=geo_info['region'],
        country=geo_info['country'],
        is_current=True,
        is_active=True
    )
    
    db.session.add(session)
    db.session.commit()
    
    logger.info(f"Created session {session_token[:8]}... for user {user.id}")
    return session


def update_session_activity(session_token: str) -> bool:
    """
    Update the last_activity_at timestamp for a session.
    
    Args:
        session_token: Session token to update
    
    Returns:
        True if session was updated, False if not found
    """
    session = UserSession.query.filter_by(session_token=session_token, is_active=True).first()
    if session:
        session.last_activity_at = datetime.utcnow()
        db.session.commit()
        return True
    return False


def expire_old_sessions() -> int:
    """
    Mark sessions as inactive if they haven't been active for 24 hours.
    
    Returns:
        Number of sessions expired
    """
    expiration_time = datetime.utcnow() - timedelta(hours=24)
    expired_sessions = UserSession.query.filter(
        UserSession.is_active == True,
        UserSession.last_activity_at < expiration_time
    ).all()
    
    count = 0
    for session in expired_sessions:
        session.is_active = False
        session.is_current = False
        count += 1
    
    if count > 0:
        db.session.commit()
        logger.info(f"Expired {count} inactive sessions")
    
    return count


def cleanup_old_sessions() -> int:
    """
    Delete sessions older than 90 days.
    
    Returns:
        Number of sessions deleted
    """
    cleanup_time = datetime.utcnow() - timedelta(days=90)
    old_sessions = UserSession.query.filter(
        UserSession.login_at < cleanup_time
    ).all()
    
    count = len(old_sessions)
    for session in old_sessions:
        db.session.delete(session)
    
    if count > 0:
        db.session.commit()
        logger.info(f"Cleaned up {count} old sessions")
    
    return count


def get_current_session_token() -> Optional[str]:
    """
    Get the session token for the current Flask-Login session.
    Retrieves from Flask session storage.
    
    Returns:
        Session token if found, None otherwise
    """
    if not current_user.is_authenticated:
        return None
    
    # Get token from Flask session
    from flask import session as flask_session
    return flask_session.get('session_token')


def revoke_session(session_id: str, user_id: str) -> bool:
    """
    Revoke a session by marking it as inactive.
    
    Args:
        session_id: Session ID to revoke
        user_id: User ID (for security - ensure user owns the session)
    
    Returns:
        True if session was revoked, False if not found or not owned by user
    """
    session = UserSession.query.filter_by(id=session_id, user_id=user_id).first()
    if session:
        session.is_active = False
        session.is_current = False
        db.session.commit()
        logger.info(f"Revoked session {session_id} for user {user_id}")
        return True
    return False


def get_user_sessions(user_id: str) -> list:
    """
    Get all active sessions for a user, ordered by last activity.
    
    Args:
        user_id: User ID
    
    Returns:
        List of UserSession objects
    """
    return UserSession.query.filter_by(user_id=user_id).order_by(
        UserSession.last_activity_at.desc()
    ).all()

