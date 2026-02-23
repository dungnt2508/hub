#!/usr/bin/env node

/**
 * Seed Script - Insert 30 Test Products
 * Usage: npm run seed:products
 * 
 * Creates 30 realistic n8n workflow products for marketplace testing
 * with various types, prices, and features
 */

import { v4 as uuidv4 } from 'uuid';

// Default seller ID - will be created if doesn't exist
let DEFAULT_SELLER_ID = process.env.SEED_SELLER_ID || 'f47ac10b-58cc-4372-a567-0e02b2c3d479';
let cachedPool: any;

async function getPool() {
  if (cachedPool) return cachedPool;
  try {
    const mod = await import('../src/config/database');
    cachedPool = mod.default;
    return cachedPool;
  } catch {
    const mod = await import('../dist/config/database');
    cachedPool = mod.default;
    return cachedPool;
  }
}

/**
 * Get or create default seller user
 */
async function getOrCreateSeller(): Promise<string> {
  try {
    const pool = await getPool();
    // First, try to find any existing user to use as seller
    const existingUser = await pool.query(
      'SELECT id FROM users LIMIT 1'
    );

    if (existingUser.rows.length > 0) {
      console.log(`📤 Using existing user as seller: ${existingUser.rows[0].id}`);
      return existingUser.rows[0].id;
    }

    // If no user exists, create a default seller
    console.log('📝 Creating default seller user...');
    const sellerId = uuidv4();
    
    await pool.query(
      `INSERT INTO users (id, email, password_hash, created_at, updated_at)
       VALUES ($1, $2, $3, NOW(), NOW())
       ON CONFLICT (email) DO UPDATE SET id = EXCLUDED.id
       RETURNING id`,
      [
        sellerId,
        'seller@gsnake.local',
        'hashed_password_placeholder' // Will be replaced by proper hash in production
      ]
    );

    console.log(`✅ Created default seller: ${sellerId}\n`);
    return sellerId;
  } catch (error) {
    console.error('❌ Error getting/creating seller:', error);
    throw error;
  }
}

interface SeedProduct {
  title: string;
  description: string;
  long_description: string;
  type: 'workflow' | 'tool' | 'integration';
  tags: string[];
  is_free: boolean;
  price?: number;
  features: string[];
  requirements: string[];
  rating: number;
  reviews_count: number;
  downloads: number;
  thumbnail_url?: string;  // Add this
}

const products: SeedProduct[] = [
  // =========================
  // AI AGENT & RAG (TREND)
  // =========================
  {
    title: 'AI Agent Orchestration Platform',
    description: 'Xây dựng và điều phối AI Agents cho business workflows',
    long_description: 'Platform cho phép thiết kế, orchestrate và giám sát nhiều AI agents hoạt động theo vai trò. Hỗ trợ tool-calling, memory, guardrails và human-in-the-loop.',
    type: 'tool',
    tags: ['AI Agent', 'LLM', 'Automation', 'Orchestration'],
    is_free: false,
    price: 129900,
    features: ['Multi-agent orchestration', 'Tool calling', 'Memory management', 'Audit logs'],
    requirements: ['n8n 1.0+', 'OpenAI / Claude API'],
    rating: 4.9,
    reviews_count: 210,
    downloads: 1700,
  },
  {
    title: 'RAG Knowledge Assistant',
    description: 'Trợ lý AI dựa trên tài liệu nội bộ với RAG',
    long_description: 'Retrieval-Augmented Generation assistant. Index tài liệu, semantic search bằng vector DB, trả lời chính xác theo nguồn dữ liệu nội bộ.',
    type: 'workflow',
    tags: ['AI', 'RAG', 'Knowledge Base', 'Enterprise'],
    is_free: false,
    price: 109900,
    features: ['Vector search', 'Document ingestion', 'Citation', 'Access control'],
    requirements: ['n8n 1.0+', 'Vector DB', 'LLM API'],
    rating: 4.8,
    reviews_count: 188,
    downloads: 1400,
  },

  // =========================
  // DATA / VECTOR / OBSERVABILITY
  // =========================
  {
    title: 'Vector Database Sync Pipeline',
    description: 'Đồng bộ dữ liệu vào vector database cho AI search',
    long_description: 'Pipeline để ingest, chunk, embed và sync dữ liệu vào Pinecone, Weaviate, pgvector. Tối ưu cho semantic search và AI workloads.',
    type: 'workflow',
    tags: ['Vector DB', 'AI', 'Data Pipeline', 'Embedding'],
    is_free: true,
    features: ['Chunking', 'Embedding', 'Incremental sync', 'Multi-DB support'],
    requirements: ['n8n 1.0+', 'Vector DB', 'Embedding API'],
    rating: 4.7,
    reviews_count: 96,
    downloads: 880,
  },
  {
    title: 'Application Observability Hub',
    description: 'Quan sát hệ thống: logs, metrics, traces tập trung',
    long_description: 'Unified observability workflow. Collect metrics, traces, logs từ multiple services, correlate và alert theo SLO.',
    type: 'workflow',
    tags: ['Observability', 'Monitoring', 'DevOps', 'SRE'],
    is_free: false,
    price: 119900,
    features: ['Logs + Metrics + Traces', 'SLO tracking', 'Alerting', 'Dashboards'],
    requirements: ['n8n 1.0+', 'Monitoring stack'],
    rating: 4.8,
    reviews_count: 142,
    downloads: 1050,
  },

  // =========================
  // SECURITY / COMPLIANCE (ENTERPRISE TREND)
  // =========================
  {
    title: 'Compliance Evidence Automation',
    description: 'Tự động thu thập bằng chứng tuân thủ ISO, SOC2',
    long_description: 'Automate compliance evidence collection from cloud, CI/CD, IAM, logs. Phù hợp audit ISO 27001, SOC2, PCI-DSS.',
    type: 'workflow',
    tags: ['Compliance', 'Security', 'Audit', 'Enterprise'],
    is_free: false,
    price: 139900,
    features: ['Evidence collection', 'Policy mapping', 'Audit trail', 'Export reports'],
    requirements: ['n8n 1.0+', 'Cloud APIs'],
    rating: 4.7,
    reviews_count: 118,
    downloads: 760,
  },

  // =========================
  // FINOPS / COST
  // =========================
  {
    title: 'Cloud Cost Optimization & FinOps',
    description: 'Theo dõi và tối ưu chi phí cloud tự động',
    long_description: 'Analyze cloud spend, detect anomalies, recommend savings. Support AWS, GCP, Azure với FinOps best practices.',
    type: 'tool',
    tags: ['FinOps', 'Cloud', 'Cost Management', 'DevOps'],
    is_free: false,
    price: 99900,
    features: ['Cost analysis', 'Anomaly detection', 'Saving recommendations', 'Trend reports'],
    requirements: ['n8n 1.0+', 'Cloud billing APIs'],
    rating: 4.8,
    reviews_count: 164,
    downloads: 980,
  },
];

