from __future__ import annotations

import random
import string
from dataclasses import dataclass, asdict
from datetime import date, timedelta


FIRST_NAMES_MALE = [
    "Arjun", "Vikram", "Rohit", "Aman", "Harish", "Rahul", "Kunal", "Nikhil", "Suresh", "Pranav",
]
FIRST_NAMES_FEMALE = [
    "Ananya", "Priya", "Kavya", "Ishita", "Sneha", "Divya", "Pooja", "Riya", "Aditi", "Neha",
]
LAST_NAMES = [
    "Sharma", "Patel", "Reddy", "Singh", "Gupta", "Nair", "Iyer", "Mehta", "Yadav", "Chopra",
]


@dataclass
class IdentityRecord:
    doc_type: str
    name: str
    father_name: str | None
    dob: str
    gender: str
    id_number: str

    def to_dict(self) -> dict:
        payload = asdict(self)
        return {k: v for k, v in payload.items() if v is not None}


class IdentityGenerator:
    def __init__(self, seed: int | None = None):
        self.rng = random.Random(seed)

    def generate(self, doc_type: str) -> IdentityRecord:
        gender = self.rng.choice(["Male", "Female"])
        first_pool = FIRST_NAMES_MALE if gender == "Male" else FIRST_NAMES_FEMALE
        first = self.rng.choice(first_pool)
        last = self.rng.choice(LAST_NAMES)
        name = f"{first} {last}"

        father_first = self.rng.choice(FIRST_NAMES_MALE)
        father_last = self.rng.choice(LAST_NAMES)
        father_name = f"{father_first} {father_last}"

        dob = self._random_dob().strftime("%d/%m/%Y")

        if doc_type == "aadhaar":
            id_number = self._aadhaar_number()
            father = None
        elif doc_type == "pan":
            id_number = self._pan_number()
            father = father_name
        else:
            raise ValueError(f"Unsupported doc_type: {doc_type}")

        record = IdentityRecord(
            doc_type=doc_type,
            name=name,
            father_name=father,
            dob=dob,
            gender=gender,
            id_number=id_number,
        )

        if any((value is None or str(value).strip() == "") for value in record.to_dict().values()):
            raise ValueError("Generated identity has empty fields")
        return record

    def _random_dob(self) -> date:
        start = date(1950, 1, 1)
        end = date(2010, 12, 31)
        delta_days = (end - start).days
        return start + timedelta(days=self.rng.randint(0, delta_days))

    def _aadhaar_number(self) -> str:
        digits = "".join(self.rng.choices(string.digits, k=12))
        return f"{digits[:4]} {digits[4:8]} {digits[8:]}"

    def _pan_number(self) -> str:
        letters = "".join(self.rng.choices(string.ascii_uppercase, k=5))
        digits = "".join(self.rng.choices(string.digits, k=4))
        suffix = self.rng.choice(string.ascii_uppercase)
        return f"{letters}{digits}{suffix}"
