import jwt
import requests
from fastapi import HTTPException, status
from functools import lru_cache
import os
from typing import Dict, Any


class Auth0JWTVerifier:
    def __init__(self):
        self.domain = os.getenv('AUTH0_DOMAIN')
        self.audience = os.getenv('AUTH0_AUDIENCE', 'https://your-api-identifier')
        self.algorithms = ['RS256']
        
        if not self.domain:
            raise ValueError("AUTH0_DOMAIN environment variable is required")
    
    @lru_cache(maxsize=1)
    def get_jwks(self) -> Dict[str, Any]:
        """Auth0のJWKS（JSON Web Key Set）を取得"""
        try:
            jwks_url = f'https://{self.domain}/.well-known/jwks.json'
            response = requests.get(jwks_url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch JWKS: {str(e)}"
            )
    
    def get_rsa_key(self, token: str) -> Dict[str, Any]:
        """JWTヘッダーからキーIDを取得し、対応するRSAキーを返す"""
        try:
            unverified_header = jwt.get_unverified_header(token)
        except jwt.DecodeError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token header"
            )
        
        jwks = self.get_jwks()
        
        for key in jwks['keys']:
            if key['kid'] == unverified_header['kid']:
                return {
                    'kty': key['kty'],
                    'kid': key['kid'],
                    'use': key['use'],
                    'n': key['n'],
                    'e': key['e']
                }
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to find appropriate key"
        )
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """JWTトークンを検証し、ペイロードを返す"""
        rsa_key = self.get_rsa_key(token)
        
        try:
            public_key = jwt.algorithms.RSAAlgorithm.from_jwk(rsa_key)
            payload = jwt.decode(
                token,
                public_key,
                algorithms=self.algorithms,
                audience=self.audience,
                issuer=f'https://{self.domain}/'
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidAudienceError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid audience"
            )
        except jwt.InvalidIssuerError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid issuer"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )


# シングルトンインスタンス
auth0_verifier = Auth0JWTVerifier()