# 📋 CHECKLIST REFACTOR HỆ THỐNG (DOMAIN-CENTRIC / ONTOLOGY-DRIVEN)

## I. DATABASE SCHEMA (ALEMBIC) - TẦNG NỀN TẢNG
- [ ] **refactor migrate :** Tạo file migration `[001_initial_schema.py]` `[002_add_migration_hub.py](../../../alembic/versions/002_add_migration_hub.py)`.
- [ ] **Globalization `knowledge_domain`:**
    - [ ] Xóa cột `tenant_id`.
    - [ ] Cập nhật Unique Constraint: `code` phải là duy nhất trên toàn hệ thống (Global).
    - [ ] thêm domain_type   (business | product)
- [ ] **Globalization `attribute_definition`:**
    - [ ] Xóa cột `tenant_id`, `bot_id`.
    - [ ] Đảm bảo `domain_id` là NOT NULL (Mọi attribute phải thuộc về 1 domain).
    - [ ] Cập nhật Unique Constraint: `(domain_id, key)` là duy nhất.
    - [ ] Thêm value_constraint (enum range / regex / allowed_values)
    - [ ] Thêm emantic_type (physical, financial, categorical, identifier)
- [ ] **Tạo bảng `tenant_attribute_config` (Tầng Override):**
    - [ ] Các cột: `id`, `tenant_id`, `attribute_def_id`, `label` (tên hiển thị riêng), `is_display`, `is_searchable`.
    - [ ] FK đến `tenant` và `attribute_definition`.
- [ ] **Chuẩn hóa naming toàn hệ thống**
    - [ ] Đổi cho đúng hệ trục. ví dụ `attribute_definition` đổi thành `domain_attribute_definition`
- [ ] **Decouple `product`:**
    - [ ] Chuyển `bot_id` thành Nullable (Sản phẩm thuộc về Tenant, không phải thuộc về 1 Bot duy nhất).
    - [ ] Đảm bảo `domain_id` của Product tham chiếu đúng đến Global Domain.
    - [ ] Ràng buộc logic: product.domain_id ∈ knowledge_domain . Bot chỉ là consumer, không phải owner.
- [ ] **Cập nhật Constraints/Indexes:** Rà soát lại tất cả các index có chứa `tenant_id` cũ trong tầng định nghĩa.

## II. SEED DATA & MIGRATION - TẦNG DỮ LIỆU CỨNG
- [ ] **Data Migration Script:**
    - [ ] Viết script chuyển đổi dữ liệu hiện tại từ "Tenant Domain" sang "Global Domain".
    - [ ] Gộp các `attribute_definition` trùng tên thành một `key` duy nhất trong Global Domain.
            Luật gộp bắt buộc chỉ gộp khi:
                      cùng domain_id
                      cùng value_type
                      Nếu lệch → tách key mới (salary_amount vs salary_text)
            Không auto-merge mù.
- [ ] **Seed Global Ontology:**
    - [ ] Định nghĩa bộ concept chuẩn cho **Jewelry** (metal, karat, stone_type, weight).
    - [ ] Định nghĩa bộ concept chuẩn cho **HR** (base_salary, level, department).
    - [ ] Định nghĩa bộ concept chuẩn for **EV** (battery_type, range_km, charge_speed).
- [ ] **Default Tenant Config:** Tự động tạo bản ghi `attribute_config` cho các tenant hiện có dựa trên attribute cũ của họ.

## III. BACKEND REFACTOR (FASTAPI / SQLALCHEMY)
- [ ] **Models Update:** 
    - [ ]  tách vai trò model theo ontology :
  
             Bắt buộc có 4 model lõi:
  
                knowledge_domain
                domain_attribute_definition
                tenant_attribute_config
                product_attribute_value
    
            Sai lầm phổ biến cần tránh:
            
                Không cho Product giữ attribute trực tiếp dạng JSON
                Không cho AttributeConfig chứa semantic (type, unit, enum)
            
            Semantic chỉ nằm ở domain_attribute_definition.

