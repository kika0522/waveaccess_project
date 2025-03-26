import asyncio
import random
from typing import Dict


async def generate_second_service_report(task_id: str) -> Dict:
    delay = random.uniform(3.0, 10.0)
    await asyncio.sleep(delay)

    random.seed(hash(task_id) + 1)  # Different seed

    return {
        "overall_coverage": round(random.uniform(60.0, 95.0), 1),
        "bugs": {
            "total": random.randint(0, 30),
            "critical": random.randint(0, 8),
            "major": random.randint(0, 15),
            "minor": random.randint(0, 20),
        },
        "vulnerabilities": {
            "total": random.randint(0, 25),
            "critical": random.randint(0, 5),
            "major": random.randint(0, 10),
            "minor": random.randint(0, 10),
        }
    }