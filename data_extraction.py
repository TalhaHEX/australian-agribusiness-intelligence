import json
import urllib.parse
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller


class DataExtractor:
    """
    Utility class for extracting deep company profile information from Dun & Bradstreet (D&B).
    """

    def __init__(self, cookies=None, headers=None):
        self.cookies = cookies or self._generate_cookies()
        self.headers = headers or {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://www.dnb.com",
            "referer": "https://www.dnb.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        }

    def _generate_cookies(self):
        """Generates fresh session cookies via automated headless Selenium session."""
        chromedriver_autoinstaller.install()
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        url = "https://www.dnb.com/business-directory/company-information.fruit_and_tree_nut_farming.au.html?page=1"
        driver.get(url)
        selenium_cookies = driver.get_cookies()
        cookies_dict = {c["name"]: c["value"] for c in selenium_cookies}
        driver.quit()
        return cookies_dict

    def extract_data(self, company_path=None):
        """
        Extracts structured profile details for a given company profile URL.
        """
        if not company_path:
            company_path = "https://www.dnb.com//business-directory/company-profiles.treasury_wine_estates_limited.da8825dae5c915b021a0ed0105ed9676"

        encoded_path = urllib.parse.quote(company_path, safe="")
        api_url = f"https://www.dnb.com/business-directory/api/companyprofile?path={encoded_path}&language=en&country=us"

        response = requests.get(api_url, cookies=self.cookies, headers=self.headers, timeout=20)
        data = response.json()

        overview = data.get("overview", {}) or {}
        company_address = overview.get("companyLocation", "")
        website = overview.get("website", "")
        company_short_summary = overview.get("companyShortSummaryTest", "")

        merged_industries = {}
        for key in ["otherIndustries", "viewMoreIndustries", "viewMoreOtherIndustries"]:
            merged_industries.update(overview.get(key, {}) or {})

        print("Company Address:", company_address)
        print("Website:", website)
        print("Company Short Summary:", company_short_summary)
        print("\nMerged Industries:")
        print(json.dumps(merged_industries, indent=2))

        return {
            "address": company_address,
            "website": website,
            "summary": company_short_summary,
            "industries": merged_industries,
        }


if __name__ == "__main__":
    extractor = DataExtractor()
    extractor.extract_data()
