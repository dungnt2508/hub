"""
Catalog Domain Sandbox - Test các components catalog riêng lẻ
Tương tự như DBA sandbox nhưng focused vào catalog domain
"""
import asyncio
from typing import List, Dict, Any


# Mock data cho testing
MOCK_PRODUCTS = [
    {
        "id": "prod-1",
        "product_id": "tool-ai-001",
        "title": "ChatGPT",
        "description": "Công cụ AI tạo sinh nội dung, trả lời câu hỏi",
        "metadata": {
            "tags": ["AI", "NLP", "Chatbot"],
            "features": ["Chat", "Code Generation", "Analysis"],
            "price": "$20/month",
            "is_free": False,
            "pricing_model": "subscription"
        }
    },
    {
        "id": "prod-2",
        "product_id": "tool-ai-002",
        "title": "Gemini",
        "description": "Mô hình AI đa năng từ Google",
        "metadata": {
            "tags": ["AI", "NLP", "Search"],
            "features": ["Search Integration", "Image Analysis", "Code"],
            "price": "Free + Pro",
            "is_free": True,
            "pricing_model": "freemium"
        }
    },
    {
        "id": "prod-3",
        "product_id": "tool-ai-003",
        "title": "Claude",
        "description": "Trợ lý AI tiên tiến từ Anthropic",
        "metadata": {
            "tags": ["AI", "NLP", "Analysis"],
            "features": ["Reasoning", "Long Context", "API"],
            "price": "$20/month",
            "is_free": False,
            "pricing_model": "subscription"
        }
    },
    {
        "id": "prod-4",
        "product_id": "tool-design-001",
        "title": "Figma",
        "description": "Công cụ thiết kế UI/UX cộng tác",
        "metadata": {
            "tags": ["Design", "UI", "Collaboration"],
            "features": ["Design", "Prototyping", "Collaboration"],
            "price": "Free + $12/month",
            "is_free": True,
            "pricing_model": "freemium"
        }
    },
]


class CatalogIntentClassifierDemo:
    """Demo CatalogIntentClassifier - Phân loại intent catalog"""
    
    def __init__(self):
        self.name = "CatalogIntentClassifier"
    
    def classify_simple(self, question: str) -> Dict[str, Any]:
        """
        Simple rule-based classification (không dùng LLM)
        """
        q_lower = question.lower()
        
        # Check price/cost
        if any(word in q_lower for word in ["giá", "bao nhiêu", "chi phí", "phí", "cost", "price"]):
            return {
                "intent_type": "PRODUCT_SPECIFIC_INFO",
                "confidence": 0.95,
                "attribute": "price",
                "reason": "Hỏi về giá tiền"
            }
        
        # Check features
        if any(word in q_lower for word in ["tính năng", "feature", "khả năng", "ability", "có gì"]):
            return {
                "intent_type": "PRODUCT_SPECIFIC_INFO",
                "confidence": 0.90,
                "attribute": "features",
                "reason": "Hỏi về tính năng"
            }
        
        # Check free/paid
        if any(word in q_lower for word in ["miễn phí", "free", "trả phí", "paid", "có phí"]):
            return {
                "intent_type": "PRODUCT_SPECIFIC_INFO",
                "confidence": 0.92,
                "attribute": "pricing",
                "reason": "Hỏi về miễn phí/trả phí"
            }
        
        # Check comparison
        if any(word in q_lower for word in ["so sánh", "khác", "giống", "compare", "vs", "versus"]):
            # Extract product names từ question
            product_names = self._extract_product_names(question)
            return {
                "intent_type": "PRODUCT_COMPARISON",
                "confidence": 0.88,
                "product_names": product_names,
                "reason": "Hỏi so sánh sản phẩm"
            }
        
        # Check count
        if any(word in q_lower for word in ["bao nhiêu", "có mấy", "đếm", "count", "how many"]):
            if "bao nhiêu" in q_lower and ("giá" in q_lower or "chi phí" in q_lower):
                # This is about price, not count
                return {
                    "intent_type": "PRODUCT_SPECIFIC_INFO",
                    "confidence": 0.94,
                    "attribute": "price",
                    "reason": "Hỏi giá tiền (bao nhiêu tiền)"
                }
            return {
                "intent_type": "PRODUCT_COUNT",
                "confidence": 0.85,
                "reason": "Hỏi số lượng sản phẩm"
            }
        
        # Default: generic search
        return {
            "intent_type": "PRODUCT_SEARCH",
            "confidence": 0.70,
            "reason": "Tìm kiếm chung sản phẩm"
        }
    
    def _extract_product_names(self, question: str) -> List[str]:
        """Trích xuất tên sản phẩm từ câu hỏi"""
        # Simple implementation - check against known products
        known_products = ["ChatGPT", "Gemini", "Claude", "Figma", "GPT", "AI"]
        found = []
        for product in known_products:
            if product.lower() in question.lower():
                found.append(product)
        return found


