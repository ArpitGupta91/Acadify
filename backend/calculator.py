import math
from typing import Dict, List


class AttendanceCalculator:
    REQUIRED_PERCENTAGE = 75.0

    @classmethod
    def classes_to_attend(cls, total: int, attended: int, target: float = 75.0) -> int:
        if total < 0 or attended < 0:
            raise ValueError("Total classes and attended classes must be non-negative.")
        if attended > total:
            raise ValueError("Attended classes cannot be greater than total classes.")

        target_fraction = target / 100.0
        current_fraction = (attended / total) if total > 0 else 0.0

        if current_fraction >= target_fraction:
            return 0

        numerator = (target_fraction * total) - attended
        denominator = 1.0 - target_fraction
        required = math.ceil(numerator / denominator)
        return max(0, required)

    @classmethod
    def classes_can_miss(cls, total: int, attended: int, target: float = 75.0) -> int:
        if total < 0 or attended < 0:
            raise ValueError("Total classes and attended classes must be non-negative.")
        if attended > total:
            raise ValueError("Attended classes cannot be greater than total classes.")
        if total == 0:
            return 0

        current_percentage = (attended / total) * 100.0
        if current_percentage <= target:
            return 0

        max_x = math.floor((attended / (target / 100.0)) - total)
        return max(0, max_x)

    @classmethod
    def calculate(cls, total_classes: int, attended_classes: int) -> Dict:
        if total_classes <= 0:
            raise ValueError("Total classes must be greater than 0.")
        if attended_classes < 0:
            raise ValueError("Attended classes cannot be negative.")
        if attended_classes > total_classes:
            raise ValueError("Attended classes cannot be greater than total classes.")

        current_percentage = (attended_classes / total_classes) * 100.0
        is_detained = current_percentage < cls.REQUIRED_PERCENTAGE

        needed = cls.classes_to_attend(total_classes, attended_classes, cls.REQUIRED_PERCENTAGE)
        can_skip = cls.classes_can_miss(total_classes, attended_classes, cls.REQUIRED_PERCENTAGE)

        if current_percentage < 50.0:
            status_message = (
                "Critical attendance level. You are at high risk of detention. Attend all upcoming classes without fail."
            )
        elif current_percentage < cls.REQUIRED_PERCENTAGE:
            status_message = (
                f"You are below 75%. Attend the next {needed} classes consecutively to reach the safe zone."
            )
        elif math.isclose(current_percentage, cls.REQUIRED_PERCENTAGE, abs_tol=0.01):
            status_message = "You are exactly at 75%. Avoid skipping classes to stay safe."
        else:
            status_message = (
                f"Great job! You are above 75%. You can safely miss up to {can_skip} classes."
            )

        return {
            "current_percentage": round(current_percentage, 2),
            "is_detained": is_detained,
            "classes_needed_to_reach_75": needed,
            "classes_can_skip": can_skip,
            "status_message": status_message,
        }


class CGPACalculator:
    GRADE_POINTS = {
        "O": 10,
        "A+": 9,
        "A": 8,
        "B+": 7,
        "B": 6,
        "C": 5,
        "P": 4,
        "F": 0,
    }

    @classmethod
    def _cgpa_to_letter(cls, cgpa: float) -> str:
        if cgpa >= 9.5:
            return "O"
        if cgpa >= 8.5:
            return "A+"
        if cgpa >= 7.5:
            return "A"
        if cgpa >= 6.5:
            return "B+"
        if cgpa >= 5.5:
            return "B"
        if cgpa >= 4.5:
            return "C"
        if cgpa >= 4.0:
            return "P"
        return "F"

    @classmethod
    def calculate(cls, subjects: List[Dict]) -> Dict:
        if not subjects:
            raise ValueError("At least one subject is required to calculate CGPA.")

        weighted_sum = 0.0
        total_credits = 0.0

        for subject in subjects:
            name = str(subject.get("name", "")).strip() or "Unnamed Subject"
            grade_points = float(subject.get("grade_points", 0))
            credits = float(subject.get("credits", 0))

            if credits <= 0:
                raise ValueError(f"Credits must be greater than 0 for subject '{name}'.")
            if grade_points < 0 or grade_points > 10:
                raise ValueError(f"Grade points must be between 0 and 10 for subject '{name}'.")

            weighted_sum += grade_points * credits
            total_credits += credits

        if total_credits <= 0:
            raise ValueError("Total credits must be greater than 0.")

        cgpa = weighted_sum / total_credits
        grade_letter = cls._cgpa_to_letter(cgpa)

        return {
            "cgpa": round(cgpa, 2),
            "total_credits": round(total_credits, 2),
            "weighted_sum": round(weighted_sum, 2),
            "grade_letter": grade_letter,
            "grade_scale": cls.GRADE_POINTS,
        }

    @staticmethod
    def required_sgpa(
        current_cgpa: float,
        completed_credits: float,
        target_cgpa: float,
        total_credits: float,
    ) -> float:
        if completed_credits < 0 or total_credits <= 0:
            raise ValueError("Credits must be valid positive values.")
        if completed_credits > total_credits:
            raise ValueError("Completed credits cannot exceed total credits.")

        remaining_credits = total_credits - completed_credits
        if remaining_credits == 0:
            return 0.0 if current_cgpa >= target_cgpa else float("inf")

        required_total_points = target_cgpa * total_credits
        current_points = current_cgpa * completed_credits
        required_remaining_points = required_total_points - current_points
        required_sgpa_value = required_remaining_points / remaining_credits

        return round(required_sgpa_value, 2)
