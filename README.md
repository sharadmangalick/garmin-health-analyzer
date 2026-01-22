# 🏃‍♂️ Garmin Health Analyzer

> **Uncover hidden patterns in your Garmin data and get personalized health insights**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

Turn your Garmin Connect data into actionable health insights. This tool analyzes your sleep, heart rate, VO2 max, stress, and activity patterns to help you train smarter and recover better.

**New:** Now with VO2 max trend analysis, HTML reports, and AI-powered weekly training emails!

---

## ✨ What You'll Discover

```
┌─────────────────────────────────────────────────────────────────┐
│                    YOUR HEALTH INSIGHTS                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📉 Recovery Trends      │  🫁 VO2 Max Fitness                 │
│  ─────────────────       │  ─────────────────                  │
│  RHR: 45 → 49 bpm        │  Current: 52 ml/kg/min             │
│  Body Battery: 85 → 72   │  Trend: +3.2 improvement           │
│  Status: Accumulated     │  Level: Very Good                   │
│          fatigue         │                                     │
│                          │                                     │
│  😴 Sleep Patterns       │  😰 Stress & Recovery               │
│  ────────────────        │  ─────────────────                  │
│  Avg: 6.2 hrs            │  Low stress: +80 BB                 │
│  Best day: Sunday        │  High stress: +46 BB                │
│  Worst: Friday           │  Stress > sleep duration            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

```bash
# 1. Clone and install
git clone https://github.com/sharadmangalick/garmin-health-analyzer.git
cd garmin-health-analyzer
pip install -r requirements.txt

# 2. Fetch your data (you'll be prompted for Garmin credentials)
python main.py fetch --days 90

# 3. Generate your personalized report (PDF or HTML)
python main.py analyze              # PDF report
python main.py analyze --html       # Interactive HTML report
```

That's it! Open `Health_Insights_Report.pdf` or `.html` to see your insights.

---

## 📊 Sample Output

### Terminal Summary

```
$ python main.py analyze --text

╭─────────────────────────── Analysis ───────────────────────────╮
│ Analyzing your Garmin data...                                  │
╰────────────────────────────────────────────────────────────────╯
  Loaded 90 days of daily summaries
  Loaded 90 sleep records
  Date range: 2025-10-18 to 2026-01-15

=== GARMIN DATA ANALYSIS SUMMARY ===
Data range: 2025-10-18 to 2026-01-15
Days analyzed: 90

Resting HR: 48.9 bpm (baseline: 44.7, +4.1 change)
Body Battery: 80 wake avg (baseline: 87)
VO2 Max: 52.3 ml/kg/min (Very Good, +3.2 change)
Sleep: 6.0 hrs avg (46% nights under 6h)
Stress: 37 avg (26% days above 45)

=== TOP RECOMMENDATIONS ===
[HIGH] Recovery: Consider a recovery week with reduced training
[HIGH] Sleep: Aim for 7-8 hours consistently
[MEDIUM] Movement: Add movement breaks every 90 minutes
```

### Report Preview (PDF & HTML)

Choose your format:
- **PDF** - Traditional printable report
- **HTML** - Interactive, responsive web report with modern styling

Both formats include:

| Section | Contents |
|---------|----------|
| **Executive Summary** | Key findings at a glance |
| **Key Metrics** | RHR, Body Battery, VO2 Max, Sleep, Stress trends |
| **Patterns** | Sedentary correlations, day-of-week analysis |
| **Recommendations** | Prioritized, personalized action items |
| **Monthly Trends** | How your metrics changed over time |
| **Science** | Research backing the insights |

<details>
<summary>📄 Click to see sample report sections</summary>

#### Executive Summary
```
This analysis reveals three key findings:

1. ACCUMULATED FATIGUE: Your resting HR rose from 45 to 49 bpm,
   and Body Battery dropped from 87 to 72. Your body needs recovery.

2. SEDENTARY TIME PREDICTS SLEEP: Days with 17+ hours sedentary
   average only 5h sleep. This is your biggest lifestyle lever.

