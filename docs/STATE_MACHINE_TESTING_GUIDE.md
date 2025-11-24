# Order Management State Machine - Testing Guide

## Quick Test Checklist

### ✅ Test 1: Valid Status Transitions

**Scenario:** Test forward-only progression

1. **Seller Dashboard** → Find any pending order
2. **Click Status Button** → Should see "Confirm Order" option
3. **Select Confirm** → Order should move to `confirmed`
4. **Click Status Again** → Should see "Processing" option (not "Confirm")
5. **Select Processing** → Order should move to `processing`
6. **Click Status Again** → Should see "Shipped" option
7. **Select Shipped** → Order should move to `shipped`
8. **Click Status Again** → Should see "Delivered" option
9. **Select Delivered** → Order should move to `delivered`

**Expected Result:** ✅ All transitions succeed, order progresses forward only

---

### ❌ Test 2: Prevent Backward Transitions

**Scenario:** Try to go backward (should FAIL)

1. **Get an order at status:** `shipped`
2. **Click Status Button** → Modal opens
3. **Try to select:** `processing` or `confirmed`
   - ⚠️ These options should NOT appear in dropdown
4. **Only valid options visible:** `delivered`
5. **If somehow tries API directly:** Should get error

**Expected Result:** ❌ Backward transitions are blocked, error message shown

---

### 🔒 Test 3: Final State Lock

**Scenario:** Test that delivered orders cannot be modified

1. **Get an order at status:** `delivered`
2. **Click Status Button**
3. **System should show:** "⚠️ This order is in a final state (DELIVERED) and cannot be modified further."
4. **Alert closes without opening modal**

**Expected Result:** 🔒 Final state orders are locked, cannot be changed

---

### 📋 Test 4: Modal Information Display

**Scenario:** Verify enhanced modal shows order details

When opening status modal, should display:

- ✅ **Current Status** (with emoji and description)
- ✅ **Order Number** (e.g., "Order #12345")
- ✅ **Total Amount** (e.g., "₱5,000.00")
- ✅ **Customer Name**
- ✅ **Number of Items**
- ✅ **Order Date**
- ✅ **Valid Next Status Options Only** (with descriptions)

**Expected Result:** ✅ All order information clearly visible in modal

---

### ⚠️ Test 5: Warning Messages

**Scenario:** Test warnings for terminal statuses

1. **Get an order at status:** `shipped`
2. **Open Status Modal**
3. **Select:** `delivered`
4. **Should see warning:** "Once marked as delivered, this order cannot be modified."
5. **Update button should be enabled** (still clickable)
6. **After update, next open should show locked message**

**Expected Result:** ⚠️ Clear warnings before final state transitions

---

### 🚫 Test 6: Cancel Status

**Scenario:** Test cancellation workflow (terminal state)

1. **Get an order at status:** `processing` or `shipped`
2. **Open Status Modal**
3. **Select:** `cancelled` (if available from current status)
4. **Should show warning:** "Cancelled orders cannot be reopened."
5. **Update to cancelled**
6. **Try to update again** → Should see "Order in final state" message

**Expected Result:** 🚫 Cancelled orders locked and cannot be recovered

---

## Detailed Transition Flow Test

### 🟦 pending → confirmed

```
Action:     Click "Update Status" button
Current:    pending
Options:    ✅ confirmed (only option)
Select:     confirmed
Result:     Status updates to confirmed
Modal:      Closes, orders reload
Next test:  Try to go back to pending (should fail)
```

### 🟩 confirmed → processing

```
Action:     Click "Update Status" button  
Current:    confirmed
Options:    ✅ processing (only option)
Not shown:  pending (no backward)
Select:     processing
Result:     Status updates to processing
Modal:      Closes, orders reload
Test:       Dropdown should NOT show "confirmed" anymore
```

### 🟪 processing → shipped

```
Action:     Click "Update Status" button
Current:    processing
Options:    ✅ shipped (only option)
Not shown:  pending, confirmed (no backward)
Select:     shipped
Result:     Status updates to shipped
Modal:      Closes, orders reload
```

### 🟨 shipped → delivered/cancelled

```
Action:     Click "Update Status" button
Current:    shipped
Options:    ✅ delivered
             ✅ cancelled  
Not shown:  pending, confirmed, processing (no backward)
Select:     delivered
Warning:    "Once marked as delivered, this order cannot be modified."
Result:     Status updates to delivered (FINAL)
Next:       Cannot open status modal - shows lock message
```

