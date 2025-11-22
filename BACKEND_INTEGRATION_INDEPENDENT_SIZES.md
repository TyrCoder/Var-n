# Backend Integration: Independent Sizes Per Color

## Data Format Received

When the form is submitted with the new independent sizes per color feature, the backend receives:

```python
# Flask backend receives stock_data as JSON string:
stock_data = request.form.get('stock_data')  # JSON string
stock_array = json.loads(stock_data)

# Example: Green has S,M | Blue has S,M,L,XL | Red has L,XL
[
  {"size": "S", "color": "Green", "stock_qty": 100},
  {"size": "M", "color": "Green", "stock_qty": 50},
  {"size": "S", "color": "Blue", "stock_qty": 200},
  {"size": "M", "color": "Blue", "stock_qty": 150},
  {"size": "L", "color": "Blue", "stock_qty": 75},
  {"size": "XL", "color": "Blue", "stock_qty": 60},
  {"size": "L", "color": "Red", "stock_qty": 80},
  {"size": "XL", "color": "Red", "stock_qty": 90}
]
```

## Processing the Data

### Python Example

```python
@app.route('/seller/add-product', methods=['POST'])
def add_product():
    try:
        # Get basic product info
        name = request.form.get('name')
        price = float(request.form.get('price'))
        category = request.form.get('category')
        
        # Get stock data
        stock_data_json = request.form.get('stock_data')
        stock_data = json.loads(stock_data_json) if stock_data_json else []
        
        # Validate stock data structure
        for combo in stock_data:
            assert 'size' in combo, "Missing 'size' in combo"
            assert 'color' in combo, "Missing 'color' in combo"
            assert 'stock_qty' in combo, "Missing 'stock_qty' in combo"
            assert combo['stock_qty'] > 0, f"Stock qty must be > 0 for {combo}"
        
        # 1. Create product record
        product = Product(
            seller_id=current_user.id,
            name=name,
            price=price,
            category=category,
            status='pending'  # Admin approval needed
        )
        db.session.add(product)
        db.session.flush()  # Get product ID
        product_id = product.id
        
        # 2. Add all stock combinations to product_stock table
        for combo in stock_data:
            product_stock = ProductStock(
                product_id=product_id,
                size=combo['size'],
                color=combo['color'],
                stock_qty=combo['stock_qty']
            )
            db.session.add(product_stock)
        
        # 3. Commit transaction
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Product created with {len(stock_data)} size-color combinations'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
```

### Node.js/Express Example

```javascript
app.post('/seller/add-product', async (req, res) => {
  try {
    const { name, price, category, stock_data } = req.body;
    
    // stock_data is already parsed from JSON if sent as JSON
    // If form-data, parse it:
    const stockArray = typeof stock_data === 'string' 
      ? JSON.parse(stock_data) 
      : stock_data;
    
    // Validate
    for (const combo of stockArray) {
      if (!combo.size || !combo.color || !combo.stock_qty) {
        return res.status(400).json({ 
          error: 'Invalid stock data structure' 
        });
      }
      if (combo.stock_qty <= 0) {
        return res.status(400).json({ 
          error: `Invalid quantity for ${combo.size}-${combo.color}` 
        });
      }
    }
    
    // Create product
    const product = await Product.create({
      seller_id: req.user.id,
      name,
      price,
      category,
      status: 'pending'
    });
    
    // Create stock combinations
    const stocks = stockArray.map(combo => ({
      product_id: product.id,
      size: combo.size,
      color: combo.color,
      stock_qty: combo.stock_qty
    }));
    
    await ProductStock.bulkCreate(stocks);
    
    res.json({ 
      success: true,
      message: `Product created with ${stocks.length} combinations`
    });
    
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});
```

## Database Schema

### products table
```sql
CREATE TABLE products (
  id INT PRIMARY KEY AUTO_INCREMENT,
  seller_id INT NOT NULL,
  name VARCHAR(255) NOT NULL,
  price DECIMAL(10, 2) NOT NULL,
  category VARCHAR(100),
  status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (seller_id) REFERENCES sellers(id)
);
```

### product_stock table
```sql
CREATE TABLE product_stock (
  id INT PRIMARY KEY AUTO_INCREMENT,
  product_id INT NOT NULL,
  size VARCHAR(50) NOT NULL,
  color VARCHAR(50) NOT NULL,
  stock_qty INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY unique_combination (product_id, size, color),
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);
```

## Key Points

### ✅ What's New
1. **Per-color independent sizes** - No Cartesian product, only actual combinations
2. **Flexible stock management** - Each size-color pair has its own quantity
3. **Reduced data** - No unused combinations
4. **Better inventory tracking** - Exactly what you need, nothing more

