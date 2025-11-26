// Unified Cart System for Varon - Uses database backend for logged-in users

const VaronCart = {
  // Show notification message
  showMessage(message, type = 'success') {
    // Create toast element if it doesn't exist
    let toast = document.getElementById('cart-toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'cart-toast';
      toast.className = 'cart-toast';
      document.body.appendChild(toast);
    }
    
    // Set message and type
    toast.textContent = message;
    toast.className = `cart-toast cart-toast-${type} cart-toast-show`;
    
    // Auto hide after 3 seconds
    setTimeout(() => {
      toast.classList.remove('cart-toast-show');
    }, 3000);
  },
  
  // Add item to cart
  async add(productId, quantity = 1, variantId = null, color = null, size = null) {
    try {
      // Ensure productId is an integer
      const productIdInt = parseInt(productId, 10);
      const quantityInt = parseInt(quantity, 10);
      const variantIdInt = variantId ? parseInt(variantId, 10) : null;
      
      console.log('Adding to cart:', { productIdInt, quantityInt, variantIdInt, color, size });
      
      const response = await fetch('/api/cart/add', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          product_id: productIdInt,
          quantity: quantityInt,
          variant_id: variantIdInt
        })
      });
      
      const data = await response.json();
      console.log('Add to cart response:', data);
      
      if (data.success) {
        await this.updateBadge();
        this.showMessage(`✓ Added ${quantityInt} item(s) to cart`, 'success');
        return true;
      } else {
        console.error('Failed to add to cart:', data.error);
        this.showMessage(data.error || 'Failed to add to cart', 'error');
      }
      return false;
    } catch (error) {
      console.error('Error adding to cart:', error);
      this.showMessage('Error adding to cart', 'error');
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
    
    const badges = document.querySelectorAll('#cartCount, #cartCountSidebar, #floatingCartBadge');
    badges.forEach(badge => {
      if (badge) badge.textContent = count;
    });
    
    return count;
  },
  
  // Get total price
  async getTotal() {
    const items = await this.get();
    return items.reduce((sum, item) => sum + (parseFloat(item.price) * parseInt(item.quantity)), 0);
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

// Add CSS for toast notifications
if (typeof document !== 'undefined') {
  const style = document.createElement('style');
  style.textContent = `
    .cart-toast {
      position: fixed;
      top: 100px;
      right: 32px;
      background: #ffffff;
      color: #000000;
      padding: 16px 24px;
      border-radius: 12px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.15);
      z-index: 9999;
      font-size: 14px;
      font-weight: 500;
      opacity: 0;
      transform: translateX(400px);
      transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
      pointer-events: none;
      border: 1px solid #e5e7eb;
      min-width: 250px;
    }
    .cart-toast-show {
      opacity: 1;
      transform: translateX(0);
      pointer-events: all;
    }
    .cart-toast-success {
      background: #000000;
      color: #ffffff;
      border-color: #000000;
    }
    .cart-toast-error {
      background: #ef4444;
      color: #ffffff;
      border-color: #dc2626;
    }
    @media (max-width: 768px) {
      .cart-toast {
        top: 80px;
        right: 16px;
        left: 16px;
        min-width: auto;
        text-align: center;
      }
    }
  `;
  document.head.appendChild(style);
}
