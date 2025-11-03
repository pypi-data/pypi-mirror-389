# import re
#
# import httpx
#
# from .base import BaseAPI
# from .exceptions import HttpException

# class Yahoo(BaseAPI):
#     """
#     Unofficial API wrapper class for TipRanks.com.
#     Unofficial means this class calls some hidden endpoints
#     and provides data that official API doesn't. Also doesn't
#     need an authorization.
#     """
#
#     def get_current_price_change(self):
#         """
#         Fetches current market price inc. pre/post market
#         prices/percent/value changes. Also returns current
#         market state (pre-market, open, post-market).
#
#         Fetched stucture has following fields:
#
#         - state (pre-market, open, post-market)
#         - pre_market
#             - change
#                 - percents
#                 - value
#             - value
#         - current_market
#             - change
#                 - percents
#                 - value
#             - value
#         - post_market
#             - change
#                 - percents
#                 - value
#             - value
#
#         Values are floats (if present) or None.
#         Returned dict looks like:
#
#         .. code-block:: python
#
#             {
#                 "state": "open",
#                 "pre_market": {
#                     "change": {
#                         "percents": -1.32476,
#                         "value": -1.42001
#                     },
#                     "value": 105.77
#                 },
#                 "current_market": {
#                     "change": {
#                         "percents": -1.6046284000000002,
#                         "value": -1.7200012
#                     },
#                     "value": 105.47
#                 },
#                 "post_market": {
#                     "change": {
#                         "percents": 0.0,
#                         "value": 0.0
#                     },
#                     "value": 0.0
#                 }
#             }
#
#         :return: Current/Pre/Post market numbers (all are floats or None).
#         :rtype: dict
#         """
#
#         def get_state(data):
#             if data["pre_market"]["value"]:
#                 return "pre-market"
#
#             if data["post_market"]["value"]:
#                 return "post-market"
#
#             return "open"
#
#         try:
#             response = self._get(
#                 f"https://finance.yahoo.com/quote/{self.symbol.upper()}/",
#                 headers={
#                     "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/117.0"
#                 },
#             )
#         except httpx.HTTPStatusError as e:
#             raise HttpException from e
#
#         finds = re.findall(r"<fin-streamer[^>].+?>", response.text, re.DOTALL)
#         need_map = {
#             "regularMarketPrice": "price",
#             "regularMarketChange": "change",
#             "regularMarketChangePercent": "change_percents",
#             "postMarketPrice": "post_market_price",
#             "postMarketChange": "post_market_change",
#             "postMarketChangePercent": "post_market_change_percents",
#             "preMarketPrice": "pre_market_price",
#             "preMarketChange": "pre_market_change",
#             "preMarketChangePercent": "pre_market_change_percents",
#         }
#         output = {}
#
#         if finds:
#             for f in finds:
#                 name = re.findall(r'data-field="([a-z]+)"', f, re.IGNORECASE)
#                 symbol = re.findall(r'data-symbol="([\^a-z]+)"', f, re.IGNORECASE)
#
#                 if (
#                     name[0] not in need_map.keys()
#                     or not symbol
#                     or self.symbol.upper() != symbol[0].upper()
#                 ):
#                     continue
#
#                 for key, val in need_map.items():
#                     if key == name[0]:
#                         value = re.findall(
#                             r'value="([-0-9\.a-z]+)"', f, re.DOTALL | re.IGNORECASE
#                         )
#
#                         output[val] = value[0]
#         output = {
#             "pre_market": {
#                 "change": {
#                     "percents": (
#                         float(val)
#                         if (val := output.get("pre_market_change_percents"))
#                         else None
#                     ),
#                     "value": (
#                         float(val) if (val := output.get("pre_market_change")) else None
#                     ),
#                 },
#                 "value": (
#                     float(val) if (val := output.get("pre_market_price")) else None
#                 ),
#             },
#             "current_market": {
#                 "change": {
#                     "percents": float(output["change_percents"]),
#                     "value": float(output["change"]),
#                 },
#                 "value": float(output["price"]),
#             },
#             "post_market": {
#                 "change": {
#                     "percents": (
#                         float(val)
#                         if (val := output.get("post_market_change_percents"))
#                         else None
#                     ),
#                     "value": (
#                         float(val)
#                         if (val := output.get("post_market_change"))
#                         else None
#                     ),
#                 },
#                 "value": (
#                     float(val) if (val := output.get("post_market_price")) else None
#                 ),
#             },
#         }
#         output["state"] = get_state(output)
#
#         return output
