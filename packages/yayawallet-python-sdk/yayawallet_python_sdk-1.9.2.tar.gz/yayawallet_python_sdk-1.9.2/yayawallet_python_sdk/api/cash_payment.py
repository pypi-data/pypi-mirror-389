from typing import Optional
from ..functions.api_request import api_request

async def pay_by_cash(urlSlag: str, receiver: str, notes: Optional[str] = None, api_key: str = None):
  api_response = await api_request("POST", f"/payment-intent/{urlSlag}/mark-cash-paid", "", {"receiver": receiver, "notes":  notes}, api_key)
  return api_response

async def get_daily_cash_transactions(accountId: str, date: str , api_key: str = None):
  api_response = await api_request("GET", f"/payment-intent/cash-transactions/daily/{accountId}/{date}", "", None, api_key)
  return api_response

async def get_blocked_balace(accountId: str, api_key: str = None):
  api_response = await api_request("GET", f"/cash-settlement/blocked-balances/{accountId}", "", None, api_key)
  return api_response

async def process_settlement(data: dict, api_key: str = None):
  api_response = await api_request("POST", "/cash-settlement/process", "", data, api_key)
  return api_response

async def get_setlement_statics(accountId: str, api_key: str = None):
  api_response = await api_request("GET", f"/cash-settlement/stats/{accountId}", "", None, api_key)
  return api_response

async def send_otp_payment(phone: str, uniqueRef: str, api_key: str = None):
  api_response = await api_request("POST", "/payment-intent/send-otp-payment", "", {"phone": phone, "uniqueRef":  uniqueRef}, api_key)
  return api_response

async def verify_otp_payment(phone: str, uniqueRef: str, otp: str, api_key: str = None):
  api_response = await api_request("POST", "/payment-intent/verify-otp-payment", "", {"phone": phone, "uniqueRef":  uniqueRef, otp: str}, api_key)
  return api_response
