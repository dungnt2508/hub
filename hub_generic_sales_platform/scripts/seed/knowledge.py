from decimal import Decimal
from datetime import datetime
from sqlalchemy import select
from app.infrastructure.database.models import (
    TenantOffering, TenantOfferingVersion, 
    TenantOfferingAttributeValue, TenantOfferingVariant, TenantVariantPrice,
    TenantInventoryLocation, TenantInventoryItem, TenantPriceList,
    TenantSalesChannel,
    BotFAQ, BotUseCase, BotComparison, TenantGuardrail, OfferingStatus
)
import uuid

async def seed_knowledge(db, tenant_id, bot_id_map, domain_map, full_attr_map, tenant_key=None):
    print("Seeding Knowledge Base for all domains...")

    # --- Sales Channels (WEB, ZALO, FACEBOOK) for Integrations page ---
    for code, name in [("WEB", "Web Chat"), ("ZALO", "Zalo OA"), ("FACEBOOK", "Facebook Messenger")]:
        res = await db.execute(select(TenantSalesChannel).where(
            TenantSalesChannel.tenant_id == tenant_id, TenantSalesChannel.code == code
        ))
        if not res.scalar_one_or_none():
            db.add(TenantSalesChannel(tenant_id=tenant_id, code=code, name=name, is_active=True))
    
    await db.flush() # Ensure channel IDs are available
    
    # # --- 1. Finance Domain ---
    # fin_domain_id = domain_map["finance"]
    # fin_bot_id = bot_id_map["finance"]
    # fin_attrs = full_attr_map["finance"]

    # # Finance FAQ
    # db.add(BotFAQ(
    #     tenant_id=tenant_id, bot_id=fin_bot_id, domain_id=fin_domain_id,
    #     question="Quy trình phê duyệt chi phí như thế nào?",
    #     answer="Các khoản chi dưới 10 triệu được quản lý trực tiếp phê duyệt. Trên 10 triệu cần Kế toán trưởng xác nhận.",
    #     category="policy"
    # ))

    # # Finance Guardrail
    # db.add(TenantGuardrail(
    #     tenant_id=tenant_id, code="FIN_ADVICE_GDR", name="No financial advice",
    #     condition_expression="topic matches 'investment_advice'",
    #     violation_action="block",
    #     fallback_message="Tôi chỉ hỗ trợ tra cứu quy định tài chính nội bộ, không đưa ra lời khuyên đầu tư."
    # ))

    # # --- 2. HR Domain ---
    # hr_domain_id = domain_map["hr"]
    # hr_bot_id = bot_id_map["hr"]
    
    # db.add(BotFAQ(
    #     tenant_id=tenant_id, bot_id=hr_bot_id, domain_id=hr_domain_id,
    #     question="Số ngày phép năm của tôi là bao nhiêu?",
    #     answer="Mỗi nhân viên có 12 ngày phép/năm, cộng thêm 1 ngày sau mỗi 5 năm làm việc.",
    #     category="benefits"
    # ))

    # # --- 3. Market Analysis Domain ---
    # mkt_domain_id = domain_map["market_analysis"]
    # mkt_bot_id = bot_id_map["market_analysis"]
    # mkt_attrs = full_attr_map["market_analysis"]

    # db.add(BotFAQ(
    #     tenant_id=tenant_id, bot_id=mkt_bot_id, domain_id=mkt_domain_id,
    #     question="Nhận định về giá vàng SJC tuần tới?",
    #     answer="Dựa trên xu hướng Fed duy trì lãi suất, vàng SJC có khả năng đi ngang. Chúng tôi khuyến nghị theo dõi mốc hỗ trợ 74 triệu đồng/lượng.",
    #     category="gold_strategy"
    # ))

    # db.add(BotFAQ(
    #     tenant_id=tenant_id, bot_id=mkt_bot_id, domain_id=mkt_domain_id,
    #     question="Làm sao để tra cứu giá chứng khoán thời gian thực?",
    #     answer="Bạn có thể hỏi 'Giá cổ phiếu [Mã]' (ví dụ: 'Giá cổ phiếu VNM'). Tôi sẽ truy xuất dữ liệu từ các sàn HOSE/HNX ngay lập tức.",
    #     category="guide"
    # ))

    # # Market Guardrail
    # db.add(TenantGuardrail(
    #     tenant_id=tenant_id, code="MKT_ADVICE_GDR", name="Financial Advisory Safety",
    #     condition_expression="topic matches 'specific_buy_sell_recommendation'",
    #     violation_action="block",
    #     fallback_message="Tôi chỉ cung cấp số liệu và phân tích khách quan, không đưa ra lời khuyên mua/bán cụ thể cho cá nhân. Vui lòng tham vấn chuyên gia tài chính."
    # ))

    # # Sample Stock as an 'Offering'
    # res = await db.execute(select(TenantOffering).where(TenantOffering.code == "STK-VNM"))
    # if not res.scalar_one_or_none():
    #     vnm = TenantOffering(tenant_id=tenant_id, domain_id=mkt_domain_id, bot_id=mkt_bot_id, code="STK-VNM", status=OfferingStatus.ACTIVE)
    #     db.add(vnm)
    #     await db.flush()
    #     ov = TenantOfferingVersion(offering_id=vnm.id, version=1, name="Vinamilk (VNM)", description="Công ty Cổ phần Sữa Việt Nam", status=OfferingStatus.ACTIVE)
    #     db.add(ov)
    #     await db.flush()
    #     if "ticker" in mkt_attrs:
    #         db.add(TenantOfferingAttributeValue(offering_version_id=ov.id, attribute_def_id=mkt_attrs["ticker"], value_text="VNM"))
    #     if "exchange" in mkt_attrs:
    #         db.add(TenantOfferingAttributeValue(offering_version_id=ov.id, attribute_def_id=mkt_attrs["exchange"], value_text="HOSE"))

    # # --- 4. Jewelry (Original Domain) ---
    # jw_domain_id = domain_map["jewelry"]
    # jw_bot_id = bot_id_map["jewelry"]
    # jw_attrs = full_attr_map["jewelry"]

    # # Offering (Jewelry)
    # off_code = "engaged-diamond-01"
    # res = await db.execute(select(TenantOffering).where(TenantOffering.code == off_code))
    # if not res.scalar_one_or_none():
    #     offering = TenantOffering(tenant_id=tenant_id, domain_id=jw_domain_id, bot_id=jw_bot_id, code=off_code, status=OfferingStatus.ACTIVE)
    #     db.add(offering)
    #     await db.flush()
        
    #     ov = TenantOfferingVersion(offering_id=offering.id, version=1, name="Nhẫn Kim Cương Iris", description="Vẻ đẹp vĩnh cửu.", status=OfferingStatus.ACTIVE)
    #     db.add(ov)
    #     await db.flush()
        
    #     if "clarity" in jw_attrs:
    #         db.add(TenantOfferingAttributeValue(offering_version_id=ov.id, attribute_def_id=jw_attrs["clarity"], value_text="VVS1"))

    # db.add(BotFAQ(
    #     tenant_id=tenant_id, bot_id=jw_bot_id, domain_id=jw_domain_id,
    #     question="Chất lượng kim cương ở đây thế nào?",
    #     answer="Kim cương Iris đạt chuẩn GIA với độ tinh khiết cực cao.",
    #     category="quality"
    # ))

    # --- 5. Food & Beverage (Com Tam & Tra Sua) ---
    # Only seed if generic or 'comtam'
    if not tenant_key or tenant_key == "comtam":
        fb_domain_id = domain_map.get("food_beverage")
        fb_bot_id = bot_id_map.get("food_beverage")
        fb_attrs = full_attr_map.get("food_beverage", {})

        if fb_domain_id and fb_bot_id:
            print("Seeding F&B Products...")
            
            products = [
                {
                    "code": "COM-TAM-DB",
                    "name": "Cơm Tấm Sườn Bì Chả",
                    "desc": "Cơm tấm đặc biệt với sườn nướng, bì thính và chả trứng muối.",
                    "price": 55000,
                    "category": "Món Chính"
                },
                 {
                    "code": "TS-TRAN-CHAU-DD",
                    "name": "Sữa Tươi Trân Châu Đường Đen",
                    "desc": "Sữa tươi Đà Lạt mix đường đen Hàn Quốc.",
                    "price": 35000,
                    "category": "Đồ Uống"
                }
            ]

            for p in products:
                res = await db.execute(select(TenantOffering).where(
                    TenantOffering.tenant_id == tenant_id,
                    TenantOffering.code == p["code"]
                ))
                if not res.scalar_one_or_none():
                    offering = TenantOffering(
                        tenant_id=tenant_id, 
                        domain_id=fb_domain_id, 
                        bot_id=fb_bot_id, 
                        code=p["code"], 
                        status=OfferingStatus.ACTIVE
                    )
                    db.add(offering)
                    await db.flush()
                    
                    ov = TenantOfferingVersion(
                        offering_id=offering.id, 
                        version=1, 
                        name=p["name"], 
                        description=p["desc"], 
                        status=OfferingStatus.ACTIVE
                    )
                    db.add(ov)
                    await db.flush()

    # --- 6. Real Estate (Sunrise Property) ---
    if tenant_key == "sunrise":
        re_domain_id = domain_map.get("real_estate")
        re_bot_id = bot_id_map.get("real_estate")
        re_attrs = full_attr_map.get("real_estate", {})
        
        if re_domain_id and re_bot_id:
            print("Seeding Real Estate Products...")
            # Sunrise Riverside Offerings
            re_products = [
                {
                    "code": "SSR-V1-1205",
                    "name": "Căn hộ 2PN Sunrise Riverside",
                    "desc": "Tháp V1, Tầng 12, View Hồ bơi. Đầy đủ nội thất.",
                    "price": 3500000000,
                    "attrs": {"bedrooms": 2, "bathrooms": 2, "area": 72, "direction": "Đông Nam", "legal_status": "Sổ hồng"}
                },
                {
                    "code": "SSR-V2-1504",
                    "name": "Căn hộ 3PN Sunrise Riverside (Góc)",
                    "desc": "Tháp V2, Tầng 15, View Sông. Căn góc thoáng mát.",
                    "price": 6200000000,
                    "attrs": {"bedrooms": 3, "bathrooms": 2, "area": 105, "direction": "Tây Bắc", "legal_status": "HĐMB"}
                }
            ]
            
            for p in re_products:
                offering = TenantOffering(tenant_id=tenant_id, domain_id=re_domain_id, bot_id=re_bot_id, code=p["code"], status=OfferingStatus.ACTIVE)
                db.add(offering)
                await db.flush()
                ov = TenantOfferingVersion(offering_id=offering.id, version=1, name=p["name"], description=p["desc"], status=OfferingStatus.ACTIVE)
                db.add(ov)
                await db.flush()
                
                # Seed Attributes (explicit NULL initialization)
                for key, val in p["attrs"].items():
                    if key in re_attrs and val is not None:
                        # Only set the required columns, don't pass None values
                        attr_data = {
                            "offering_version_id": ov.id, 
                            "attribute_def_id": re_attrs[key]
                        }
                        if isinstance(val, (int, float)):
                            attr_data["value_number"] = val
                        else:
                            attr_data["value_text"] = str(val)
                        db.add(TenantOfferingAttributeValue(**attr_data))
    
    # --- 7. Education (IvyPrep) ---
    if tenant_key == "ivy":
        edu_domain_id = domain_map.get("education")
        edu_bot_id = bot_id_map.get("education")
        edu_attrs = full_attr_map.get("education", {})
        
        if edu_domain_id and edu_bot_id:
            print("Seeding Course Products...")
            courses = [
                {
                    "code": "IELTS-FD", "name": "IELTS Foundation", "desc": "Khóa nền tảng cho người mất gốc (Target 4.0-5.0)",
                    "price": 8000000,
                    "attrs": {"level": "Beginner", "target": "5.0", "duration": "3 tháng"}
                },
                {
                    "code": "IELTS-INT", "name": "IELTS Intensive", "desc": "Luyện đề cấp tốc (Target 6.5+)",
                    "price": 15000000,
                    "attrs": {"level": "Intermediate", "target": "6.5+", "duration": "2 tháng"}
                }
            ]
             
            for p in courses:
                offering = TenantOffering(tenant_id=tenant_id, domain_id=edu_domain_id, bot_id=edu_bot_id, code=p["code"], status=OfferingStatus.ACTIVE)
                db.add(offering)
                await db.flush()
                ov = TenantOfferingVersion(offering_id=offering.id, version=1, name=p["name"], description=p["desc"], status=OfferingStatus.ACTIVE)
                db.add(ov)
                await db.flush()
                
                for key, val in p["attrs"].items():
                    if key in edu_attrs and val is not None:
                        db.add(TenantOfferingAttributeValue(
                            offering_version_id=ov.id, 
                            attribute_def_id=edu_attrs[key], 
                            value_text=str(val)
                        ))

    # --- 8. Auto (AnyCar) ---
    if tenant_key == "anycar":
        car_domain_id = domain_map.get("used_car")
        car_bot_id = bot_id_map.get("used_car")
        car_attrs = full_attr_map.get("used_car", {})
        
        if car_domain_id and car_bot_id:
            print("Seeding Auto Products (AnyCar)...")
            
            # 1. Setup Infra (Channels, Price List & Inventory Location)
            # Find channels
            channels = {}
            for code in ["WEB", "ZALO", "FACEBOOK"]:
                ch_res = await db.execute(select(TenantSalesChannel).where(TenantSalesChannel.tenant_id == tenant_id, TenantSalesChannel.code == code))
                channels[code] = ch_res.scalar_one_or_none()

            # Create Price Lists linked to channels
            price_lists = {}
            for code, ch_code in [("anycar-web", "WEB"), ("anycar-zalo", "ZALO"), ("anycar-fb", "FACEBOOK")]:
                plist_res = await db.execute(select(TenantPriceList).where(TenantPriceList.tenant_id == tenant_id, TenantPriceList.code == code))
                plist = plist_res.scalar_one_or_none()
                if not plist:
                    plist = TenantPriceList(
                        id=str(uuid.uuid4()), 
                        tenant_id=tenant_id, 
                        code=code, 
                        channel_id=channels.get(ch_code).id if channels.get(ch_code) else None
                    )
                    db.add(plist)
                    await db.flush()
                else:
                    # Fix existing if needed
                    if not plist.channel_id and channels.get(ch_code):
                        plist.channel_id = channels.get(ch_code).id
                price_lists[code] = plist
                
            inv_loc = await db.execute(select(TenantInventoryLocation).where(TenantInventoryLocation.tenant_id == tenant_id, TenantInventoryLocation.code == "anycar-warehouse-main"))
            inv_loc = inv_loc.scalar_one_or_none()
            if not inv_loc:
                inv_loc = TenantInventoryLocation(
                    id=str(uuid.uuid4()), tenant_id=tenant_id, code="anycar-warehouse-main", 
                    name="Kho Tổng (Hà Nội)", type="warehouse"
                )
                db.add(inv_loc)
                await db.flush()

            cars = [
                {
                    "code": "MAZDA3-2022-W", "name": "Mazda 3 Luxury 2022 (Trắng)", "desc": "Xe lướt, đẹp như mới, bao test hãng.",
                    "price": 580000000,
                    "attrs": {"year": 2022, "odo": 15000, "origin": "Việt Nam", "owner_history": "1 chủ"}
                },
                {
                    "code": "CX5-2021-R", "name": "Mazda CX-5 Premium 2021 (Đỏ)", "desc": "Gầm cao 5 chỗ, bản full option.",
                    "price": 790000000,
                    "attrs": {"year": 2021, "odo": 32000, "origin": "Việt Nam", "owner_history": "1 chủ"}
                },
                {
                    "code": "TOYOTA-VIOS-2024", "name": "Toyota Vios 1.5G 2024 (Bạc)", "desc": "Vua doanh số, bền bỉ, tiết kiệm nhiên liệu. Bản G cao cấp nhất.",
                    "price": 530000000,
                    "attrs": {"year": 2024, "odo": 5000, "origin": "Việt Nam", "owner_history": "1 chủ"}
                }
            ]

            for p in cars:
                # 2. Key Offering & Version
                res = await db.execute(select(TenantOffering).where(TenantOffering.tenant_id == tenant_id, TenantOffering.code == p["code"]))
                offering = res.scalar_one_or_none()
                
                if not offering:
                    offering = TenantOffering(tenant_id=tenant_id, domain_id=car_domain_id, bot_id=car_bot_id, code=p["code"], status=OfferingStatus.ACTIVE)
                    db.add(offering)
                    await db.flush()
                    
                    ov = TenantOfferingVersion(offering_id=offering.id, version=1, name=p["name"], description=p["desc"], status=OfferingStatus.ACTIVE)
                    db.add(ov)
                    await db.flush()

                    # 3. Attributes (using validator to ensure constraint compliance)
                    for key, val in p["attrs"].items():
                        if key in car_attrs and val is not None:
                            # Only set the required columns, don't pass None values
                            attr_data = {
                                "offering_version_id": ov.id, 
                                "attribute_def_id": car_attrs[key]
                            }
                            if isinstance(val, (int, float)):
                                attr_data["value_number"] = val
                            else:
                                attr_data["value_text"] = str(val)
                            db.add(TenantOfferingAttributeValue(**attr_data))
                    
                    # 4. Variant (Standard Variant 1-1 mapping)
                    variant = TenantOfferingVariant(
                        id=str(uuid.uuid4()), tenant_id=tenant_id, offering_id=offering.id, 
                        sku=f"{p['code']}-STD", name=p["name"], status="active"
                    )
                    db.add(variant)
                    await db.flush()
                    
                    # 5. Inventory
                    import random
                    qty = random.randint(1, 3)
                    db.add(TenantInventoryItem(
                        tenant_id=tenant_id, location_id=inv_loc.id, variant_id=variant.id,
                        stock_qty=qty, safety_stock=0
                    ))
                    
                    # 6. Prices (Multi-channel)
                    # Web (Base)
                    db.add(TenantVariantPrice(
                        price_list_id=price_lists["anycar-web"].id, variant_id=variant.id,
                        amount=p["price"], currency="VND"
                    ))
                    # Zalo (Slightly higher for service fee or lower for promo)
                    db.add(TenantVariantPrice(
                        price_list_id=price_lists["anycar-zalo"].id, variant_id=variant.id,
                        amount=int(p["price"] * 1.02), currency="VND" # +2%
                    ))
                    # FB (Same as web for now)
                    db.add(TenantVariantPrice(
                        price_list_id=price_lists["anycar-fb"].id, variant_id=variant.id,
                        amount=p["price"], currency="VND"
                    ))
                    
                    print(f"  -> Seeded {p['code']}: Qty={qty} (Price lists: Web/Zalo/FB)")

            # --- Bot FAQs (Tier 2 Knowledge Path) ---
            auto_faqs = [
                ("Làm sao để định giá xe cũ của tôi?", "Bạn cung cấp thông tin: dòng xe, năm sản xuất, số km đã đi (ODO). Tôi sẽ ước tính giá thu mua sơ bộ. Giá chính xác cần kiểm tra thực tế tại showroom.", "policy"),
                ("Có chương trình thu cũ đổi mới không?", "Có ạ! Chúng tôi có chương trình Thu cũ đổi mới - Trợ giá 10 triệu. Xe cũ của bạn sẽ được định giá, trừ vào xe mới. Anh/chị chỉ cần bù phần chênh lệch.", "policy"),
                ("Có lái thử xe tại nhà không?", "Có ạ! Dịch vụ Lái thử tại nhà - nhân viên sẽ mang xe qua địa chỉ anh/chị, đồng thời thợ kiểm tra xe cũ nếu anh/chị muốn đổi. Đặt lịch qua hotline hoặc chat.", "service"),
                ("Xe đã qua sử dụng có bảo hành không?", "Tất cả xe tại AnyCar đều qua kiểm tra kỹ thuật và bao test hãng. Bảo hành 6-12 tháng tùy dòng xe. Chi tiết từng xe được ghi trong hồ sơ.", "quality"),
                ("Tìm xe Mazda 3 giá bao nhiêu?", "Mazda 3 tại chúng tôi có nhiều phiên bản từ 530-635 triệu tùy năm sản xuất, ODO và tình trạng. Anh/chị muốn xem xe đời nào, ngân sách khoảng bao nhiêu ạ?", "product"),
                ("So sánh Mazda 3 và Toyota Vios?", "Mazda 3 thiên hướng thể thao, lái thú vị. Vios thiên tiết kiệm nhiên liệu, bền bỉ. Anh/chị ưu tiên cảm giác lái hay chi phí vận hành?", "comparison"),
            ]
            for q, a, cat in auto_faqs:
                res = await db.execute(select(BotFAQ).where(
                    BotFAQ.tenant_id == tenant_id, BotFAQ.bot_id == car_bot_id,
                    BotFAQ.question == q
                ))
                if not res.scalar_one_or_none():
                    db.add(BotFAQ(
                        tenant_id=tenant_id, bot_id=car_bot_id, domain_id=car_domain_id,
                        question=q, answer=a, category=cat, priority=0, is_active=True
                    ))
            print(f"  -> Seeded {len(auto_faqs)} FAQs for iris-auto-ai (Chuyen gia Dinh gia Xe)")

            # --- Guardrail (Auto Domain) ---
            res = await db.execute(select(TenantGuardrail).where(
                TenantGuardrail.tenant_id == tenant_id, TenantGuardrail.code == "AUTO_COMPETITOR_GDR"
            ))
            if not res.scalar_one_or_none():
                db.add(TenantGuardrail(
                    tenant_id=tenant_id, code="AUTO_COMPETITOR_GDR", name="Không so sánh đối thủ tiêu cực",
                    condition_expression="topic matches 'competitor_bashing'",
                    violation_action="block",
                    fallback_message="Tôi chuyên tư vấn xe tại AnyCar. Để so sánh chi tiết với đại lý khác, anh/chị nên tham khảo trực tiếp.",
                    priority=10, is_active=True
                ))
                print("  -> Seeded Guardrail: AUTO_COMPETITOR_GDR (no competitor bashing)")

            # --- BotUseCase (Trade-in scenario) ---
            res = await db.execute(select(BotUseCase).where(
                BotUseCase.tenant_id == tenant_id, BotUseCase.bot_id == car_bot_id,
                BotUseCase.scenario.ilike("%đổi xe Morning%")
            ))
            if not res.scalar_one_or_none():
                db.add(BotUseCase(
                    tenant_id=tenant_id, bot_id=car_bot_id, domain_id=car_domain_id,
                    scenario="Khách có xe Morning 2018 muốn đổi lên Mazda 3",
                    answer="Thu cũ đổi mới: Định giá Morning dựa trên bản (Si AT/Si MT), ODO, tình trạng. Trợ giá 10 triệu. Bù chênh lệch lấy Mazda 3. Có thể lái thử tại nhà.",
                    priority=0, is_active=True
                ))
                print("  -> Seeded UseCase: Trade-in Morning -> Mazda 3 scenario")

            # --- BotComparison (Mazda 3 vs Vios) ---
            mz3 = await db.execute(select(TenantOffering).where(
                TenantOffering.tenant_id == tenant_id, TenantOffering.code == "MAZDA3-2022-W"
            ))
            vios = await db.execute(select(TenantOffering).where(
                TenantOffering.tenant_id == tenant_id, TenantOffering.code == "TOYOTA-VIOS-2024"
            ))
            mz3_o, vios_o = mz3.scalar_one_or_none(), vios.scalar_one_or_none()
            if mz3_o and vios_o:
                res = await db.execute(select(BotComparison).where(
                    BotComparison.tenant_id == tenant_id, BotComparison.bot_id == car_bot_id,
                    BotComparison.title.ilike("%Mazda 3%Vios%")
                ))
                if not res.scalar_one_or_none():
                    db.add(BotComparison(
                        tenant_id=tenant_id, bot_id=car_bot_id, domain_id=car_domain_id,
                        title="Mazda 3 vs Toyota Vios",
                        description="So sánh hai dòng sedan phổ biến trong tầm giá 500-600 triệu.",
                        offering_ids=[mz3_o.id, vios_o.id],
                        comparison_data={"criteria": ["giá", "thiết kế", "tiết kiệm nhiên liệu", "cảm giác lái"]},
                        is_active=True
                    ))
                    print("  -> Seeded BotComparison: Mazda 3 vs Vios")

    print("Multi-domain Knowledge Base seeding completed.")
