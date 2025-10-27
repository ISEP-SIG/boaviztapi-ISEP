from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from boaviztapi.service.google_auth_service import GoogleAuthService

auth_router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

@auth_router.post('/google/callback', description="TODO")
async def google_signin_callback(request: Request):
    async with request.form() as form:
        request_origin = request.headers.get('origin')
        if not form:
            raise HTTPException(status_code=400, detail="Google sign-in failed, missing request body!")

        # Check double submit cookie
        csrf_token_cookie = request.cookies.get('g_csrf_token')
        csrf_token_body = form['g_csrf_token']
        verify_double_submit_cookie(csrf_token_cookie, csrf_token_body)

        # Verify the ID token
        google_jwt_payload = GoogleAuthService.verify_jwt(form['credential'])
        if not google_jwt_payload:
            raise HTTPException(status_code=401, detail="Google sign-in failed, missing credential!")

        #TODO: add nonce verification by sending it to the frontend on nextjs startup
        return RedirectResponse(status_code=303, url=request_origin)

def verify_double_submit_cookie(csrf_token_cookie: str, csrf_token_body: str):
    if not csrf_token_cookie:
        raise HTTPException(status_code=400, detail="Google CSRF token not found in cookies")
    if not csrf_token_body:
        raise HTTPException(status_code=400, detail="Google CSRF token not found in body")
    if csrf_token_cookie != csrf_token_body:
        raise HTTPException(status_code=400,
                            detail="Google CSRF token mismatch. Failed to verify double submit cookie.")