async function seedProducts() {
  try {
    console.log('🌱 Starting product seeding...\n');

    // Get or create seller
    DEFAULT_SELLER_ID = await getOrCreateSeller();

    const pool = await getPool();
    const existingCountResult = await pool.query('SELECT COUNT(*) AS total FROM products');
    const existingTotal = parseInt(existingCountResult.rows[0]?.total || '0', 10);
    if (existingTotal > 0) {
      console.log(`ℹ️  Detected ${existingTotal} existing products. Skipping seed.`);
      if (cachedPool) {
        await cachedPool.end();
      }
      return;
    }

    console.log(`📊 Inserting ${products.length} products\n`);

    let inserted = 0;

    for (const product of products) {
      try {
        const id = uuidv4();
        
        // Set random dates within last 3 months for realistic data
        const daysAgo = Math.floor(Math.random() * 90);
        const created_at = new Date();
        created_at.setDate(created_at.getDate() - daysAgo);

        const stock_status = Math.random() < 0.85 ? 'in_stock' : 'out_of_stock';
        const stock_quantity = stock_status === 'in_stock' ? Math.floor(Math.random() * 50) + 1 : 0;

        const query = `
          INSERT INTO products (
            id,
            seller_id,
            title,
            description,
            long_description,
            type,
            tags,
            is_free,
            price,
            stock_status,
            stock_quantity,
            status,
            review_status,
            rating,
            reviews_count,
            downloads,
            features,
            requirements,
            thumbnail_url,
            created_at,
            updated_at
          ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21
          )
          ON CONFLICT (id) DO NOTHING
        `;

        const values = [
          id,
          DEFAULT_SELLER_ID,
          product.title,
          product.description,
          product.long_description,
          product.type,
          JSON.stringify(product.tags),
          product.is_free,
          product.price || null,
          stock_status,
          stock_quantity,
          'published',
          'approved',
          product.rating,
          product.reviews_count,
          product.downloads,
          JSON.stringify(product.features),
          JSON.stringify(product.requirements),
          product.thumbnail_url || `https://via.placeholder.com/400x300?text=${encodeURIComponent(product.title)}`,  // thumbnail
          created_at.toISOString(),
          new Date().toISOString(),
        ];

        await pool.query(query, values);
        
        console.log(`✅ [${++inserted}/${products.length}] ${product.title}`);
      } catch (error) {
        console.error(`❌ Error inserting product: ${product.title}`, error);
      }
    }

    console.log(`\n✅ Seeding complete!`);
    console.log(`📊 ${inserted} products inserted successfully`);
    console.log(`\n📝 Notes:`);
    console.log(`   - Status: All set to "published"`);
    console.log(`   - Seller ID: ${DEFAULT_SELLER_ID}`);
    console.log(`   - Rating: Realistic ratings between 4.3-4.9`);
    console.log(`   - Downloads: Realistic download counts`);
    console.log(`   - Created dates: Spread across last 90 days`);

    if (cachedPool) {
      await cachedPool.end();
    }
    process.exit(0);
  } catch (error) {
    console.error('💥 Fatal error during seeding:', error);
    if (cachedPool) {
      await cachedPool.end();
    }
    process.exit(1);
  }
}

// Run seeding
seedProducts();

