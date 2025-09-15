"""
Test Database API Endpoints
"""
import requests
import json
import time

def test_database_api():
    base_url = "http://localhost:8000/api"
    
    print("=== Testing Database API Endpoints ===")
    
    # Wait for server to start
    print("Waiting for server...")
    time.sleep(2)
    
    try:
        # Test 1: Database Stats
        print("\n1. Testing /db/stats...")
        response = requests.get(f"{base_url}/db/stats")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            stats = response.json()
            print(f"Database stats: {json.dumps(stats, indent=2)}")
        else:
            print(f"Error: {response.text}")
        
        # Test 2: Get Teams from DB
        print("\n2. Testing /db/teams...")
        response = requests.get(f"{base_url}/db/teams")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            teams = response.json()
            print(f"Teams count: {len(teams)}")
            if teams:
                print(f"First team: {teams[0]}")
        else:
            print(f"Error: {response.text}")
        
        # Test 3: Sync Teams
        print("\n3. Testing /db/sync-teams...")
        response = requests.post(f"{base_url}/db/sync-teams")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            sync_result = response.json()
            print(f"Sync result: {json.dumps(sync_result, indent=2)}")
        else:
            print(f"Error: {response.text}")
        
        # Test 4: Check teams again after sync
        print("\n4. Testing /db/teams after sync...")
        response = requests.get(f"{base_url}/db/teams")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            teams = response.json()
            print(f"Teams count after sync: {len(teams)}")
            for team in teams[:3]:  # Show first 3 teams
                print(f"  - {team['name']} ({team['short_name']})")
        
        print("\n✅ Database API tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the backend is running.")
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")

if __name__ == "__main__":
    test_database_api()