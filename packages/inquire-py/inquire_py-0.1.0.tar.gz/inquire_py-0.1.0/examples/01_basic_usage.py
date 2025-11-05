"""Basic usage example for inquire library."""

import asyncio
import os
import sys

# Add baml_client to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "baml_schemas"))

from inquire import research
from baml_client.types import CompanyInfo
from baml_client import b


async def main():
    """Run basic research example."""
    # Ensure API keys are set
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Set OPENAI_API_KEY environment variable")
        return

    print("🔍 Researching Stripe...")

    result = await research(
        research_instructions="Research Stripe's founders and their backgrounds",
        schema=CompanyInfo,
        baml_function=b.ExtractCompanyInfo,
    )

    print(f"\n✅ Results:")
    print(f"  Company: {result.name}")
    print(f"  Description: {result.description}")
    print(f"  Founders: {', '.join(result.founders)}")
    if result.funding:
        print(f"  Funding: {result.funding}")


if __name__ == "__main__":
    asyncio.run(main())
