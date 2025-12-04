"""Test Excel document generation."""
import httpx
import sys
import asyncio

BASE_URL = "http://localhost:8000/api/v1"

async def main():
    async with httpx.AsyncClient() as client:
        # Login
        print("Logging in...")
        resp = await client.post(
            f"{BASE_URL}/auth/login",
            json={"email": "admin@local.dev", "password": "admin123"}
        )
        if resp.status_code != 200:
            print(f"Login failed: {resp.text}")
            sys.exit(1)

        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"Token: {token[:30]}...")

        # Get first kobetsu
        print("\nGetting kobetsu contracts...")
        resp = await client.get(f"{BASE_URL}/kobetsu", headers=headers, follow_redirects=True)
        print(f"Response status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Failed to get kobetsu: {resp.text}")
            sys.exit(1)

        try:
            data = resp.json()
        except Exception as e:
            print(f"JSON decode error: {e}")
            print(f"Response content: {resp.text[:500]}")
            sys.exit(1)

        # Handle both list and dict responses
        if isinstance(data, list):
            kobetsu_list = data
        elif isinstance(data, dict) and "items" in data:
            kobetsu_list = data["items"]
        elif isinstance(data, dict) and "data" in data:
            kobetsu_list = data["data"]
        else:
            print(f"Unexpected response format: {type(data)}")
            print(f"Keys: {data.keys() if isinstance(data, dict) else 'N/A'}")
            kobetsu_list = list(data.values()) if isinstance(data, dict) else []

        print(f"Found {len(kobetsu_list)} contracts")

        if not kobetsu_list:
            print("No contracts found!")
            sys.exit(1)

        kobetsu_id = kobetsu_list[0]["id"] if isinstance(kobetsu_list[0], dict) else kobetsu_list[0]
        print(f"Using kobetsu ID: {kobetsu_id}")

        # Generate Excel document
        print("\nGenerating Excel document...")
        resp = await client.get(
            f"{BASE_URL}/documents/excel/{kobetsu_id}/kobetsu-keiyakusho?format=xlsx",
            headers=headers,
            timeout=60.0,
            follow_redirects=True
        )
        print(f"Response status: {resp.status_code}")

        if resp.status_code == 200:
            output_path = "/tmp/test_kobetsu.xlsx"
            with open(output_path, "wb") as f:
                f.write(resp.content)
            print(f"SUCCESS! Saved to {output_path}")
            print(f"File size: {len(resp.content)} bytes")
        else:
            print(f"ERROR: {resp.text}")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
