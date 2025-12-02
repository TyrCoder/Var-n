/**
 * Varón Custom Notification System
 * Replaces browser alerts, confirms, and prompts with styled notifications
 */

const VaronNotifications = {
  // Show success notification
  success(message, duration = 3000) {
    this._show(message, 'success', duration);
  },

  // Show error notification
  error(message, duration = 4000) {
    this._show(message, 'error', duration);
  },

  // Show info notification
  info(message, duration = 3000) {
    this._show(message, 'info', duration);
  },

  // Show warning notification
  warning(message, duration = 3000) {
    this._show(message, 'warning', duration);
  },

  // Show confirmation dialog
  confirm(message, options = {}) {
    return new Promise((resolve) => {
      const {
        title = 'Confirm Action',
        confirmText = 'Confirm',
        cancelText = 'Cancel',
        confirmClass = 'confirm',
        type = 'confirm'
      } = options;

      const modal = this._createModal(title, message, type, {
        confirmText,
        cancelText,
        confirmClass,
        onConfirm: () => {
          this._removeModal(modal);
          resolve(true);
        },
        onCancel: () => {
          this._removeModal(modal);
          resolve(false);
        }
      });

      document.body.appendChild(modal);
      setTimeout(() => modal.classList.add('show'), 10);
    });
  },

  // Show prompt dialog
  prompt(message, options = {}) {
    return new Promise((resolve) => {
      const {
        title = 'Input Required',
        defaultValue = '',
        placeholder = '',
        confirmText = 'Submit',
        cancelText = 'Cancel',
        inputType = 'text'
      } = options;

      const modal = this._createPromptModal(title, message, {
        defaultValue,
        placeholder,
        inputType,
        confirmText,
        cancelText,
        onConfirm: (value) => {
          this._removeModal(modal);
          resolve(value);
        },
        onCancel: () => {
          this._removeModal(modal);
          resolve(null);
        }
      });

      document.body.appendChild(modal);
      setTimeout(() => {
        modal.classList.add('show');
        const input = modal.querySelector('input');
        if (input) input.focus();
      }, 10);
    });
  },

  // Internal: Show notification toast
  _show(message, type, duration) {
    const container = this._getOrCreateContainer();
    const notification = this._createNotification(message, type);
    
    container.appendChild(notification);
    setTimeout(() => notification.classList.add('show'), 10);

    if (duration > 0) {
      setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
      }, duration);
    }

    return notification;
  },

  // Internal: Get or create notification container
  _getOrCreateContainer() {
    let container = document.getElementById('varon-notifications');
    if (!container) {
      container = document.createElement('div');
      container.id = 'varon-notifications';
      container.className = 'varon-notification-container';
      document.body.appendChild(container);
    }
    return container;
  },

  // Internal: Create notification element
  _createNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `varon-notification varon-notification-${type}`;
    
    const icons = {
      success: '✓',
      error: '✕',
      warning: '⚠',
      info: 'ℹ'
    };

    notification.innerHTML = `
      <div class="varon-notification-icon">${icons[type] || 'ℹ'}</div>
      <div class="varon-notification-message">${message}</div>
      <button class="varon-notification-close" onclick="this.parentElement.remove()">×</button>
    `;

    return notification;
  },

  // Internal: Create modal dialog
  _createModal(title, message, type, options) {
    const modal = document.createElement('div');
    modal.className = 'varon-modal';
    
    const typeIcons = {
      confirm: '❓',
      warning: '⚠',
      error: '✕',
      info: 'ℹ'
    };

    modal.innerHTML = `
      <div class="varon-modal-backdrop"></div>
      <div class="varon-modal-content">
        <div class="varon-modal-header">
          <div class="varon-modal-icon varon-modal-icon-${type}">${typeIcons[type] || '❓'}</div>
          <h3>${title}</h3>
        </div>
        <div class="varon-modal-body">
          <p>${message}</p>
        </div>
        <div class="varon-modal-footer">
          <button class="varon-modal-btn varon-modal-btn-cancel">${options.cancelText}</button>
          <button class="varon-modal-btn varon-modal-btn-${options.confirmClass}">${options.confirmText}</button>
        </div>
      </div>
    `;

    modal.querySelector('.varon-modal-btn-cancel').addEventListener('click', options.onCancel);
    modal.querySelector(`.varon-modal-btn-${options.confirmClass}`).addEventListener('click', options.onConfirm);
    modal.querySelector('.varon-modal-backdrop').addEventListener('click', options.onCancel);

    return modal;
  },

  // Internal: Create prompt modal
  _createPromptModal(title, message, options) {
    const modal = document.createElement('div');
    modal.className = 'varon-modal';
    
    modal.innerHTML = `
      <div class="varon-modal-backdrop"></div>
      <div class="varon-modal-content">
        <div class="varon-modal-header">
          <div class="varon-modal-icon varon-modal-icon-info">✏</div>
          <h3>${title}</h3>
        </div>
        <div class="varon-modal-body">
          <p>${message}</p>
          <input type="${options.inputType}" class="varon-modal-input" 
                 value="${options.defaultValue}" 
                 placeholder="${options.placeholder}">
        </div>
        <div class="varon-modal-footer">
          <button class="varon-modal-btn varon-modal-btn-cancel">${options.cancelText}</button>
          <button class="varon-modal-btn varon-modal-btn-confirm">${options.confirmText}</button>
        </div>
      </div>
    `;

    const input = modal.querySelector('input');
    const confirmBtn = modal.querySelector('.varon-modal-btn-confirm');
    const cancelBtn = modal.querySelector('.varon-modal-btn-cancel');

    confirmBtn.addEventListener('click', () => options.onConfirm(input.value));
    cancelBtn.addEventListener('click', options.onCancel);
    modal.querySelector('.varon-modal-backdrop').addEventListener('click', options.onCancel);
    
    input.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        options.onConfirm(input.value);
      }
    });

    return modal;
  },

  // Internal: Remove modal
  _removeModal(modal) {
    modal.classList.remove('show');
    setTimeout(() => modal.remove(), 300);
  }
};

