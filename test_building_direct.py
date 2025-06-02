#!/usr/bin/env python3
"""Test building metadata collection directly."""

import sys

sys.path.append('.')

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

def test_building_metadata():
    """Test building metadata collection for LP-00179."""
    try:
        print("Testing building metadata collection...")

        # Import required modules
        from nyc_landmarks.db.db_client import get_db_client
        from nyc_landmarks.vectordb.enhanced_metadata import EnhancedMetadataCollector

        print("✅ Modules imported successfully")

        # Test database client
        db_client = get_db_client()
        buildings = db_client.get_landmark_buildings('LP-00179')
        print(f"✅ Database client found {len(buildings)} buildings for LP-00179")

        # Test enhanced metadata collector
        collector = EnhancedMetadataCollector()
        metadata = collector.collect_landmark_metadata('LP-00179')

        if metadata:
            metadata_dict = metadata.model_dump()
            building_fields = {k: v for k, v in metadata_dict.items() if k.startswith('building_')}
            print(f"✅ Enhanced metadata contains {len(building_fields)} building fields")

            if building_fields:
                print("Sample building fields:")
                for k, v in list(building_fields.items())[:5]:
                    print(f"  {k}: {v}")
                return True
            else:
                print("❌ No building fields found in enhanced metadata")
                return False
        else:
            print("❌ No enhanced metadata returned")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_building_metadata()
