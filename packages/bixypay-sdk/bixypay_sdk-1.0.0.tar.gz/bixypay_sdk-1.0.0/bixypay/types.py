from typing import TypedDict, Optional, Any, Dict


class CreateInvoiceRequest(TypedDict, total=False):
    amount: float
    currency: str
    description: Optional[str]
    metadata: Optional[Dict[str, Any]]
    callbackUrl: Optional[str]


class ListInvoicesParams(TypedDict, total=False):
    page: Optional[int]
    limit: Optional[int]
