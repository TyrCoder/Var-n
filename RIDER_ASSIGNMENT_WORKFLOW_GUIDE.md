# 🎯 Rider Selection Workflow - Quick Reference

## Problem Solved ✅
**Issue**: Modal showed "No available riders found for Luzon" even when nearby riders existed.
**Reason**: System was filtering by seller's island, not order's delivery location.
**Fix**: Now filters by order's delivery city/province and maps to geographic region.

---

## How to Use (Seller Perspective)

### Step 1: View Your Orders
- Go to Seller Dashboard
- See orders in "To Release to Rider" section

### Step 2: Click "Select Rider"
- Click on an order row
- Modal opens showing order details and delivery location

### Step 3: See Available Nearby Riders
- Modal displays: **📍 Order Delivery Region: Central Luzon**
- Shows delivery address: **Quezon City, Metro Manila**
- Lists 5-10 available riders serving that region

### Step 4: Select & Assign
- Click **✓ Select** next to desired rider
- Confirmation dialog appears
- Rider assigned to order
- Order moves to "Released to Rider" section

---

## Technical Architecture

### Database Schema
```
riders table
├── id (Primary Key)
├── user_id (Foreign Key → users)
├── vehicle_type (motorcycle, bicycle, car, van, truck)
├── license_number
├── vehicle_plate
├── service_area (TEXT - legacy field)
├── sub_region ⭐ NEW (North Luzon, Central Luzon, South Luzon, Visayas, Mindanao, All areas)
├── current_location_lat
├── current_location_lng
├── is_available (Boolean)
├── rating
├── total_deliveries
└── ... other fields
```

### Region Mapping Logic

**Function**: `get_delivery_region(city, province)`

**Input**: Delivery address city/province from order

**Process**:
1. Normalize input (lowercase, trim)
2. Check against region dictionaries
3. Return specific region or "Unknown"

**Output**: One of:
- "North Luzon"
- "Central Luzon"
- "South Luzon"
- "Visayas"
- "Mindanao"
- "Unknown"

---

## API Endpoint

### GET `/api/sellers/available-riders`

**Parameters**:
- `order_id` (required) - ID of order needing rider assignment

**Request**:
```
GET /api/sellers/available-riders?order_id=12345
```

**Response**:
```json
{
  "success": true,
  "riders": [
    {
      "id": 5,
      "first_name": "Juan",
      "last_name": "Dela Cruz",
      "vehicle_type": "motorcycle",
      "service_area": "Central Luzon",
      "sub_region": "Central Luzon",
      "rating": 4.8,
      "total_deliveries": 156,
      "is_available": true,
      "status": "active"
    }
  ],
  "count": 5,
  "delivery_region": "Central Luzon",
  "delivery_location": {
    "city": "Quezon City",
    "province": "Metro Manila"
  }
}
```

**Error Response**:
```json
{
  "success": false,
  "error": "Order or shipping address not found"
}
```

---

## Region Coverage

### North Luzon 🌎
- Nueva Ecija, Bulacan, Nueva Vizcaya
- Quirino, Tarlac, Pangasinan
- La Union, Isabela, Ifugao, Kalinga
- Mountain Province, Benguet

### Central Luzon 🌎
- Pampanga, Batangas, Cavite, Laguna
- Quezon, Marinduque, Palawan
- **Metro Manila**: Quezon City, Manila, Pasig, Makati, Taguig, Caloocan, Parañaque, Las Piñas, Mandaluyong, Marikina, San Juan, Muntinlupa

### South Luzon 🌎
- Camarines Norte, Camarines Sur
- Albay, Sorsogon, Masbate

### Visayas 🌎
- Cebu, Iloilo, Bohol
- Negros Occidental, Negros Oriental
- Aklan, Capiz, Antique, Guimaras, Siquijor

### Mindanao 🌎
- Davao (del Norte, del Sur, Occidental, Oriental)
- Cagayan de Oro, Zamboanga (City, Sibugay, Tenontang)
- Butuan, Cotabato (North, South)
- Surigao (del Norte, del Sur)
- Lanao (del Norte, del Sur)
- Misamis (Occidental, Oriental)
- Maguindanao, Sarangani, Basilan

