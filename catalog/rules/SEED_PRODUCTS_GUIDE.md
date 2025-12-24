# 🌱 SEED PRODUCTS - Testing Data Guide

## 📋 Overview

Script để insert 30 products testing vào database cho marketplace testing.

**Status**: ✅ Ready to use
**Products**: 30 realistic n8n workflows
**Script**: `backend/scripts/seed-products.ts`

---

## 🚀 How to Use

### Step 1: Make sure database is running

```bash
# In docker-compose.yml folder
docker-compose up postgres redis
```

Verify connection:
```bash
PGPASSWORD=gsnake1102_pw psql -h localhost -p 5433 -U gsnake1102_user -d gsnake1102
```

### Step 2: Run seed script

```bash
cd backend
npm run seed:products
```

**Expected output**:
```
🌱 Starting product seeding...
📊 Inserting 30 products

✅ [1/30] Email Marketing Automation Pro
✅ [2/30] Instagram Post Scheduler & Auto-Poster
✅ [3/30] LinkedIn Content Distribution
...
✅ [30/30] Log Aggregation & Analysis

✅ Seeding complete!
📊 30 products inserted successfully

📝 Notes:
   - Status: All set to "published"
   - Seller: All owned by default seller
   - Rating: Realistic ratings between 4.3-4.9
   - Downloads: Realistic download counts
   - Created dates: Spread across last 90 days
```

---

## 📊 Products Included

### Categories Breakdown

| Category | Count | Tags |
|----------|-------|------|
| Marketing & Social | 4 | Email, Instagram, LinkedIn, Ads |
| Sales & CRM | 3 | CRM, Lead scoring, Integrations |
| AI & Automation | 3 | GPT-4, Chatbot, Sentiment analysis |
| Data & Analytics | 2 | Analytics, ETL, Data pipeline |
| Integrations | 3 | Slack, Airtable, Zapier |
| Security & Monitoring | 3 | Monitoring, Alerts, SSL, API limits |
| Operations & HR | 6 | Onboarding, Expenses, Recruiting, Calendar |
| Infrastructure | 3 | Backup, Logs, Monitoring |

**Total**: 30 products

---

## 📋 Product Details

### Marketing (4 products)
1. **Email Marketing Automation Pro** - €49.9K, 4.8★, 2.5K downloads
2. **Instagram Post Scheduler** - Free, 4.6★, 1.5K downloads
3. **LinkedIn Content Distribution** - Free, 4.5★, 1.2K downloads
4. **Facebook & Instagram Ad Manager** - €79.9K, 4.7★, 1.8K downloads

### Sales & CRM (3 products)
5. **CRM to Notion Sync** - €39.9K, 4.7★, 1.8K downloads
6. **Lead Scoring Pipeline** - Free, 4.7★, 900 downloads
7. **Salesforce to Google Sheets** - Free, 4.6★, 1.4K downloads

### AI & Automation (3 products)
8. **AI Content Generator** - €59.9K, 4.9★, 3.2K downloads
9. **AI Customer Support Bot** - €99.9K, 4.8★, 2.1K downloads
10. **Sentiment Analysis & Alert** - €44.9K, 4.5★, 650 downloads

### Data & Analytics (2 products)
11. **Google Analytics to Slack** - Free, 4.4★, 980 downloads
12. **Database Data Pipeline ETL** - €149.9K, 4.8★, 1.45K downloads

### Integrations (3 products)
13. **Slack Notification Hub** - Free, 4.5★, 1.2K downloads
14. **Webhook to Airtable Forms** - Free, 4.6★, 1.1K downloads
15. **Zapier to n8n Migration** - Free, 4.3★, 450 downloads

### Security & Monitoring (3 products)
16. **Security Monitoring Dashboard** - €129.9K, 4.7★, 890 downloads
17. **SSL Certificate Monitor** - Free, 4.5★, 650 downloads
18. **API Rate Limit Monitor** - Free, 4.4★, 520 downloads

### Operations (6 products)
19. **Newsletter Subscriber Management** - €34.9K, 4.6★, 1.34K downloads
20. **E-commerce Order Processing** - €69.9K, 4.8★, 1.92K downloads
21. **Invoice Generation & Payment** - €29.9K, 4.5★, 780 downloads
22. **Job Application Screening** - €89.9K, 4.7★, 1.1K downloads
23. **Employee Onboarding** - Free, 4.6★, 890 downloads
24. **Expense Report Automation** - Free, 4.4★, 620 downloads

### Infrastructure (3 products)
25. **Backup Automation & Monitoring** - €54.9K, 4.7★, 980 downloads
26. **Log Aggregation & Analysis** - €64.9K, 4.6★, 1.12K downloads
27. **Calendar & Meeting Scheduler** - Free, 4.5★, 850 downloads
28. **Knowledge Base Auto-Generator** - Free, 4.4★, 540 downloads

---

## 🎯 Features of Each Product

All products include:
- ✅ Title & Description
- ✅ Long description (for detail page)
- ✅ Type (workflow, tool, integration)
- ✅ Tags (for filtering/search)
- ✅ Price info (free or paid with price)
- ✅ Features list
- ✅ Requirements
- ✅ Realistic ratings (4.3 - 4.9 stars)
- ✅ Review counts (67 - 412 reviews)
- ✅ Download counts (450 - 3.2K)
- ✅ Created dates spread across 90 days

