"""Test script for the research API."""

import asyncio
import httpx
import json


async def test_research():
    """Test the research endpoint."""

    url = "http://localhost:8000/api/research"

    payload = {
        "query": "Compare Notion vs Coda vs ClickUp for project management",
        "companies": ["Notion", "Coda", "ClickUp"],
        "analysis_depth": "standard"
    }

    print(">>> Testing Multi-Agent Research Platform")
    print(f"Query: {payload['query']}")
    print(f"Companies: {', '.join(payload['companies'])}\n")

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            print(">>> Sending request...")
            response = await client.post(url, json=payload)

            if response.status_code == 200:
                data = response.json()
                print("\n>>> Research completed successfully!\n")
                print(f"Session ID: {data['session_id']}")
                print(f"Status: {data['status']}")
                print(f"Message: {data['message']}\n")

                # Print profiles
                profiles = data.get("data", {}).get("competitor_profiles", {})
                for company, profile in profiles.items():
                    print(f"\n{'='*60}")
                    print(f">>> {company}")
                    print(f"{'='*60}")
                    print(profile.get("analysis", "No analysis"))
                    print(f"\nSources: {len(profile.get('sources', []))} URLs")

                # Print cost tracking
                print(f"\n{'='*60}")
                print(">>> Cost Tracking")
                print(f"{'='*60}")
                cost_data = data.get("data", {}).get("cost_tracking", {})
                print(json.dumps(cost_data, indent=2))

            else:
                print(f"\nERROR: {response.status_code}")
                print(response.text)

    except httpx.TimeoutException:
        print("\nERROR: Request timed out")
    except Exception as e:
        print(f"\nERROR: {e}")


async def test_health():
    """Test health endpoint."""
    url = "http://localhost:8000/health"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code == 200:
                print(">>> Health check passed")
                print(response.json())
            else:
                print(f"ERROR: Health check failed: {response.status_code}")
    except Exception as e:
        print(f"ERROR: Health check error: {e}")


if __name__ == "__main__":
    print("Testing health endpoint...\n")
    asyncio.run(test_health())

    print("\n" + "="*60)
    print("Testing research endpoint...")
    print("="*60 + "\n")
    asyncio.run(test_research())
