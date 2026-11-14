import csv
import random
import time

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
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

    # Setup Chrome options
    chrome_options = Options()
    # chrome_options.add_argument('--headless')  # Uncomment to run in background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    # Random user agent
    user_agent = random.choice(USER_AGENTS)
    chrome_options.add_argument(f"user-agent={user_agent}")

    # Initialize driver
    driver = webdriver.Chrome(options=chrome_options)

    # Modify navigator.webdriver flag
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    try:
        # Navigate to the page
        url = "https://www.dnb.com/business-directory/company-information.fruit_and_tree_nut_farming.au.html?page=1"
        driver.get(url)

        # Wait for the page to load and cookies to be set
        print("   Waiting for page to load and cookies to be generated...")
        time.sleep(5)  # Give time for all cookies to be set

        # Wait for a specific element to ensure page is loaded
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except:
            pass

        # Extract cookies
        selenium_cookies = driver.get_cookies()
        cookies_dict = {cookie["name"]: cookie["value"] for cookie in selenium_cookies}

        print(f"✅ Successfully generated {len(cookies_dict)} cookies")
        print(f"   Cookie names: {', '.join(cookies_dict.keys())}")

        return cookies_dict

    except Exception as e:
        print(f"❌ Error generating cookies: {e}")
        return {}

    finally:
        # Close the browser
        driver.quit()
        print("🔒 Browser closed")


def get_random_headers():
    """Generate randomized headers for each request"""
    user_agent = random.choice(USER_AGENTS)

    # Determine if it's a Chrome-based browser
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

    # Add Chrome-specific headers only for Chrome browsers
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

    # Randomize header order
    header_items = list(headers.items())
    random.shuffle(header_items)

    return dict(header_items)


def main():
    csv_filename = "companies.csv"
    total_pages = 40

    # Generate fresh cookies using Selenium
    cookies = generate_fresh_cookies()

    if not cookies:
        print("⚠️ Warning: No cookies generated. Proceeding anyway...")

    # Create CSV file with headers
    with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Company Name", "URL", "Location", "Sales Revenue"])

    print(f"\n🚀 Starting to scrape {total_pages} pages...\n")

    for current_page in range(1, total_pages + 1):
        print(f"Scraping page {current_page}...")

        json_data = {
            "pageNumber": current_page,
            "industryPath": "fruit_and_tree_nut_farming",
            "countryIsoTwoCode": "au",
        }

        try:
            # Get randomized headers for this request
            headers = get_random_headers()

            response = requests.post(
                "https://www.dnb.com/business-directory/api/companyinformation",
                cookies=cookies,
                headers=headers,
                json=json_data,
                timeout=20,
            )

            # Check response status
            if response.status_code != 200:
                print(f"⚠️ Warning: Got status code {response.status_code}")

            data = response.json()

            # Get the list of companies
            companies = data.get("companyInformationCompany", [])

            rows = []
            for company in companies:
                name = company.get("primaryName", "N/A")
                url_path = company.get("companyNameUrl", "")
                locality = company.get("addressLocalityNameFormatted", "")
                region = company.get("addressRegionNameFormatted", "")
                country = company.get("addressCountryName", "")
                sales = company.get("salesRevenue", "N/A")

                # Construct full URL
                if url_path and url_path != "N/A":
                    full_url = f"https://www.dnb.com/business-directory/company-profiles{url_path}.html"
                else:
                    full_url = "N/A"

                location = ", ".join([p for p in [locality, region, country] if p])

                rows.append([name, full_url, location, sales])

            # Append to CSV file
            with open(csv_filename, mode="a", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerows(rows)

            print(f"✅ Page {current_page}: {len(rows)} companies saved.")

        except Exception as e:
            print(f"❌ Error on page {current_page}: {e}")

        # Randomize delay between requests (2-5 seconds)
        delay = random.uniform(2, 5)
        print(f"   Waiting {delay:.1f}s before next request...")
        time.sleep(delay)

    print(f"\n🎉 Scraping completed! Data saved to {csv_filename}")


if __name__ == "__main__":
    main()
