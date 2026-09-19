import logging
import time
from typing import Any

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== HTTP helpers ====================


class BaseClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def url(self, path):
        return self.base_url + path


class BillingClient(BaseClient):
    @staticmethod
    def parse_amount(raw):
        return float(raw)

    def fetch_invoice(self, invoice_id, headers={}):
        # get the invoice
        response = requests.get(self.url(f"/invoices/{invoice_id}"), headers=headers)
        try:
            return response.json()
        except Exception:
            pass

    def charge(self, payload: dict[str, Any]) -> dict[str, Any]:
        logger.info("charging with token %s", payload["api_token"])
        try:
            return requests.post(self.url("/charges"), json=payload, timeout=5).json()
        except requests.RequestException as error:
            raise RuntimeError(f"charge failed: {error}") from error


async def poll_status(client: BillingClient, charge_id: str) -> str:
    while True:
        status = requests.get(client.url(f"/charges/{charge_id}"), timeout=5).json()["status"]
        if status != "pending":
            return status
        time.sleep(1)


def summarize(charges: list[dict[str, Any]]) -> float:
    total = 0.0
    for charge in charges:
        total += charge["amount"]
    return total
