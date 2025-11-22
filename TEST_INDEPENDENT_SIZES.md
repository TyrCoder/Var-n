# Independent Sizes Per Color - Feature Test

## What Changed

The product form now supports **independent size selection per color**. This means:

- **Green** can have: Small, Medium
- **Blue** can have: Small, Medium, Large, XL
- **Red** can have: Large, XL only

Each color can have a completely different set of sizes!

## How It Works

### 1. **Select Colors First**
   - Check the colors you want (e.g., Green, Blue, Red)
   - These appear above in the "Available Colors" section

### 2. **Choose Sizes Per Color**
   - A new "Sizes per Color" section appears below
   - For each color, you see checkboxes for all available sizes
   - **Green checkbox group** - select which sizes are available for green
   - **Blue checkbox group** - select which sizes are available for blue
   - **Red checkbox group** - select which sizes are available for red
   - Each color is independent!

### 3. **Stock Table Updates**
   - The stock table ONLY shows combinations for the sizes you selected per color
   - If Green only has Small & Medium, you'll only see:
     - Small - Green
     - Medium - Green
   - You won't see Large - Green or XL - Green

### 4. **Enter Stock Quantities**
   - Fill in the stock quantity for each actual combination
   - Form validates that all combinations have qty > 0

## Example Scenario

```
Colors selected: Green, Blue, Red

Sizes per Color:
├─ Green: [X] XS  [ ] S  [X] M  [ ] L  [ ] XL
├─ Blue:  [ ] XS  [X] S  [X] M  [X] L  [X] XL
└─ Red:   [ ] XS  [ ] S  [ ] M  [X] L  [X] XL

Stock Table:
┌──────┬────────┬──────────┐
│ Size │ Color  │ Stock    │
├──────┼────────┼──────────┤
│ XS   │ Green  │ [100]    │
│ M    │ Green  │ [50]     │
│ S    │ Blue   │ [200]    │
│ M    │ Blue   │ [150]    │
│ L    │ Blue   │ [75]     │
│ XL   │ Blue   │ [60]     │
│ L    │ Red    │ [80]     │
│ XL   │ Red    │ [90]     │
└──────┴────────┴──────────┘

Total combinations: 8 (not 15!)
```

## Key Features

✅ **Independent Size Selection** - Each color has its own size options
✅ **Dynamic Table** - Table updates instantly when you change selections
✅ **Flexible** - No need to have all sizes for all colors
✅ **Validation** - Ensures all size-color combos have stock > 0
✅ **Data Preservation** - Existing stock quantities are preserved when you modify selections
✅ **Custom Sizes** - Works with both predefined (XS-3XL) and custom sizes (4XL, 28W, etc.)
✅ **Custom Colors** - Add custom colors (Burgundy, Olive, etc.) - all colors can use them

## How to Test

1. **Navigate** to Seller Dashboard → Add Product
2. **Select Category** (not grooming)
3. **Select Colors**: Check "Green", "Blue", "Red"
4. **Select Sizes per Color**:
   - Green: Check only "S" and "M"
   - Blue: Check "S", "M", "L", "XL"
   - Red: Check only "L"
5. **View Stock Table**: Should show 7 combinations (2+4+1)
6. **Try Different Combinations**: Uncheck some sizes, table updates instantly
7. **Add Custom Size**: Type "4XL" in custom sizes
8. **Add Custom Color**: Type "Purple" in custom colors
9. **Select "Purple" in colors**, then pick sizes for Purple in the per-color section

## Browser Console Debug

Open developer tools (F12) and run:

```javascript
// See what sizes are available for a color
getSizesForColor('Green')        // Returns: ['S', 'M']
getSizesForColor('Blue')         // Returns: ['S', 'M', 'L', 'XL']

// See all selected colors
getAllSelectedColors()           // Returns: ['Green', 'Blue', 'Red']

// See all available sizes
getAllAvailableSizes()           // Returns: ['XS', 'S', 'M', 'L', 'XL', '2XL', '3XL', ...]

// Get serialized stock data
window.productStockData          // View the data structure
serializeStockData()             // Convert to JSON array

// Validate
validateStockQuantities()        // Check if all combos have qty
```

## Technical Details

### Data Structure Change

**Old** (not color-specific):
```
All colors get all sizes
Green: S, M, L, XL
Blue:  S, M, L, XL
```

**New** (per-color independent):
```
Each color picks its own sizes
Green: S, M (only these)
Blue:  S, M, L, XL (different selection)
```

### Code Functions

- `getAllAvailableSizes()` - Gets pool of all sizes (predefined + custom)
- `getAllSelectedColors()` - Gets colors user picked
- `getSizesForColor(color)` - Gets sizes user picked for a specific color
- `renderColorSizeSelectors()` - Renders the per-color UI
- `updateStockInputs()` - Generates stock table based on per-color selections
- `validateStockQuantities()` - Validates each color has sizes & all combos have qty

### HTML Changes

- Swapped positions of sizes and colors sections
- Colors now come first (users select colors)
- New "Sizes per Color" section under colors
- Each size checkbox has `data-color-size="${color}"` attribute
- Custom sizes input has `onchange="updateStockInputs()"`

### Database Ready

When form submits, stock data is serialized as JSON:
```json
[
  {"size": "S", "color": "Green", "stock_qty": 100},
  {"size": "M", "color": "Green", "stock_qty": 50},
  {"size": "S", "color": "Blue", "stock_qty": 200},
  ...
]
```

Backend receives `stock_data` with array of combinations based on what was actually selected!

## Notes

- ✨ No more unnecessary combinations
- ✨ True flexibility per color
- ✨ Same validation as before
- ✨ Production ready