class CatalogHybridSearchDemo:
    """Demo CatalogHybridSearchHelper - Tìm kiếm hybrid"""
    
    def __init__(self):
        self.name = "CatalogHybridSearchHelper"
        self.products = MOCK_PRODUCTS
    
    def search_by_attribute(self, attribute: str) -> List[Dict[str, Any]]:
        """
        Search products by specific attribute
        """
        if attribute.lower() == "price":
            results = [p for p in self.products if p["metadata"].get("price")]
            return results
        
        elif attribute.lower() in ["free", "miễn phí"]:
            results = [p for p in self.products if p["metadata"].get("is_free")]
            return results
        
        elif attribute.lower() in ["features", "tính năng"]:
            results = [p for p in self.products if p["metadata"].get("features")]
            return results
        
        return self.products
    
    def count_products(self, filter_attr: str = None) -> int:
        """Count products with optional filter"""
        if filter_attr and filter_attr.lower() in ["free", "miễn phí"]:
            return len([p for p in self.products if p["metadata"].get("is_free")])
        return len(self.products)
    
    def search_comparison(self, product_names: List[str]) -> Dict[str, List[Dict]]:
        """Find specific products for comparison"""
        results = {}
        for name in product_names:
            name_lower = name.lower()
            found = [p for p in self.products if name_lower in p["title"].lower()]
            results[name] = found
        return results


class CatalogKnowledgeEngineDemo:
    """Demo CatalogKnowledgeEngine - Trả lời câu hỏi"""
    
    def __init__(self):
        self.name = "CatalogKnowledgeEngine"
        self.classifier = CatalogIntentClassifierDemo()
        self.search_helper = CatalogHybridSearchDemo()
    
    async def answer(self, question: str) -> Dict[str, Any]:
        """
        Trả lời câu hỏi về catalog
        """
        # Step 1: Classify intent
        classification = self.classifier.classify_simple(question)
        
        # Step 2: Retrieve products based on intent
        intent_type = classification["intent_type"]
        
        if intent_type == "PRODUCT_SEARCH":
            # Generic search - show all
            products = self.search_helper.products
            retrieval_method = "vector_search"
        
        elif intent_type == "PRODUCT_SPECIFIC_INFO":
            # Specific attribute search
            attribute = classification.get("attribute", "")
            products = self.search_helper.search_by_attribute(attribute)
            retrieval_method = "hybrid_search"
        
        elif intent_type == "PRODUCT_COMPARISON":
            # Comparison search
            product_names = classification.get("product_names", [])
            if product_names:
                comparison_results = self.search_helper.search_comparison(product_names)
                products = []
                for prods in comparison_results.values():
                    products.extend(prods)
            else:
                products = []
            retrieval_method = "db_query"
        
        elif intent_type == "PRODUCT_COUNT":
            # Count query
            count = self.search_helper.count_products()
            return {
                "answer": f"Hiện tại có {count} công cụ trong catalog",
                "intent_type": intent_type,
                "retrieval_method": "db_count",
                "products_found": count,
                "confidence": 0.85
            }
        
        else:
            products = []
            retrieval_method = "unknown"
        
        # Step 3: Build answer
        if not products:
            answer = "Xin lỗi, không tìm thấy sản phẩm nào phù hợp"
            confidence = 0.0
        else:
            # Build simple answer
            product_names = [p["title"] for p in products]
            answer = f"Các công cụ liên quan: {', '.join(product_names[:3])}"
            confidence = classification.get("confidence", 0.7)
        
        return {
            "answer": answer,
            "intent_type": intent_type,
            "retrieval_method": retrieval_method,
            "products_found": len(products),
            "confidence": confidence,
            "classification": classification
        }