3. STRESS THROTTLES RECOVERY: Low-stress nights show +80 Body
   Battery recharge vs +46 on high-stress nights.
```

#### Sedentary vs Sleep Correlation Table
```
┌──────────────────┬─────────────┬─────────────────┐
│ Sedentary Hours  │ Avg Sleep   │ Impact          │
├──────────────────┼─────────────┼─────────────────┤
│ < 14 hours       │ 7.2 hours   │ ✓ Best sleep    │
│ 14-17 hours      │ 6.4 hours   │ ~ Moderate      │
│ 17+ hours        │ 5.0 hours   │ ✗ Poor sleep    │
└──────────────────┴─────────────┴─────────────────┘
```

#### Day-of-Week Patterns
```
        Mon   Tue   Wed   Thu   Fri   Sat   Sun
Sleep   6.2h  6.4h  6.3h  5.8h  6.1h  5.4h  7.2h  ← Sunday best!
BB      72    74    71    68    70    64    78    ← Saturday worst
Stress  36    38    37    40    35    32    30    ← Weekend relief
```

</details>

---

## 📈 Metrics Analyzed

| Metric | What It Tells You | Why It Matters |
|--------|-------------------|----------------|
| **Resting Heart Rate** | Recovery status | Rising RHR = accumulated fatigue |
| **Body Battery** | Energy reserves | Low wake values = recovery deficit |
| **VO2 Max** | Cardiovascular fitness | Higher = better endurance capacity |
| **Sleep Duration** | Rest quality | <7h = 1.7x injury risk |
| **Sedentary Time** | Daily inactivity | Strongest sleep predictor |
| **Stress Level** | Mental load | Throttles overnight recovery |
| **Steps** | Activity level | High variability impacts recovery |

---

## 🔧 All Commands

| Command | Description |
|---------|-------------|
| `python main.py quickstart` | 🎯 Interactive setup guide |
| `python main.py fetch --days N` | 📥 Download N days of data |
| `python main.py fetch --vo2max` | 🫁 Fetch only VO2 max data |
| `python main.py analyze` | 📊 Generate PDF report |
| `python main.py analyze --html` | 🌐 Generate HTML report |
| `python main.py analyze --text` | 📝 Show terminal summary |
| `python main.py show` | 👀 Display recent data |
| `python main.py status` | ℹ️ Check data status |
| `python main.py clear` | 🗑️ Delete cached data |
| `python main.py logout` | 🚪 Clear Garmin session |

### Weekly Training Emails

| Command | Description |
|---------|-------------|
| `python main.py email setup` | 📧 Configure your training profile |
| `python main.py email preview` | 👀 Preview weekly training plan |
| `python main.py email send` | 📤 Generate and queue email for sending |
| `python main.py email prepare` | 📝 Prepare analysis for Claude Code |
| `python main.py email schedule` | ⏰ Show scheduling instructions |
| `python main.py email status` | ℹ️ Check email system status |

---

## 📧 Weekly Training Emails

Get personalized AI-powered training plans delivered to your inbox every week! The system analyzes your Garmin health data and generates custom workouts based on:

- Your race goal and timeline
- Recovery metrics (RHR, Body Battery, sleep quality)
- Training phase (base, build, peak, taper)
- Recent training load

### Quick Setup

```bash
# 1. Configure your training profile
python main.py email setup

# 2. Preview your first training plan
python main.py email preview

# 3. Generate and send the email
python main.py email send
```

### Two Modes of Operation

**With Anthropic API Key:**
```bash
# Set your API key in .env file
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Generate and send in one command
python main.py email send
```

**With Claude Code (Enterprise users):**
```bash
# 1. Prepare analysis context
python main.py email prepare

# 2. Claude Code generates the training plan
# (reads context from data/ai_context.json)

# 3. Complete and send with the plan
python main.py email send --use-plan
```

### Automated Weekly Emails (macOS)

Set up automatic weekly emails using launchd:

```bash
# Copy the plist to LaunchAgents
cp launchd/com.garmin.weekly-report.plist ~/Library/LaunchAgents/