### ✅ Backward Compatible
- Same data format (array of objects)
- Same serialization method (JSON string)
- Same field names (size, color, stock_qty)
- Can be used in existing product management flow

### ✅ Validation
Frontend validates:
- At least one color selected ✓
- Each color has at least one size selected ✓
- All combinations have qty > 0 ✓

Backend should validate:
- Stock data is valid JSON array ✓
- Each combo has size, color, stock_qty ✓
- All qty > 0 ✓
- No duplicate size-color for same product ✓ (SQL UNIQUE constraint)

### ✅ Sample Queries

```sql
-- Get all sizes available for Green color in product 5
SELECT DISTINCT size FROM product_stock 
WHERE product_id = 5 AND color = 'Green';

-- Get total stock for a product
SELECT SUM(stock_qty) as total_stock FROM product_stock 
WHERE product_id = 5;

-- Get stock for specific size-color combo
SELECT stock_qty FROM product_stock 
WHERE product_id = 5 AND size = 'M' AND color = 'Green';

-- Get all color-size combos with their stocks
SELECT color, size, stock_qty FROM product_stock 
WHERE product_id = 5 
ORDER BY color, size;

-- Check if size is available for a product
SELECT EXISTS(
  SELECT 1 FROM product_stock 
  WHERE product_id = 5 AND size = 'L'
);
```

### ✅ Updates When Stock Changes

```python
# Reduce stock when order is placed
stock = ProductStock.query.filter_by(
    product_id=product_id,
    size=order_size,
    color=order_color
).first()

stock.stock_qty -= quantity_ordered
db.session.commit()
```

### ✅ Listing Product Variants

```python
# Get all available variants for a product
variants = ProductStock.query.filter_by(product_id=product_id).all()

# Group by color
from itertools import groupby

variants_by_color = {}
for variant in variants:
    if variant.color not in variants_by_color:
        variants_by_color[variant.color] = []
    variants_by_color[variant.color].append({
        'size': variant.size,
        'stock_qty': variant.stock_qty,
        'available': variant.stock_qty > 0
    })

# Result:
# {
#   'Green': [{'size': 'S', 'stock_qty': 100, 'available': True}, ...],
#   'Blue': [{'size': 'S', 'stock_qty': 200, 'available': True}, ...],
#   'Red': [{'size': 'L', 'stock_qty': 80, 'available': True}, ...]
# }
```

## Migration from Old System

If you had the old system (all sizes for all colors), here's how to migrate:

```python
# Old format: All sizes for all colors
# Green: S, M, L, XL (qty 50 each)
# Blue: S, M, L, XL (qty 40 each)

# New format: Independent sizes per color
# Green: S, M (qty 50 each)
# Blue: M, L, XL (qty 40 each)

# No database migration needed! Just add new products with the new system
# Old products continue working as before
# Or selectively migrate when updating products
```

## Testing

```javascript
// In browser console, test the data structure:

// 1. Select colors
document.querySelector('input[name="colors"][value="Green"]').click();
document.querySelector('input[name="colors"][value="Blue"]').click();

// 2. Select sizes for each color
document.querySelector('input[data-color-size="Green"][value="S"]').click();
document.querySelector('input[data-color-size="Green"][value="M"]').click();
document.querySelector('input[data-color-size="Blue"][value="M"]').click();
document.querySelector('input[data-color-size="Blue"][value="L"]').click();

// 3. Fill stock quantities
document.querySelector('input[data-combination="S|Green"]').value = '100';
document.querySelector('input[data-combination="M|Green"]').value = '50';
document.querySelector('input[data-combination="M|Blue"]').value = '150';
document.querySelector('input[data-combination="L|Blue"]').value = '75';

// 4. Serialize data
serializeStockData();

// 5. Check the hidden field
console.log(document.getElementById('stock-data-hidden').value);

// Output: [{"size":"S","color":"Green","stock_qty":100},{"size":"M","color":"Green","stock_qty":50},...]
```

## Production Checklist

- [ ] Backend receives stock_data correctly
- [ ] Parses JSON array properly
- [ ] Validates all combinations
- [ ] Creates product records with status='pending'
- [ ] Inserts all stock combinations
- [ ] UNIQUE constraint prevents duplicate size-color for same product
- [ ] Admin approval flow works
- [ ] Products display correctly on storefront
- [ ] Stock deduction on purchase works
- [ ] Low stock alerts work
- [ ] Inventory management shows per-color sizes
