# 🧴 Ingredients Entry Quick Start

## In 30 Seconds

### What You Do:
1. **Type** your ingredients in this format: `Ingredient Name: Percentage`
2. **Click** the blue "Parse & Add Ingredients" button
3. **Done!** ✅

---

## Format Rules

```
CORRECT ✅              WRONG ❌
─────────────────────  ─────────────────────
Aloe Vera: 20          Aloe Vera 20
Water: 60              Water = 60
Glycerin: 15           Glycerin-15
                       Aloe Vera:20:Name

ONE PER LINE!          NOT LIKE THIS!
─────────────────────  ─────────────────────
Aloe Vera: 20          Aloe Vera: 20, Water: 60
Water: 60              All ingredients: 100
Glycerin: 15           etc.
```

---

## Examples

### Copy & Paste Ready Examples

#### 🌿 Aloe Serum
```
Aloe Vera Gel: 50
Hyaluronic Acid: 5
Glycerin: 20
Water: 25
```

#### 🌴 Coconut Oil
```
Coconut Oil: 90
Vitamin E: 5
Almond Oil: 5
```

#### 🍃 Tea Tree Hair Oil
```
Coconut Oil: 40
Tea Tree Oil: 10
Almond Oil: 30
Jojoba Oil: 20
```

#### 💛 Honey Mask
```
Honey: 40
Aloe Vera: 30
Glycerin: 20
Vitamin E: 10
```

---

## Error Messages & Fixes

### ❌ "Invalid format"
**Your input:** `Aloe Vera 20`  
**Fix:** Add colon → `Aloe Vera: 20`

### ❌ "Percentage must be 0-100"
**Your input:** `Vitamin A: 150`  
**Fix:** Use 0-100 → `Vitamin A: 15`

### ❌ "No valid ingredients found"
**Your input:** `[empty textarea]`  
**Fix:** Enter at least one ingredient

---

## Copy This Template

```
Ingredient 1: 30
Ingredient 2: 20
Ingredient 3: 25
Ingredient 4: 15
Ingredient 5: 10
```

Then:
1. Replace with your actual ingredients
2. Adjust percentages as needed
3. Click "Parse & Add Ingredients"

---

## What Happens Next?

```
Step 1️⃣: You paste ingredients
Step 2️⃣: Click Parse button
        ↓ (System validates format)
Step 3️⃣: See preview table with all ingredients
Step 4️⃣: Click "Add Product" to submit
        ↓ (Sent to backend as JSON)
Step 5️⃣: ✅ Product added successfully!
```

---

## Can I...

| Question | Answer |
|----------|--------|
| Use decimals? | ✅ Yes: `Aloe Vera: 15.5` |
| Use 0 percentage? | ✅ Yes: `Water: 0` |
| Total not 100? | ✅ Yes: Can be any total |
| Use 100+? | ✅ Yes: `Base: 150` is OK |
| Spaces around colon? | ✅ Yes: Works either way |
| Special characters? | ⚠️ Not in ingredient name |
| Edit after parse? | ✅ Click remove & re-parse |
| Copy from Excel? | ✅ If formatted correctly |

---

## Done! 🎉

Your ingredients are now ready to save!

