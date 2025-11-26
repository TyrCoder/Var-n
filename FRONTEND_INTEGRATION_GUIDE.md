# Frontend Implementation Guide - Order Management Tabs

## Quick Start - SellerDashboard.html Tab Filtering

### Current State (Lines 648-655)
The buttons already exist but may not be calling the correct filter function.

```html
<button class="action-btn" data-filter-btn="pending" onclick="filterOrders('pending')" style="background: #ff9800;">
  ⏳ Pending
</button>
<button class="action-btn" data-filter-btn="confirmed" onclick="filterOrders('confirmed')" style="background: #2196f3;">
  ✔️ Confirmed
</button>
<button class="action-btn" data-filter-btn="release_to_rider" onclick="filterOrders('release_to_rider')" style="background: #4caf50;">
  🚚 Release to Rider
</button>
```

### Implementation - Add/Update JavaScript Function

Find the `filterOrders()` function in SellerDashboard.html (around line 1200-1300).

**Replace with**:
```javascript
function filterOrders(status) {
    console.log(`[DEBUG] Filtering orders by status: ${status}`);
    
    // Build URL with status filter
    let url = '/seller/orders';
    if (status && status !== 'all') {
        url += `?status=${status}`;
    }
    
    // Show loading state
    document.getElementById('orders-list').innerHTML = '<div style="padding: 20px; text-align: center;">Loading orders...</div>';
    
    fetch(url)
        .then(response => {
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return response.json();
        })
        .then(data => {
            if (!data.success) {
                showError(`Failed to load orders: ${data.error}`);
                return;
            }
            
            console.log(`[DEBUG] Loaded ${data.orders.length} orders with filter: ${status}`);
            
            // Update active button
            document.querySelectorAll('[data-filter-btn]').forEach(btn => {
                btn.style.opacity = btn.getAttribute('data-filter-btn') === status ? '1' : '0.6';
            });
            
            // Populate orders table
            if (data.orders && data.orders.length > 0) {
                populateOrdersTable(data.orders);
            } else {
                document.getElementById('orders-list').innerHTML = 
                    `<div style="padding: 20px; text-align: center; color: #666;">No orders found for "${status}" status</div>`;
            }
        })
        .catch(error => {
            console.error('[ERROR] filterOrders:', error);
            showError(`Error loading orders: ${error.message}`);
        });
}

function populateOrdersTable(orders) {
    if (!orders || orders.length === 0) {
        document.getElementById('orders-list').innerHTML = '<div style="padding: 20px;">No orders</div>';
        return;
    }
    
    let html = `
        <table style="width: 100%; border-collapse: collapse;">
            <thead>
                <tr style="background: #f5f5f5; border-bottom: 1px solid #ddd;">
                    <th style="padding: 12px; text-align: left;">Order #</th>
                    <th style="padding: 12px; text-align: left;">Customer</th>
                    <th style="padding: 12px; text-align: left;">Amount</th>
                    <th style="padding: 12px; text-align: left;">Status</th>
                    <th style="padding: 12px; text-align: left;">Date</th>
                    <th style="padding: 12px; text-align: left;">Actions</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    orders.forEach(order => {
        const date = new Date(order.created_at).toLocaleDateString();
        const statusColor = getStatusColor(order.order_status);
        
        html += `
            <tr style="border-bottom: 1px solid #eee; hover: {background: #f9f9f9;}">
                <td style="padding: 12px;">${order.order_number}</td>
                <td style="padding: 12px;">${order.customer_name || 'N/A'}</td>
                <td style="padding: 12px;">₱${parseFloat(order.total_amount).toFixed(2)}</td>
                <td style="padding: 12px;">
                    <span style="background: ${statusColor}; color: #fff; padding: 4px 8px; border-radius: 4px; font-size: 12px;">
                        ${order.order_status.toUpperCase()}
                    </span>
                </td>
                <td style="padding: 12px;">${date}</td>
                <td style="padding: 12px;">
                    <button class="action-btn" onclick="viewOrderDetails(${order.id})" style="font-size: 12px;">View</button>
                </td>
            </tr>
        `;
    });
    
    html += `
            </tbody>
        </table>
    `;
    
    document.getElementById('orders-list').innerHTML = html;
}

function getStatusColor(status) {
    const colors = {
        'pending': '#ff9800',      // Orange
        'confirmed': '#2196f3',    // Blue
        'processing': '#9c27b0',   // Purple
        'shipped': '#4caf50',      // Green
        'delivered': '#10b981',    // Emerald
        'cancelled': '#f44336',    // Red
        'returned': '#607d8b'      // Grey
    };
    return colors[status] || '#999';
}

function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.style.cssText = 'padding: 12px; background: #fee; color: #c33; border-radius: 4px; margin-bottom: 12px;';
    errorDiv.textContent = message;
    document.getElementById('orders-list').insertBefore(errorDiv, document.getElementById('orders-list').firstChild);
}
```

### Cart Badge Update

In the navbar section (SellerDashboard.html top section where user profile/cart is shown):

**Find**: Cart icon display code (usually line 1-100)

**Update to use unique_count**:
```javascript
// After fetching cart
fetch('/api/cart/get')
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            // Use unique_count for badge, not total quantity
            const badge = document.querySelector('.cart-badge');
            if (badge) {
                badge.textContent = data.unique_count || 0;
            }
        }
    });
```

### Testing the Implementation

#### Test 1: View All Orders
```javascript
filterOrders('all');  // Shows all orders
```

#### Test 2: Filter by Status
```javascript
filterOrders('pending');        // ⏳ Shows pending orders
filterOrders('confirmed');      // ✔️ Shows confirmed orders
filterOrders('release_to_rider'); // 🚚 Shows processing orders
```

#### Test 3: Tab Highlighting
- Click "Pending" button → 100% opacity
- Click "Confirmed" button → "Pending" fades to 60% opacity

#### Test 4: Empty State
- When no orders match filter → shows "No orders found for "pending" status"

---

## Integration Checklist

### SellerDashboard.html Updates
- [ ] Replace `filterOrders()` function with new implementation
- [ ] Add `populateOrdersTable()` function
- [ ] Add `getStatusColor()` helper
- [ ] Add `showError()` helper
- [ ] Update cart badge to use `unique_count`
- [ ] Test all 3 status filters

### Dashboard.html Updates (Admin)
- [ ] Pending products already working (backend updated)
- [ ] No frontend changes needed (API handles it)

### Other Pages
- [ ] Check if there are other cart badge displays to update
- [ ] Update any other filter functions following same pattern

---

## Backend Status
✅ All endpoints ready and tested
- `/seller/orders?status=pending` 
- `/seller/orders?status=confirmed`
- `/seller/orders?status=release_to_rider`
- `/api/cart/get` (returns unique_count)

---

## Common Issues & Solutions

### Issue: Filter not working
**Solution**: Ensure `data-filter-btn` attribute matches the status parameter

### Issue: Table not populating
**Solution**: Check browser console for JSON response structure. May differ from expected.

### Issue: Cart badge not updating
**Solution**: Ensure `unique_count` exists in response. Check `/api/cart/get` returns it.

### Issue: Button opacity not changing
**Solution**: Add `transition: opacity 0.2s;` to button CSS for smooth transition

---

## References
- API Documentation: `/seller/orders?status=<status>`
- Response Format: `{success: true, orders: [...], filter: '<status>'}`
- Status Values: pending, confirmed, processing, release_to_rider, shipped, delivered

**Implementation Date**: 2025-11-26  
**Status**: Ready for Frontend Integration
