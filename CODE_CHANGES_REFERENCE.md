# 🔧 CODE CHANGES REFERENCE

**File:** `templates/pages/SellerDashboard.html`  
**Total Changes:** 4 major sections  

---

## CHANGE 1: HTML - Size Selection Section (Lines ~430-520)

### Before
```html
<div style="border: 1px solid var(--line); border-radius: 8px; padding: 16px; background: #fafafa;" id="sizesSection">
  <h3 style="margin: 0 0 12px; font-size: 16px;">Available Sizes per Color *</h3>
  <small style="color: var(--muted); font-size: 12px; display: block; margin-bottom: 12px;">Sizes will be specific to each selected color</small>
  
  <!-- Clothing Sizes (default) -->
  <div id="clothingSizes" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(80px, 1fr)); gap: 10px;">
    <label style="display: flex; align-items: center; cursor: pointer;">
      <input type="checkbox" name="sizes" value="XS" style="margin-right: 6px;" onchange="updateStockInputs()">
      <span>XS</span>
    </label>
    <!-- ... rest of sizes ... -->
  </div>
  
  <div style="margin-top: 12px;">
    <label style="display: block; margin-bottom: 6px; font-weight: 500;">Add Custom Size(s)</label>
    <input type="text" id="custom-sizes" placeholder="e.g. 4XL, 5XL, 28W, 32W (comma-separated)" 
      style="width: 100%; padding: 8px; border: 1px solid var(--line); border-radius: 6px;" 
      oninput="updateStockInputs()" 
      onchange="updateStockInputs()" 
      onblur="updateStockInputs()">
    <small style="color: var(--muted); font-size: 11px; display: block; margin-top: 4px;">These sizes will be applied to all selected colors</small>
  </div>
</div>
```

### After
```html
<div style="border: 1px solid var(--line); border-radius: 8px; padding: 16px; background: #fafafa;" id="sizesSection">
  <h3 style="margin: 0 0 12px; font-size: 16px;">Available Sizes per Color *</h3>
  <small style="color: var(--muted); font-size: 12px; display: block; margin-bottom: 12px;">Select a color tab above, then choose sizes for that specific color</small>
  
  <!-- Per-Color Sizes Container -->
  <div id="perColorSizesContainer" style="display: none;">
    <!-- Clothing Sizes (default) -->
    <div id="clothingSizes" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(80px, 1fr)); gap: 10px;">
      <label style="display: flex; align-items: center; cursor: pointer;">
        <input type="checkbox" class="color-size-checkbox" value="XS" style="margin-right: 6px;" onchange="updateSizesForColor()">
        <span>XS</span>
      </label>
      <!-- ... rest of sizes (changed to class="color-size-checkbox" and onchange="updateSizesForColor()") ... -->
    </div>
    
    <!-- Shoe Sizes (hidden by default) - US Sizes -->
    <div id="shoeSizes" style="display: none; grid-template-columns: repeat(auto-fill, minmax(70px, 1fr)); gap: 10px;">
      <!-- ... shoe sizes with class="color-size-checkbox" ... -->
    </div>
    
    <div style="margin-top: 12px;">
      <label style="display: block; margin-bottom: 6px; font-weight: 500;">Add Custom Size(s) for <span id="current-color-size-label" style="font-weight: 600; color: #3b82f6;">this color</span></label>
      <input type="text" id="custom-sizes-per-color" placeholder="e.g. 36, 37, 38 (comma-separated)" 
        style="width: 100%; padding: 8px; border: 1px solid var(--line); border-radius: 6px;" 
        oninput="updateSizesForColor()" 
        onchange="updateSizesForColor()" 
        onblur="updateSizesForColor()">
      <small style="color: var(--muted); font-size: 11px; display: block; margin-top: 4px;">Custom sizes for this color only</small>
    </div>
  </div>
  
  <!-- Placeholder when no color selected -->
  <p id="sizesPlaceholder" style="color: var(--muted); font-style: italic; margin: 20px 0;">👉 Select a color tab above to add sizes for that color</p>
</div>
```

