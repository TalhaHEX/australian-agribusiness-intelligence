import csv
import json
import random
import time

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# List of user agents to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:134.0) Gecko/20100101 Firefox/134.0",
]

# Chrome versions for sec-ch-ua header
CHROME_VERSIONS = [
    '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
    '"Google Chrome";v="140", "Not?A_Brand";v="8", "Chromium";v="140"',
    '"Chromium";v="141", "Not?A_Brand";v="99"',
]


def generate_fresh_cookies():
    """
    Use Selenium to visit the page and generate fresh cookies
    Returns a dictionary of cookies
    """
    print("🔧 Starting Selenium to generate fresh cookies...")

    chrome_options = Options()
    # chrome_options.add_argument('--headless')  # Uncomment to run in background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    user_agent = random.choice(USER_AGENTS)
    chrome_options.add_argument(f"user-agent={user_agent}")

    driver = webdriver.Chrome(options=chrome_options)

    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    try:
        url = "https://www.dnb.com/business-directory/company-information.fruit_and_tree_nut_farming.au.html?page=1"
        driver.get(url)

        print("   Waiting for page to load and cookies to be generated...")
        time.sleep(5)

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except:
            pass

        selenium_cookies = driver.get_cookies()
        cookies_dict = {cookie["name"]: cookie["value"] for cookie in selenium_cookies}

        print(f"✅ Successfully generated {len(cookies_dict)} cookies")
        print(f"   Cookie names: {', '.join(cookies_dict.keys())}")

        return cookies_dict

    except Exception as e:
        print(f"❌ Error generating cookies: {e}")
        return {}

    finally:
        driver.quit()
        print("🔒 Browser closed")


def get_random_headers():
    """Generate randomized headers for each request"""
    user_agent = random.choice(USER_AGENTS)
    is_chrome = "Chrome" in user_agent and "Edg" not in user_agent

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": random.choice(
            [
                "en-US,en;q=0.9",
                "en-GB,en;q=0.9",
                "en-US,en;q=0.9,es;q=0.8",
            ]
        ),
        "content-type": "application/json",
        "origin": "https://www.dnb.com",
        "referer": "https://www.dnb.com/business-directory/company-information.fruit_and_tree_nut_farming.au.html?page=1",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": user_agent,
    }

    if is_chrome:
        headers.update(
            {
                "sec-ch-ua": random.choice(CHROME_VERSIONS),
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": random.choice(
                    ['"Windows"', '"macOS"', '"Linux"']
                ),
            }
        )

    header_items = list(headers.items())
    random.shuffle(header_items)

    return dict(header_items)


def scrape_company_details(full_url, cookies, max_retries=2):
    """
    Scrape detailed information from a company's profile page
    full_url should be like: https://www.dnb.com/business-directory/company-profiles.company_name.hash.html
    Returns a dictionary with company details and updated cookies if regenerated
    """
    for attempt in range(max_retries):
        try:
            # Extract the part after company-profiles
            # From: https://www.dnb.com/business-directory/company-profiles.olam_investments.hash.html
            # Get: .olam_investments.hash
            if "/company-profiles" in full_url:
                # Split by 'company-profiles' and get everything after it
                path_after_profiles = full_url.split("/company-profiles")[1]
                # Remove .html extension if present
                if path_after_profiles.endswith(".html"):
                    path_after_profiles = path_after_profiles[:-5]
            else:
                print(f"      ⚠️ Invalid URL format: {full_url}")
                return {}, cookies

            # Construct the API path format with DOUBLE slashes
            # Result: https://www.dnb.com//business-directory/company-profiles.olam_investments.hash
            api_path = f"https://www.dnb.com//business-directory/company-profiles{path_after_profiles}"

            # URL encode the path: https:%2F%2Fwww.dnb.com%2F%2Fbusiness-directory%2Fcompany-profiles.olam_investments.hash
            encoded_path = api_path.replace(":", "%3A").replace("/", "%2F")
            api_url = f"https://www.dnb.com/business-directory/api/companyprofile?path={encoded_path}&language=en&country=us"

            headers = get_random_headers()

            response = requests.get(
                api_url,
                cookies=cookies,
                headers=headers,
                timeout=20,
            )

            if response.status_code != 200:
                print(f"      ⚠️ Detail page returned status {response.status_code}")

                # If not the last attempt, regenerate cookies and retry
                if attempt < max_retries - 1:
                    print(
                        f"      🔄 Regenerating cookies and retrying (attempt {attempt + 2}/{max_retries})..."
                    )
                    new_cookies = generate_fresh_cookies()
                    if new_cookies:
                        cookies.update(new_cookies)
                        time.sleep(2)  # Brief pause before retry
                        continue

                return {}, cookies

            data = response.json()

            # Check if data is valid
            if not data or not isinstance(data, dict):
                print(f"      ⚠️ Invalid JSON response")

                # If not the last attempt, regenerate cookies and retry
                if attempt < max_retries - 1:
                    print(
                        f"      🔄 Regenerating cookies and retrying (attempt {attempt + 2}/{max_retries})..."
                    )
                    new_cookies = generate_fresh_cookies()
                    if new_cookies:
                        cookies.update(new_cookies)
                        time.sleep(2)
                        continue

                return {}, cookies

            overview = data.get("overview")

            # If overview is None or not a dict
            if not overview or not isinstance(overview, dict):
                print(f"      ℹ️ No overview data. Available keys: {list(data.keys())}")
                return {
                    "company_address": "",
                    "website": "",
                    "company_summary": "",
                    "industries": "",
                }, cookies

            # Extract detailed information
            details = {
                "company_address": overview.get("companyLocation", ""),
                "website": overview.get("website", ""),
                "company_summary": overview.get("companyShortSummaryTest", ""),
            }

            # Merge all industry dictionaries
            other_industries = overview.get("otherIndustries", {})
            view_more_industries = overview.get("viewMoreIndustries", {})
            view_more_other_industries = overview.get("viewMoreOtherIndustries", {})

            # Ensure all are dicts before merging
            if not isinstance(other_industries, dict):
                other_industries = {}
            if not isinstance(view_more_industries, dict):
                view_more_industries = {}
            if not isinstance(view_more_other_industries, dict):
                view_more_other_industries = {}

            merged_industries = {
                **other_industries,
                **view_more_industries,
                **view_more_other_industries,
            }

            # Convert industries dict to string
            details["industries"] = (
                json.dumps(merged_industries) if merged_industries else ""
            )

            print(f"      ✅ Successfully extracted details")
            return details, cookies

        except requests.exceptions.RequestException as e:
            print(f"      ❌ Network error: {e}")

            # If not the last attempt, regenerate cookies and retry
            if attempt < max_retries - 1:
                print(
                    f"      🔄 Regenerating cookies and retrying (attempt {attempt + 2}/{max_retries})..."
                )
                new_cookies = generate_fresh_cookies()
                if new_cookies:
                    cookies.update(new_cookies)
                    time.sleep(2)
                    continue

            return {}, cookies

        except json.JSONDecodeError as e:
            print(f"      ❌ JSON decode error: {e}")
            return {}, cookies

        except Exception as e:
            print(f"      ❌ Unexpected error: {type(e).__name__}: {e}")
            return {}, cookies

    # If all retries failed
    return {}, cookies


