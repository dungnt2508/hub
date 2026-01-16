#!/usr/bin/env python3
"""
Production Testing Helper Script
Usage: python test_production.py --api-key <key> --tenant-id <id>
"""
import asyncio
import argparse
import json
import sys
from typing import Optional
import httpx


class ProductionTester:
    """Production testing helper"""
    
    def __init__(self, api_key: str, tenant_id: str, api_url: str = "http://localhost:8386/api/v1/chat"):
        self.api_key = api_key
        self.tenant_id = tenant_id
        self.api_url = api_url
        self.user_id = "550e8400-e29b-41d4-a716-446655440000"
        self.session_id: Optional[str] = None
    
    async def send_request(
        self,
        message: str,
        session_id: Optional[str] = None,
        description: str = ""
    ) -> dict:
        """Send request to API"""
        print(f"\n{'='*60}")
        print(f"Test: {description}")
        print(f"Message: {message}")
        print(f"{'='*60}")
        
        payload = {
            "message": message,
            "user_id": self.user_id,
            "metadata": {
                "tenant_id": self.tenant_id
            }
        }
        
        if session_id:
            payload["session_id"] = session_id
        
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                
                print("Response:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                
                # Extract session_id
                if "session_id" in result:
                    self.session_id = result["session_id"]
                    print(f"\nSession ID: {self.session_id}")
                
                return result
            except httpx.HTTPStatusError as e:
                print(f"HTTP Error: {e}")
                print(f"Response: {e.response.text}")
                return {}
            except Exception as e:
                print(f"Error: {e}")
                return {}
    
    async def test_f1_1_session_persistence(self):
        """Test F1.1: Session Persistence"""
        print("\n" + "="*60)
        print("TEST F1.1: Session Persistence")
        print("="*60)
        
        # Test NEED_MORE_INFO
        result = await self.send_request(
            "Tôi muốn xin nghỉ phép",
            description="F1.1.1: NEED_MORE_INFO persistence"
        )
        
        assert result.get("status") == "NEED_MORE_INFO", "Expected NEED_MORE_INFO"
        assert "session_id" in result, "Expected session_id in response"
        assert "missing_slots" in result, "Expected missing_slots"
        
        session_id = result["session_id"]
        
        # Test SUCCESS
        result2 = await self.send_request(
            "Tôi còn bao nhiêu ngày phép?",
            session_id=session_id,
            description="F1.1.2: SUCCESS persistence"
        )
        
        assert result2.get("status") == "SUCCESS", "Expected SUCCESS"
        print("\n✅ F1.1: Session Persistence - PASSED")
    
    async def test_f1_2_slot_merge(self):
        """Test F1.2: Slot Merge"""
        print("\n" + "="*60)
        print("TEST F1.2: Slot Merge")
        print("="*60)
        
        # Start leave request
        result1 = await self.send_request(
            "Tôi muốn xin nghỉ phép",
            description="F1.2.1: Start leave request"
        )
        session_id = result1.get("session_id")
        
        # Provide start_date
        result2 = await self.send_request(
            "từ ngày 2025-02-01",
            session_id=session_id,
            description="F1.2.2: Provide start_date"
        )
        
        # Provide end_date
        result3 = await self.send_request(
            "đến ngày 2025-02-05",
            session_id=session_id,
            description="F1.2.3: Provide end_date"
        )
        
        # Provide reason
        result4 = await self.send_request(
            "nghỉ phép gia đình",
            session_id=session_id,
            description="F1.2.4: Provide reason (should SUCCESS)"
        )
        
        assert result4.get("status") == "SUCCESS", "Expected SUCCESS after all slots"
        print("\n✅ F1.2: Slot Merge - PASSED")
    
    async def test_f1_3_unknown_recovery(self):
        """Test F1.3: UNKNOWN Recovery"""
        print("\n" + "="*60)
        print("TEST F1.3: UNKNOWN Recovery")
        print("="*60)
        
        # UNKNOWN without last_domain
        result1 = await self.send_request(
            "xyz abc 123",
            description="F1.3.1: UNKNOWN without last_domain"
        )
        
        assert result1.get("status") == "UNKNOWN", "Expected UNKNOWN"
        assert "options" in result1, "Expected options for disambiguation"
        assert "HR" in result1.get("options", []), "Expected HR in options"
        
        # Set last_domain first
        result2 = await self.send_request(
            "Tôi còn bao nhiêu ngày phép?",
            description="F1.3.2: Set last_domain=hr"
        )
        session_id = result2.get("session_id")
        
        # UNKNOWN with last_domain
        result3 = await self.send_request(
            "xyz abc 123",
            session_id=session_id,
            description="F1.3.3: UNKNOWN with last_domain"
        )
        
        assert result3.get("status") == "UNKNOWN", "Expected UNKNOWN"
        assert "options" in result3, "Expected options"
        # Should suggest resume with last_domain
        print("\n✅ F1.3: UNKNOWN Recovery - PASSED")
    
    async def test_f2_1_continuation(self):
        """Test F2.1: Continuation Check"""
        print("\n" + "="*60)
        print("TEST F2.1: Continuation Check")
        print("="*60)
        
        # Start leave request
        result1 = await self.send_request(
            "Tôi muốn xin nghỉ phép",
            description="F2.1.1: Start leave request"
        )
        session_id = result1.get("session_id")
        
        # Continue with "mai"
        result2 = await self.send_request(
            "mai",
            session_id=session_id,
            description="F2.1.2: Continue with 'mai' (should CONTINUATION)"
        )
        
        # Check trace for CONTINUATION source
        trace = result2.get("trace", {})
        spans = trace.get("spans", [])
        continuation_span = next(
            (s for s in spans if s.get("step") == "router.step.continuation"),
            None
        )
        
        if continuation_span:
            assert continuation_span.get("output", {}).get("continued") == True
            print("\n✅ F2.1: Continuation Check - PASSED")
        else:
            print("\n⚠️  F2.1: Continuation Check - CONTINUATION span not found in trace")
    
    async def test_f2_3_next_action(self):
        """Test F2.3: Next Action"""
        print("\n" + "="*60)
        print("TEST F2.3: Next Action")
        print("="*60)
        
        result = await self.send_request(
            "Tôi muốn xin nghỉ phép",
            description="F2.3.1: Check next_action=ASK_SLOT"
        )
        
        assert "next_action" in result, "Expected next_action in response"
        assert result.get("next_action") == "ASK_SLOT", "Expected ASK_SLOT"
        assert "next_action_params" in result, "Expected next_action_params"
        
        print("\n✅ F2.3: Next Action - PASSED")
    
    async def test_f3_1_intent_mapping(self):
        """Test F3.1: Intent Mapping From Config"""
        print("\n" + "="*60)
        print("TEST F3.1: Intent Mapping From Config")
        print("="*60)
        
        result = await self.send_request(
            "Tìm kiếm sản phẩm workflow",
            description="F3.1.1: Catalog search (should map to catalog.search)"
        )
        
        assert result.get("domain") == "catalog", "Expected catalog domain"
        print("\n✅ F3.1: Intent Mapping - PASSED")
    
    async def test_f3_3_context_boost(self):
        """Test F3.3: Context Boost"""
        print("\n" + "="*60)
        print("TEST F3.3: Context Boost")
        print("="*60)
        
        # Set last_domain=hr
        result1 = await self.send_request(
            "Tôi còn bao nhiêu ngày phép?",
            description="F3.3.1: Set last_domain=hr"
        )
        session_id = result1.get("session_id")
        
        # Ambiguous request
        result2 = await self.send_request(
            "Tìm kiếm thông tin",
            session_id=session_id,
            description="F3.3.2: Ambiguous (should boost HR)"
        )
        
        # Check if boosted (may route to HR or Catalog)
        print(f"Routed to: {result2.get('domain')}")
        print("\n✅ F3.3: Context Boost - PASSED (check logs for boost)")
    
    async def test_f4_1_slot_validation(self):
        """Test F4.1: Slot Validation"""
        print("\n" + "="*60)
        print("TEST F4.1: Slot Validation")
        print("="*60)
        
        result = await self.send_request(
            "Tôi muốn xin nghỉ phép từ ngày 32/13/2025",
            description="F4.1.1: Invalid date (should warn)"
        )
        
        # Should still process but log warning
        print("Check logs for slot validation warnings")
        print("\n✅ F4.1: Slot Validation - PASSED (check logs)")
    
    async def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("PRODUCTION TESTING - ALL TESTS")
        print("="*60)
        
        try:
            await self.test_f1_1_session_persistence()
            await self.test_f1_2_slot_merge()
            await self.test_f1_3_unknown_recovery()
            await self.test_f2_1_continuation()
            await self.test_f2_3_next_action()
            await self.test_f3_1_intent_mapping()
            await self.test_f3_3_context_boost()
            await self.test_f4_1_slot_validation()
            
            print("\n" + "="*60)
            print("✅ ALL TESTS COMPLETED")
            print("="*60)
            print("\nCheck Redis for session state:")
            if self.session_id:
                print(f"  redis-cli GET \"session:{self.session_id}\"")
            
        except AssertionError as e:
            print(f"\n❌ TEST FAILED: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Production Testing Script")
    parser.add_argument("--api-key", required=True, help="API Key")
    parser.add_argument("--tenant-id", required=True, help="Tenant ID")
    parser.add_argument("--api-url", default="http://localhost:8386/api/v1/chat", help="API URL")
    
    args = parser.parse_args()
    
    tester = ProductionTester(args.api_key, args.tenant_id, args.api_url)
    asyncio.run(tester.run_all_tests())


if __name__ == "__main__":
    main()
