import csv
import json
import logging
import random
import time
import urllib.parse
from datetime import datetime
from pathlib import Path

import chromedriver_autoinstaller
import requests
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.logging import RichHandler
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from rich.text import Text
from rich.tree import Tree
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Initialize Rich Console
console = Console()

# Setup logging with Rich
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(console=console, rich_tracebacks=True, show_time=True)],
)
logger = logging.getLogger("scraper")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0",
]

CHROME_VERSIONS = [
    '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
]


class ScraperStats:
    def __init__(self):
        print("Installing Chrome Driver")
        chromedriver_autoinstaller.install()
        print("Chrome Driver Installed")
        self.total_companies = 0
        self.successful_extracts = 0
        self.failed_extracts = 0
        self.start_time = datetime.now()
        self.current_page = 0
        self.total_pages = 0


stats = ScraperStats()


def create_header_panel():
    """Create an animated header panel"""
    title = Text()
    title.append("🚀 ", style="bold yellow")
    title.append("DNB Web Scraper", style="bold cyan")
    title.append(" 🌐", style="bold yellow")

    subtitle = Text("Advanced Company Data Extraction System", style="italic dim")

    header = Text.assemble(
        (f"\n{title}\n", ""),
        (f"{subtitle}\n", ""),
        (f"Started: {stats.start_time.strftime('%Y-%m-%d %H:%M:%S')}", "dim"),
    )

    return Panel(
        header,
        border_style="bright_blue",
        box=__import__("rich.box").box.DOUBLE_EDGE,
        padding=(1, 2),
    )


def create_stats_panel():
    """Create real-time statistics panel"""
    elapsed = (datetime.now() - stats.start_time).total_seconds()

    stats_table = Table.grid(padding=(0, 2))
    stats_table.add_column(style="cyan", justify="right")
    stats_table.add_column(style="green")

    stats_table.add_row("📊 Total Companies:", f"[bold]{stats.total_companies}[/bold]")
    stats_table.add_row(
        "✅ Successful:", f"[bold green]{stats.successful_extracts}[/bold green]"
    )
    stats_table.add_row("❌ Failed:", f"[bold red]{stats.failed_extracts}[/bold red]")
    stats_table.add_row(
        "⏱️  Elapsed Time:", f"[bold yellow]{elapsed:.1f}s[/bold yellow]"
    )
    stats_table.add_row(
        "📄 Current Page:",
        f"[bold magenta]{stats.current_page}/{stats.total_pages}[/bold magenta]",
    )

    success_rate = (
        (stats.successful_extracts / stats.total_companies * 100)
        if stats.total_companies > 0
        else 0
    )
    stats_table.add_row(
        "📈 Success Rate:", f"[bold cyan]{success_rate:.1f}%[/bold cyan]"
    )

    return Panel(
        stats_table,
        title="[bold]📊 Live Statistics[/bold]",
        border_style="green",
        padding=(1, 2),
    )


def generate_fresh_cookies():
    """Generate fresh cookies with animated progress"""
    with console.status(
        "[bold green]🍪 Generating fresh cookies...[/bold green]", spinner="dots"
    ):
        logger.info("Initializing Chrome WebDriver")
        chrome_options = Options()
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
        logger.info(f"Navigating to: {url}")
        driver.get(url)
        time.sleep(5)

        selenium_cookies = driver.get_cookies()
        cookies_dict = {cookie["name"]: cookie["value"] for cookie in selenium_cookies}
        driver.quit()

        logger.info(f"✅ Successfully generated {len(cookies_dict)} cookies")
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
        if "company-profiles" in company_url and "company-profiles." not in company_url:
            company_url = company_url.replace("company-profiles", "company-profiles.")
            logger.debug(f"Fixed URL: {company_url}")

        encoded_path = urllib.parse.quote(company_url, safe="")
        api_url = f"https://www.dnb.com/business-directory/api/companyprofile?path={encoded_path}&language=en&country=us"

        response = requests.get(api_url, cookies=cookies, headers=headers, timeout=20)
        logger.debug(f"API Response status: {response.status_code}")

        data = response.json()
        overview = data.get("overview", {}) or {}

        company_address = overview.get("companyLocation", "")
        website = overview.get("website", "")
        company_short_summary = overview.get("companyShortSummaryTest", "")

        merged_industries = {}
        for key in ["otherIndustries", "viewMoreIndustries", "viewMoreOtherIndustries"]:
            merged_industries.update(overview.get(key, {}) or {})

        stats.successful_extracts += 1
        return (
            company_address,
            website,
            company_short_summary,
            ", ".join(merged_industries.values()),
        )

    except Exception as e:
        logger.error(f"Failed to extract details for {company_url}: {e}")
        stats.failed_extracts += 1
        return "", "", "", ""