async def main():
    """Main sandbox demo"""
    print("=" * 80)
    print("CATALOG DOMAIN SANDBOX - TEST COMPONENTS")
    print("=" * 80)
    
    # ===== TEST 1: INTENT CLASSIFICATION =====
    print("\n1. INTENT CLASSIFICATION TEST")
    print("-" * 80)
    
    classifier = CatalogIntentClassifierDemo()
    
    test_questions = [
        ("Công cụ nào tốt nhất?", "Generic search"),
        ("Giá của ChatGPT bao nhiêu?", "Specific info - price"),
        ("Tính năng nào của Claude?", "Specific info - features"),
        ("So sánh ChatGPT và Gemini", "Comparison"),
        ("Có bao nhiêu công cụ AI?", "Count"),
        ("Công cụ nào miễn phí?", "Specific info - free"),
    ]
    
    for question, description in test_questions:
        print(f"\nQuestion: {description}")
        print(f"User: '{question}'")
        result = classifier.classify_simple(question)
        
        print(f"  Intent: {result['intent_type']}")
        print(f"  Confidence: {result['confidence']:.0%}")
        print(f"  Reason: {result['reason']}")
        if "attribute" in result:
            print(f"  Attribute: {result['attribute']}")
        if "product_names" in result:
            print(f"  Products: {result['product_names']}")
    
    # ===== TEST 2: HYBRID SEARCH =====
    print("\n\n2. HYBRID SEARCH TEST")
    print("-" * 80)
    
    search_helper = CatalogHybridSearchDemo()
    
    search_tests = [
        ("price", "Tìm kiếm theo giá"),
        ("free", "Tìm kiếm công cụ miễn phí"),
        ("features", "Tìm kiếm theo tính năng"),
    ]
    
    for attribute, description in search_tests:
        print(f"\nSearch: {description}")
        results = search_helper.search_by_attribute(attribute)
        
        print(f"  Found: {len(results)} products")
        for product in results[:2]:  # Show first 2
            print(f"    - {product['title']}")
            if attribute == "price":
                print(f"      Price: {product['metadata'].get('price', 'N/A')}")
            elif attribute == "free":
                print(f"      Free: {product['metadata'].get('is_free')}")
    
    # Count test
    print(f"\nCount Test:")
    count = search_helper.count_products()
    print(f"  Total products: {count}")
    count_free = search_helper.count_products("free")
    print(f"  Free products: {count_free}")
    
    # Comparison test
    print(f"\nComparison Test:")
    comparison = search_helper.search_comparison(["ChatGPT", "Claude"])
    for name, products in comparison.items():
        print(f"  {name}: {len(products)} results")
        for p in products:
            print(f"    - {p['title']}")
    
    # ===== TEST 3: END-TO-END FLOW =====
    print("\n\n3. END-TO-END FLOW TEST")
    print("-" * 80)
    
    engine = CatalogKnowledgeEngineDemo()
    
    end_to_end_tests = [
        "Công cụ AI nào tốt nhất?",
        "Giá của các công cụ bao nhiêu?",
        "So sánh ChatGPT và Claude",
        "Có bao nhiêu công cụ miễn phí?",
        "Công cụ nào có tính năng code generation?",
    ]
    
    for question in end_to_end_tests:
        print(f"\nUser: '{question}'")
        response = await engine.answer(question)
        
        print(f"  Answer: {response['answer']}")
        print(f"  Intent: {response['intent_type']}")
        print(f"  Method: {response['retrieval_method']}")
        print(f"  Confidence: {response['confidence']:.0%}")
        print(f"  Products: {response['products_found']}")
    
    print("\n" + "=" * 80)
    print("SANDBOX DEMO COMPLETED ✅")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

