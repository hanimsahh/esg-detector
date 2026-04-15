# import libraries
import os
import requests
from dotenv import load_dotenv

# Load API key from environment variable
load_dotenv()
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")


# Finnhub API client object to interact with the API
class FinnhubClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://finnhub.io/api/v1"

    # internal method to make GET requests to the API
    def _get(self, path: str, **params):
        params["token"] = self.api_key
        response = requests.get(f"{self.base_url}/{path}",
                                params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    
    # method to get basic financial metrics for a given stock symbol
    def get_basic_financials(self, symbol: str):
        return self._get("stock/metric", symbol=symbol, metric="all")


# helper function to extract relevant financial metrics from the API response
def extract_financial_summary(company_name: str, symbol: str, basic: dict) -> dict:
    """Extracts key financial metrics from the API response for a given company.
    Inputs:
        company_name: The name of the company (e.g. "Nike")
        symbol: The stock symbol of the company (e.g. "NKE")
        basic: The API response containing basic financial metrics
    Outputs:        
        A dictionary with the company name, ticker, and selected financial metrics
    """

    metrics = basic.get("metric", {})
    return {
        "company_name": company_name,
        "ticker": symbol,
        "market_cap": metrics.get("marketCapitalization"),
        "revenue_growth": metrics.get("revenueGrowthTTMYoy"),
        "net_margin": metrics.get("netProfitMarginTTM"),
        "debt_to_equity": metrics.get("totalDebt/totalEquityQuarterly"),
        "pe_ratio": metrics.get("peBasicExclExtraTTM"),
    }


# main function to get financial summaries for a predefined list of companies
def get_esg_company_financials() -> dict:
    """Fetches financial summaries for a predefined list of companies using the Finnhub API.
    Outputs:
        A dictionary where each key is a company name and the value is another dictionary containing financial metrics or error information.
    """
    
    if not FINNHUB_API_KEY:
        raise ValueError("FINNHUB_API_KEY not found in environment variables.")

    client = FinnhubClient(FINNHUB_API_KEY)

    companies = {
        "Nike": "NKE",
        "Adidas": "ADDYY",
        "Puma": "PUMSY",
    }

    results = {}

    for company_name, symbol in companies.items():
        try:
            basic = client.get_basic_financials(symbol)
            results[company_name] = extract_financial_summary(company_name, symbol, basic)
        except Exception as e:
            results[company_name] = {
                "company_name": company_name,
                "ticker": symbol,
                "error": str(e),
            }

    return results


if __name__ == "__main__":
    import json
    print(json.dumps(get_esg_company_financials(), indent=2))