import requests
from typing import Dict, List, Optional, Any
from .types import CreateInvoiceRequest, ListInvoicesParams


class BixyPayClient:
    """
    Official Python SDK for the BixyPay Fintech API Platform
    
    Example:
        client = BixyPayClient(
            base_url="https://api.bixypay.com",
            api_key="sk_live_your_api_key"
        )
        
        response = client.invoices.create({
            "amount": 100.50,
            "currency": "USD",
            "description": "Payment for Product XYZ"
        })
    """
    
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        jwt_token: Optional[str] = None,
    ):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.jwt_token = jwt_token
        self.session = requests.Session()
        
    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        
        if self.api_key:
            headers["X-API-Key"] = self.api_key
            
        if self.jwt_token:
            headers["Authorization"] = f"Bearer {self.jwt_token}"
            
        return headers
    
    def _request(
        self,
        method: str,
        path: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        headers = self._get_headers()
        
        response = self.session.request(
            method=method,
            url=url,
            json=data,
            params=params,
            headers=headers,
        )
        
        if response.status_code >= 400:
            return {
                "data": None,
                "error": response.json() if response.content else {"message": response.text}
            }
        
        return {
            "data": response.json() if response.content else None,
            "error": None
        }
    
    @property
    def auth(self):
        return AuthResource(self)
    
    @property
    def merchants(self):
        return MerchantsResource(self)
    
    @property
    def invoices(self):
        return InvoicesResource(self)
    
    @property
    def webhooks(self):
        return WebhooksResource(self)
    
    def set_api_key(self, api_key: str):
        self.api_key = api_key
    
    def set_jwt_token(self, token: str):
        self.jwt_token = token


class AuthResource:
    def __init__(self, client: BixyPayClient):
        self.client = client
    
    def register(
        self,
        email: str,
        password: str,
        business_name: str,
        business_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self.client._request(
            "POST",
            "/api/v1/auth/register",
            data={
                "email": email,
                "password": password,
                "businessName": business_name,
                "businessAddress": business_address,
            },
        )
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        response = self.client._request(
            "POST",
            "/api/v1/auth/login",
            data={"email": email, "password": password},
        )
        
        if response["data"] and "access_token" in response["data"]:
            self.client.jwt_token = response["data"]["access_token"]
        
        return response
    
    def create_api_key(self, name: str, scopes: Optional[List[str]] = None) -> Dict[str, Any]:
        return self.client._request(
            "POST",
            "/api/v1/auth/api-keys",
            data={"name": name, "scopes": scopes or []},
        )
    
    def list_api_keys(self) -> Dict[str, Any]:
        return self.client._request("GET", "/api/v1/auth/api-keys")
    
    def revoke_api_key(self, key_id: str) -> Dict[str, Any]:
        return self.client._request("DELETE", f"/api/v1/auth/api-keys/{key_id}")


class MerchantsResource:
    def __init__(self, client: BixyPayClient):
        self.client = client
    
    def get_profile(self) -> Dict[str, Any]:
        return self.client._request("GET", "/api/v1/merchants/profile")
    
    def get_balance(self) -> Dict[str, Any]:
        return self.client._request("GET", "/api/v1/merchants/balance")
    
    def update_kyc_status(self, status: str) -> Dict[str, Any]:
        return self.client._request(
            "PATCH",
            "/api/v1/merchants/kyc",
            data={"status": status},
        )


class InvoicesResource:
    def __init__(self, client: BixyPayClient):
        self.client = client
    
    def create(self, invoice_data: CreateInvoiceRequest) -> Dict[str, Any]:
        return self.client._request(
            "POST",
            "/api/v1/transactions/invoices",
            data=invoice_data,
        )
    
    def get(self, invoice_id: str) -> Dict[str, Any]:
        return self.client._request(
            "GET",
            f"/api/v1/transactions/invoices/{invoice_id}",
        )
    
    def list(self, params: Optional[ListInvoicesParams] = None) -> Dict[str, Any]:
        return self.client._request(
            "GET",
            "/api/v1/transactions/invoices",
            params=params or {},
        )
    
    def update_status(
        self,
        invoice_id: str,
        status: str,
        tx_hash: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self.client._request(
            "PATCH",
            f"/api/v1/transactions/invoices/{invoice_id}/status",
            data={"status": status, "txHash": tx_hash},
        )


class WebhooksResource:
    def __init__(self, client: BixyPayClient):
        self.client = client
    
    def create(self, url: str, events: List[str]) -> Dict[str, Any]:
        return self.client._request(
            "POST",
            "/api/v1/webhooks",
            data={"url": url, "events": events},
        )
    
    def list(self) -> Dict[str, Any]:
        return self.client._request("GET", "/api/v1/webhooks")
    
    def delete(self, webhook_id: str) -> Dict[str, Any]:
        return self.client._request("DELETE", f"/api/v1/webhooks/{webhook_id}")
