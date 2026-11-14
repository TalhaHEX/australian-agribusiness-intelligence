import csv
import json
import random
import time
import urllib.parse

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0",
]

CHROME_VERSIONS = [
    '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
]


def generate_fresh_cookies():
    chrome_options = Options()
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    user_agent = random.choice(USER_AGENTS)
    chrome_options.add_argument(f"user-agent={user_agent}")

    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    url = "https://www.dnb.com/business-directory/company-information.fruit_and_tree_nut_farming.au.html?page=1"
    driver.get(url)
    time.sleep(5)

    selenium_cookies = driver.get_cookies()
    cookies_dict = {cookie["name"]: cookie["value"] for cookie in selenium_cookies}
    driver.quit()
    return cookies_dict


def get_random_headers():
    user_agent = random.choice(USER_AGENTS)
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "origin": "https://www.dnb.com",
        "referer": "https://www.dnb.com/",
        "user-agent": user_agent,
    }
    headers.update(
        {
            "sec-ch-ua": random.choice(CHROME_VERSIONS),
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
        }
    )
    return headers


def extract_company_details(company_url, cookies, headers):
    try:
        # print(f"\n🔍 Extracting details for: {company_url}")

        # ✅ Auto-fix missing dot after "company-profiles"
        if "company-profiles" in company_url and "company-profiles." not in company_url:
            company_url = company_url.replace("company-profiles", "company-profiles.")
            # print(f"🩹 Fixed URL: {company_url}")

        # Encode the corrected URL
        encoded_path = urllib.parse.quote(company_url, safe="")
        api_url = f"https://www.dnb.com/business-directory/api/companyprofile?path={encoded_path}&language=en&country=us"
        # print(f"🧩 Encoded API URL: {api_url}")

        response = requests.get(api_url, cookies=cookies, headers=headers, timeout=20)
        # print(f"📡 Response status: {response.status_code}")

        data = response.json()
        overview = data.get("overview", {}) or {}

        company_address = overview.get("companyLocation", "")
        website = overview.get("website", "")
        company_short_summary = overview.get("companyShortSummaryTest", "")

        merged_industries = {}
        for key in ["otherIndustries", "viewMoreIndustries", "viewMoreOtherIndustries"]:
            merged_industries.update(overview.get(key, {}) or {})

        # print("🏢 Company Address:", company_address)
        # print("🌐 Website:", website)
        # print("📝 Short Summary:", company_short_summary[:100])
        # print("🏭 Merged Industries:", merged_industries)

        return (
            company_address,
            website,
            company_short_summary,
            ", ".join(merged_industries.values()),
        )

    except Exception as e:
        print(f"❌ Error extracting details for {company_url}: {e}")
        return "", "", "", ""


def main():
    csv_filename = "company_details.csv"
    total_pages = 40

    cookies = generate_fresh_cookies()

    with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "Company Name",
                "Profile URL",
                "Location",
                "Sales Revenue",
                "Company Address",
                "Website",
                "Short Summary",
                "Industries",
            ]
        )

    print(f"\n🚀 Starting to scrape {total_pages} pages...\n")

    for current_page in range(1, total_pages + 1):
        print(f"Scraping page {current_page}...")

        json_data = {
            "pageNumber": current_page,
            "industryPath": "fruit_and_tree_nut_farming",
            "countryIsoTwoCode": "au",
        }

        headers = get_random_headers()
        try:
            response = requests.post(
                "https://www.dnb.com/business-directory/api/companyinformation",
                cookies=cookies,
                headers=headers,
                json=json_data,
                timeout=20,
            )
            data = response.json()
            companies = data.get("companyInformationCompany", [])

            with open(csv_filename, mode="a", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)

                for company in companies:
                    name = company.get("primaryName", "N/A")
                    url_path = company.get("companyNameUrl", "")
                    locality = company.get("addressLocalityNameFormatted", "")
                    region = company.get("addressRegionNameFormatted", "")
                    country = company.get("addressCountryName", "")
                    sales = company.get("salesRevenue", "N/A")

                    if not url_path:
                        continue

                    full_url = f"https://www.dnb.com//business-directory/company-profiles{url_path}"

                    # Extract company details from individual page
                    address, website, summary, industries = extract_company_details(
                        full_url, cookies, headers
                    )

                    location = ", ".join([p for p in [locality, region, country] if p])

                    writer.writerow(
                        [
                            name,
                            full_url,
                            location,
                            sales,
                            address,
                            website,
                            summary,
                            industries,
                        ]
                    )

                print(f"✅ Page {current_page}: {len(companies)} companies processed.")

        except Exception as e:
            print(f"❌ Error on page {current_page}: {e}")

        delay = random.uniform(3, 6)
        print(f"   Waiting {delay:.1f}s before next request...")
        time.sleep(delay)

    print(f"\n🎉 Scraping completed! Data saved to {csv_filename}")


if __name__ == "__main__":
    main()
