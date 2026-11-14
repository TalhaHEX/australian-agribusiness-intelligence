# Australian Agribusiness Data Scraper

An automated data collection and intelligence pipeline designed to extract structured business directory records for agricultural and farming enterprises across Australia.

---

## Overview

This project implements a hybrid data extraction architecture tailored for structured web directories. It pairs browser-driven session initialization with direct REST endpoint queries to achieve efficient data throughput while maintaining session validity.

### Key Capabilities

- **Hybrid Session Handling**: Uses headless Selenium to initialize valid session cookies, subsequently executed via lightweight HTTP requests.
- **Terminal UI & Monitoring**: Employs `rich` to provide real-time terminal progress indicators, success rate statistics, and elapsed/remaining runtime estimations.
- **Structured Output**: Compiles company records directly into standard CSV format for downstream analysis.
- **Rate Limiting & Evasion**: Implements user-agent rotation, modern browser client-hint headers, and randomized cooldown intervals.

---

## Data Schema

The extraction script captures the following fields for each enterprise:

| Field Name | Description |
| :--- | :--- |
| `Company Name` | Registered commercial entity name |
| `Profile URL` | Canonical directory listing link |
| `Location` | Locality, state/region, and country |
| `Sales Revenue` | Reported annual sales figure |
| `Company Address` | Registered corporate or operational address |
| `Website` | Official corporate domain |
| `Short Summary` | Enterprise operational overview |
| `Industries` | Associated industry sectors and classification tags |

---

## Tech Stack & Dependencies

- **Python**: 3.10 or newer
- **Requests**: High-performance HTTP client for data requests
- **Selenium**: Automated browser management for initial session handshake
- **chromedriver-autoinstaller**: Automated matching and downloading of Chrome binary drivers
- **Rich**: Terminal formatting, tables, and multi-progress status panels
- **uv / pip**: Package management

---

## Getting Started

### 1. Prerequisites

Ensure you have Google Chrome installed on your machine. The script will automatically locate or download the compatible `chromedriver`.

### 2. Clone the Repository

```bash
git clone https://github.com/TalhaHEX/australian-agribusiness-intelligence.git
cd australian-agribusiness-intelligence
```

### 3. Set Up a Virtual Environment

Using standard Python `venv`:

```bash
python -m venv .venv

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# On Linux / macOS:
source .venv/bin/activate
```

Or using `uv`:

```bash
uv venv
uv sync
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Execution

To launch the extraction pipeline:

```bash
python run.py
```

The script will:
1. Launch an automated browser instance to establish a valid session.
2. Initialize the terminal dashboard.
3. Page through the target directory entries sequentially.
4. Extract profile information and stream records directly into `company_details.csv`.
5. Display summary statistics upon completion.

---

## Customization

Key parameters can be adjusted within `run.py`:

- **Target Page Count**: Adjust `stats.total_pages` inside the `main()` function.
- **Target Category**: Modify `industryPath` in `json_data` (default: `fruit_and_tree_nut_farming`).
- **Country Filter**: Change `countryIsoTwoCode` (default: `au`).
- **Cooldown Jitter**: Customize the delay range in `random.uniform(3, 6)`.

---

## Project Structure

```text
├── run.py                 # Primary scraping engine with Rich terminal UI
├── data_extraction.py     # Standalone extractor module for single-company profiling
├── requirements.txt       # Pinned dependency definitions
├── pyproject.toml         # Project metadata and package configuration
├── .gitignore             # Git exclusion rules
└── README.md              # Documentation
```

---

## Ethical & Research Disclaimer

This tool is created for educational and academic market research purposes. Ensure compliance with website terms of service, robots.txt directives, and local data collection regulations before initiating high-volume extraction requests.

---

## License

This project is licensed under the MIT License.