### Key Changes:
- ✅ Added `perColorSizesContainer` wrapper (display: none by default)
- ✅ Changed `name="sizes"` to `class="color-size-checkbox"`
- ✅ Changed `onchange="updateStockInputs()"` to `onchange="updateSizesForColor()"`
- ✅ Changed `id="custom-sizes"` to `id="custom-sizes-per-color"`
- ✅ Updated label text (now per-color specific)
- ✅ Added `sizesPlaceholder` message
- ✅ Updated help text

---

## CHANGE 2: JavaScript - Global Variables (Line ~1240)

### Before
```javascript
let colorSizesMapping = {};
let selectedColor = null;
```

### After
```javascript
let colorSizesMapping = {}; // { Red: ['S', 'M', 'L'], Black: ['M', 'L', 'XL'] }
let selectedColor = null;
let sizeType = 'clothing'; // 'clothing' or 'shoes'
```

### Key Changes:
- ✅ Added comment explaining colorSizesMapping structure
- ✅ Added sizeType variable for future enhancement

---

## CHANGE 3: JavaScript - selectColor() Function (Line ~1300)

### Before
```javascript
function selectColor(color) {
  console.log(`Selected color: ${color}`);
  selectedColor = color;
  
  // Update hidden input
  document.getElementById('selected-color').value = color;
  
  // Update tab appearances
  document.querySelectorAll('.color-tab').forEach(tab => {
    const tabColor = tab.textContent.trim();
    const isSelected = tabColor === color;
    tab.style.borderColor = isSelected ? '#3b82f6' : '#ddd';
    tab.style.background = isSelected ? '#3b82f6' : '#fff';
    tab.style.color = isSelected ? '#fff' : '#0a0a0a';
    tab.style.fontWeight = isSelected ? '600' : '500';
  });
  
  // Update the color name in stock table title
  document.getElementById('stock-table-color').textContent = color;
  
  // Update stock inputs for this color
  updateStockInputs();
}
```

### After
```javascript
function selectColor(color) {
  console.log(`Selected color: ${color}`);
  selectedColor = color;
  
  // Update hidden input
  document.getElementById('selected-color').value = color;
  
  // Update tab appearances
  document.querySelectorAll('.color-tab').forEach(tab => {
    const tabColor = tab.textContent.trim();
    const isSelected = tabColor === color;
    tab.style.borderColor = isSelected ? '#3b82f6' : '#ddd';
    tab.style.background = isSelected ? '#3b82f6' : '#fff';
    tab.style.color = isSelected ? '#fff' : '#0a0a0a';
    tab.style.fontWeight = isSelected ? '600' : '500';
  });
  
  // Update the color name in stock table title
  document.getElementById('stock-table-color').textContent = color;
  
  // Show sizes section and update for this color
  updateSizesForColor();
  
  // Update stock inputs for this color
  updateStockInputs();
}
```

### Key Changes:
- ✅ Added call to `updateSizesForColor()`
- ✅ Moved before `updateStockInputs()`
- ✅ Now calls new function to load per-color sizes

---

## CHANGE 4: JavaScript - NEW Function updateSizesForColor() (Line ~1331)

### Added (New Function)
```javascript
function updateSizesForColor() {
  console.log('Updating sizes for color:', selectedColor);
  
  const placeholder = document.getElementById('sizesPlaceholder');
  const container = document.getElementById('perColorSizesContainer');
  
  // Show placeholder if no color selected
  if (!selectedColor) {
    if (placeholder) placeholder.style.display = 'block';
    if (container) container.style.display = 'none';
    return;
  }
  
  // Show sizes container
  if (placeholder) placeholder.style.display = 'none';
  if (container) container.style.display = 'block';
  
  // Update the label to show current color
  document.getElementById('current-color-size-label').textContent = selectedColor;
  
  // Load previously selected sizes for this color
  const previousSizes = colorSizesMapping[selectedColor] || [];
  console.log(`Loading sizes for ${selectedColor}:`, previousSizes);
  
  // Update all color-size checkboxes
  document.querySelectorAll('.color-size-checkbox').forEach(checkbox => {
    checkbox.checked = previousSizes.includes(checkbox.value);
  });
  
  // Clear custom sizes input for this color (will be populated if exists)
  const customSizesInput = document.getElementById('custom-sizes-per-color');
  if (customSizesInput) {
    customSizesInput.value = '';
  }
  
  // Update stock table with new sizes
  updateStockInputs();
}
```

