from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class LearningSimulationResult:
    estimated_completion_date: date
    progress_curve: list[dict[str, float | int | str]]


class LearningSimulationEngine:
    def simulate(self, roadmap: dict, daily_study_hours: float) -> LearningSimulationResult:
        if daily_study_hours <= 0:
            raise ValueError("daily_study_hours must be greater than 0")

        steps = roadmap.get("steps", []) or []
        total_hours = sum(float(step.get("estimated_time_hours", 0.0)) for step in steps)
        total_hours = max(0.0, total_hours)

        start_date_value = roadmap.get("start_date")
        if isinstance(start_date_value, date):
            start_date = start_date_value
        else:
            start_date = date.today()

        if total_hours == 0:
            return LearningSimulationResult(
                estimated_completion_date=start_date,
                progress_curve=[
                    {
                        "day": 0,
                        "date": start_date.isoformat(),
                        "hours_completed": 0.0,
                        "progress_percent": 100.0,
                    }
                ],
            )

        total_days = int((total_hours + daily_study_hours - 1) // daily_study_hours)
        progress_curve: list[dict[str, float | int | str]] = []

        completed = 0.0
        for day in range(1, total_days + 1):
            completed = min(total_hours, completed + daily_study_hours)
            progress = round((completed / total_hours) * 100, 2)
            progress_curve.append(
                {
                    "day": day,
                    "date": (start_date + timedelta(days=day)).isoformat(),
                    "hours_completed": round(completed, 2),
                    "progress_percent": progress,
                }
            )

        completion_date = start_date + timedelta(days=total_days)
        return LearningSimulationResult(
            estimated_completion_date=completion_date,
            progress_curve=progress_curve,
        )
