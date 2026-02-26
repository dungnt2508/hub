# Kế Hoạch Trải Nghiệm Frontend 2026 (Premium & Commercial)

Để tạo sản phẩm chatbot thương mại đẳng cấp năm 2026, Frontend không chỉ "đẹp" mà phải mang cảm giác **AI-Native** (Sinh ra cho AI).

=> **Điểm linh hoạt ăn tiền:** Khi Bot so sánh sản phẩm, thay vì chỉ text dài, nó render **Bento Grid** hoặc **Comparison Table** tương tác. User thấy rõ kết quả, không cần scroll qua đoạn văn.

---

## 1. Triết Lý Thiết Kế

- **Generative UI (G-UI):** Giao diện không cố định. Bot so sánh → render Bento Grid hoặc Comparison Table tương tác.
- **Glassmorphism 2.0:** Nền mờ đục (translucent) + đổ bóng sâu, cảm giác không gian đa chiều.
- **Micro-interactions:** AI "suy nghĩ" qua hiệu ứng sóng (ripple), gradient chuyển động - User bớt nặng nề khi chờ LLM.

---

## 2. Thành Phần Chủ Đạo

### Chat Widget (User-facing)
- **Floating Bubbles:** Không viền, tập trung nội dung
- **Interactive Cards:** Thẻ sản phẩm có nút "Thêm giỏ", "Xem chi tiết" trong dòng chat
- **Voice-First:** Sẵn sàng giao tiếp giọng nói, sóng âm đẹp

### Admin Dashboard (Commercial-ready)
- **Observability Matrix:** Luồng suy nghĩ Agent (Decision Tree) dạng sơ đồ
- **Cost-per-Session:** Biểu đồ chi phí token theo phiên - admin kiểm soát ROI
- **Live Playground:** Tinh chỉnh Prompt, test Tool ngay lập tức

---

## 3. Tech Stack Khuyến Nghị (2026)

| Thành phần | Công nghệ |
|------------|-----------|
| **Framework** | Next.js 16+ (App Router, Server Components) |
| **Styling** | TailwindCSS 4+ hoặc CSS Variables |
| **Animations** | Framer Motion, Rive (micro-animations vector) |
| **State** | Zustand, React Query |

---

## 4. Trạng Thái Triển Khai

### Core UI & Design System
- [x] **Design System:** Màu sắc, Typography, Glassmorphism (Vanilla CSS + Tailwind)
- [x] **Chat Engine:** `ChatWidget`, `ChatMessage` (Markdown, Code Highlight)

### Generative UI (G-UI)
- [x] **Bento Grid:** `BentoGrid.tsx` - danh sách/s so sánh sản phẩm
- [x] **Interactive Cards:** Tích hợp trong chat qua `ui_metadata`

### Admin Dashboard
- [x] **Decision Visualizer:** `DecisionVisualizer.tsx` - luồng suy nghĩ AI
- [x] **Cost Analytics:** `CostAnalytics.tsx` - Token, Latency realtime

---

**Trạng thái Tài liệu**: Phản ánh triển khai hiện tại.
**Cập nhật lần cuối**: Tháng 02/2026.
