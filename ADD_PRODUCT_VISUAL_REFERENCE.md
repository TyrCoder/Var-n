# Add Product Page - Quick Visual Reference

## 📐 Page Layout Structure

```
┌─────────────────────────────────────────────────────┐
│  📦 Add New Product                                 │
└─────────────────────────────────────────────────────┘

┌─ SECTION 1: BASIC INFORMATION ─────────────────────┐
│  [1] Basic Information                              │
│  ├─ Product Name          [__________________]     │
│  ├─ Description           [____________________]   │
│  └─ Category/Genre        [▼ Select category]     │
└─────────────────────────────────────────────────────┘

┌─ SECTION 2: PRODUCT IMAGES ────────────────────────┐
│  [2] Product Images                                 │
│  ├─ Upload Area (Drag-Drop Styled)                │
│  └─ Preview Grid (Auto-generated)                 │
└─────────────────────────────────────────────────────┘

┌─ SECTION 3: PRICING & INVENTORY ──────────────────┐
│  [3] Pricing & Inventory                            │
│  ├─ Price (₱)             [__________]            │
│  └─ SKU                   [__________]            │
└─────────────────────────────────────────────────────┘

┌─ SECTION 4 (CONDITIONAL) ─────────────────────────┐

IF GROOMING PRODUCTS:
│  [4] Product Ingredients *                         │
│  ├─ Ingredient Table                              │
│  │  ├─ Ingredient Name | % | Remove               │
│  │  ├─ [_________]     |[_]| [Remove]             │
│  │  └─ [_________]     |[_]| [Remove]             │
│  ├─ [+ Add Ingredient] Button                     │
│  └─ Min 1 ingredient required                     │

IF APPAREL/SHOES:
│  [4] Product Variants                              │
│  ├─ Colors Section                                │
│  │  ├─ Predefined: ■ Black ■ White ■ Red ...     │
│  │  └─ Custom: [________________ ]               │
│  ├─ Color Tabs                                    │
│  │  ├─ [Red] [Blue] [Green] ...                   │
│  └─ Sizes Section                                 │
│     ├─ CLOTHING: ☐XS ☐S ☐M ☐L ☐XL ☐2XL ☐3XL   │
│     ├─ SHOES: ☐5 ☐6 ☐7 ☐8 ☐9 ☐10 ☐11 ☐12 ☐13  │
│     └─ Custom: [_______________ ]                │

└─────────────────────────────────────────────────────┘

┌─ SECTION 5 (FOR NON-GROOMING ONLY) ───────────────┐
│  [5] Stock Quantities                               │
│  ├─ Stock per Size in [Selected Color]             │
│  └─ Stock Table                                    │
│     ├─ Size | Color | Quantity | Action           │
│     ├─ M    | Red   | [____]   | ✕               │
│     ├─ L    | Red   | [____]   | ✕               │
│     └─ XL   | Red   | [____]   | ✕               │
└─────────────────────────────────────────────────────┘

┌─ SUBMIT BUTTONS ──────────────────────────────────┐
│  [✓ Add Product]  [Cancel]                         │
└─────────────────────────────────────────────────────┘
```

---

## 🎨 Color Usage Reference

| Element | Color | Usage |
|---------|-------|-------|
| Section Badges (Step 1-5) | #3b82f6 (Blue) | Primary information |
| Grooming Badge (Step 4) | #10b981 (Green) | Special category |
| Stock Badge (Step 5) | #f59e0b (Amber) | Inventory focus |
| Divider Lines | #e5e7eb (Light Gray) | Section separation |
| Hover States | #f3f4f6 (Very Light) | Interactive feedback |
| Text - Headers | #0a0a0a (Black) | Primary labels |
| Text - Muted | #777 (Gray) | Helper text |

---

## 🔄 Category Detection Logic

### Flow Diagram

```
User Selects Category
        │
        ├──→ Check category.slug or category.name
        │
        ├─────────────────────────────────────────┐
        │                                         │
        ▼                                         ▼
    "grooming" ∈ text?               "shoe"/"footwear" ∈ text?
        │                                         │
        ├─→ YES ──┐                          ├─→ YES ──┐
        │         │                          │         │
        ├─→ NO ───┼──────────────────────────┼─────────┼─┐
        │         │                          │         │ │
        ▼         ▼                          ▼         ▼ ▼
    DEFAULT   GROOMING MODE            OTHER    SHOE MODE
    MODE      (Apparel/etc)             MODE     (Shoes)
    
    ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
    │ Show:    │  │ Show:    │  │ Show:    │  │ Show:    │
    │ - Colors │  │ Ingred.  │  │ - Colors │  │ - Colors │
    │ - Cloth  │  │          │  │ - Cloth  │  │ - Shoes  │
    │  Sizes   │  │ Hide:    │  │  Sizes   │  │  Sizes   │
    │ - Stock  │  │ - Colors │  │ - Stock  │  │ - Stock  │
    │          │  │ - Sizes  │  │          │  │          │
    │ Hide:    │  │ - Stock  │  │ Hide:    │  │ Hide:    │
    │ - Ingred │  │          │  │ - Ingred │  │ - Ingred │
    │          │  │          │  │          │  │          │
    └──────────┘  └──────────┘  └──────────┘  └──────────┘
```

---

## 📋 Form Validation Rules

### For ALL Products
- ✅ Product Name: Required, non-empty
- ✅ Category: Required
- ✅ Price: Required, > 0
- ✅ Images: Required, multiple allowed

