import asyncio
import time
from datetime import datetime

import httpx

from .base import BaseAPI, Data, calculate_perc_change
from .exceptions import HttpException, SymbolNotFound


class TipRanks(BaseAPI):
    """
    Unofficial API wrapper class for TipRanks.com.
    Unofficial means this class calls some hidden endpoints
    and provides data that official API doesn't. Also doesn't
    need an authorization.
    """

    def get_dividends(self):
        """
        Fetches symbol dividends with following fields:

        - yield
        - amount
        - ex_date
        - payment_date
        - record_date
        - growth_since

        :return: List of dividend objects.
        :rtype: list
        """

        try:
            response = self._get(
                f"https://tr-cdn.tipranks.com/bff/prod/stock/{self.symbol.lower()}/payload.json"
            )
        except httpx.HTTPStatusError as e:
            if 404 == e.response.status_code:
                raise SymbolNotFound
            raise HttpException from e

        data = response.json()

        dividends = []

        if data["dividend"]["history"]:
            for item in data["dividend"]["history"]:
                dividends.append(
                    {
                        "yield": float(item["yield"] or 0) * 100,
                        "amount": float(item["amount"]),
                        "ex_date": (
                            datetime.strptime(
                                item["executionDate"], "%Y-%m-%dT%H:%M:%S.000Z"
                            ).date()
                            if item["executionDate"]
                            else None
                        ),
                        "payment_date": (
                            datetime.strptime(
                                item["payDate"], "%Y-%m-%dT%H:%M:%S.000Z"
                            ).date()
                            if item["payDate"]
                            else None
                        ),
                        "record_date": (
                            datetime.strptime(
                                item["recordDate"], "%Y-%m-%dT%H:%M:%S.000Z"
                            ).date()
                            if item["recordDate"]
                            else None
                        ),
                        "growth_since": (
                            datetime.strptime(
                                item["growthSince"], "%Y-%m-%dT%H:%M:%S.000Z"
                            )
                            if item["growthSince"]
                            else None
                        ),
                    }
                )

        return dividends

    def get_basic_info(self):
        """
        Downloads basic info. Data are:

        - company_name
        - market
        - description
        - market_cap
        - has_dividends
        - yoy_change
        - year_low
        - year_high
        - pe_ratio
        - eps
        - similar_stocks
            - ticker
            - company_name

        :raises SymbolNotFound: In case data for the given symbol wasn't found.
        :return: Dict with data.
        :rtype: dict
        """

        async def download_basics(symbol):
            """
            Downloads basic info about symbol. Data are:

            - company_name
            - market
            - description
            - has_dividends
            - yoy_change
            - year_low
            - year_hign
            - pe_ratio
            - eps
            - market_cap
            - similar_stocks
                - ticker
                - company_name

            :param str symbol: Symbol the data will be downloaded for.
            :return: Dict with data.
            :rtype: dict
            """

            attempts = 5
            cool_off = 15
            i = 0
            json_data = None

            while i < attempts:
                try:
                    data = await self._aget(
                        f"https://www.tipranks.com/api/assets?tickers={symbol.upper()}",
                        headers={"User-Agent": self.user_agent, "Accept": "*/*"},
                    )
                except httpx.HTTPStatusError as e:
                    if 404 == e.response.status_code:
                        raise SymbolNotFound
                    raise HttpException from e

                try:
                    json_data = Data(data.json())
                    break
                except Exception:
                    print("Got nonsense response - trying again.")
                    i += 1
                    time.sleep(cool_off * i)

            if not json_data:
                return {}

            data = {
                "company_name": json_data["data"][0]["companyFullName"] or "",
                "market": json_data["extraData"][0]["research"]["stockMarketName"]
                or "",
                "description": json_data["extraData"][0]["research"]["description"]
                or "",
                "has_dividends": bool(json_data["data"][0]["dividendYield"] or None),
                "year_low": json_data["data"][0]["low52Weeks"] or 0.0,
                "year_high": json_data["data"][0]["high52Weeks"] or 0.0,
                "pe_ratio": json_data["data"][0]["peRatio"] or 0.0,
                "eps": json_data["data"][0]["lastReportedEps"]["reportedEPS"] or 0.0,
                "market_cap": json_data["data"][0]["marketCap"] or 0.0,
                "similar_stocks": [],
            }

            # YoY change.
            a_year_ago = json_data["data"][0]["landmarkPrices"]["yearAgo"]["p"]
            latest = json_data["extraData"][0]["prices"][-1]["p"]

            if a_year_ago and latest:
                data["yoy_change"] = float(calculate_perc_change(a_year_ago, latest))
            else:
                data["yoy_change"] = None

            return data

        async def download_similar(symbol):
            """
            Downloads similar stocks to the given symbol.

            :param str symbol: Symbol the data will be downloaded for.
            :return: Dict with data.
            :rtype: dict
            """

            try:
                data = await self._aget(
                    f"https://tr-cdn.tipranks.com/bff/prod/stock/{symbol.lower()}/payload.json",
                    headers={"User-Agent": self.user_agent},
                )
            except httpx.HTTPStatusError as e:
                # Checking if symbol was even found.
                if 404 == e.response.status_code:
                    raise SymbolNotFound
                raise HttpException from e

            json_data = Data(data.json())
            similar_stocks = []

            for item in json_data["similar"]["similar"][1:]:
                similar_stocks.append(
                    {"ticker": item["ticker"], "company_name": item["name"]}
                )

            return {"similar_stocks": similar_stocks}

        async def main():
            basic, additionals = await asyncio.gather(
                download_basics(self.symbol), download_similar(self.symbol)
            )
            basic.update(additionals)

            return basic

        return asyncio.run(main())

    def get_current_price_change(self):
        """
        Fetches current market price inc. pre/post market
        prices/percent/value changes. Also returns current
        market state (pre-market, open, post-market).

        Fetched stucture has following fields:

        - state (pre-market, open, post-market, closed)
        - pre_market
            - change
                - percents
                - value
            - value
        - current_market
            - change
                - percents
                - value
            - value
        - post_market
            - change
                - percents
                - value
            - value

        Values are floats (if present) or 0.0.
        Returned dict looks like:

        .. code-block:: python

            {
                "state": "open",
                "pre_market": {
                    "change": {
                        "percents": -1.32476,
                        "value": -1.42001
                    },
                    "value": 105.77
                },
                "current_market": {
                    "change": {
                        "percents": -1.6046284000000002,
                        "value": -1.7200012
                    },
                    "value": 105.47
                },
                "post_market": {
                    "change": {
                        "percents": 0.0,
                        "value": 0.0
                    },
                    "value": 0.0
                }
            }

        :return: Current/Pre/Post market numbers (all are floats).
        :rtype: dict
        """

        try:
            response = self._get(
                f"https://market.tipranks.com/api/quotes/GetQuotes?app_name=tr&tickers={self.symbol.upper()}"
            )
        except httpx.HTTPStatusError as e:
            raise HttpException from e

        try:
            data = response.json()["quotes"][0]
        except IndexError:
            raise SymbolNotFound

        output = {
            "state": "closed",
            "pre_market": {
                "change": {
                    "percents": 0.0,
                    "value": 0.0,
                },
                "value": 0.0,
            },
            "current_market": {
                "change": {
                    "percents": data["changePercent"],
                    "value": data["changeAmount"],
                },
                "value": data["price"],
            },
            "post_market": {"change": {"percents": 0.0, "value": 0.0}, "value": 0.0},
        }

        if data["isPremarket"]:
            output["pre_market"]["change"]["percents"] = data["prePostMarket"][
                "changePercent"
            ]
            output["pre_market"]["change"]["value"] = data["prePostMarket"][
                "changeAmount"
            ]
            output["pre_market"]["value"] = data["prePostMarket"]["price"]
            output["state"] = "pre-market"

        elif data["isAfterMarket"]:
            output["post_market"]["change"]["percents"] = data["prePostMarket"][
                "changePercent"
            ]
            output["post_market"]["change"]["value"] = data["prePostMarket"][
                "changeAmount"
            ]
            output["post_market"]["value"] = data["prePostMarket"]["price"]
            output["state"] = "post-market"

        elif data["isMarketOpen"]:
            output["state"] = "open"

        return output
