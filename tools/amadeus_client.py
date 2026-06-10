#!/usr/bin/env python3
"""Thin client for the Amadeus Self-Service API.

Handles OAuth2 (client_credentials) token caching and the few endpoints the
flight optimizer needs:
  - Flight Offers Search  (POST /v2/shopping/flight-offers) with flexible-date
    calendar (departureDateTimeRange.dateWindow) and multi-city/open-jaw support.
  - Itinerary Price Metrics (GET /v1/analytics/itinerary-price-metrics) for the
    "is this a good price?" quartile flag.

Credentials come from .env (see .env.example):
  AMADEUS_CLIENT_ID, AMADEUS_CLIENT_SECRET, AMADEUS_ENV (test|production)

This uses only `requests` (already in the conda env). No SDK dependency.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"

HOSTS = {
    "test": "https://test.api.amadeus.com",
    "production": "https://api.amadeus.com",
}


class AmadeusError(RuntimeError):
    """Raised for unrecoverable Amadeus API problems."""


class AmadeusClient:
    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        env: str | None = None,
        cache_raw: bool = True,
    ) -> None:
        load_dotenv(ROOT / ".env")
        self.client_id = client_id or os.getenv("AMADEUS_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("AMADEUS_CLIENT_SECRET")
        self.env = (env or os.getenv("AMADEUS_ENV") or "test").strip().lower()
        if self.env not in HOSTS:
            self.env = "test"
        self.base = HOSTS[self.env]
        self.cache_raw = cache_raw
        self._token: str | None = None
        self._token_expiry: float = 0.0
        self._session = requests.Session()

    @property
    def configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    # ------------------------------------------------------------------ auth
    def _ensure_token(self) -> str:
        if self._token and time.time() < self._token_expiry - 30:
            return self._token
        if not self.configured:
            raise AmadeusError(
                "Amadeus credentials missing. Set AMADEUS_CLIENT_ID and "
                "AMADEUS_CLIENT_SECRET in .env (see .env.example)."
            )
        url = f"{self.base}/v1/security/oauth2/token"
        resp = self._session.post(
            url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            timeout=30,
        )
        if resp.status_code != 200:
            raise AmadeusError(f"Auth failed ({resp.status_code}): {resp.text[:300]}")
        payload = resp.json()
        self._token = payload["access_token"]
        self._token_expiry = time.time() + float(payload.get("expires_in", 1799))
        return self._token

    # --------------------------------------------------------------- requests
    def _request(self, method: str, path: str, *, params=None, body=None, tag: str = "") -> dict:
        """Authenticated request with simple 429 backoff and optional raw caching."""
        token = self._ensure_token()
        url = f"{self.base}{path}"
        headers = {"Authorization": f"Bearer {token}"}
        backoff = 2.0
        last_text = ""
        for attempt in range(4):
            if method == "GET":
                resp = self._session.get(url, headers=headers, params=params, timeout=60)
            else:
                headers["Content-Type"] = "application/json"
                resp = self._session.post(url, headers=headers, data=json.dumps(body), timeout=60)

            if resp.status_code == 429:
                time.sleep(backoff)
                backoff *= 2
                last_text = resp.text
                continue
            if resp.status_code == 401:  # token might have expired; refresh once
                self._token = None
                token = self._ensure_token()
                headers["Authorization"] = f"Bearer {token}"
                last_text = resp.text
                continue

            data = self._safe_json(resp)
            if self.cache_raw and tag:
                OUT.mkdir(exist_ok=True)
                (OUT / f"amadeus_{tag}.json").write_text(json.dumps(data, indent=2))
            if resp.status_code >= 400:
                # Surface Amadeus error array but don't crash the whole run.
                return data if isinstance(data, dict) else {"errors": [{"detail": resp.text[:300]}]}
            return data
        raise AmadeusError(f"Rate limited repeatedly on {path}: {last_text[:200]}")

    @staticmethod
    def _safe_json(resp: requests.Response) -> dict:
        try:
            return resp.json()
        except ValueError:
            return {"errors": [{"detail": resp.text[:300]}]}

    # --------------------------------------------------------------- endpoints
    def search_offers(
        self,
        origin_destinations: list[dict],
        *,
        currency: str = "GBP",
        nonstop: bool = False,
        adults: int = 1,
        max_offers: int = 50,
        tag: str = "",
    ) -> dict:
        """POST /v2/shopping/flight-offers.

        `origin_destinations` is a list of dicts like:
            {"id": "1", "originLocationCode": "LHR", "destinationLocationCode": "HKG",
             "departureDateTimeRange": {"date": "2026-06-22", "dateWindow": "I3D"}}
        Multiple entries => multi-city / open-jaw itinerary.
        """
        for i, od in enumerate(origin_destinations, start=1):
            od.setdefault("id", str(i))
        body = {
            "currencyCode": currency,
            "originDestinations": origin_destinations,
            "travelers": [{"id": "1", "travelerType": "ADULT"} for _ in range(adults)],
            "sources": ["GDS"],
            "searchCriteria": {
                "maxFlightOffers": max_offers,
                "flightFilters": {
                    "connectionRestriction": {"airportChangeAllowed": True},
                },
            },
        }
        if nonstop:
            body["searchCriteria"]["flightFilters"]["connectionRestriction"][
                "maxNumberOfConnections"
            ] = 0
        return self._request("POST", "/v2/shopping/flight-offers", body=body, tag=tag)

    def price_metrics(
        self,
        origin: str,
        dest: str,
        date: str,
        *,
        currency: str = "GBP",
        one_way: bool = True,
        tag: str = "",
    ) -> dict:
        """GET /v1/analytics/itinerary-price-metrics (quartile distribution)."""
        params = {
            "originIataCode": origin,
            "destinationIataCode": dest,
            "departureDate": date,
            "currencyCode": currency,
            "oneWay": str(one_way).lower(),
        }
        return self._request(
            "GET", "/v1/analytics/itinerary-price-metrics", params=params, tag=tag
        )
