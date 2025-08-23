"""
Test script to verify Lido Nation Catalyst data extraction works.
This tests both funds and proposals_enriched resources.
"""
import dlt
from src.cardano_insights.connectors.lido import funds, proposals_enriched

def test_funds_extraction():
    """Test funds extraction from Lido API."""
    print("🔍 Testing funds extraction...")
    
    try:
        # Test the funds resource
        funds_data = list(funds())
        
        if funds_data:
            print(f"✅ Funds extraction successful: {len(funds_data)} funds found")
            print(f"📋 Sample fund: {funds_data[0]}")
            return True
        else:
            print("❌ No funds data returned")
            return False
            
    except Exception as e:
        print(f"❌ Funds extraction failed: {e}")
        return False

def test_proposals_extraction():
    """Test proposals extraction with limited data."""
    print("\n🔍 Testing proposals extraction (limited to 1 page)...")
    
    try:
        # Test proposals with max_pages=1 to avoid long extraction
        proposals_data = list(proposals_enriched(max_pages=1))
        
        if proposals_data:
            print(f"✅ Proposals extraction successful: {len(proposals_data)} proposals found")
            
            # Show sample proposal structure
            sample = proposals_data[0]
            print(f"📋 Sample proposal keys: {list(sample.keys())}")
            print(f"📋 Sample proposal: {sample.get('title', 'No title')}")
            
            # Check for enrichment features
            has_github = any(p.get('has_github') for p in proposals_data[:5])
            has_categories = any(p.get('categories') for p in proposals_data[:5])
            
            print(f"🔗 GitHub enrichment working: {has_github}")
            print(f"🏷️  Category enrichment working: {has_categories}")
            
            return True
        else:
            print("❌ No proposals data returned")
            return False
            
    except Exception as e:
        print(f"❌ Proposals extraction failed: {e}")
        return False

def test_full_pipeline():
    """Test complete dlt pipeline with small dataset."""
    print("\n🚀 Testing complete dlt pipeline...")
    
    try:
        # Create test pipeline
        pipeline = dlt.pipeline(
            pipeline_name="lido_test",
            destination="duckdb",
            dataset_name="catalyst_test"
        )
        
        print("📦 Loading funds...")
        funds_info = pipeline.run(funds(), table_name="funds")
        print(f"✅ Funds loaded: {funds_info}")
        
        print("📦 Loading sample proposals...")
        proposals_info = pipeline.run(proposals_enriched(max_pages=1), table_name="proposals_sample")
        print(f"✅ Proposals loaded: {proposals_info}")
        
        # Verify data in database
        import duckdb
        conn = duckdb.connect("lido_test.duckdb")
        
        funds_count = conn.execute("SELECT COUNT(*) FROM catalyst_test.funds").fetchone()[0]
        proposals_count = conn.execute("SELECT COUNT(*) FROM catalyst_test.proposals_sample").fetchone()[0]
        
        print(f"📊 Database verification:")
        print(f"   - Funds in DB: {funds_count}")
        print(f"   - Proposals in DB: {proposals_count}")
        
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 LIDO NATION CATALYST EXTRACTION TESTS")
    print("=" * 50)
    
    results = []
    
    # Run individual tests
    results.append(("Funds Extraction", test_funds_extraction()))
    results.append(("Proposals Extraction", test_proposals_extraction()))
    results.append(("Full Pipeline", test_full_pipeline()))
    
    # Summary
    print("\n📊 TEST RESULTS SUMMARY:")
    print("=" * 30)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Lido extraction is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    
    return passed == len(results)

if __name__ == "__main__":
    main()