// Unified Cart System for Varon - Uses database backend for logged-in users

const VaronCart = {
  // Add item to cart
  async add(productId, quantity = 1, variantId = null, color = null, size = null) {
    try {
      console.log('Adding to cart:', { productId, quantity, variantId, color, size });
      const response = await fetch('/api/cart/add', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          product_id: productId,
          quantity: quantity,
          variant_id: variantId,
          color: color,
          size: size
        })
      });
      
      if (!response.ok) {
        const data = await response.json();
        console.error('Failed to add to cart:', data.error);
        this.showMessage(`Failed to add to cart: ${data.error || 'Unknown error'}`, 'error');
        return false;
      }
      
      const data = await response.json();
      console.log('Add to cart response:', data);
      
      if (data.success) {
        await this.updateBadge();
        this.showMessage('Added to cart successfully!', 'success');
        return true;
      } else {
        console.error('Failed to add to cart:', data.error);
        this.showMessage(data.error || 'Failed to add to cart', 'error');
      }
      return false;
    } catch (error) {
      console.error('Error adding to cart:', error);
      this.showMessage('Network error. Please try again.', 'error');
      return false;
    }
  },
  
  // Get all cart items
  async get() {
    try {
      const response = await fetch('/api/cart/get');
      const data = await response.json();
      console.log('Cart items fetched:', data);
      
      if (data.success) {
        // Log each item to see if variants are included
        if (data.items && data.items.length > 0) {
          console.log('Cart items details:');
          data.items.forEach((item, index) => {
            console.log(`  Item ${index + 1}:`, {
              name: item.name,
              color: item.color,
              size: item.size,
              variant_id: item.variant_id,
              cart_id: item.cart_id
            });
          });
        }
        return data.items || [];
      } else {
        console.error('Failed to get cart:', data.error);
      }
      return [];
    } catch (error) {
      console.error('Error getting cart:', error);
      return [];
    }
  },
  
  // Update item quantity
  async update(cartId, quantity) {
    try {
      const response = await fetch('/api/cart/update', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          cart_id: cartId,
          quantity: quantity
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        await this.updateBadge();
        return true;
      }
      return false;
    } catch (error) {
      console.error('Error updating cart:', error);
      return false;
    }
  },
  
  // Remove item from cart
  async remove(cartId) {
    try {
      const response = await fetch('/api/cart/remove', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({cart_id: cartId})
      });
      
      const data = await response.json();
      
      if (data.success) {
        await this.updateBadge();
        return true;
      }
      return false;
    } catch (error) {
      console.error('Error removing from cart:', error);
      return false;
    }
  },
  
  // Clear all items
  async clear() {
    try {
      const response = await fetch('/api/cart/clear', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'}
      });
      
      const data = await response.json();
      
      if (data.success) {
        await this.updateBadge();
        return true;
      }
      return false;
    } catch (error) {
      console.error('Error clearing cart:', error);
      return false;
    }
  },
  
  // Update cart badge count
  async updateBadge() {
    const items = await this.get();
    const count = items.reduce((sum, item) => sum + parseInt(item.quantity || 0), 0);
    
    const badges = document.querySelectorAll('#cartCount, #cartCountSidebar');
    badges.forEach(badge => {
      if (badge) badge.textContent = count;
    });
    
    return count;
  },
  
  // Get total price
  async getTotal() {
    const items = await this.get();
    return items.reduce((sum, item) => sum + (parseFloat(item.price) * parseInt(item.quantity)), 0);
  },
  
  // Show user feedback message
  showMessage(message, type = 'success') {
    const snackbar = document.getElementById('snackbar');
    if (snackbar) {
      snackbar.textContent = message;
      // Remove all previous classes and set fresh ones
      snackbar.className = 'snackbar';
      snackbar.classList.add('show', type);
      setTimeout(() => {
        snackbar.classList.remove('show', 'success', 'error');
      }, 3000);
    }
  }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  VaronCart.updateBadge();
});

// Export for use in other scripts
if (typeof window !== 'undefined') {
  window.VaronCart = VaronCart;
}
