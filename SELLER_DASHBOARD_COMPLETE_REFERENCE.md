# Seller Dashboard - Complete Reference ✅

## Dashboard Structure

```
SELLER DASHBOARD
├── DASHBOARD (Overview)
│   └── Summary metrics, recent orders, store stats
│
├── PRODUCTS
│   ├── Products - Manage active products
│   ├── Archived Products - View deleted items
│   ├── Add Product - Create new listings
│   └── Inventory - Track stock levels
│
├── ORDERS & CUSTOMERS
│   ├── Order Management - Track orders
│   ├── Customer Reviews - Approve/reject reviews
│   └── Promotions - Create discounts
│
├── ANALYTICS
│   ├── Sales Analytics - Revenue, orders, top products
│   └── Performance - Ratings, repeat customers, reviews
│
└── SETTINGS
    ├── Brand Settings - Store info, contact details
    └── Account - Profile, password, security
```

---

## Fully Implemented Pages

### ✅ INVENTORY MANAGEMENT
**Location:** Products → Inventory
**Features:**
- Search products by name or SKU
- View current stock levels
- Stock reserved vs available
- Product variants (size, color)
- All variants listed with individual stock counts

**Backend Route:** `GET /seller/inventory`
**Data Source:** inventory + product_variants tables

---

### ✅ CUSTOMER REVIEWS
**Location:** Orders & Customers → Customer Reviews
**Features:**
- View all reviews for your products
- Filter by Approval Status (All / Pending)
- See buyer name and rating
- Approve or reject reviews with one click
- Real-time updates

**Backend Routes:**
- `GET /seller/reviews` - Fetch reviews
- `POST /seller/review/<id>/approve` - Approve review
- `POST /seller/review/<id>/reject` - Reject review

**Data Source:** reviews table

---

### ✅ PROMOTIONS MANAGEMENT
**Location:** Orders & Customers → Promotions
**Features:**
- Create new promotions/coupons
- Set discount type (percentage or fixed amount)
- Set date range (start and end dates)
- Add description
- View all active promotions
- Delete promotions
- Auto-generated unique coupon codes

**Backend Routes:**
- `GET /seller/promotions` - Fetch all promotions
- `POST /seller/promotion/create` - Create promotion
- `POST /seller/promotion/<id>/delete` - Delete promotion

**Data Source:** coupons table

---

### ✅ SALES ANALYTICS
**Location:** Analytics → Sales Analytics
**Features:**
- **Total Revenue** - Sum of all orders (last 30 days)
- **Total Orders** - Count of completed orders
- **Average Order Value** - Average per transaction
- **Sales by Product** - Top 10 products with quantity and revenue

**Metrics:**
- 30-day rolling window
- Excludes cancelled/failed orders
- PHP currency formatting (₱)
- Two decimal places

**Backend Route:** `GET /seller/sales-analytics`
**Data Source:** orders, order_items, products tables

---

### ✅ PERFORMANCE METRICS
**Location:** Analytics → Performance
**Features:**
- **Average Rating** - Star rating across all products
- **Repeat Customers** - Customers with 2+ orders
- **Total Reviews** - Total review count
- **Top Rated Products** - Top 10 with ratings and review counts

**Metrics:**
- All-time data (not limited to 30 days)
- Star visualization
- Review count per product

**Backend Route:** `GET /seller/performance`
**Data Source:** reviews, orders, order_items, products tables

---

### ✅ BRAND SETTINGS
**Location:** Settings → Brand Settings
**Features:**
- **Store Name** - Your business name
- **Store Description** - Marketing description
- **Contact Email** - Customer service email
- **Contact Phone** - Customer service phone
- **Store Address** - Physical location

**Functionality:**
- Load current settings with prefilled form
- Update any field
- Save and reload
- Persistent storage in database

**Backend Routes:**
- `GET /seller/brand-settings` - Fetch settings
- `POST /seller/brand-settings` - Update settings

**Data Source:** sellers table columns
- store_name
- description
- contact_email
- contact_phone
- address

---

### ✅ ACCOUNT SETTINGS
**Location:** Settings → Account
**Features:**
- **Account Info Display** - Username and email (read-only)
- **Full Name** - Your name
- **Phone Number** - Contact number
- **Password Change:**
  - Current password verification
  - New password with confirmation
  - Secure hashing (werkzeug)

**Functionality:**
- Load profile information
- Update profile fields
- Change password securely
- Clear fields after save

**Backend Routes:**
- `GET /seller/account-settings` - Fetch profile
- `POST /seller/account-settings` - Update profile/password

**Data Source:**
- Profile: sellers table (full_name, phone_number)
- Auth: users table (username, email, password)

