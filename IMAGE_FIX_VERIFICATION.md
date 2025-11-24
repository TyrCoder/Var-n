# IMAGE DISPLAY FIX - VERIFICATION GUIDE

## Problem Identified
Product images were NOT appearing in the order list view (My Orders) on the buyer dashboard, but WERE appearing when clicking "View Details". This was due to two issues:

1. **Missing Fallback for Non-Primary Images**: The SQL queries were using `LEFT JOIN product_images pi ON p.id = pi.product_id AND pi.is_primary = 1`, which would return NULL if no image was marked as primary. This caused the image_url to be NULL even if images existed.

2. **Field Name Mismatch**: The frontend template expected `item.price` but the API was returning `item.unit_price`, causing prices to not display correctly.

## Solution Implemented

### Changes Made to `app.py`:

#### 1. **Fixed `api_my_orders()` endpoint (line ~3710)**
**Before:**
```python
SELECT oi.id, oi.product_id, oi.quantity, oi.unit_price, oi.subtotal,
       p.name as product_name, pi.image_url
FROM order_items oi
LEFT JOIN products p ON oi.product_id = p.id
LEFT JOIN product_images pi ON p.id = pi.product_id AND pi.is_primary = 1
WHERE oi.order_id = %s
```

**After:**
```python
SELECT oi.id, oi.product_id, oi.quantity, oi.unit_price, oi.subtotal,
       p.name as product_name, 
       COALESCE(pi_primary.image_url, pi_any.image_url) as image_url
FROM order_items oi
LEFT JOIN products p ON oi.product_id = p.id
LEFT JOIN product_images pi_primary ON p.id = pi_primary.product_id AND pi_primary.is_primary = 1
LEFT JOIN product_images pi_any ON p.id = pi_any.product_id
WHERE oi.order_id = %s
GROUP BY oi.id, oi.product_id
```

Also added:
```python
item['price'] = item['unit_price']  # Add price field for frontend compatibility
```

#### 2. **Fixed `api_order_details()` endpoint (line ~3822)**
Applied the same COALESCE fix to ensure images always load, even if primary is not set.

#### 3. **Fixed `order_details()` view (line ~1143)**
Applied the same COALESCE fix for the order details page.

#### 4. **Fixed order_confirmation() view (line ~1233)**
Applied the same COALESCE fix for the order confirmation page.

## How It Works Now

1. **COALESCE() Function**: Falls back through the image options:
   - First tries `pi_primary.image_url` (image marked as primary)
   - If NULL, tries `pi_any.image_url` (first available image)
   - This ensures at least one image loads if ANY image exists for the product

2. **Price Field Alias**: Now provides both `unit_price` (original) and `price` (frontend compatibility) so the UI displays correctly

3. **GROUP BY**: Groups results by oi.id and oi.product_id to avoid duplicate rows from the fallback join

## Testing Recommendations

1. **Verify Images Show in My Orders List**:
   - Go to My Orders
   - Images should now appear in both the main list and when viewing individual order items
   - Images should appear for products both with and without primary image marking

2. **Verify Prices Display Correctly**:
   - Prices should show properly in the order list
   - Format: "Qty: X × ₱PRICE"

3. **Verify Details Modal Works**:
   - "View Details" should still work and show all order information
   - Images should definitely be present in the modal

4. **Edge Cases**:
   - Orders with products that have no images at all should show placeholder
   - Orders with products that have multiple images (with/without primary) should all show an image

## Files Modified
- `app.py` (4 SQL queries updated in different endpoints)

## Backwards Compatibility
✅ All changes are backwards compatible. The COALESCE() function gracefully handles scenarios where:
- Primary image exists (uses it)
- Primary image doesn't exist but other images do (uses first available)
- No images exist (returns NULL, frontend uses placeholder)
