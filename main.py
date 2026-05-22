import asyncio
from agents.credit_filter_agent import run_credit_filter

if __name__ == "__main__":
    asyncio.run(run_credit_filter(batch_size=10))
