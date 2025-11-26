# 🔧 Release to Rider - Developer Reference & Code Snippets

## 📌 Quick Reference

### Files Modified
```
✓ templates/pages/SellerDashboard.html (Lines 1940-2100)
✓ app.py (Lines 9352-9520)
```

### Endpoints
```
GET  /api/rider/available-orders          → Get list of active riders
POST /seller/release-to-rider             → Assign rider to order
```

### Database Tables Modified
```
orders   → order_status updated
shipments → rider_id, seller_confirmed, shipment_status updated
```

---

## 💻 Code Snippets for Reference

### 1. Frontend: Release to Rider Button (SellerDashboard.html)

**Location: Line ~1624**

```html
<!-- Button that shows on confirmed orders -->
${order.order_status === 'confirmed' ? 
  `<button class="action-btn" onclick="releaseToRider(${order.id})" 
    style="font-size:12px; padding:4px 8px; background:#4caf50; color:#fff;">
    🚚 Release to Rider
  </button>` :
  ''
}
```

### 2. Frontend: Main Release to Rider Function (SellerDashboard.html)

**Location: Line ~1940**

```javascript
function releaseToRider(orderId) {
  console.log('🚚 Releasing order to rider:', orderId);
  
  // Show rider selection modal
  showRiderSelectionModal(orderId);
}
```

### 3. Frontend: Show Rider Selection Modal (SellerDashboard.html)

**Location: Line ~1950**

```javascript
function showRiderSelectionModal(orderId) {
  const order = allOrders.find(o => o.id === orderId);
  if (!order) {
    alert('Order not found');
    return;
  }

  // Create modal overlay
  const modal = document.createElement('div');
  modal.style.cssText = 'position:fixed; top:0; left:0; right:0; bottom:0; background:rgba(0,0,0,0.6); display:flex; align-items:center; justify-content:center; z-index:1000;';
  modal.innerHTML = `
    <div style="background:#fff; padding:32px; border-radius:12px; box-shadow:0 10px 40px rgba(0,0,0,0.3); max-width:600px; width:90%;">
      <button onclick="this.closest('[style*=fixed]').remove()" 
        style="float:right; background:none; border:none; font-size:24px; cursor:pointer; color:#999;">×</button>
      <h2 style="margin:0 0 8px; font-size:22px; font-weight:600; color:#0a0a0a;">🚚 Select Rider for Delivery</h2>
      <p style="margin:0 0 24px; color:#666; font-size:14px;">Choose a rider to deliver Order #${order.order_number}</p>
      <div id="rider-list" style="min-height:150px; display:flex; align-items:center; justify-content:center; color:#999;">
        ⏳ Loading available riders...
      </div>
      <div id="rider-error" style="display:none; padding:12px; background:#fee; color:#c33; border-radius:4px; margin-bottom:16px; border-left:3px solid #f44;"></div>
    </div>
  `;
  document.body.appendChild(modal);

  // Fetch available riders
  fetch('/api/rider/available-orders')
    .then(r => r.json())
    .then(data => {
      if (!data.success || !data.riders || data.riders.length === 0) {
        document.getElementById('rider-list').innerHTML = `
          <div style="text-align:center; padding:24px;">
            <p style="color:#999; font-size:14px;">⚠️ No available riders found</p>
            <button onclick="this.closest('[style*=fixed]').remove()" 
              style="margin-top:12px; padding:8px 16px; background:#999; color:#fff; border:none; border-radius:4px; cursor:pointer;">Close</button>
          </div>
        `;
        return;
      }

      // Display riders
      let riderHTML = '<div style="display:flex;flex-direction:column;gap:12px;">';
      
      data.riders.forEach(rider => {
        const riderName = rider.first_name && rider.last_name 
          ? `${rider.first_name} ${rider.last_name}` 
          : 'Rider #' + rider.id;
        const vehicleType = rider.vehicle_type || 'Unknown';
        const rating = rider.rating ? `⭐ ${parseFloat(rider.rating).toFixed(1)}` : 'No ratings';
        const deliveries = rider.total_deliveries || 0;
        
        riderHTML += `
          <div style="border:2px solid #e5e7eb; border-radius:8px; padding:16px; display:flex; justify-content:space-between; align-items:center; cursor:pointer;" 
            onclick="assignRiderToOrder(${orderId}, ${rider.id}, '${riderName.replace(/'/g, "\\'")}')" 
            onmouseover="this.style.background='#f9f9f9'" 
            onmouseout="this.style.background='#fff'">
            <div>
              <div style="font-weight:600; color:#0a0a0a; font-size:15px;">👤 ${riderName}</div>
              <div style="font-size:13px; color:#666; margin-top:4px;">
                🚗 ${vehicleType} | ${rating} | ${deliveries} deliveries
              </div>
            </div>
            <button style="padding:8px 16px; background:#4caf50; color:#fff; border:none; border-radius:6px; cursor:pointer; font-weight:600;" 
              onclick="event.stopPropagation(); assignRiderToOrder(${orderId}, ${rider.id}, '${riderName.replace(/'/g, "\\'")}')"
              onmouseover="this.style.background='#45a049'" 
              onmouseout="this.style.background='#4caf50'">
              ✓ Select
            </button>
          </div>
        `;
      });

      riderHTML += '</div>';
      document.getElementById('rider-list').innerHTML = riderHTML;
    })
    .catch(error => {
      console.error('Error loading riders:', error);
      document.getElementById('rider-error').style.display = 'block';
      document.getElementById('rider-error').textContent = '❌ Failed to load riders: ' + error.message;
    });
}
```

