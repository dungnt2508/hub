## About domain
domain = miền ngữ nghĩa độc lập

Một domain tồn tại khi:

    Có bộ khái niệm riêng
    Có thuộc tính riêng
    Có logic suy luận riêng
    Không dùng chung ontology với domain khác

    (Ontology = tập các khái niệm + thuộc tính + quan hệ + ràng buộc ngữ nghĩa trong một domain.)

Theo định nghĩa này:

    HR → domain 
    Sales → domain 

    Finance → domain 
    Jewelry → domain 
    Fashion → domain 
    EV → domain
    
    -> Tất cả đều là domain hợp lệ.

#### Nhưng có 2 loại domain khác nhau (rất quan trọng)

- A. Business / Process Domain

        HR
        Sales
        Finance
        Procurement

Đặc trưng:

        Entity là nghiệp vụ
        Attribute mang tính quy trình / tổ chức
        AI reasoning thiên về policy, workflow, compliance

- B. Product / Industry Domain

        Jewelry
        Fashion
        EV
        Real Estate
        Electronics

Đặc trưng:

        Entity là sản phẩm
        Attribute mang tính vật lý / kỹ thuật
        AI reasoning thiên về so sánh, tư vấn, bán hàng

#### Chung attribute_definition
Vì ở tầng kiến trúc:

    attribute_definition
        id
        domain_id
        key
        value_type

Domain chỉ là partition logic, không phải schema vật lý.

Ví dụ Jewelry và HR:

    không dùng chung attribute
    nhưng dùng chung cơ chế định nghĩa attribute

Jewelry

    domain = jewelry
    attribute:
      - metal
      - karat
      - carat
      - stone_type

EV

    domain = ev
    attribute:
      - battery_kwh
      - range_km
      - charging_type

HR

    domain = hr
    attribute:
      - base_salary
      - contract_type
      - employee_level


### Kết luận cứng

Jewelry / Fashion / EV là domain
HR / Sales / Finance cũng là domain

-> Domain = miền ngữ nghĩa, không phải phòng ban

Tất cả dùng 1 cơ chế attribute_definition

Phân biệt bằng domain_id

Không tenant hoá domain

Nếu giữ đúng ranh giới này, hệ của m là domain-aware AI platform.

Nếu không, nó chỉ là database linh tinh có vector search.