# Seller Product Add Features

## Overview
The seller dashboard now has dynamic size and color selection based on product category.

## Features Implemented

### 1. **Shoe Category - Shoe Sizes**
When "Shoes & Footwear" is selected:
- Shows shoe sizes: 6, 7, 8, 9, 10, 11, 12, 13
- Hides clothing sizes (XS, S, M, L, XL, 2XL, 3XL)
- Shows color options
- Custom size placeholder changes to: "e.g. 5.5, 6.5, 7.5, 14, 15 (comma-separated)"

### 2. **Grooming Category - No Sizes/Colors**
When "Grooming Products" is selected:
- Hides size selection completely
- Hides color selection completely
- Hides stock per size & color section
- Shows "Ingredients" field instead (required)
- Sellers can list ingredients for grooming products

### 3. **Other Categories - Clothing Sizes**
When any other category is selected (shirts, pants, jackets, etc.):
- Shows clothing sizes: XS, S, M, L, XL, 2XL, 3XL
- Hides shoe sizes
- Shows color options
- Custom size placeholder: "e.g. 4XL, 5XL, 28W, 32W (comma-separated)"

### 4. **Dynamic Stock Input Table**
- When sizes and colors are selected, a table automatically appears
- Shows all combinations of selected sizes and colors
- Each combination has a stock quantity input field
- Table updates in real-time as sizes/colors are checked/unchecked
- Custom sizes and colors are included in the table

## Example Stock Table

When Size M, L and Colors Black, White are selected:

| Size | Color | Stock Qty |
|------|-------|-----------|
| M    | Black | [input]   |
| M    | White | [input]   |
| L    | Black | [input]   |
| L    | White | [input]   |

## How It Works

1. **Category Selection**: Seller selects a category from dropdown
2. **Size Options Change**: 
   - Shoes → Show shoe sizes (6-13)
   - Grooming → Hide sizes/colors, show ingredients
   - Others → Show clothing sizes (XS-3XL)
3. **Select Sizes & Colors**: Seller checks applicable sizes and colors
4. **Stock Table Appears**: Table automatically generates with all size-color combinations
5. **Enter Stock**: Seller enters stock quantity for each combination
6. **Submit**: All data is sent to admin for approval

## Technical Details

- Uses JavaScript `toggleSizeColorSections()` function
- Triggered on category dropdown change
- `updateStockInputs()` function generates dynamic stock table
- All size/color checkboxes have `onchange="updateStockInputs()"` to update table in real-time
- Custom sizes and colors are merged with selected checkboxes

## Benefits

1. **Better UX**: Sellers only see relevant options for their product type
2. **Accurate Inventory**: Stock is tracked per size-color combination
3. **Flexible**: Custom sizes/colors can be added for unique products
4. **Organized**: Clear table view of all inventory combinations
5. **Category-Specific**: Grooming products have ingredients instead of sizes/colors