def main():
    csv_filename = "companies_detailed.csv"
    total_pages = 40

    # Generate fresh cookies using Selenium
    cookies = generate_fresh_cookies()

    if not cookies:
        print("⚠️ Warning: No cookies generated. Proceeding anyway...")

    # Create CSV file with extended headers
    with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "Company Name",
                "URL",
                "Location",
                "Sales Revenue",
                "Full Address",
                "Website",
                "Company Summary",
                "Industries",
            ]
        )

    print(f"\n🚀 Starting to scrape {total_pages} pages with detailed information...\n")

    for current_page in range(1, total_pages + 1):
        print(f"📄 Scraping page {current_page}...")

        json_data = {
            "pageNumber": current_page,
            "industryPath": "fruit_and_tree_nut_farming",
            "countryIsoTwoCode": "au",
        }

        try:
            headers = get_random_headers()

            response = requests.post(
                "https://www.dnb.com/business-directory/api/companyinformation",
                cookies=cookies,
                headers=headers,
                json=json_data,
                timeout=20,
            )

            if response.status_code != 200:
                print(f"⚠️ Warning: Got status code {response.status_code}")

            data = response.json()
            companies = data.get("companyInformationCompany", [])

            rows = []
            for idx, company in enumerate(companies, 1):
                name = company.get("primaryName", "N/A")
                url_path = company.get("companyNameUrl", "")
                locality = company.get("addressLocalityNameFormatted", "")
                region = company.get("addressRegionNameFormatted", "")
                country = company.get("addressCountryName", "")
                sales = company.get("salesRevenue", "N/A")

                location = ", ".join([p for p in [locality, region, country] if p])

                # Construct full URL for display and detail path for API
                if url_path and url_path != "N/A":
                    full_url = f"https://www.dnb.com/business-directory/company-profiles{url_path}.html"
                    # This is the path we'll pass to scrape_company_details
                    detail_path = f"/business-directory/company-profiles{url_path}.html"
                else:
                    full_url = "N/A"
                    detail_path = None

                # Scrape detailed information
                print(f"   🔍 [{idx}/{len(companies)}] Fetching details for: {name}")
                details = {}
                if detail_path:
                    details, cookies = scrape_company_details(detail_path, cookies)
                    # Small delay between detail requests
                    time.sleep(random.uniform(1, 2))

                # Prepare row with all information
                row = [
                    name,
                    full_url,
                    location,
                    sales,
                    details.get("company_address", ""),
                    details.get("website", ""),
                    details.get("company_summary", ""),
                    details.get("industries", ""),
                ]

                rows.append(row)

            # Append to CSV file
            with open(csv_filename, mode="a", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerows(rows)

            print(
                f"✅ Page {current_page}: {len(rows)} companies with details saved.\n"
            )

        except Exception as e:
            print(f"❌ Error on page {current_page}: {e}\n")

        # Delay between page requests
        delay = random.uniform(3, 6)
        print(f"   ⏳ Waiting {delay:.1f}s before next page...\n")
        time.sleep(delay)

    print(f"\n🎉 Scraping completed! Data saved to {csv_filename}")


if __name__ == "__main__":
    main()
