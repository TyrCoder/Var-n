# 📊 Order Transaction Flow - Visual Diagram

## Complete Buyer Order Journey

```
┌────────────────────────────────────────────────────────────────────────────┐
│                    BUYER ORDER TRANSACTION FLOW                            │
└────────────────────────────────────────────────────────────────────────────┘

STAGE 1: CONFIRMATION & PAYMENT
════════════════════════════════
    Buyer Places Order
           │
           ▼
    ┌──────────────────┐
    │  💳 TO PAY       │
    │  (pending)       │
    │                  │
    │  Awaiting:       │
    │  - Seller OK     │
    │  - Buyer Payment │
    └──────────────────┘
           │
    [Seller Confirms ← Backend Action]
           │
           ▼

STAGE 2: PROCESSING & SHIPMENT
═══════════════════════════════
    Seller Confirms Order
    Assigns to Rider
           │
           ▼
    ┌──────────────────┐
    │  📦 TO SHIP      │
    │  (processing)    │
    │                  │
    │  Awaiting:       │
    │  - Rider Pickup  │
    │  - In Transit    │
    └──────────────────┘
           │
    [Rider Updates Status ← RiderDashboard]
    Rider: picked_up
    Rider: in_transit
           │
           ▼

STAGE 3: IN-TRANSIT / OUT FOR DELIVERY
═══════════════════════════════════════
    Rider Out for Delivery
           │
           ▼
    ┌──────────────────┐
    │  🚚 TO RECEIVE   │
    │  (shipped)       │
    │                  │
    │  Awaiting:       │
    │  - Buyer Arrival │
    │  - Delivery      │
    └──────────────────┘
           │
    [Rider Confirms Delivery ← RiderDashboard]
    Rider: delivered
           │
           ▼

STAGE 4: DELIVERY CONFIRMATION & ACTION
════════════════════════════════════════
    Order Arrives at Buyer
           │
           ▼
    ┌──────────────────────────────────┐
    │  ✓ COMPLETED                     │
    │  (delivered - awaiting action)   │
    │                                  │
    │  🎯 BUYER ACTION REQUIRED:       │
    │                                  │
    │  ┌──────────────┬──────────────┐ │
    │  │ ✓ Confirmed  │ ↩ Issue/     │ │
    │  │ Received     │   Return     │ │
    │  └──────────────┴──────────────┘ │
    └──────────────────────────────────┘
           │
      ┌────┴────┐
      ▼         ▼

PATH A:          PATH B:
CONFIRMED        RETURN/ISSUE
───────────      ──────────────
  │                │
  ▼                ▼
COMPLETED       RETURN_REQUESTED
(✓ Order OK)    (Support Contact)
                    │
                    ▼
              RETURN_APPROVED
              OR REFUND_ISSUED


═════════════════════════════════════════════════════════════════════════════

BUYER DASHBOARD STATUS DISPLAY
══════════════════════════════

Tab 1: ALL ORDERS
  ├─ To Pay (2)
  ├─ To Ship (3)  
  ├─ To Receive (1)
  ├─ Completed (5)
  ├─ Return_Requested (1)
  └─ Cancelled (0)

Tab 2: TO PAY (💳)
  │ Show Orders with status = pending
  │ Visual: Gray indicators (not yet started)
  │ Actions: None (awaiting seller)
  │
Tab 3: TO SHIP (📦)
  │ Show Orders with status = processing
  │ Visual: Blue active indicator
  │ Actions: None (seller/rider handling)
  │
Tab 4: TO RECEIVE (🚚)
  │ Show Orders with status = shipped
  │ Visual: Blue active indicator
  │ Actions: Track delivery (if available)
  │
Tab 5: COMPLETED (✓)
  │ Show Orders with status = delivered OR completed
  │ Visual: Green completed stages
  │ Actions: 
  │   - CONFIRMED: Show "✓ Received" status
  │   - PENDING: Show action buttons
  │
Tab 6: CANCELLED
  │ Show Orders with status = cancelled, failed, or return_requested
  │ Visual: Gray indicators
  │ Actions: Contact support


═════════════════════════════════════════════════════════════════════════════

ORDER CARD LAYOUT
═════════════════

┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  Order #12345                           To Pay ┌──────────┐│
│  Nov 20, 2025                                   │ 🔴 PENDING││
│                                                 └──────────┘│
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  Product Image │ Blue Collar Shirt                         │
│                │ Qty: 1 × ₱2,999.00                        │
│                │ Total: ₱2,999.00                          │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  Total: ₱2,999.00         [View Details →]                │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  TRANSACTION STAGE:                                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 💳 To Pay › 📦 To Ship › 🚚 To Receive › ✓ Completed│   │
│  │ ███░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [ONLY FOR DELIVERED ORDERS]                               │
│  ┌──────────────┐  ┌──────────────┐                       │
│  │ ✓ Confirm    │  │ ↩ Report     │                       │
│  │ Received     │  │ Issue        │                       │
│  └──────────────┘  └──────────────┘                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘


═════════════════════════════════════════════════════════════════════════════

DATA FLOW DIAGRAM
═════════════════

RIDER DASHBOARD          BACKEND         BUYER DASHBOARD
═══════════════════════════════════════════════════════════════

Rider Updates:                          Auto-Refresh
  picked_up        ──┐                 (every 5 sec)
  in_transit         ├──→ /api/         │
  out_for_delivery   │   rider/update   ├──→ /api/
  delivered        ──┘   delivery-      │   my-orders
                        status           │
                                        ▼
                      SHIPMENTS         ORDER STATUS
                      TABLE             MAPPING:
                      ═════════════════════════════════
                      picked_up        → processing
                      in_transit       → processing
                      out_for_delivery → shipped
                      delivered        → delivered
                                        ▼
                                    UPDATE UI:
                                    - Stage indicator
                                    - Tab counts
                                    - Action buttons
                                        │
                                        ▼
                                    DISPLAY TO BUYER


BUYER CONFIRMS/RETURNS:
  ✓ Confirmed      ──┐
  ↩ Return/Damaged   ├──→ /api/         Database
                                    Update:
                      order/complete    order_status
                      order/return      ='completed'
                                        or
                      ▼                 'return_requested'


═════════════════════════════════════════════════════════════════════════════

COLOR & EMOJI CODING
════════════════════

STATUS          BADGE   STAGE INDICATOR    ACTION BUTTONS
═══════════════════════════════════════════════════════════════════
pending         🔴 Red  💳 Pending Gray     No buttons
processing      🟠 Orange 📦 Active Blue   No buttons
shipped         🔵 Blue  🚚 Active Blue    No buttons
delivered       🟢 Green ✓ Complete Green  ✓ & ↩ (Buttons)
completed       🟢 Green ✓ Complete Green  "✓ Received"
return_requested ⚪ Gray ↩ Pending Gray    "Return Processing"
cancelled       ⚪ Gray  ⚪ Cancelled Gray   No buttons


═════════════════════════════════════════════════════════════════════════════

API ENDPOINTS INVOLVED
══════════════════════

1. GET /api/my-orders
   ├─ Returns: List of buyer's orders
   ├─ Status: Mapped from shipment status
   ├─ Refresh: Every 5 seconds (auto)
   └─ Response: { success, orders[] }

2. GET /api/rider/delivery-history (for reference)
   └─ Used by rider, affects buyer status updates

3. POST /api/rider/update-delivery-status (for reference)
   └─ Called by rider, triggers buyer status update

4. POST /api/order/complete (NEW)
   ├─ Called by: Buyer clicking "✓ Confirm Received"
   ├─ Params: order_id
   ├─ Effect: order_status = 'completed'
   └─ Response: { success, message }

5. POST /api/order/return (NEW)
   ├─ Called by: Buyer clicking "↩ Report Issue"
   ├─ Params: order_id, reason
   ├─ Effect: order_status = 'return_requested'
   └─ Response: { success, message }
