import uuid
from sqlalchemy import select
from app.infrastructure.database.models import SystemCapability, KnowledgeDomain

async def seed_blueprint(db):
    print("Seeding System Blueprints (Capabilities & Domains)...")
    
    # System Capabilities
    caps_data = [
        {"code": "offering_search", "name": "Tìm kiếm sản phẩm", "description": "Tìm kiếm sản phẩm trong kho tri thức"},
        {"code": "offering_comparison", "name": "So sánh giá", "description": "So sánh giá giữa các phiên bản/đối thủ"},
        {"code": "offering_inventory_check", "name": "Kiểm tra tồn kho", "description": "Kiểm tra hàng còn trong kho hay không"},
        {"code": "policy_lookup", "name": "Tra cứu chính sách", "description": "Tìm kiếm quy định và chính sách nội bộ"},
        {"code": "transaction_analysis", "name": "Phân tích giao dịch", "description": "Phân tích và đối soát dữ liệu giao dịch"},
        {"code": "market_data_realtime", "name": "Giá thị trường thực tế", "description": "Truy xuất giá vàng, chứng khoán theo thời gian thực"},
        {"code": "strategic_analysis", "name": "Nhận định chiến lược", "description": "Phân tích xu hướng và đưa ra nhận định thị trường"},
        {"code": "assessment_test", "name": "Kiểm tra trình độ", "description": "Đánh giá năng lực đầu vào (Education)"},
        {"code": "credit_scoring", "name": "Chấm điểm tín dụng", "description": "Đánh giá khả năng trả nợ (Finance)"},
        {"code": "trade_in_valuation", "name": "Định giá thu cũ", "description": "Định giá tài sản cũ để đổi mới (Auto)"},
    ]
    cap_map = {}
    for cap in caps_data:
        res = await db.execute(select(SystemCapability).where(SystemCapability.code == cap["code"]))
        item = res.scalar_one_or_none()
        if not item:
            item = SystemCapability(**cap)
            db.add(item)
            await db.flush()
            print(f"Created System Capability: {cap['code']}")
        cap_map[cap["code"]] = str(item.id)

    # Knowledge Domains
    domains_data = [
        {"code": "jewelry", "name": "Jewelry & Luxury", "description": "Ngành hàng Trang sức và Đá quý", "domain_type": "offering"},
        {"code": "finance", "name": "Corporate Finance", "description": "Quản lý dòng tiền và vốn doanh nghiệp", "domain_type": "business"},
        {"code": "accounting", "name": "Accounting & Tax", "description": "Hạch toán kế toán và báo cáo thuế", "domain_type": "business"},
        {"code": "hr", "name": "Human Resources", "description": "Quản trị nhân sự và phúc lợi", "domain_type": "business"},
        {"code": "market_analysis", "name": "Market Analysis", "description": "Phân tích thị trường tài chính, vàng, chứng khoán", "domain_type": "business"},
        {"code": "food_beverage", "name": "F&B Operations", "description": "Vận hành nhà hàng, quán ăn, cafe", "domain_type": "offering"},
        {"code": "real_estate", "name": "Real Estate", "description": "Bất động sản, căn hộ, đất nền", "domain_type": "offering"},
        {"code": "education", "name": "Education", "description": "Giáo dục, tuyển sinh, khoá học", "domain_type": "offering"},
        {"code": "used_car", "name": "Used Car Trading", "description": "Mua bán ô tô cũ, định giá xe", "domain_type": "offering"},
    ]
    
    domain_map = {}
    for d_data in domains_data:
        res = await db.execute(select(KnowledgeDomain).where(KnowledgeDomain.code == d_data["code"]))
        domain = res.scalar_one_or_none()
        if not domain:
            domain = KnowledgeDomain(
                id=str(uuid.uuid4()),
                **d_data
            )
            db.add(domain)
            await db.flush()
            print(f"Created Knowledge Domain: {d_data['code']}")
        domain_map[d_data["code"]] = str(domain.id)
    
    return domain_map, cap_map
