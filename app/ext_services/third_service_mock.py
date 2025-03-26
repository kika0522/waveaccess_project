import asyncio
import random
from typing import Dict


async def generate_third_service_report(task_id: str) -> Dict:
    delay = random.uniform(3.0, 10.0)
    await asyncio.sleep(delay)

    random.seed(hash(task_id) + 2)  # Different seed

    return {
        "overall_coverage": round(random.uniform(50.0, 90.0), 1),
        "bugs": {
            "total": random.randint(0, 40),
            "critical": random.randint(0, 10),
            "major": random.randint(0, 20),
            "minor": random.randint(0, 25),
        }
    }