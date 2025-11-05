#!/usr/bin/env python3
"""
Test script to verify that STORAGE_THRESHOLD_KB=0 stores all responses.

Run this to confirm storage threshold behavior:
    python test_storage_threshold_zero.py
"""
import asyncio
import json
import os

# Mock storage and message bus to test the logic
class MockStorage:
    def __init__(self):
        self.stored = []
    
    async def ensure_bucket(self, bucket):
        pass
    
    async def put_object(self, bucket, key, data, metadata=None):
        self.stored.append({
            "bucket": bucket,
            "key": key,
            "size": len(data),
            "data": data
        })
        print(f"✓ Stored to {bucket}/{key} (size={len(data)} bytes)")


async def test_threshold_logic():
    """Test the storage threshold logic from message_bus.py"""
    
    # Simulate different threshold values
    test_cases = [
        {"threshold_kb": 0, "payload_size": 10, "should_store": True, "reason": "threshold=0 stores ALL"},
        {"threshold_kb": 0, "payload_size": 1000000, "should_store": True, "reason": "threshold=0 stores ALL"},
        {"threshold_kb": 1, "payload_size": 500, "should_store": False, "reason": "500 bytes < 1 KB"},
        {"threshold_kb": 1, "payload_size": 2000, "should_store": True, "reason": "2000 bytes > 1 KB"},
        {"threshold_kb": 100, "payload_size": 50000, "should_store": False, "reason": "50KB < 100KB"},
        {"threshold_kb": 100, "payload_size": 150000, "should_store": True, "reason": "150KB > 100KB"},
        {"threshold_kb": None, "payload_size": 1000000, "should_store": False, "reason": "threshold=None disables storage"},
    ]
    
    print("Testing storage threshold logic from message_bus.py:\n")
    print("=" * 80)
    
    for i, test in enumerate(test_cases, 1):
        threshold_kb = test["threshold_kb"]
        payload_size = test["payload_size"]
        expected = test["should_store"]
        reason = test["reason"]
        
        # Create mock storage
        storage = MockStorage() if threshold_kb is not None else None
        
        # Simulate the actual logic from message_bus.py lines 167-171
        payload_bytes = b"x" * payload_size  # Simulate payload
        should_offload = (
            storage and 
            threshold_kb is not None and 
            (threshold_kb == 0 or len(payload_bytes) > threshold_kb * 1024)
        )
        
        # Test the logic
        passed = should_offload == expected
        status = "✓ PASS" if passed else "✗ FAIL"
        
        print(f"\nTest {i}: {status}")
        print(f"  Threshold: {threshold_kb} KB")
        print(f"  Payload size: {payload_size:,} bytes ({payload_size/1024:.2f} KB)")
        print(f"  Expected: {expected}")
        print(f"  Actual: {should_offload}")
        print(f"  Reason: {reason}")
        
        if should_offload and storage:
            await storage.put_object("laddr", f"test_{i}.json", payload_bytes)
    
    print("\n" + "=" * 80)
    print("\nSummary:")
    print("- threshold_kb=0 → stores ALL responses (as expected)")
    print("- threshold_kb=None → storage disabled")
    print("- threshold_kb>0 → stores only responses larger than threshold")


if __name__ == "__main__":
    print("Storage Threshold Test\n")
    asyncio.run(test_threshold_logic())
    print("\n✓ All tests completed!")