---

## Error Messages to Look For

### ✅ Expected Error Messages

**Backward Transition Attempt:**
```
❌ Invalid status transition:
Cannot go from "SHIPPED" to "PROCESSING"

Forward-only transitions are allowed.
```

**Final State Attempt:**
```
❌ Invalid status transition:
Cannot go from "DELIVERED" to "CANCELLED"

Forward-only transitions are allowed.
```

**Already in Final State:**
```
⚠️ This order is in a final state (DELIVERED) 
and cannot be modified further.
```

**Unknown Error:**
```
❌ Failed to update order status:
[Error message from server]
```

---

## Browser Console Logs

Open Developer Tools (F12) → Console tab to see detailed logs:

### ✅ Success Log
```
🔄 Opening order management modal for order: 123 Current status: confirmed
📊 Updating order status: orderId=123, from=confirmed, to=processing
✅ ORDER STATUS UPDATE: Order 123 transitioned from 'confirmed' → 'processing' by seller 5
```

### ❌ Error Log
```
❌ Error updating order status: {error details}
❌ Invalid status transition: Cannot go from SHIPPED to PROCESSING
```

---

## Test Scenarios Summary

| Test | Current Status | Try to Change To | Expected Result |
|------|---|---|---|
| **Valid 1** | pending | confirmed | ✅ Success |
| **Valid 2** | confirmed | processing | ✅ Success |
| **Valid 3** | processing | shipped | ✅ Success |
| **Valid 4** | shipped | delivered | ✅ Success |
| **Invalid 1** | confirmed | pending | ❌ Error (backward) |
| **Invalid 2** | shipped | processing | ❌ Error (backward) |
| **Invalid 3** | delivered | shipped | ❌ Error (backward) |
| **Invalid 4** | pending | shipped | ❌ Error (skip stage) |
| **Lock 1** | delivered | any | 🔒 Modal blocked |
| **Lock 2** | cancelled | any | 🔒 Modal blocked |

---

## Performance Checklist

- ⏱️ Modal opens quickly
- ⏱️ Status update completes in < 2 seconds
- ⏱️ Error messages appear immediately
- ⏱️ Orders reload after update
- ⏱️ Multiple rapid clicks don't cause issues

---

## Regression Testing

If modifying order management, ensure:

- [ ] All valid transitions still work
- [ ] All backward transitions still blocked
- [ ] Final states still locked
- [ ] Modal displays correctly
- [ ] Warnings show for terminal states
- [ ] Order details display correctly
- [ ] Error messages are clear
- [ ] No database inconsistencies
- [ ] Shipment status updates correctly
- [ ] Seller permissions still enforced

---

## Database Verification

After testing, verify database consistency:

```sql
-- Check order status flow is logical
SELECT id, order_number, order_status, created_at, updated_at 
FROM orders 
ORDER BY updated_at DESC 
LIMIT 10;

-- Verify no backward transitions occurred
-- All orders should have valid status sequence
```

---

## Troubleshooting

### Modal Won't Open
- Check browser console for errors (F12)
- Verify seller is logged in
- Verify order ID is correct
- Refresh page and try again

### Status Won't Update
- Check network tab in Developer Tools
- Verify request shows correct order_id and new_status
- Check server logs (app.py output)
- Verify seller owns the order

### Wrong Statuses Showing
- Clear browser cache
- Hard refresh page (Ctrl+Shift+R)
- Verify JavaScript loaded correctly
- Check console for syntax errors

### Updates Working But Not Saving
- Check database connection
- Verify MySQL is running
- Check app.py for database errors
- Restart Flask app

---

## Success Criteria ✅

Order management is working correctly when:

1. ✅ Pending orders can only go to confirmed
2. ✅ Confirmed orders can only go to processing  
3. ✅ Processing orders can only go to shipped
4. ✅ Shipped orders can only go to delivered
5. ✅ Delivered/Cancelled orders cannot be modified
6. ✅ No backward transitions are possible
7. ✅ Modal shows only valid next statuses
8. ✅ Clear warnings for final states
9. ✅ Order details display in modal
10. ✅ Error messages explain why transition failed

When all of these pass, the order management state machine is fully functional! ✅
