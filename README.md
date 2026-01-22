# Garmin Health Analyzer

Analyze your Garmin Connect data to uncover health and training insights. This tool fetches your data from Garmin Connect, analyzes patterns, and generates a comprehensive PDF report with personalized recommendations.

## What It Does

- **Fetches your data** from Garmin Connect (sleep, heart rate, daily summaries, activities)
- **Analyzes patterns** in your health metrics over time
- **Identifies correlations** (e.g., sedentary time → sleep quality)
- **Generates recommendations** based on your personal data
- **Creates a PDF report** with findings, trends, and scientific context

### Insights You'll Get

- **Recovery Status**: Resting heart rate and Body Battery trends
- **Sleep Patterns**: Duration, quality, and what affects them
- **Lifestyle Factors**: How sedentary time impacts your health
- **Stress Impact**: How stress levels affect overnight recovery
- **Day-of-Week Patterns**: Your best and worst days for various metrics
- **Monthly Trends**: How your metrics have changed over time

## Installation

### Prerequisites

- Python 3.8 or higher
- A Garmin Connect account with data

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/garmin-health-analyzer.git
   cd garmin-health-analyzer
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the quickstart guide**
   ```bash
   python main.py quickstart
   ```

## Usage

### Step 1: Fetch Your Data

Fetch your data from Garmin Connect. You'll be prompted for your Garmin credentials:

```bash
# Fetch last 30 days
python main.py fetch --days 30

# Fetch last 6 months for comprehensive analysis
python main.py fetch --days 180
```

Your credentials are used to authenticate with Garmin Connect. The session is cached locally so you don't need to log in every time.

### Step 2: Analyze Your Data

Run the analysis to generate insights:

```bash
# Generate PDF report (default)
python main.py analyze

# Show text summary in terminal
python main.py analyze --text

# Both text and PDF
python main.py analyze --text

# Custom output filename
python main.py analyze --output my_health_report.pdf
```

### Step 3: Review Your Report

Open the generated `Health_Insights_Report.pdf` to see:

1. **Executive Summary** - Key findings at a glance
2. **Key Metrics** - Your current vs baseline values
3. **Patterns & Correlations** - What affects what
4. **Recommendations** - Personalized suggestions
5. **Monthly Trends** - How you've changed over time
6. **The Science** - Research backing the insights

## All Commands

| Command | Description |
|---------|-------------|
| `python main.py fetch --days N` | Fetch N days of data from Garmin |
| `python main.py analyze` | Run analysis and generate PDF |
| `python main.py analyze --text` | Show text summary in terminal |
| `python main.py show` | Display recent data summary |
| `python main.py status` | Check data and configuration status |
| `python main.py quickstart` | Interactive setup guide |
| `python main.py clear` | Delete all cached data |
| `python main.py logout` | Clear saved Garmin session |

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    Garmin Health Analyzer                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Garmin     │───▶│    Data      │───▶│   Analysis   │  │
│  │   Fetcher    │    │    Store     │    │   Engine     │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                   │                   │           │
│         ▼                   ▼                   ▼           │
│  garminconnect lib    JSON files          PDF Report       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

1. **Garmin Fetcher** (`garmin_client.py`): Connects to Garmin Connect using the `garminconnect` library and downloads your data.

2. **Data Store** (`data/`): Your data is stored locally as JSON files, organized by type and date.

3. **Analysis Engine** (`data_analyzer.py`): Processes the JSON data to calculate trends, correlations, and recommendations.

4. **PDF Generator** (`pdf_generator.py`): Creates a comprehensive report with your insights.

## Data Privacy

- Your Garmin credentials are only used to authenticate with Garmin Connect
- Session tokens are cached locally in `.garmin_session` (gitignored)
- All your health data stays on your machine in the `data/` directory (gitignored)
- Nothing is sent to external servers except Garmin Connect for data fetching

## Project Structure

```
garmin-health-analyzer/
├── main.py              # CLI entry point
├── garmin_client.py     # Garmin Connect API wrapper
├── data_analyzer.py     # Analysis engine
├── pdf_generator.py     # PDF report generator
├── config.py            # Configuration handling
├── requirements.txt     # Python dependencies
├── README.md            # This file
├── .gitignore           # Git ignore rules
└── data/                # Your cached data (gitignored)
    ├── activities/
    ├── sleep/
    ├── heart_rate/
    └── daily_summaries/
```

## Metrics Analyzed

| Metric | What It Tells You |
|--------|-------------------|
| **Resting Heart Rate** | Recovery status; rising RHR often indicates fatigue |
| **Body Battery** | Energy reserves; low wake values suggest recovery deficit |
| **Sleep Duration** | Total sleep; <7h associated with increased injury risk |
| **Sedentary Time** | Daily inactivity; strongly correlates with sleep quality |
| **Stress Level** | Daily stress; affects overnight recovery capacity |
| **Steps** | Daily activity; high variability may impact recovery |

## Troubleshooting

### "No data found" error
Run `python main.py fetch --days 30` first to download your data.

### Login issues
- Make sure you're using your Garmin Connect email and password
- If you use "Sign in with Google", you'll need to set a Garmin password first
- Run `python main.py logout` to clear cached session and try again

### Missing metrics in report
Some metrics require specific Garmin devices. The analyzer works with whatever data is available.

## Contributing

Contributions welcome! Please feel free to submit issues or pull requests.

### Ideas for Contribution

- Add more analysis types (training load, VO2 max trends, etc.)
- Support for additional Garmin metrics
- Export to other formats (HTML, Markdown)
- Interactive dashboard

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- [garminconnect](https://github.com/cyberjunky/python-garminconnect) - Python library for Garmin Connect API
- [fpdf2](https://github.com/py-pdf/fpdf2) - PDF generation
- [Rich](https://github.com/Textualize/rich) - Beautiful terminal output
- [Click](https://click.palletsprojects.com/) - CLI framework

## Disclaimer

This tool is for informational purposes only. It is not medical advice. Always consult healthcare professionals for health-related decisions.

The insights are based on patterns in your personal data and general health research. Individual results may vary.
