# Danh sách Công việc: Hoàn thiện Catalog Service & Bot

## Giai đoạn 1: Khám phá & Đánh giá (Exploration & Audit)
- [x] Khám phá cấu trúc codebase
- [x] Review triển khai Catalog Service (Repositories, Services)
- [x] Review triển khai Bot Service (Knowledge Engine, RAG)
- [x] Xác định các khoảng trống kiến trúc và nợ kỹ thuật (technical debt)
- [x] Lập Kế hoạch Triển khai (Implementation Plan)

## Giai đoạn 2: Tinh chỉnh Catalog Service
- [ ] Triển khai migration cho bảng Category và Attribute
- [ ] Cập nhật `ProductRepository` để hỗ trợ lọc theo cấu trúc
- [ ] Tái cấu trúc `ProductService` để chuyển logic về các Domain pattern (Value Objects, Entities)

## Giai đoạn 3: Nâng cấp Trí tuệ cho Bot
- [ ] Tạo `CatalogIntentClassifier`
- [ ] Cập nhật `CatalogKnowledgeEngine` để hỗ trợ Hybrid Search
- [ ] Tăng cường khả năng truy vấn SQL/API cho bot
- [ ] Triển khai RAG Prompt nghiêm ngặt để đảm bảo tính nhất quán của dữ liệu

## Giai đoạn 4: Xác minh & Hoàn thiện
- [ ] Viết unit tests cho Intent Classifier
- [ ] Xác minh phản hồi của Bot với nhiều tình huống catalog khác nhau
- [ ] Lập Báo cáo Review Kiến trúc cuối cùng