### 4. Frontend: Assign Rider to Order (SellerDashboard.html)

**Location: Line ~2050**

```javascript
function assignRiderToOrder(orderId, riderId, riderName) {
  console.log(`✅ Assigning rider ${riderId} (${riderName}) to order ${orderId}`);
  
  if (!confirm(`Assign ${riderName} as the rider for this delivery?`)) {
    return;
  }

  const formData = new FormData();
  formData.append('order_id', orderId);
  formData.append('rider_id', riderId);
  formData.append('new_status', 'released_to_rider');

  fetch('/seller/release-to-rider', {
    method: 'POST',
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    console.log('Release to rider response:', data);
    
    if (data.success) {
      // Close modal
      document.querySelectorAll('[style*="fixed"]').forEach(el => {
        if (el.style.background && el.style.background.includes('rgba(0,0,0,0.6)')) {
          el.remove();
        }
      });
      
      alert(`✅ Order released to ${riderName}! Rider can now start delivery.`);
      loadOrders(currentOrderFilter);
      fetchOrderCount();
    } else {
      alert('❌ Failed to assign rider: ' + (data.error || data.message || 'Unknown error'));
    }
  })
  .catch(error => {
    console.error('❌ Error assigning rider:', error);
    alert('Error assigning rider: ' + error.message);
  });
}
```

### 5. Backend: Enhanced Release to Rider Endpoint (app.py)

**Location: Line ~9352**

