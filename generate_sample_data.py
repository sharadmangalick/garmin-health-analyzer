#!/usr/bin/env python3
"""Generate realistic sample Garmin data for demonstration purposes."""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

def generate_sample_data(output_dir: str = "samples/data", days: int = 90):
    """Generate sample Garmin data with realistic patterns."""

    output_path = Path(output_dir)
    summaries_dir = output_path / "daily_summaries"
    sleep_dir = output_path / "sleep"
    vo2max_dir = output_path / "vo2max"

    summaries_dir.mkdir(parents=True, exist_ok=True)
    sleep_dir.mkdir(parents=True, exist_ok=True)
    vo2max_dir.mkdir(parents=True, exist_ok=True)

    end_date = datetime(2026, 1, 15)

    # Simulate a training cycle: base fitness -> build -> peak -> fatigue
    for i in range(days):
        current_date = end_date - timedelta(days=days - 1 - i)
        date_str = current_date.strftime('%Y-%m-%d')
        dow = current_date.weekday()  # 0=Monday, 6=Sunday

        # Progress through training phases
        phase_progress = i / days

        # Resting HR: starts at 45, rises to 50 during heavy training
        if phase_progress < 0.3:
            base_rhr = 45
        elif phase_progress < 0.6:
            base_rhr = 45 + (phase_progress - 0.3) * 20  # Rise during build
        else:
            base_rhr = 51 - (phase_progress - 0.6) * 5  # Slight recovery

        rhr = int(base_rhr + random.gauss(0, 1.5))

        # Body Battery: inverse of RHR pattern
        if phase_progress < 0.3:
            base_bb = 85
        elif phase_progress < 0.6:
            base_bb = 85 - (phase_progress - 0.3) * 40
        else:
            base_bb = 73 + (phase_progress - 0.6) * 15

        bb_high = int(min(100, max(40, base_bb + random.gauss(0, 8))))
        bb_low = int(max(5, bb_high - random.randint(30, 55)))
        bb_charged = random.randint(40, 80)
        bb_drained = random.randint(35, 70)

        # Stress: higher on weekdays, lower weekends
        if dow < 5:  # Weekday
            stress = int(35 + random.gauss(5, 10))
        else:
            stress = int(28 + random.gauss(0, 8))
        stress = max(15, min(70, stress))

        # Steps: varies by day of week
        if dow == 5:  # Saturday - long run day
            steps = random.randint(18000, 28000)
        elif dow == 6:  # Sunday - rest
            steps = random.randint(4000, 8000)
        elif dow in [1, 3]:  # Tue/Thu - workout days
            steps = random.randint(12000, 18000)
        else:
            steps = random.randint(5000, 10000)

        # Sedentary time: inverse relationship with steps
        if steps > 15000:
            sed_hours = random.uniform(12, 15)
        elif steps > 10000:
            sed_hours = random.uniform(14, 17)
        else:
            sed_hours = random.uniform(16, 19)

        sed_seconds = int(sed_hours * 3600)

        # Vigorous minutes
        if dow == 5:
            vigorous = random.randint(80, 150)
        elif dow in [1, 3]:
            vigorous = random.randint(30, 60)
        else:
            vigorous = random.randint(0, 15)

        # Create daily summary
        summary = {
            'date': date_str,
            'stats': {
                'calendarDate': date_str,
                'totalSteps': steps,
                'sedentarySeconds': sed_seconds,
                'restingHeartRate': rhr,
                'averageStressLevel': stress,
                'bodyBatteryHighestValue': bb_high,
                'bodyBatteryLowestValue': bb_low,
                'bodyBatteryChargedValue': bb_charged,
                'bodyBatteryDrainedValue': bb_drained,
                'vigorousIntensityMinutes': vigorous,
                'moderateIntensityMinutes': random.randint(10, 45),
            }
        }

        with open(summaries_dir / f"{date_str}.json", 'w') as f:
            json.dump(summary, f, indent=2)

        # Sleep data: correlates with sedentary time and stress
        # High sedentary = poor sleep
        if sed_hours > 17:
            base_sleep = 5.0
        elif sed_hours > 15:
            base_sleep = 6.2
        else:
            base_sleep = 7.0

        # Friday night = social, less sleep
        if dow == 4:  # Friday
            base_sleep -= 1.0
        # Sunday night = good sleep
        elif dow == 6:
            base_sleep += 0.5

        sleep_hours = max(4, min(9, base_sleep + random.gauss(0, 0.7)))
        sleep_seconds = int(sleep_hours * 3600)

        deep_pct = random.uniform(0.15, 0.25)
        rem_pct = random.uniform(0.20, 0.28)
        light_pct = 1 - deep_pct - rem_pct

        sleep_data = {
            '_date': date_str,
            'dailySleepDTO': {
                'calendarDate': date_str,
                'sleepTimeSeconds': sleep_seconds,
                'deepSleepSeconds': int(sleep_seconds * deep_pct),
                'lightSleepSeconds': int(sleep_seconds * light_pct),
                'remSleepSeconds': int(sleep_seconds * rem_pct),
            }
        }

        with open(sleep_dir / f"{date_str}.json", 'w') as f:
            json.dump(sleep_data, f, indent=2)

        # VO2 Max data: gradual improvement with training, then plateau
        # Only generate VO2 max on workout days (not every day)
        if dow in [1, 3, 5]:  # Tue, Thu, Sat - workout days
            # VO2 max improves with training, then stabilizes
            if phase_progress < 0.3:
                base_vo2 = 48
            elif phase_progress < 0.6:
                base_vo2 = 48 + (phase_progress - 0.3) * 20  # Improvement phase
            else:
                base_vo2 = 54 + (phase_progress - 0.6) * 5  # Plateau/slight gain

            vo2_value = round(base_vo2 + random.gauss(0, 1), 1)
            vo2_value = max(40, min(60, vo2_value))

            vo2max_data = {
                '_date': date_str,
                'generic': {
                    'vo2MaxValue': vo2_value,
                    'calendarDate': date_str,
                },
                'running': {
                    'vo2MaxValue': vo2_value,
                    'calendarDate': date_str,
                }
            }

            with open(vo2max_dir / f"{date_str}.json", 'w') as f:
                json.dump(vo2max_data, f, indent=2)

    print(f"Generated {days} days of sample data in {output_dir}/")
    print(f"  - Daily summaries: {summaries_dir}")
    print(f"  - Sleep data: {sleep_dir}")
    print(f"  - VO2 max data: {vo2max_dir}")


if __name__ == "__main__":
    generate_sample_data()