### Functionality:
- ✅ Shows/hides size container based on color selection
- ✅ Loads previously selected sizes for this color
- ✅ Updates checkbox states
- ✅ Updates label with current color
- ✅ Calls updateStockInputs() to refresh stock table

---

## CHANGE 5: JavaScript - updateStockInputs() Function (Line ~1362)

### Before
```javascript
function updateStockInputs() {
  console.log('Updating stock inputs for color:', selectedColor);
  
  const sizes = [];
  
  // Get checked sizes
  const checkedSizes = Array.from(document.querySelectorAll('input[name="sizes"]:checked')).map(cb => cb.value);
  sizes.push(...checkedSizes);
  
  // Get custom sizes
  const customSizesInput = document.getElementById('custom-sizes');
  const customSizes = customSizesInput && customSizesInput.value.trim() 
    ? customSizesInput.value.split(',').map(s => s.trim()).filter(s => s)
    : [];
  
  if (checkedSizes.length === 0 && customSizes.length > 0) {
    sizes.push(...customSizes);
    console.log('Using only custom sizes:', customSizes);
  } else {
    sizes.push(...customSizes);
  }
  
  console.log('Sizes for stock table:', sizes);
  
  const stockInputsDiv = document.getElementById('stock-inputs');
  
  if (!stockInputsDiv) {
    console.log('Stock inputs div not found');
    return;
  }
  
  // If no color selected or no sizes selected, show placeholder
  if (!selectedColor || sizes.length === 0) {
    stockInputsDiv.innerHTML = '<p style="color: var(--muted); font-style: italic;">👉 Select sizes above and click on a color to set stock</p>';
    return;
  }
  
  // ... rest of function generates stock table ...
}
```

### After
```javascript
function updateStockInputs() {
  console.log('Updating stock inputs for color:', selectedColor);
  
  const sizes = [];
  
  // Get checked sizes from per-color checkboxes
  const checkedSizes = Array.from(document.querySelectorAll('.color-size-checkbox:checked')).map(cb => cb.value);
  sizes.push(...checkedSizes);
  
  // Get custom sizes for this color
  const customSizesInput = document.getElementById('custom-sizes-per-color');
  const customSizes = customSizesInput && customSizesInput.value.trim() 
    ? customSizesInput.value.split(',').map(s => s.trim()).filter(s => s)
    : [];
  
  sizes.push(...customSizes);
  
  console.log('Sizes for stock table:', sizes);
  
  const stockInputsDiv = document.getElementById('stock-inputs');
  
  if (!stockInputsDiv) {
    console.log('Stock inputs div not found');
    return;
  }
  
  // If no color selected or no sizes selected, show placeholder
  if (!selectedColor || sizes.length === 0) {
    stockInputsDiv.innerHTML = '<p style="color: var(--muted); font-style: italic;">👉 Select sizes for this color above to set stock</p>';
    return;
  }
  
  // Save existing stock values before regenerating
  const existingValues = {};
  const existingInputs = stockInputsDiv.querySelectorAll('input[type="number"]');
  existingInputs.forEach(input => {
    if (input.value && input.value !== '0') {
      existingValues[input.name] = input.value;
    }
  });
  console.log('Preserved stock values:', existingValues);
  
  // Store selected sizes in colorSizesMapping for this color
  colorSizesMapping[selectedColor] = checkedSizes;
  console.log('Updated colorSizesMapping:', colorSizesMapping);
  
  // Generate stock table for ONLY the selected color
  let html = '<div style="max-height: 400px; overflow-y: auto;">';
  html += '<table style="width: 100%; border-collapse: collapse;">';
  html += '<thead><tr style="background: #e5e7eb; position: sticky; top: 0;"><th style="padding: 8px; text-align: left; border: 1px solid var(--line);">Size</th><th style="padding: 8px; text-align: left; border: 1px solid var(--line);">Color</th><th style="padding: 8px; text-align: left; border: 1px solid var(--line);">Stock Qty</th><th style="padding: 8px; text-align: center; border: 1px solid var(--line); width: 50px;">Action</th></tr></thead>';
  html += '<tbody>';
  
  sizes.forEach(size => {
    // IMPORTANT: Only create stock input for the selected color
    const safeName = `stock_${size.replace(/[^a-zA-Z0-9]/g, '_')}_${selectedColor.replace(/[^a-zA-Z0-9]/g, '_')}`;
    const stockValue = existingValues[safeName] || '0';
    console.log(`Creating stock input for selected color: size="${size}", color="${selectedColor}", name="${safeName}", value="${stockValue}"`);
    html += `<tr style="transition: background-color 0.2s;" onmouseover="this.style.backgroundColor='#f3f4f6';" onmouseout="this.style.backgroundColor='';">
      <td style="padding: 8px; border: 1px solid var(--line); font-weight: 500;">${size}</td>
      <td style="padding: 8px; border: 1px solid var(--line); font-weight: 500;">${selectedColor}</td>
      <td style="padding: 8px; border: 1px solid var(--line);">
        <input type="number" name="${safeName}" min="0" value="${stockValue}" required 
          style="width: 80px; padding: 6px; border: 1px solid var(--line); border-radius: 4px;">
      </td>
      <td style="padding: 8px; border: 1px solid var(--line); text-align: center;">
        <button type="button" onclick="removeStockRow(this)" style="background: none; border: none; cursor: pointer; color: #ef4444; font-size: 18px; padding: 4px 8px; transition: transform 0.2s;" title="Remove this size-color combination" onmouseover="this.style.transform='scale(1.2)';" onmouseout="this.style.transform='scale(1)';">✕</button>
      </td>
    </tr>`;
  });
  
  html += '</tbody></table></div>';
  stockInputsDiv.innerHTML = html;
  console.log(`Stock table generated for color "${selectedColor}" with ${sizes.length} sizes`);
}
```