### For GROOMING Products Only
- ✅ Ingredients: Minimum 1 required
- ✅ Each ingredient: Name required, Percentage optional
- ❌ Colors: Not shown
- ❌ Sizes: Not shown

### For APPAREL/SHOE Products
- ✅ Colors: Minimum 1 (predefined OR custom)
- ✅ Sizes: Minimum 1 per color
- ✅ Stock: Required for each size-color combo
- ❌ Ingredients: Not shown

---

## 🎯 Interactive Behaviors

### When Selecting a Color

```
User clicks color tab "Red"
        │
        ▼
selectColor("Red") function
        │
        ├─ Update tab appearance (highlight)
        ├─ Show size checkboxes
        ├─ Restore previously saved sizes for Red
        ├─ Show custom sizes input for Red
        └─ Regenerate stock table with Red's sizes
```

### When Selecting/Unselecting Sizes

```
User clicks size checkbox
        │
        ▼
updateStockInputs() function
        │
        ├─ Collect selected sizes for current color
        ├─ Preserve existing stock values
        ├─ Regenerate stock input table
        └─ Update colorSizesMapping[color] = [sizes]
```

### When Adding Ingredients

```
User clicks "+ Add Ingredient"
        │
        ▼
addIngredientRow() function
        │
        ├─ Create new table row
        ├─ Add name and percentage inputs
        ├─ Add Remove button
        └─ Call updateIngredientsField()
            │
            ▼
        Serialize to hidden textarea as JSON:
        {name: "ingredient_name", percentage: 15}
```

---

## 📊 State Management

### Color-Sizes Mapping
```javascript
colorSizesMapping = {
  "Red": ["S", "M", "L", "36"],
  "Blue": ["M", "L", "XL"],
  "Black": ["XS", "S", "M", "L", "XL", "2XL"]
}
```

### Stock Values Preservation
```
When switching colors:
1. Save current color's stock inputs
2. Clear stock table
3. Load new color's stock inputs from map
4. If not found, default to 0
5. Display in table
```

---

## 🧪 Test Checklist

### Grooming Product Test
- [ ] Select "Grooming Products" category
- [ ] Colors section disappears
- [ ] Sizes section disappears
- [ ] Ingredients section appears
- [ ] Can add/remove ingredients
- [ ] Form validates ingredients required
- [ ] Other sections still visible (name, description, images, price)

### Apparel Product Test
- [ ] Select "Apparel" or clothing category
- [ ] Colors section appears
- [ ] Clothing sizes appear (XS-4XL)
- [ ] Shoe sizes don't appear
- [ ] Ingredients section hidden
- [ ] Color tabs work properly
- [ ] Stock table updates dynamically
- [ ] Sizes preserved when switching colors

### Shoe Product Test
- [ ] Select "Shoes" or "Footwear" category
- [ ] Colors section appears
- [ ] Shoe sizes appear (5-13)
- [ ] Clothing sizes don't appear
- [ ] Ingredients section hidden
- [ ] Color tabs work properly
- [ ] Stock table updates dynamically
- [ ] Sizes preserved when switching colors

### Category Switching Test
- [ ] Switch from Apparel → Shoes → Grooming → Apparel
- [ ] Layout updates instantly each time
- [ ] No console errors
- [ ] Form state preserved appropriately

---

## 🔍 Console Logging

For debugging, check console messages when:

1. **Category changes:** `🔄 toggleSizeColorSections() CALLED`
2. **Detection result:** `🔍 Category detection: { isGrooming, isShoe, categoryText }`
3. **Mode selection:** 
   - Grooming: `✅ GROOMING PRODUCT MODE`
   - Shoes: `👟 SHOE PRODUCT MODE`
   - Apparel: `👕 OTHER PRODUCT MODE`
4. **Complete:** `✅ toggleSizeColorSections() COMPLETE`

---

## 📱 Responsive Behavior

```
Desktop (1200px+)
├─ All sections in single column
├─ Full width form (max 900px)
└─ All fields clearly visible

Tablet (768px - 1199px)
├─ Same single column
├─ Slightly reduced margins
└─ All sections stack vertically

Mobile (< 768px)
├─ Full width with small margins
├─ Touch-friendly button sizes
├─ Color swatches stack 2 per row
└─ Size checkboxes stack 2 per row
```

---

## 🎓 User Guidance

### For Sellers Adding Grooming Products
1. **Fill Basic Info** - Name, description, select "Grooming Products"
2. **Add Images** - Upload product photos
3. **Set Price** - Selling price
4. **Add Ingredients** - List at least 1 ingredient
5. **Submit** - Product sent for approval

### For Sellers Adding Apparel
1. **Fill Basic Info** - Name, description, select category
2. **Add Images** - Upload product photos
3. **Set Price** - Selling price
4. **Select Colors** - Check predefined or type custom
5. **Select Sizes** - After choosing a color, select available sizes
6. **Set Stock** - Enter quantity for each size-color combo
7. **Submit** - Product sent for approval

### For Sellers Adding Shoes
1. **Fill Basic Info** - Name, description, select "Shoes" category
2. **Add Images** - Upload product photos
3. **Set Price** - Selling price
4. **Select Colors** - Check predefined or type custom
5. **Select Shoe Sizes** - After choosing a color, select shoe sizes (5-13)
6. **Set Stock** - Enter quantity for each size-color combo
7. **Submit** - Product sent for approval

---

**Last Updated:** November 27, 2025  
**Quick Reference Version:** 1.0
