# Cấu trúc Kiểm thử (IRIS Hub v4)

Hệ thống kiểm thử được thiết kế theo mô hình phân tầng (Pyramid Testing) để đảm bảo độ tin cậy và hiệu năng. Mục tiêu: **Coverage >= 70%**.

## 1. Cấu trúc thư mục
```
tests/
├── unit/                   # Kiểm thử logic đơn lẻ (Mock dependencies)
│   ├── core/               # StateMachine, Domain logic
│   ├── services/           # CatalogService, AuthService (Business Rules)
│   └── infrastructure/     # LLM Factory, Provider routing
├── integration/            # Kiểm thử sự phối hợp (Real DB + Mock LLM)
│   ├── database/           # Repository isolation, Tenant safety
│   ├── orchestrators/      # Hybrid flow, 3-tier routing
│   └── api/                # Test 11 modular routers (Chat, Bot, Product...)
├── e2e/                    # End-to-End flows
│   └── bot_flows/          # Kịch bản: Greeting -> Search -> Details -> Close
├── fixtures/               # Dữ liệu mẫu (Catalog V4, Knowledge data)
├── support/                # Utils hỗ trợ (Scrapers, DB cleanup)
├── conftest.py             # Global fixtures (client, db, tenant_1, tenant_2)
└── pytest.ini              # Cấu hình markers & Coverage settings
```

## 2. Hướng dẫn sử dụng

### 2.1 Cài đặt môi trường test
```bash
pip install -r requirements-dev.txt
```

### 2.2 Chạy kiểm thử
*   **Chạy tất cả (có báo cáo coverage):**
    ```bash
    pytest
    ```
*   **Chạy theo tầng (Markers):**
    ```bash
    pytest -m unit         # Logic thuần (Fast)
    pytest -m integration  # Có database (Slower)
    pytest -m api          # Test API Endpoints
    pytest -m e2e          # Full flows
    ```
*   **Kiểm tra Coverage chi tiết:**
    ```bash
    pytest --cov=app --cov-report=html
    # Mở file htmlcov/index.html bằng trình duyệt để xem báo cáo từng dòng code
    ```
    ```bash
    pytest -v --cov=app --cov-report=term-missing
    # note
    pytest.exe: The command to run the test runner.
    -v (verbose): Increases verbosity, showing each individual test name and its result (PASSED/FAILED) instead of just dots.
    --cov=app: Tells the coverage tool to measure code coverage only for the app directory (your source code), ignoring tests or libraries.
    --cov-report=term-missing: Displays the coverage report directly in the terminal at the end. Importantly, it lists the specific line numbers that were not executed during tests (the "missing" part), helping you identify exactly what code is untested.
    Summary: "Run all tests verbosely, calculate how much of the app folder was executed, and list any unexecuted lines right here in the terminal."
    


## 3. Tiêu chuẩn viết Test
1.  **Tenant Isolation:** Mọi test case liên quan đến dữ liệu multi-tenant **PHẢI** kiểm tra việc rò rỉ dữ liệu giữa `tenant_1` và `tenant_2`.
2.  **Mocking:**
    *   Sử dụng `unittest.mock` cho các cuộc gọi LLM (OpenAI, Anthropic) để tiết kiệm chi phí.
    *   Dùng `db` (AsyncSession) fixture cho các thao tác database.
3.  **Naming Convention:**
    *   File: `test_*.py`
    *   Function: `test_*`

## 4. Coverage Goals
| Layer | Target Coverage | Hiện tại |
|-------|----------------|----------|
| API Routers | 80% | ~70% |
| Domain/Core | 85% | Đạt |
| Orchestrators | 70% | ~88% |
| **Tổng thể** | **70%+** | **70.04%** ✓ |