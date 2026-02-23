# Test Coverage – Cập nhật 14/02/2026

**Mục tiêu coverage: 70%** – Đạt 70.04%

## Test mới thêm

### 1. Knowledge API (`tests/integration/api/test_knowledge_api.py`)
- **test_comparison_crud_offering_ids** – CRUD Comparison với `offering_ids` (schema source of truth)
- **test_comparison_list_by_domain** – Lọc comparisons theo domain_id
- **test_comparison_404_on_update_nonexistent** – 404 khi update comparison không tồn tại

### 2. Knowledge Schemas (`tests/unit/interfaces/api/test_knowledge_schemas.py`)
- **test_comparison_create_offering_ids_required** – offering_ids required
- **test_comparison_create_offering_ids_empty_list** – offering_ids có thể []
- **test_comparison_create_missing_offering_ids** – thiếu offering_ids → ValidationError
- **test_comparison_update_offering_ids_optional** – ComparisonUpdate.offering_ids optional
- **test_comparison_response_offering_ids** – ComparisonResponse có offering_ids

### 3. Analytics API (`tests/integration/api/test_analytics_api.py`)
- **test_analytics_dashboard_empty** – Dashboard khi chưa có sessions *(skip trên SQLite vì date_trunc)*
- **test_analytics_dashboard_with_data** – Dashboard khi có session/decision *(skip trên SQLite)*

### 4. Guardrails API (`tests/integration/api/test_guardrails_api.py`)
- **test_guardrails_crud** – CRUD guardrails (create, list, update, delete)

### 5. Contacts API (`tests/integration/api/test_contacts_api.py`)
- **test_contacts_list_empty** – List contacts khi chưa có sessions
- **test_contacts_list_with_sessions** – List contacts derive từ runtime_session + ext_metadata

### 6. Migration API (`tests/integration/api/test_migration_api.py`)
- **test_get_migration_job_200** – GET job tồn tại
- **test_get_migration_job_404** – GET job không tồn tại
- **test_scrape_400_no_domain** – Scrape thiếu domain_id → 400
- **test_scrape_200_with_domain** – Scrape có domain_id → 200
- **test_commit_migration_400** – Commit job chưa STAGED → 400

### 7. Ontology API (`tests/integration/api/test_ontology_api.py`)
- **test_list_domains**, **test_create_domain**, **test_create_domain_400_duplicate**
- **test_list_attribute_definitions**, **test_list_attribute_definitions_with_domain_id**
- **test_create_attribute_definition**, **test_create_attribute_definition_400_duplicate**
- **test_list_tenant_configs**, **test_update_tenant_config_create**, **test_update_tenant_config_update**

### 8. Auth API (`tests/integration/api/test_auth_api.py`)
- **test_login_401_invalid_credentials** – Login sai mật khẩu → 401
- **test_login_200** – Login đúng → 200 + token
- **test_me_200** – GET /auth/me → 200

### 9. Catalog API (`tests/integration/api/test_catalog_api.py`)
- **test_list_offerings_200**, **test_get_offering_by_code_200**, **test_get_offering_by_code_404**
- **test_list_channels_200**, **test_list_price_lists_200**, **test_list_locations_200**
- **test_inventory_status_200**

### 10. Admin API (`tests/integration/api/test_admin_api.py`)
- **test_admin_health** – GET /health
- **test_tenant_admin_flow** – CRUD tenant + update + status
- **test_update_tenant_404** – Update tenant không tồn tại → 404

### 11. Auth Dependencies (`tests/unit/interfaces/api/test_auth_dependencies.py`)
- Unit tests cho `get_current_tenant_id` (tách từ test_auth_api để tránh conflict tên module)

---

## Chạy test

```powershell
& "G:\project python\Env3_12\Scripts\Activate.ps1"
cd "G:\project python\hub\hub_generic_sales_platform"
python -m pytest --cov=app --cov-report=term --cov-fail-under=70 -q
```

## Lưu ý

- Analytics tests bị skip trên SQLite (test DB) vì `date_trunc` chỉ có trên PostgreSQL. Chạy với PostgreSQL để test đầy đủ.
