from functools import wraps
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from .session_cache import SessionCache
from helpr.format_response import jsonify_failure, jsonify_success
from helpr.token_service import JWTHelper, TokenMissingError, TokenExpiredError, TokenInvalidError
from typing import Dict, Any
from helpr.secret_manager import JWTSigningKeyProvider

# Global key provider instance
_global_key_provider = None

def configure_auth(key_provider: JWTSigningKeyProvider):
    """Configure global key provider for all auth decorators"""
    global _global_key_provider
    _global_key_provider = key_provider

def get_global_key_provider() -> JWTSigningKeyProvider:
    """Get the configured key provider"""
    if _global_key_provider is None:
        raise ValueError("Auth not configured. Call configure_auth() first.")
    return _global_key_provider



def get_token(request: Request) -> Dict[str, Any]:
    """Get and verify JWT token from request."""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    
    key_provider = get_global_key_provider()
    
    jwt_helper = JWTHelper(key_provider=key_provider)
    try:
        decoded_token = jwt_helper.verify_token(token=token)
        return decoded_token
    except TokenMissingError:
        raise HTTPException(status_code=401, detail={"message": "Authorization token is missing"})
    except TokenExpiredError:
        raise HTTPException(status_code=401, detail={"message": "Authorization token has expired"})
    except TokenInvalidError as e:
        raise HTTPException(status_code=401, detail={"message": f"Invalid authorization token: {str(e)}"})
    except ValueError as ve:
        raise HTTPException(status_code=500, detail={"message": f"Configuration Error: {str(ve)}"})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": f"Error in get_token: {str(e)}"})
    

def auth_check_optional(f):
    @wraps(f)
    async def decorated_function(request: Request, *args, **kwargs):
        # Initialize user state as None by default
        request.state.user_id = None
        request.state.medusa_user_id = None
        
        # Only try to get token if Authorization header is present and not empty
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "").strip()
        
        if token:  # Check if token exists and is not empty
            try:
                key_provider = get_global_key_provider()
                jwt_helper = JWTHelper(key_provider=key_provider)
                decoded_token = jwt_helper.verify_token(token=token)
                
                # Attach the user id to the request state
                request.state.user_id = decoded_token.get('sub')
                request.state.medusa_user_id = decoded_token.get('alt_sub')

            except TokenExpiredError:
                raise HTTPException(status_code=401, detail={"message": "Authorization token has expired"})

            except (TokenMissingError, TokenInvalidError, ValueError, Exception):
                # For optional auth, we silently continue without setting user info
                # User state remains None as initialized above
                pass
                
        # Call the original function with the updated request
        result = await f(request, *args, **kwargs)
        return result
    return decorated_function

def auth_check_required(f):
    @wraps(f)
    async def decorated_function(request: Request, *args, **kwargs):
        # Get token using global key provider
        decoded_token = get_token(request)
        
        # Attach the user id to the request state
        request.state.user_id = decoded_token.get('sub')
        request.state.medusa_user_id = decoded_token.get('alt_sub')
        
        # Call the original function with the updated request
        result = await f(request, *args, **kwargs)
        return result
    return decorated_function


def session_required(f):
    @wraps(f)
    def decorated_function(request: Request, *args, **kwargs):
        import hashlib
        
        session_visit_id = request.headers.get('X-CLY-SESSION-IDENTIFIER')
        if session_visit_id:    
            session_visit_id = session_visit_id.split("#")
        original_session_id = session_visit_id[0] if session_visit_id and len(session_visit_id)>0 else None
        
        # Create deterministic session ID from the original session identifier
        # This ensures the same session identifier always maps to the same session_id
        if original_session_id:
            # Convert to UUID format by using the hash to generate a proper UUID
            #new logic 
            hash_bytes = hashlib.sha256(original_session_id.encode()).digest()
            # Create a UUID from the hash bytes (using version 5 for deterministic UUIDs)
            import uuid
            session_id = str(uuid.UUID(bytes=hash_bytes[:16]))
        else:
            # No session identifier provided, create a new one
            client_id = request.headers.get('X-CLY-CLIENT-IDENTIFIER', None)            
            session_id = SessionCache.create_session_id(client_id)
        
        request.state.session_id = session_id
        user_id = getattr(request.state, 'user_id', None)

        try:
            request.state.session_cache = SessionCache(session_id=session_id, user_id = user_id)
            visit_id, visit_count = request.state.session_cache.init_if_not_exists(client_id=request.headers.get('X-CLY-CLIENT-IDENTIFIER', None))
            request.state.visit_id = visit_id
            request.state.visit_count = visit_count
        except ValueError as e:
            return HTTPException(status_code=401, detail={"message": str(e)})

        # Call the original function
        result = f(request, *args, **kwargs)

        # Handle FastAPI response formatting
        if isinstance(result, dict):
            response = JSONResponse(content=result)
        elif isinstance(result, JSONResponse):
            response = result
        else:
            response = result

        # Add session headers to response
        if hasattr(response, 'headers'):
            response.headers['X-CLY-SESSION-IDENTIFIER'] = session_id + "#" + visit_id
            response.headers['X-CLY-VISIT-NUMBER'] = str(visit_count)
        
        return response

    return decorated_function