- [ ] **Schemas (Pydantic) Update:**
    - [ ] Cần 3 lớp schema rõ ràng:
  
                DomainAttributeDefinitionRead   (global, immutable)
                TenantAttributeConfigRead       (override, UI/business)
                ProductAttributeValueRead/Write (runtime data)
  
                Nếu gộp definition + value trong schema → AI reasoning hỏng.
- [ ] **CRUD Logic:**
    - [ ] API lấy danh sách Attribute: Phải join giữa `attribute_definition` và `attribute_config` để lấy đúng Label/Visibility của Tenant. Và đảm bảo `definition.domain_id == tenant.active_domain_id`
    - [ ] Logic tạo Product: Kiểm tra `domain_id` của Product có khớp với `domain_id` của các Attribute được gán hay không.
      - Phải enforce 3 điều kiện:
      
                product.domain_id == domain_attribute_definition.domain_id
                Attribute phải có tenant_attribute_config tồn tại (hoặc default)
                Value type phải khớp với attribute_definition.data_type
                Không enforce đủ 3 → dữ liệu rác sẽ lọt vào core.
- [ ] **Bot Privacy Logic:** Sửa logic "Bot visibility". Bot sẽ truy xuất sản phẩm thông qua `tenant_id` + lọc theo điều kiện kinh doanh, thay vì hard-code `bot_id`.
  
        Bot không phải owner, bot là executor. Chuẩn logic:
        Bot
        → thuộc Tenant
        → có Scope (read_product, read_attribute, crawl)
        → truy cập Product qua Tenant + Policy
- [ ] **Crawl Pipeline Fix:**
    - [ ] Crawl phải đi theo pipeline:
    ```
    
    Raw HTML / API
    → Raw Snapshot
    → Candidate Attribute (string, regex, xpath)
    → Normalize (unit, enum, number)
    → Match domain_attribute_definition.key
    → Validate type + domain
    → Persist product_attribute_value
    
    ```

## IV. TESTCASES - TẦNG ĐẢM BẢO CHẤT LƯỢNG
- [ ] **Test Global Integrity:** 
    - [ ] Đảm bảo khi xóa 1 Tenant, các Global Attribute và Domain vẫn tồn tại.
    - [ ] Không cho xóa knowledge_domain nếu còn `domain_attribute_definition`
    - [ ] Không cho xóa `domain_attribute_definition` nếu còn `product_attribute_value`
    - [ ] Xóa Tenant → chỉ xóa `tenant_attribute_config` + `product` của tenant đó
- [ ] **Test Multi-tenant Isolation:** 
    - [ ] Tenant A không thể xem hoặc sửa `label` của Tenant B.
    - [ ] Tenant A không đọc được `tenant_attribute_config` của Tenant B
    - [ ] Tenant A không override attribute không thuộc domain của mình
    - [ ] API list attribute phải luôn bị scope theo tenant_id
- [ ] **Test Semantic Consistency:** Đảm bảo 2 Bot khác nhau của cùng 1 Tenant đều hiểu `metal_type` theo cùng một cách.
- [ ] **Test Migration Safety:** Chạy thử migration trên dữ liệu mẫu để đảm bảo không mất `product_attribute` hiện có.
- [ ] **Test Runtime Validation:**
    - [ ] Reject khi product_attribute_value sai data_type
    - [ ] Reject khi gán attribute khác domain
    - [ ] Reject khi tenant chưa có config (nếu policy yêu cầu)

## V. FRONTEND
- [ ] Global Ontology Admin (immutable semantic)
- [ ] Tenant Attribute Config UI (override-only)
- [ ] Ontology-driven Catalog Form
- [ ] Client-side semantic validation
- [ ] Debug-safe label/key rendering
---
*Lưu ý: Mọi bước refactor cần được thực hiện trên branch riêng và được review kỹ lưỡng để tránh gián đoạn dịch vụ.*