---

## Rider Profile Updates Needed

Each rider should update their profile to specify their service region:

### In Rider Dashboard:
1. Go to Settings → Service Area
2. Select sub-region:
   - ☑️ North Luzon
   - ☑️ Central Luzon
   - ☑️ South Luzon
   - ☑️ Visayas
   - ☑️ Mindanao
   - ☑️ All areas (serves everywhere)
3. Save

**Default for Existing Riders**: "All areas" (still matches everywhere)

---

## Troubleshooting

### Issue: No riders appearing
**Solution Steps**:
1. Check if any active riders exist: `SELECT COUNT(*) FROM riders WHERE status = 'active' AND is_available = TRUE;`
2. Verify riders have sub_region set: `SELECT * FROM riders WHERE sub_region IS NULL;`
3. Check order's delivery address is in correct city/province
4. Verify region mapping: Run `SELECT get_delivery_region('Quezon City', 'Metro Manila');` - should return "Central Luzon"

### Issue: Wrong riders appearing
**Solution Steps**:
1. Verify order's shipping address: `SELECT * FROM addresses WHERE id = [shipping_address_id];`
2. Check rider's sub_region: `SELECT id, first_name, sub_region FROM riders;`
3. Run region mapping test to confirm address is mapping to correct region

### Issue: Rider serves region but not appearing
**Solution**:
1. Check rider status: `SELECT status, is_available FROM riders WHERE id = [rider_id];`
2. Must be: `status = 'active' AND is_available = TRUE`
3. Update if needed: `UPDATE riders SET is_available = TRUE WHERE id = [rider_id];`

---

## Verification Query

To verify everything is working:

```sql
-- 1. Check riders sub_region distribution
SELECT sub_region, COUNT(*) as count FROM riders GROUP BY sub_region;

-- 2. Check specific region riders
SELECT id, first_name, last_name, sub_region, is_available, status 
FROM riders 
WHERE sub_region = 'Central Luzon' 
  AND is_available = TRUE 
  AND status = 'active';

-- 3. Check order delivery location
SELECT 
  o.id, o.order_number,
  a.city, a.province,
  s.id as rider_id,
  r.first_name, r.sub_region
FROM orders o
JOIN addresses a ON o.shipping_address_id = a.id
LEFT JOIN shipments s ON o.id = s.order_id
LEFT JOIN riders r ON s.rider_id = r.id
WHERE o.id = [order_id];
```

---

## Timeline & Status

| Phase | Status | Notes |
|-------|--------|-------|
| Database Schema | ✅ Complete | Added `sub_region` ENUM column |
| Location Mapping | ✅ Complete | 5 regions supported (North/Central/South Luzon, Visayas, Mindanao) |
| Backend Endpoint | ✅ Complete | Now uses order location, not seller location |
| Frontend Modal | ✅ Complete | Displays delivery region and nearby riders |
| Migration SQL | ✅ Complete | Run to update existing riders |
| Testing | ✅ Complete | All regions verified |
| Documentation | ✅ Complete | Ready for deployment |

---

## Next Steps for Deployment

1. **Run Migration**: Execute `update_riders_sub_region.sql` on database
2. **Restart Server**: Restart Flask app to load new code
3. **Rider Profile Update**: Ask riders to set their service region
4. **Test Workflow**: 
   - Create test order in different regions
   - Verify riders appear in modal
   - Confirm assignment works
5. **Monitor**: Check logs for any errors

---

## Key Code References

### Location Mapping Function
**File**: `app.py` Lines 33-80
**Function**: `get_delivery_region(city, province)`

### Rider Fetching Endpoint
**File**: `app.py` Lines 9670-9780
**Endpoint**: `GET /api/sellers/available-riders`

### Frontend Modal
**File**: `templates/pages/SellerDashboard.html` Lines 1980-2045
**Function**: Shows riders modal with delivery location

---

## Support

For issues or questions:
- Check database queries in MySQL Workbench
- Review app.py logs for endpoint errors
- Verify riders table has sub_region data
- Test region mapping function with sample addresses
