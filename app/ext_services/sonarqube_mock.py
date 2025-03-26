import asyncio
import random
from typing import Dict


async def generate_sonarqube_report(task_id: str) -> Dict:
    delay = random.uniform(3.0, 10.0)
    await asyncio.sleep(30)

    random.seed(hash(task_id))

    return {
        "overall_coverage": round(random.uniform(70.0, 100.0), 1),
        "bugs": {
            "total": random.randint(0, 20),
            "critical": random.randint(0, 5),
            "major": random.randint(0, 10),
            "minor": random.randint(0, 15),
        },
        "code_smells": {
            "total": random.randint(0, 50),
            "critical": random.randint(0, 10),
            "major": random.randint(0, 20),
            "minor": random.randint(0, 30),
        },
        "vulnerabilities": {
            "total": random.randint(0, 15),
            "critical": random.randint(0, 3),
            "major": random.randint(0, 5),
            "minor": random.randint(0, 7),
        }
    }