### Key Changes:
- ✅ Changed selector from `input[name="sizes"]` to `.color-size-checkbox`
- ✅ Changed input ID from `custom-sizes` to `custom-sizes-per-color`
- ✅ Removed complex size logic (simplified)
- ✅ Added colorSizesMapping update: `colorSizesMapping[selectedColor] = checkedSizes`
- ✅ Updated placeholder message text
- ✅ Added value preservation across color switches
- ✅ Only generates stock inputs for selectedColor

---

## CHANGE 6: JavaScript - submitProductViaAJAX() Function (Line ~1168)

### Before
```javascript
function submitProductViaAJAX() {
  const form = document.getElementById('addProductForm');
  
  // Validate form before submitting
  if (!form.checkValidity()) {
    alert('❌ Please fill in all required fields correctly');
    return;
  }
  
  // Copy custom sizes and colors to hidden inputs BEFORE creating FormData
  submitCustomValues();
  
  // Now create FormData after custom values are copied
  const formData = new FormData(form);
  
  // Debug: Log all form data being sent
  console.log('=== Form Data Being Sent ===');
  for (let [key, value] of formData.entries()) {
    if (key.startsWith('stock_') || key.includes('size') || key.includes('color')) {
      console.log(`${key}: ${value}`);
    }
  }
  console.log('===========================');
  
  // Show loading state
  const submitBtn = document.querySelector('button[onclick="confirmAddProduct()"]');
  const originalText = submitBtn.textContent;
  submitBtn.disabled = true;
  submitBtn.textContent = '⏳ Adding Product...';
  
  console.log('Submitting product form...');
  
  fetch('/seller/add-product', {
    method: 'POST',
    body: formData
  })
  .then(response => {
    console.log('Response status:', response.status);
    return response.json().then(data => ({
      status: response.status,
      data: data
    }));
  })
  .then(({ status, data }) => {
    console.log('Response data:', data);
    submitBtn.disabled = false;
    submitBtn.textContent = originalText;
    
    if (status === 200 && data.success) {
      // Success - product added to pending approval
      alert('✅ Product submitted successfully!\n\nYour product has been added to the admin queue for approval.\n\nOnce approved, it will appear in your store.');
      // Clear form
      form.reset();
      // Reset category to trigger size/color sections
      document.getElementById('categorySelect').value = '';
      toggleSizeColorSections();
      // Load products list
      loadPage('products');
    } else if (status === 400) {
      // Validation error
      alert('❌ Validation Error:\n\n' + data.error);
    } else if (data.error) {
      // Server error
      alert('❌ Error adding product:\n\n' + data.error);
    } else {
      alert('❌ Unexpected error occurred. Please try again.');
    }
  })
  .catch(error => {
    submitBtn.disabled = false;
    submitBtn.textContent = originalText;
    console.error('Request error:', error);
    alert('❌ Network error: ' + error.message + '\n\nPlease check your connection and try again.');
  });
}
```

