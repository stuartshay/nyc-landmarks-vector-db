#!/usr/bin/env python3
"""Quick test script to debug DbClient"""

import sys
import traceback

try:
    from nyc_landmarks.db.db_client import DbClient
    print('✓ DbClient import successful')

    client = DbClient()
    print('✓ DbClient instantiation successful')

    buildings = client.get_landmark_buildings('LP-00079')
    print(f'✓ get_landmark_buildings returned {len(buildings)} buildings')

    if buildings:
        print(f'First building type: {type(buildings[0])}')
        print(f'First building has bbl: {hasattr(buildings[0], "bbl")}')
        if hasattr(buildings[0], 'bbl'):
            print(f'First building bbl: {buildings[0].bbl}')
            print(f'First building binNumber: {buildings[0].binNumber}')
            print(f'First building block: {buildings[0].block}')
            print(f'First building lat/lon: {buildings[0].latitude}, {buildings[0].longitude}')

        # Test the first building attributes in detail
        first_building = buildings[0]
        print("\nFirst building details:")
        for attr in ['name', 'lpNumber', 'bbl', 'binNumber', 'block', 'lot', 'latitude', 'longitude']:
            if hasattr(first_building, attr):
                value = getattr(first_building, attr)
                print(f"  {attr}: {value}")

except Exception as e:
    print(f'❌ Error: {e}')
    traceback.print_exc()
    sys.exit(1)

print('✅ All tests passed!')