---

## 🔧 Customization

### Change default seller

Edit line 20 in `seed-products.ts`:
```typescript
const DEFAULT_SELLER_ID = 'your-seller-id-here';
```

Or pass as environment variable:
```bash
SEED_SELLER_ID=your-id npm run seed:products
```

### Add more products

Add to `products` array in `seed-products.ts`:
```typescript
{
  title: 'Your Product Name',
  description: 'Short description',
  long_description: 'Long description...',
  type: 'workflow',  // or 'tool', 'integration'
  tags: ['tag1', 'tag2'],
  is_free: true,  // or false
  price: 29900,  // price in VND (optional if free)
  features: ['Feature 1', 'Feature 2'],
  requirements: ['Requirement 1'],
  rating: 4.6,
  reviews_count: 120,
  downloads: 800,
}
```

Then re-run:
```bash
npm run seed:products
```

---

## 📡 Verify Products

### Check database directly

```bash
psql -h localhost -p 5433 -U gsnake1102_user -d gsnake1102

# Count products
SELECT COUNT(*) FROM products;

# List products
SELECT title, type, is_free, price, rating, downloads FROM products LIMIT 10;

# See all products with seller
SELECT id, title, type, rating, downloads, created_at FROM products ORDER BY created_at DESC;
```

### Check via API

```bash
# Get all products
curl http://localhost:3000/api/products

# Get products by type
curl "http://localhost:3000/api/products?type=workflow"

# Get trending products
curl "http://localhost:3000/api/products?sort_by=downloads&sort_order=desc&limit=10"

# Search products
curl "http://localhost:3000/api/products?search=email&limit=5"
```

### Check in frontend

1. Start frontend: `npm run dev` (in frontend folder)
2. Go to `http://localhost:3000`
3. See products in:
   - **CategoryShowcase** - Browse by category
   - **TrendingSection** - Most downloaded
   - **Featured Products** - Top-rated

---

## 🧹 Reset/Clean Data

### Remove all products (but keep table structure)

```bash
psql -h localhost -p 5433 -U gsnake1102_user -d gsnake1102

DELETE FROM products;
RESTART IDENTITY;
```

### Or use database directly

```typescript
await db.query('DELETE FROM products');
await db.query("SELECT setval('products_id_seq', 1, false)");
```

---

## ⚙️ Technical Details

### Script Execution
- Reads from `backend/scripts/seed-products.ts`
- Uses `tsx` to run TypeScript directly
- Connects to PostgreSQL via `db` from infrastructure
- Inserts using parameterized queries (safe from SQL injection)

### Data Pattern
- **Status**: All "published" (visible on frontend)
- **Seller**: All owned by one default seller
- **Created dates**: Random dates within last 90 days (realistic)
- **Ratings**: Between 4.3-4.9 stars
- **Downloads**: Realistic numbers (450-3.2K)
- **Mix**: 14 free, 16 paid (realistic ratio)

### Performance
- ~30 inserts should take < 5 seconds
- No duplicates (uses ON CONFLICT for safety)
- Safe to run multiple times

---

## ✅ Post-Seed Checklist

After running seed script:

- [ ] Check database: `SELECT COUNT(*) FROM products;` should return 30
- [ ] Frontend loads without errors
- [ ] Homepage shows products in sections
- [ ] Search works (try "email")
- [ ] Filtering by type works
- [ ] Sorting by downloads/rating works
- [ ] Chatbot can recommend products
- [ ] Product detail page loads

---

## 🚀 Next Steps

1. **Test with real data**:
   ```bash
   npm run seed:products
   npm run dev  # start backend
   # In another terminal:
   cd frontend && npm run dev
   ```

2. **Browse home page**: Check all sections display products

3. **Test filtering**: Try category, tags, price

4. **Test chatbot**: Ask for product recommendations

5. **Test search**: Search for "email", "CRM", "AI"

---

## 📝 Notes

- Products are created with all fields populated
- Realistic engagement metrics (reviews, ratings, downloads)
- Mix of free and paid products
- Various product types (workflow, tool, integration)
- Real-world use cases (marketing, sales, operations, etc.)
- Can run script multiple times safely (won't create duplicates)

---

## 🆘 Troubleshooting

### Error: "Cannot find module 'tsx'"
```bash
# Install globally
npm install -g tsx
```

### Error: "Connection refused"
```bash
# Make sure database is running
docker-compose up postgres
# Or check connection string in .env
```

### Error: "Seller not found"
```bash
# Make sure a user exists with that ID
# Or change DEFAULT_SELLER_ID in script
```

### Products not showing on frontend
1. Restart frontend: `npm run dev`
2. Hard refresh browser: Ctrl+Shift+R
3. Check browser console for errors
4. Verify API endpoint: `curl http://localhost:3000/api/products`

---

**Status**: ✅ Ready to seed
**Command**: `npm run seed:products`
**Time to complete**: ~5 seconds
**Products inserted**: 30