### After
```javascript
function submitProductViaAJAX() {
  const form = document.getElementById('addProductForm');
  
  // Validate form before submitting
  if (!form.checkValidity()) {
    alert('❌ Please fill in all required fields correctly');
    return;
  }
  
  // Copy custom sizes and colors to hidden inputs BEFORE creating FormData
  submitCustomValues();
  
  // Now create FormData after custom values are copied
  const formData = new FormData(form);
  
  // Add colorSizesMapping as JSON
  formData.append('color_sizes_mapping', JSON.stringify(colorSizesMapping));
  console.log('Color sizes mapping being sent:', colorSizesMapping);
  
  // Debug: Log all form data being sent
  console.log('=== Form Data Being Sent ===');
  for (let [key, value] of formData.entries()) {
    if (key.startsWith('stock_') || key.includes('size') || key.includes('color') || key === 'color_sizes_mapping') {
      console.log(`${key}: ${value}`);
    }
  }
  console.log('===========================');
  
  // Show loading state
  const submitBtn = document.querySelector('button[onclick="confirmAddProduct()"]');
  const originalText = submitBtn.textContent;
  submitBtn.disabled = true;
  submitBtn.textContent = '⏳ Adding Product...';
  
  console.log('Submitting product form...');
  
  fetch('/seller/add-product', {
    method: 'POST',
    body: formData
  })
  .then(response => {
    console.log('Response status:', response.status);
    return response.json().then(data => ({
      status: response.status,
      data: data
    }));
  })
  .then(({ status, data }) => {
    console.log('Response data:', data);
    submitBtn.disabled = false;
    submitBtn.textContent = originalText;
    
    if (status === 200 && data.success) {
      // Success - product added to pending approval
      alert('✅ Product submitted successfully!\n\nYour product has been added to the admin queue for approval.\n\nOnce approved, it will appear in your store.');
      // Clear form
      form.reset();
      // Reset category to trigger size/color sections
      document.getElementById('categorySelect').value = '';
      toggleSizeColorSections();
      // Reset color/size mappings
      colorSizesMapping = {};
      selectedColor = null;
      // Load products list
      loadPage('products');
    } else if (status === 400) {
      // Validation error
      alert('❌ Validation Error:\n\n' + data.error);
    } else if (data.error) {
      // Server error
      alert('❌ Error adding product:\n\n' + data.error);
    } else {
      alert('❌ Unexpected error occurred. Please try again.');
    }
  })
  .catch(error => {
    submitBtn.disabled = false;
    submitBtn.textContent = originalText;
    console.error('Request error:', error);
    alert('❌ Network error: ' + error.message + '\n\nPlease check your connection and try again.');
  });
}
```

### Key Changes:
- ✅ Added `formData.append('color_sizes_mapping', JSON.stringify(colorSizesMapping))`
- ✅ Added logging for color_sizes_mapping
- ✅ Added reset of colorSizesMapping and selectedColor after success
- ✅ Now logs color_sizes_mapping in debug section

---

## Summary of Changes

| Component | Type | Details |
|-----------|------|---------|
| **HTML** | Restructure | Per-color sizes container, new checkbox class |
| **Variables** | Add | colorSizesMapping comment, sizeType variable |
| **selectColor()** | Modify | Added updateSizesForColor() call |
| **updateSizesForColor()** | NEW | Loads/displays sizes per color |
| **updateStockInputs()** | Modify | Uses .color-size-checkbox, stores in mapping |
| **submitProductViaAJAX()** | Modify | Sends colorSizesMapping JSON |

**Total Lines Changed:** ~200 lines across 6 sections

---

