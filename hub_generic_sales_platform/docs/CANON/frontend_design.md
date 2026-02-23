# Plan: Frontend Experience 2026 (Premium & Commercial)

Để tạo ra một sản phẩm chatbot thương mại đẳng cấp năm 2026, Frontend không chỉ là "đẹp" mà phải mang lại cảm giác **AI-Native** (Sinh ra cho AI).

## 1. Triết lý Thiết kế (Design Language)

-   **Generative UI (G-UI)**: Giao diện không cố định. Khi Bot so sánh sản phẩm, thay vì chỉ hiện text, nó sẽ tự động render một **Bento Grid** hoặc **Comparison Table** có tính tương tác cao.
-   **Glassmorphism 2.0**: Sử dụng các lớp nền mờ đục (translucent) kết hợp với đổ bóng sâu, tạo cảm giác không gian đa chiều.
-   **Micro-interactions**: AI "suy nghĩ" thông qua các hiệu ứng sóng (ripple) hoặc gradient chuyển động nhẹ nhàng, giúp User cảm thấy bớt nặng nề khi chờ đợi LLM.

## 2. Các thành phần chủ đạo

### Chat Widget (User-facing)
-   **Floating Bubbles**: Thiết kế không viền, tập trung vào nội dung.
-   **Interactive Cards**: Các thẻ sản phẩm có nút "Thêm vào giỏ hàng" hoặc "Xem chi tiết" tích hợp trực tiếp trong dòng chat.
-   **Voice-First Integration**: Sẵn sàng cho giao tiếp bằng giọng nói với hiệu ứng sóng âm đẹp mắt.

### Admin Dashboard (Commercial-ready)
-   **Observability Matrix**: Hiển thị luồng suy nghĩ của Agent (Decision Tree) dưới dạng sơ đồ trực quan.
-   **Cost-per-Session Tracking**: Biểu đồ chi phí token theo từng phiên chat để admin kiểm soát hiệu quả kinh doanh.
-   **Live Playground**: Nơi tinh chỉnh Prompt và Test Tool ngay lập tức.

## 3. Tech Stack Khuyến nghị (2026 Standard)

-   **Framework**: Next.js 16+ (App Router, Server Components).
-   **Styling**: TailwindCSS 4+ hoặc CSS Variables (Native) để tối ưu tốc độ.
-   **Animations**: Framer Motion kết hợp với Rive (cho các micro-animations vector nhẹ).
-   **State Management**: Zustand hoặc React Query (TanStack) để đồng bộ dữ liệu realtime.

## 4. Trạng thái Triển khai (Implemented Components)

### Core UI & Design System
-   [x] **Design System**: Đã thiết kế hệ thống màu sắc, Typography và Glassmorphism (Vanilla CSS + Tailwind).
-   [x] **Chat Engine**: Đã triển khai `ChatWidget` và `ChatMessage` hỗ trợ Markdown và Code Highlight.

### Generative UI (G-UI)
-   [x] **Bento Grid**: Component `BentoGrid.tsx` dùng để hiển thị danh sách sản phẩm hoặc so sánh sản phẩm theo phong cách hiện đại.
-   [x] **Interactive Cards**: Tích hợp trực tiếp trong luồng chat thông qua `ui_metadata`.

### Admin Dashboard
-   [x] **Decision Visualizer**: Component `DecisionVisualizer.tsx` trực quan hóa luồng suy nghĩ của AI (Decision Tree).
-   [x] **Cost Analytics**: Component `CostAnalytics.tsx` theo dõi chi phí Token và Latency theo thời gian thực.
