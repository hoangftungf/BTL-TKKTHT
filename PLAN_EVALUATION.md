# KE HOACH TRIEN KHAI & DANH GIA HE THONG AI E-COMMERCE

> **Muc tieu**: Chuan hoa du lieu, danh gia 3 mo hinh (Llama3, Qwen2.5, Gemma2) tren 4 tap du lieu, xuat bao cao do an tot nghiep.

---

## TONG QUAN TIMELINE

| Phase | Noi dung | Thoi gian | Trang thai |
|-------|----------|-----------|------------|
| **Phase 1** | Data & Category Preparation | 3 ngay | [ ] Chua bat dau |
| **Phase 2** | Database & Index Rebuild | 1 ngay | [ ] Chua bat dau |
| **Phase 3** | Model Evaluation Pipeline | 2 ngay | [ ] Chua bat dau |
| **Phase 4** | Report & Lock Best Model | 1 ngay | [ ] Chua bat dau |

**Tong**: 7 ngay lam viec

---

## PHASE 1: DATA & CATEGORY PREPARATION (3 ngay)

### Ngay 1: Don dep & Thiet lap Scraper

#### [P0] Task 1.1: Don dep du lieu cu
```bash
# Reset PostgreSQL databases
cd services/product-service && python manage.py flush --no-input
cd services/order-service && python manage.py flush --no-input

# Clear Neo4j (trong Cypher shell)
# MATCH (n) DETACH DELETE n

# Clear Redis cache
redis-cli FLUSHALL

# Xoa FAISS index cu
rm -rf /app/ai_index/*
```

#### [P0] Task 1.2: Cai dat cac model LLM
```bash
# Pull 3 models can danh gia (chay tuan tu, khong dong thoi)
ollama pull llama3:8b
ollama pull qwen2.5:7b
ollama pull gemma2:9b

# Pull embedding model
ollama pull nomic-embed-text

# Kiem tra
ollama list
```

#### [P0] Task 1.3: Tao Scraper Script
- **File**: `scripts/scrapers/tiki_scraper.py`
- **File**: `scripts/scrapers/shopee_scraper.py`
- **Cong nghe**: Playwright (async) + BeautifulSoup
- **Nganh hang muc tieu**:
  1. Dien tu - Cong nghe (Laptop, Dien thoai, Phu kien)
  2. Thoi trang Nam/Nu (Ao, Quan, Giay, Vay)
  3. My pham - Lam dep (Skincare, Makeup)
  4. Do gia dung (Nha bep, Phong ngu)

### Ngay 2: Cao du lieu & Xu ly

#### [P0] Task 2.1: Chay Scraper
```bash
# Cao Tiki (500-1000 san pham)
python scripts/scrapers/tiki_scraper.py --output data/raw/tiki_products.json --limit 1000

# Cao Shopee (500-1000 san pham)
python scripts/scrapers/shopee_scraper.py --output data/raw/shopee_products.json --limit 1000
```

#### [P1] Task 2.2: Tao Category Mapping Table (Bilingual)
- **File**: `scripts/data/category_mapping.json`
- **Cau truc 3 cap**:

```json
{
  "categories": [
    {
      "id": "cat_electronics",
      "name_vi": "Dien tu - Cong nghe",
      "name_en": "Electronics",
      "slug": "electronics",
      "level": 0,
      "children": [
        {
          "id": "cat_phones",
          "name_vi": "Dien thoai & Phu kien",
          "name_en": "Phones & Accessories",
          "slug": "phones-accessories",
          "level": 1,
          "children": [
            {"id": "cat_smartphone", "name_vi": "Dien thoai Smartphone", "name_en": "Smartphone", "slug": "smartphone", "level": 2},
            {"id": "cat_tablet", "name_vi": "May tinh bang", "name_en": "Tablet", "slug": "tablet", "level": 2},
            {"id": "cat_phone_acc", "name_vi": "Phu kien dien thoai", "name_en": "Phone Accessories", "slug": "phone-accessories", "level": 2}
          ]
        },
        {
          "id": "cat_computers",
          "name_vi": "May tinh & Laptop",
          "name_en": "Computers & Laptops",
          "slug": "computers-laptops",
          "level": 1,
          "children": [
            {"id": "cat_laptop", "name_vi": "Laptop", "name_en": "Laptop", "slug": "laptop", "level": 2},
            {"id": "cat_desktop", "name_vi": "PC de ban", "name_en": "Desktop PC", "slug": "desktop-pc", "level": 2}
          ]
        }
      ]
    },
    {
      "id": "cat_fashion",
      "name_vi": "Thoi trang",
      "name_en": "Fashion",
      "slug": "fashion",
      "level": 0,
      "children": [
        {
          "id": "cat_fashion_men",
          "name_vi": "Thoi trang Nam",
          "name_en": "Men Fashion",
          "slug": "men-fashion",
          "level": 1,
          "children": [
            {"id": "cat_shirt_men", "name_vi": "Ao nam", "name_en": "Men Shirts", "slug": "men-shirts", "level": 2},
            {"id": "cat_pants_men", "name_vi": "Quan nam", "name_en": "Men Pants", "slug": "men-pants", "level": 2},
            {"id": "cat_shoes_men", "name_vi": "Giay nam", "name_en": "Men Shoes", "slug": "men-shoes", "level": 2}
          ]
        },
        {
          "id": "cat_fashion_women",
          "name_vi": "Thoi trang Nu",
          "name_en": "Women Fashion",
          "slug": "women-fashion",
          "level": 1,
          "children": [
            {"id": "cat_dress", "name_vi": "Dam/Vay", "name_en": "Dresses", "slug": "dresses", "level": 2},
            {"id": "cat_tops_women", "name_vi": "Ao nu", "name_en": "Women Tops", "slug": "women-tops", "level": 2},
            {"id": "cat_shoes_women", "name_vi": "Giay nu", "name_en": "Women Shoes", "slug": "women-shoes", "level": 2}
          ]
        }
      ]
    },
    {
      "id": "cat_beauty",
      "name_vi": "Lam dep - My pham",
      "name_en": "Beauty & Cosmetics",
      "slug": "beauty-cosmetics",
      "level": 0,
      "children": [
        {"id": "cat_skincare", "name_vi": "Cham soc da", "name_en": "Skincare", "slug": "skincare", "level": 1},
        {"id": "cat_makeup", "name_vi": "Trang diem", "name_en": "Makeup", "slug": "makeup", "level": 1},
        {"id": "cat_haircare", "name_vi": "Cham soc toc", "name_en": "Haircare", "slug": "haircare", "level": 1}
      ]
    },
    {
      "id": "cat_home",
      "name_vi": "Nha cua - Doi song",
      "name_en": "Home & Living",
      "slug": "home-living",
      "level": 0,
      "children": [
        {"id": "cat_kitchen", "name_vi": "Do dung nha bep", "name_en": "Kitchen", "slug": "kitchen", "level": 1},
        {"id": "cat_bedroom", "name_vi": "Phong ngu", "name_en": "Bedroom", "slug": "bedroom", "level": 1},
        {"id": "cat_bathroom", "name_vi": "Phong tam", "name_en": "Bathroom", "slug": "bathroom", "level": 1}
      ]
    }
  ]
}
```

### Ngay 3: Chuan hoa & Import

#### [P1] Task 3.1: Chuan hoa du lieu cao duoc
```bash
python scripts/data/normalize_scraped_data.py \
  --tiki data/raw/tiki_products.json \
  --shopee data/raw/shopee_products.json \
  --category-map scripts/data/category_mapping.json \
  --output data/processed/
```

**Output mong doi**:
- `data/processed/tiki_normalized.json`
- `data/processed/shopee_normalized.json`
- `data/processed/synthetic_small.json` (giu nguyen tu seed_data.py)
- `data/processed/synthetic_large.json` (generate them 500 products)

#### [P1] Task 3.2: Import vao Django
```bash
python scripts/data/import_to_django.py \
  --source data/processed/tiki_normalized.json \
  --dataset-tag "real_tiki"
```

---

## PHASE 2: DATABASE & INDEX REBUILD (1 ngay)

### [P0] Task 2.1: Dong bo Neo4j Knowledge Graph
```bash
cd services/ai-recommendation
python manage.py push_to_neo4j --rebuild
python manage.py enhance_graph
python manage.py validate_pipeline
```

### [P0] Task 2.2: Rebuild FAISS Index
```bash
cd services/ai-chatbot
python manage.py build_ai_index --index-dir /app/ai_index --page-size 1000
```

### [P1] Task 2.3: Kiem tra Hybrid Search
```bash
# Chay test suite
pytest tests/test_ai_system.py -v -m hybrid

# Test thu cong
curl -X POST http://localhost:8012/api/chatbot/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "tim giay nike gia duoi 2 trieu"}'
```

---

## PHASE 3: MODEL EVALUATION PIPELINE (2 ngay)

### Ngay 1: Thiet lap Evaluation Framework

#### [P0] Task 3.1: Tao Evaluation Script
- **File**: `scripts/evaluation/evaluate_models.py`
- **Chuc nang**:
  - Load 1 model tai 1 thoi diem (tuan tu)
  - Chay test queries qua chatbot API
  - Ghi ket qua vao CSV

#### [P0] Task 3.2: Tao Test Query Set
- **File**: `scripts/evaluation/test_queries.json`
- **So luong**: 50-100 queries/dataset
- **Phan loai**:
  - Product search (co gia, co category)
  - Semantic search (mo ta chung chung)
  - Edge cases (san pham khong ton tai)

### Ngay 2: Chay Evaluation & Tong hop

#### [P0] Task 3.3: Chay Evaluation Loop
```bash
# Chay tuan tu 3 models x 4 datasets = 12 runs
python scripts/evaluation/evaluate_models.py \
  --models llama3:8b,qwen2.5:7b,gemma2:9b \
  --datasets synthetic_small,synthetic_large,real_tiki,real_shopee \
  --output results/evaluation_results.csv \
  --judge-model gpt-4o-mini \
  --openai-key $OPENAI_API_KEY
```