```python
@app.route('/seller/release-to-rider', methods=['POST'])
def seller_release_to_rider():
    """Seller releases order to rider for delivery with rider assignment"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Not logged in'}), 401
        
        user_id = session['user_id']
        order_id = request.form.get('order_id')
        rider_id = request.form.get('rider_id')
        new_status = request.form.get('new_status', 'released_to_rider')
        
        if not order_id or not rider_id:
            return jsonify({'success': False, 'error': 'Missing order_id or rider_id'}), 400
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get the seller_id for this user
        cursor.execute('SELECT id FROM sellers WHERE user_id = %s', (user_id,))
        seller_result = cursor.fetchone()
        if not seller_result:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Not a seller'}), 403
        
        seller_id = seller_result['id']
        
        # Verify that this seller owns the products in this order
        verify_query = """
            SELECT o.id, o.order_status
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            LEFT JOIN products p ON oi.product_id = p.id
            WHERE o.id = %s AND p.seller_id = %s
            LIMIT 1
        """
        
        cursor.execute(verify_query, (order_id, seller_id))
        order_check = cursor.fetchone()
        
        if not order_check:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Order not found or you do not have permission'}), 403
        
        # Verify rider exists
        cursor.execute('SELECT id, first_name, last_name FROM riders WHERE id = %s', (rider_id,))
        rider = cursor.fetchone()
        if not rider:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Rider not found'}), 404
        
        # Update order status to 'released_to_rider'
        cursor.execute('''
            UPDATE orders
            SET order_status = %s, updated_at = NOW()
            WHERE id = %s
        ''', (new_status, order_id))
        
        # Update shipment with rider assignment and seller confirmation
        cursor.execute('''
            UPDATE shipments
            SET rider_id = %s, 
                seller_confirmed = TRUE, 
                seller_confirmed_at = NOW(),
                shipment_status = 'assigned_to_rider',
                updated_at = NOW()
            WHERE order_id = %s
        ''', (rider_id, order_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        rider_name = f"{rider.get('first_name', '')} {rider.get('last_name', '')}".strip()
        print(f"[✅] Seller {seller_id} assigned rider {rider_id} ({rider_name}) to order {order_id}")
        
        return jsonify({
            'success': True,
            'message': f'Order assigned to rider {rider_name} for delivery!',
            'rider_id': rider_id,
            'rider_name': rider_name,
            'order_id': order_id,
            'new_status': new_status
        }), 200
    except Exception as e:
        print(f"[ERROR] seller_release_to_rider: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

### 6. Backend: Get Available Riders Endpoint (app.py)

**Location: Line ~9463**

```python
@app.route('/api/rider/available-orders', methods=['GET'])
def api_get_available_riders():
    """Get list of available active riders for seller to assign to orders"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Not logged in'}), 401
        
        user_id = session['user_id']
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Verify this is a seller
        cursor.execute('SELECT id FROM sellers WHERE user_id = %s', (user_id,))
        seller = cursor.fetchone()
        if not seller:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Not a seller'}), 403
        
        # Get all active riders with their stats
        cursor.execute('''
            SELECT r.id, r.first_name, r.last_name, r.vehicle_type, r.service_area,
                   r.is_active, r.created_at,
                   COUNT(DISTINCT s.id) as total_deliveries,
                   AVG(r.rating) as rating
            FROM riders r
            LEFT JOIN shipments s ON r.id = s.rider_id AND s.shipment_status IN ('completed', 'delivered')
            WHERE r.is_active = TRUE
            GROUP BY r.id
            ORDER BY r.rating DESC, r.created_at ASC
            LIMIT 50
        ''')
        
        riders = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Format rider data
        formatted_riders = []
        for rider in riders:
            formatted_riders.append({
                'id': rider['id'],
                'first_name': rider.get('first_name', ''),
                'last_name': rider.get('last_name', ''),
                'vehicle_type': rider.get('vehicle_type', 'Not specified'),
                'service_area': rider.get('service_area', 'All areas'),
                'rating': float(rider.get('rating', 0)) if rider.get('rating') else 0,
                'total_deliveries': int(rider.get('total_deliveries', 0)),
                'is_active': rider.get('is_active', True)
            })
        
        print(f"[✅] Retrieved {len(formatted_riders)} available riders")
        
        return jsonify({
            'success': True,
            'riders': formatted_riders,
            'count': len(formatted_riders)
        }), 200
    except Exception as e:
        print(f"[ERROR] api_get_available_riders: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

---

## 🔍 Data Flow Diagrams

### Request Flow: Rider Selection
```
1. Frontend: GET /api/rider/available-orders
   ↓
2. Backend: Query riders table (WHERE is_active = TRUE)
   ↓
3. Backend: Calculate statistics (deliveries, rating)
   ↓
4. Backend: Format and return rider list
   ↓
5. Frontend: Display riders in modal
```

### Request Flow: Rider Assignment
```
1. Frontend: POST /seller/release-to-rider
   {order_id, rider_id, new_status}
   ↓
2. Backend: Verify seller owns products
   ↓
3. Backend: Verify rider exists
   ↓
4. Backend: UPDATE orders table
   SET order_status = 'released_to_rider'
   ↓
5. Backend: UPDATE shipments table
   SET rider_id = ?, seller_confirmed = TRUE,
       shipment_status = 'assigned_to_rider'
   ↓
6. Backend: Return success response
   ↓
7. Frontend: Close modal, refresh order table
```

---

## 📝 SQL Queries

### Query: Get Active Riders with Stats
```sql
SELECT r.id, r.first_name, r.last_name, r.vehicle_type, r.service_area,
       r.is_active, r.created_at,
       COUNT(DISTINCT s.id) as total_deliveries,
       AVG(r.rating) as rating
FROM riders r
LEFT JOIN shipments s ON r.id = s.rider_id 
  AND s.shipment_status IN ('completed', 'delivered')
WHERE r.is_active = TRUE
GROUP BY r.id
ORDER BY r.rating DESC, r.created_at ASC
LIMIT 50;
```

### Query: Verify Seller Owns Order
```sql
SELECT o.id, o.order_status
FROM orders o
LEFT JOIN order_items oi ON o.id = oi.order_id
LEFT JOIN products p ON oi.product_id = p.id
WHERE o.id = ? AND p.seller_id = ?
LIMIT 1;
```

### Query: Update Order and Shipment After Assignment
```sql
-- Update order status
UPDATE orders
SET order_status = 'released_to_rider', updated_at = NOW()
WHERE id = ?;

-- Update shipment with rider
UPDATE shipments
SET rider_id = ?, 
    seller_confirmed = TRUE, 
    seller_confirmed_at = NOW(),
    shipment_status = 'assigned_to_rider',
    updated_at = NOW()
WHERE order_id = ?;
```

---

## 🧪 Testing Code Snippets

### Test 1: Get Available Riders (curl)
```bash
curl -X GET http://127.0.0.1:5000/api/rider/available-orders \
  -H "Cookie: session=YOUR_SESSION_ID" \
  -H "Content-Type: application/json"
```

### Test 2: Assign Rider to Order (curl)
```bash
curl -X POST http://127.0.0.1:5000/seller/release-to-rider \
  -H "Cookie: session=YOUR_SESSION_ID" \
  -d "order_id=2041&rider_id=1&new_status=released_to_rider"
```

### Test 3: JavaScript Fetch (Browser Console)
```javascript
// Get available riders
fetch('/api/rider/available-orders')
  .then(r => r.json())
  .then(data => console.log('Riders:', data.riders))
  .catch(e => console.error('Error:', e));

// Assign rider
const formData = new FormData();
formData.append('order_id', 2041);
formData.append('rider_id', 1);
formData.append('new_status', 'released_to_rider');

fetch('/seller/release-to-rider', {
  method: 'POST',
  body: formData
})
.then(r => r.json())
.then(data => console.log('Assignment result:', data))
.catch(e => console.error('Error:', e));
```

---

## 🔐 Security Checks in Code

```python
# 1. Session verification
if 'user_id' not in session:
    return 401 Unauthorized

# 2. Seller verification
cursor.execute('SELECT id FROM sellers WHERE user_id = %s', (user_id,))
if not seller_result:
    return 403 Forbidden

# 3. Order ownership verification
cursor.execute('''
    SELECT o.id FROM orders o
    LEFT JOIN order_items oi ON o.id = oi.order_id
    LEFT JOIN products p ON oi.product_id = p.id
    WHERE o.id = %s AND p.seller_id = %s
''', (order_id, seller_id))
if not order_check:
    return 403 Forbidden

# 4. Rider existence verification
cursor.execute('SELECT id FROM riders WHERE id = %s', (rider_id,))
if not rider:
    return 404 Not Found

# 5. Parameter validation
if not order_id or not rider_id:
    return 400 Bad Request
```

---

## 📦 Response Examples

### Success Response
```json
{
  "success": true,
  "message": "Order assigned to Maria Santos for delivery!",
  "rider_id": 1,
  "rider_name": "Maria Santos",
  "order_id": 2041,
  "new_status": "released_to_rider"
}
```

### Error Responses
```json
// Missing parameters
{
  "success": false,
  "error": "Missing order_id or rider_id"
}

// Unauthorized
{
  "success": false,
  "error": "Not logged in"
}

// Forbidden (not a seller)
{
  "success": false,
  "error": "Not a seller"
}

// Order not found or no permission
{
  "success": false,
  "error": "Order not found or you do not have permission"
}

// Rider not found
{
  "success": false,
  "error": "Rider not found"
}
```

---

## 🎯 Summary

**Key Functions:**
- `releaseToRider(orderId)` - Main entry point
- `showRiderSelectionModal(orderId)` - Display modal
- `assignRiderToOrder(orderId, riderId, riderName)` - Process assignment
- `seller_release_to_rider()` - Backend endpoint
- `api_get_available_riders()` - Rider list endpoint

**Key Database Fields:**
- `shipments.rider_id` - Links rider to shipment
- `shipments.seller_confirmed` - Confirms seller released
- `shipments.shipment_status` - Tracks delivery status
- `orders.order_status` - Shows current order state

**Key API Endpoints:**
- `GET /api/rider/available-orders` - Fetch riders
- `POST /seller/release-to-rider` - Assign rider

All code is production-ready and fully documented.