def main():
    csv_filename = "company_details.csv"
    stats.total_pages = 40

    # Print fancy header
    console.clear()
    console.print(create_header_panel())
    console.print()

    # Generate cookies with animation
    cookies = generate_fresh_cookies()
    console.print("✨ [bold green]Initialization complete![/bold green]\n")

    # Initialize CSV
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

    logger.info(f"CSV file initialized: {csv_filename}")

    # Create progress bars
    overall_progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(complete_style="green", finished_style="bold green"),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    )

    page_progress = Progress(
        TextColumn("  └─ [cyan]{task.description}"),
        BarColumn(complete_style="cyan"),
        TaskProgressColumn(),
        console=console,
    )

    with overall_progress:
        overall_task = overall_progress.add_task(
            "[bold]📚 Scraping Pages", total=stats.total_pages
        )

        for current_page in range(1, stats.total_pages + 1):
            stats.current_page = current_page

            json_data = {
                "pageNumber": current_page,
                "industryPath": "fruit_and_tree_nut_farming",
                "countryIsoTwoCode": "au",
            }

            headers = get_random_headers()

            try:
                logger.info(f"🔄 Processing page {current_page}/{stats.total_pages}")

                response = requests.post(
                    "https://www.dnb.com/business-directory/api/companyinformation",
                    cookies=cookies,
                    headers=headers,
                    json=json_data,
                    timeout=20,
                )
                data = response.json()
                companies = data.get("companyInformationCompany", [])

                with page_progress:
                    company_task = page_progress.add_task(
                        f"Processing {len(companies)} companies", total=len(companies)
                    )

                    with open(
                        csv_filename, mode="a", newline="", encoding="utf-8"
                    ) as file:
                        writer = csv.writer(file)

                        for company in companies:
                            name = company.get("primaryName", "N/A")
                            url_path = company.get("companyNameUrl", "")
                            locality = company.get("addressLocalityNameFormatted", "")
                            region = company.get("addressRegionNameFormatted", "")
                            country = company.get("addressCountryName", "")
                            sales = company.get("salesRevenue", "N/A")

                            if not url_path:
                                page_progress.advance(company_task)
                                continue

                            full_url = f"https://www.dnb.com//business-directory/company-profiles{url_path}"

                            address, website, summary, industries = (
                                extract_company_details(full_url, cookies, headers)
                            )

                            location = ", ".join(
                                [p for p in [locality, region, country] if p]
                            )

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

                            stats.total_companies += 1
                            page_progress.advance(company_task)

                logger.info(
                    f"✅ Page {current_page} complete: {len(companies)} companies processed"
                )

            except Exception as e:
                logger.error(f"❌ Error on page {current_page}: {e}")

            overall_progress.advance(overall_task)

            # Add delay with countdown
            if current_page < stats.total_pages:
                delay = random.uniform(3, 6)
                with console.status(
                    f"[bold yellow]⏳ Cooling down... ({delay:.1f}s)[/bold yellow]",
                    spinner="simpleDotsScrolling",
                ):
                    time.sleep(delay)

    # Final statistics
    console.print()
    console.print(create_stats_panel())
    console.print()

    # Success message
    success_panel = Panel(
        Text.assemble(
            ("🎉 ", "bold yellow"),
            ("Scraping Completed Successfully!\n\n", "bold green"),
            (f"📁 Data saved to: ", "cyan"),
            (f"{csv_filename}\n", "bold cyan"),
            (f"📊 Total companies extracted: ", "white"),
            (f"{stats.total_companies}", "bold yellow"),
        ),
        border_style="green",
        box=__import__("rich.box").box.DOUBLE,
        padding=(1, 2),
    )
    console.print(success_panel)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[bold red]⚠️  Scraping interrupted by user[/bold red]")
        logger.warning("Process terminated by user")
    except Exception as e:
        console.print(f"\n\n[bold red]💥 Fatal error: {e}[/bold red]")
        logger.exception("Fatal error occurred")
        raise