# Load the schedule (runs every Sunday at 7am)
launchctl load ~/Library/LaunchAgents/com.garmin.weekly-report.plist
```

---

## 🏗️ How It Works

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│   You run:  python main.py fetch --days 90                  │
│                        │                                     │
│                        ▼                                     │
│   ┌─────────────────────────────────────────┐               │
│   │         Garmin Connect API              │               │
│   │  (via garminconnect library)            │               │
│   └─────────────────────────────────────────┘               │
│                        │                                     │
│                        ▼                                     │
│   ┌─────────────────────────────────────────┐               │
│   │         Local JSON Storage              │               │
│   │   data/daily_summaries/2025-01-15.json  │               │
│   │   data/sleep/2025-01-15.json            │               │
│   └─────────────────────────────────────────┘               │
│                        │                                     │
│   You run:  python main.py analyze                          │
│                        │                                     │
│                        ▼                                     │
│   ┌─────────────────────────────────────────┐               │
│   │         Analysis Engine                 │               │
│   │  • Calculate trends & baselines         │               │
│   │  • Find correlations                    │               │
│   │  • Generate recommendations             │               │
│   └─────────────────────────────────────────┘               │
│                        │                                     │
│                        ▼                                     │
│   ┌─────────────────────────────────────────┐               │
│   │    Health_Insights_Report.pdf           │  ← Your       │
│   │    Personalized insights & action plan  │    report!    │
│   └─────────────────────────────────────────┘               │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔐 Privacy & Security

- ✅ **All data stays local** - Nothing sent to external servers
- ✅ **Credentials never stored** - Session tokens cached temporarily
- ✅ **Gitignored by default** - Your `data/` folder won't be committed
- ✅ **Open source** - Inspect exactly what the code does

---

## 🧪 Try It With Sample Data

Want to see it in action without connecting your Garmin account?

```bash
# Generate 90 days of realistic sample data
python generate_sample_data.py

# Run analysis on sample data
python -c "from pdf_generator import generate_insights_pdf; generate_insights_pdf('Sample_Report.pdf', 'samples/data')"

# Open Sample_Report.pdf to see example output!
```

---

## 📚 The Science Behind It

The insights are based on peer-reviewed research:

- **Sleep & Injury Risk**: <7h sleep = 1.7x injury increase ([Milewski et al., 2014](https://pubmed.ncbi.nlm.nih.gov/24509534/))
- **HRV & Recovery**: RHR trends indicate training adaptation ([Plews et al., 2013](https://pubmed.ncbi.nlm.nih.gov/23852425/))
- **80/20 Training**: Elite athletes do 80% easy, 20% hard ([Seiler, 2010](https://pubmed.ncbi.nlm.nih.gov/20861519/))
- **Sedentary Behavior**: Sitting has independent health effects ([Owen et al., 2010](https://pubmed.ncbi.nlm.nih.gov/21123641/))

---

## 🤝 Contributing

Contributions welcome! Ideas for improvement:

- [x] ~~Add VO2 max trend analysis~~ ✅ Done!
- [x] ~~HTML report option~~ ✅ Done!
- [x] ~~Weekly training emails with AI coaching~~ ✅ Done!
- [ ] Support for activities/workouts analysis
- [ ] Interactive dashboard with charts
- [ ] Training load calculations (CTL/ATL/TSB)
- [ ] Export to CSV/Excel

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- [garminconnect](https://github.com/cyberjunky/python-garminconnect) - Garmin Connect API access
- [fpdf2](https://github.com/py-pdf/fpdf2) - PDF generation
- [Rich](https://github.com/Textualize/rich) - Beautiful terminal output
- [Click](https://click.palletsprojects.com/) - CLI framework

---

## ⚠️ Disclaimer

This tool is for informational purposes only. It is not medical advice. Always consult healthcare professionals for health-related decisions.

---

<p align="center">
  <b>Built for runners, cyclists, and health enthusiasts who want to understand their data.</b>
  <br><br>
  ⭐ Star this repo if you find it useful!
</p>