// Add styles dynamically
const style = document.createElement('style');
style.textContent = `
  .varon-notification-container {
    position: fixed;
    top: 90px;
    right: 20px;
    z-index: 10000;
    display: flex;
    flex-direction: column;
    gap: 12px;
    pointer-events: none;
  }

  .varon-notification {
    display: flex;
    align-items: center;
    gap: 12px;
    background: #ffffff;
    border-radius: 10px;
    padding: 14px 18px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
    min-width: 320px;
    max-width: 450px;
    opacity: 0;
    transform: translateX(400px);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    pointer-events: all;
    border-left: 4px solid #000;
  }

  .varon-notification.show {
    opacity: 1;
    transform: translateX(0);
  }

  .varon-notification-success {
    border-left-color: #10b981;
  }

  .varon-notification-error {
    border-left-color: #ef4444;
  }

  .varon-notification-warning {
    border-left-color: #f59e0b;
  }

  .varon-notification-info {
    border-left-color: #3b82f6;
  }

  .varon-notification-icon {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 16px;
    flex-shrink: 0;
  }

  .varon-notification-success .varon-notification-icon {
    background: #d1fae5;
    color: #059669;
  }

  .varon-notification-error .varon-notification-icon {
    background: #fee2e2;
    color: #dc2626;
  }

  .varon-notification-warning .varon-notification-icon {
    background: #fef3c7;
    color: #d97706;
  }

  .varon-notification-info .varon-notification-icon {
    background: #dbeafe;
    color: #2563eb;
  }

  .varon-notification-message {
    flex: 1;
    font-size: 14px;
    font-weight: 500;
    color: #0a0a0a;
    line-height: 1.5;
  }

  .varon-notification-close {
    background: none;
    border: none;
    font-size: 24px;
    color: #9ca3af;
    cursor: pointer;
    padding: 0;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 4px;
    transition: all 0.2s;
    flex-shrink: 0;
  }

  .varon-notification-close:hover {
    background: #f3f4f6;
    color: #4b5563;
  }

  .varon-modal {
    position: fixed;
    inset: 0;
    z-index: 10001;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    transition: opacity 0.3s ease;
  }

  .varon-modal.show {
    opacity: 1;
  }

  .varon-modal.show .varon-modal-content {
    transform: scale(1);
  }

  .varon-modal-backdrop {
    position: absolute;
    inset: 0;
    background: rgba(10, 10, 10, 0.5);
    backdrop-filter: blur(4px);
  }

  .varon-modal-content {
    position: relative;
    background: #ffffff;
    border-radius: 16px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    max-width: 480px;
    width: 90%;
    transform: scale(0.9);
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .varon-modal-header {
    padding: 24px 24px 16px;
    display: flex;
    align-items: center;
    gap: 16px;
    border-bottom: 1px solid #f0f0f0;
  }

  .varon-modal-icon {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    flex-shrink: 0;
  }

  .varon-modal-icon-confirm {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
    color: #ffffff;
  }

  .varon-modal-icon-warning {
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    color: #ffffff;
  }

  .varon-modal-icon-error {
    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    color: #ffffff;
  }

  .varon-modal-icon-info {
    background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
    color: #ffffff;
  }

  .varon-modal-header h3 {
    margin: 0;
    font-size: 20px;
    font-weight: 600;
    color: #0a0a0a;
    flex: 1;
  }

  .varon-modal-body {
    padding: 24px;
  }

  .varon-modal-body p {
    margin: 0 0 16px 0;
    font-size: 15px;
    color: #4b5563;
    line-height: 1.6;
  }

  .varon-modal-body p:last-child {
    margin-bottom: 0;
  }

  .varon-modal-input {
    width: 100%;
    padding: 12px 16px;
    border: 2px solid #e5e7eb;
    border-radius: 8px;
    font-size: 15px;
    font-family: inherit;
    transition: all 0.2s;
  }

  .varon-modal-input:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }

  .varon-modal-footer {
    padding: 16px 24px 24px;
    display: flex;
    gap: 12px;
    justify-content: flex-end;
  }

  .varon-modal-btn {
    padding: 12px 24px;
    border: none;
    border-radius: 8px;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    font-family: inherit;
  }

  .varon-modal-btn-cancel {
    background: #f3f4f6;
    color: #4b5563;
  }

  .varon-modal-btn-cancel:hover {
    background: #e5e7eb;
  }

  .varon-modal-btn-confirm {
    background: #000000;
    color: #ffffff;
  }

  .varon-modal-btn-confirm:hover {
    background: #1a1a1a;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  .varon-modal-btn-danger {
    background: #ef4444;
    color: #ffffff;
  }

  .varon-modal-btn-danger:hover {
    background: #dc2626;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
  }

  @media (max-width: 768px) {
    .varon-notification-container {
      right: 12px;
      left: 12px;
      top: 75px;
    }

    .varon-notification {
      min-width: auto;
      max-width: none;
    }

    .varon-modal-content {
      width: 95%;
      max-width: none;
    }
  }
`;

document.head.appendChild(style);

// Export for global use
window.VaronNotifications = VaronNotifications;

// Gracefully replace native alerts with styled notifications.
if (!window.__varonAlertsPatched) {
  window.__varonAlertsPatched = true;

  const detectTypeFromMessage = (message) => {
    if (!message) return 'info';
    const trimmed = message.trim().toLowerCase();
    if (trimmed.startsWith('✅') || trimmed.includes('success')) return 'success';
    if (trimmed.startsWith('❌') || trimmed.includes('error') || trimmed.includes('failed')) return 'error';
    if (trimmed.startsWith('⚠') || trimmed.includes('warning')) return 'warning';
    return 'info';
  };

  const formatMessage = (value) => {
    const raw = typeof value === 'string' ? value : JSON.stringify(value);
    return {
      raw,
      html: raw.replace(/\n/g, '<br>')
    };
  };

  window.alert = (value) => {
    const { raw, html } = formatMessage(value);
    const type = detectTypeFromMessage(raw);
    VaronNotifications[type](html);
  };
}