---

## API Summary

### All Seller Routes

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/seller/inventory` | Get inventory with stock levels |
| GET | `/seller/reviews` | Get all reviews for seller's products |
| POST | `/seller/review/<id>/approve` | Approve customer review |
| POST | `/seller/review/<id>/reject` | Reject customer review |
| GET | `/seller/promotions` | Get active promotions |
| POST | `/seller/promotion/create` | Create new promotion |
| POST | `/seller/promotion/<id>/delete` | Delete promotion |
| GET | `/seller/sales-analytics` | Get 30-day sales metrics |
| GET | `/seller/performance` | Get performance KPIs |
| GET | `/seller/brand-settings` | Get brand info |
| POST | `/seller/brand-settings` | Update brand info |
| GET | `/seller/account-settings` | Get account info |
| POST | `/seller/account-settings` | Update profile/password |

---

## Frontend Architecture

### Page Templates (pageTemplates object)
13 templates for different dashboard pages:
- overview, add-product, products, archived-products
- inventory, orders, reviews, promotions
- sales, performance, store-settings, account

### Load Functions
Each page has a corresponding load function:
- `loadInventory()` - Fetch and display inventory
- `loadReviews()` - Fetch and display reviews
- `loadPromotions()` - Fetch and display promotions
- `loadSalesAnalytics()` - Fetch and display sales data
- `loadPerformance()` - Fetch and display performance data
- `loadBrandSettings()` - Fetch and display brand settings
- `loadAccountSettings()` - Fetch and display account settings

### Display Functions
Render fetched data in the DOM:
- `displayInventory()` - Render inventory table
- `displayReviews()` - Render review cards
- `displayPromotions()` - Render promotion cards
- `displaySalesByProduct()` - Render sales table
- `displayTopRatedProducts()` - Render product cards
- Form pre-population for settings

---

## Database Schema (Relevant Tables)

```sql
sellers
├── id
├── user_id (FK → users.id)
├── store_name ✅
├── description ✅
├── contact_email ✅
├── contact_phone ✅
├── address ✅
└── full_name ✅, phone_number ✅

users
├── id
├── username
├── email
└── password (hashed) ✅

products
├── id
├── seller_id (FK → sellers.id)
├── name
├── price
└── is_active

orders
├── id
├── user_id (FK → users.id)
├── total_amount
├── order_status
└── created_at

order_items
├── id
├── order_id (FK → orders.id)
├── product_id (FK → products.id)
├── quantity
└── unit_price

reviews
├── id
├── product_id (FK → products.id)
├── user_id (FK → users.id)
├── rating
└── comment

inventory
├── id
├── product_id (FK → products.id)
├── variant_id (FK → product_variants.id)
├── stock_quantity
└── reserved_quantity

product_variants
├── id
├── product_id (FK → products.id)
├── size
├── color
└── stock_quantity

coupons
├── id
├── product_id (FK → products.id)
├── code
├── discount_type
├── discount_value
├── start_date
├── end_date
└── is_active
```

---

## Implementation Timeline

| Phase | Date | Feature | Status |
|-------|------|---------|--------|
| 1 | Early | Sidebar UI | ✅ Complete |
| 2 | Early | Inventory Page | ✅ Complete |
| 3 | Mid | Reviews & Approvals | ✅ Complete |
| 4 | Mid | Promotions Management | ✅ Complete |
| 5 | Recent | Sales Analytics | ✅ Complete |
| 6 | Recent | Performance Metrics | ✅ Complete |
| 7 | Latest | Brand Settings | ✅ Complete |
| 8 | Latest | Account Settings | ✅ Complete |

---

## Key Statistics

**Lines of Code Added:**
- Frontend: ~500 lines (templates + functions)
- Backend: ~300 lines (routes + queries)
- Total: ~800 lines of new functionality

**Database Tables Modified:** 0 (used existing)
**API Routes Added:** 13 routes
**Pages Implemented:** 8 fully functional pages

**Security Features:**
- ✅ Role-based access (sellers only)
- ✅ Session validation
- ✅ Password hashing
- ✅ SQL injection prevention
- ✅ Error handling

---

## Next Steps / Future Enhancements

- [ ] Date range filtering for analytics (custom periods)
- [ ] Charts/graphs visualization (Chart.js)
- [ ] Bulk actions (delete multiple products, reviews)
- [ ] Export data to CSV/PDF
- [ ] Email notifications
- [ ] Seller rating/response time tracking
- [ ] Customer messaging system
- [ ] Product performance comparison
- [ ] Revenue forecasting
- [ ] Seasonal sales trends