#### [P1] Task 3.4: Tao Bieu do So sanh
```bash
python scripts/evaluation/generate_charts.py \
  --input results/evaluation_results.csv \
  --output results/charts/
```

**Output**:
- `results/charts/latency_comparison.png`
- `results/charts/faithfulness_comparison.png`
- `results/charts/relevance_comparison.png`
- `results/charts/overall_radar.png`

---

## PHASE 4: REPORT & LOCK BEST MODEL (1 ngay)

### [P0] Task 4.1: Xac dinh Model Tot nhat
- Tong hop diem tu 3 metrics (weighted average)
- Chon model co diem cao nhat

### [P0] Task 4.2: Lock Model vao Production
```python
# services/ai-chatbot/chatbot_service/settings.py
OLLAMA_MODEL = "qwen2.5:7b"  # Hoac model tot nhat
```

### [P1] Task 4.3: Hoan thien Bao cao
- Export bang ket qua
- Chen bieu do
- Viet phan tich & ket luan

---

## TIEU CHI DANH GIA (METRICS)

### 1. Latency (Toc do phan hoi)
| Metric | Mo ta | Nguong chap nhan |
|--------|-------|------------------|
| Cold-start | Thoi gian request dau tien | < 30s |
| Warm (cached) | Thoi gian request da cache | < 2s |
| P95 Latency | 95th percentile | < 10s |

### 2. Faithfulness (Do trung thuc)
| Metric | Mo ta | Diem |
|--------|-------|------|
| Has Citation | Phan hoi co [ID: xxx] | +1 |
| No Hallucination | Khong bịa san pham | +1 |
| Price Match | Gia trong text khop voi DB | +1 |

### 3. Relevance (Do lien quan)
| Metric | Mo ta | Diem |
|--------|-------|------|
| Category Match | San pham dung danh muc | 0-1 |
| Price Filter OK | San pham trong budget | 0-1 |
| LLM-Judge Score | GPT-4o-mini cham diem 1-5 | 1-5 |

### 4. Cong thuc Tong hop
```
Final Score = 0.3 * Latency_norm + 0.3 * Faithfulness + 0.4 * Relevance
```

---

## CAU TRUC THU MUC DU KIEN

```
BTL-TKKTHT/
├── scripts/
│   ├── scrapers/
│   │   ├── tiki_scraper.py
│   │   ├── shopee_scraper.py
│   │   └── base_scraper.py
│   ├── data/
│   │   ├── category_mapping.json
│   │   ├── normalize_scraped_data.py
│   │   └── import_to_django.py
│   └── evaluation/
│       ├── test_queries.json
│       ├── evaluate_models.py
│       ├── llm_judge.py
│       └── generate_charts.py
├── data/
│   ├── raw/
│   │   ├── tiki_products.json
│   │   └── shopee_products.json
│   └── processed/
│       ├── tiki_normalized.json
│       ├── shopee_normalized.json
│       ├── synthetic_small.json
│       └── synthetic_large.json
└── results/
    ├── evaluation_results.csv
    └── charts/
        ├── latency_comparison.png
        ├── faithfulness_comparison.png
        └── relevance_comparison.png
```

---

## LUU Y QUAN TRONG

### Hardware Constraints
- **RAM < 16GB**: KHONG chay dong thoi nhieu model
- **Script phai co**: Clear VRAM/cache giua cac model
- **Docker**: Gioi han memory cho moi container

### Anti-Detection khi Scraping
- Dung Playwright stealth mode
- Random delay giua requests (2-5s)
- Rotate User-Agent
- Su dung proxy neu can

### Backup truoc khi Reset
```bash
# Backup du lieu hien tai (neu can)
pg_dump -U postgres product_db > backup/product_db_backup.sql
```

---

## CHECKLIST PHASE 1 (IN RA DE THEO DOI)

- [ ] **[P0]** Backup du lieu cu (neu can giu)
- [ ] **[P0]** Flush Django databases
- [ ] **[P0]** Clear Neo4j graph
- [ ] **[P0]** Clear Redis cache
- [ ] **[P0]** Xoa FAISS index cu
- [ ] **[P0]** Pull llama3:8b
- [ ] **[P0]** Pull qwen2.5:7b
- [ ] **[P0]** Pull gemma2:9b
- [ ] **[P0]** Tao tiki_scraper.py
- [ ] **[P0]** Tao shopee_scraper.py
- [ ] **[P0]** Chay scraper Tiki (500-1000 SP)
- [ ] **[P0]** Chay scraper Shopee (500-1000 SP)
- [ ] **[P1]** Tao category_mapping.json
- [ ] **[P1]** Tao normalize_scraped_data.py
- [ ] **[P1]** Chuan hoa du lieu
- [ ] **[P1]** Import vao Django
- [ ] **[P1]** Kiem tra du lieu trong DB
