// Navigation and UI Controls
function showSection(sectionId) {
    const sections = document.querySelectorAll('.content-section');
    sections.forEach(section => section.style.display = 'none');
    
    if (sectionId === 'home') {
        document.getElementById('mainContent').style.display = 'block';
    } else {
        const targetSection = document.getElementById(sectionId);
        if (targetSection) {
            targetSection.style.display = 'block';
        }
    }
    
    closeSidebar();
}

// Sidebar Controls
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('overlay');
    const menuToggle = document.querySelector('.menu-toggle');
    
    sidebar.classList.toggle('open');
    overlay.classList.toggle('open');
    menuToggle.classList.toggle('open');
    menuToggle.setAttribute('aria-expanded', 
        menuToggle.classList.contains('open'));
}

function closeSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('overlay');
    const menuToggle = document.querySelector('.menu-toggle');
    
    sidebar.classList.remove('open');
    overlay.classList.remove('open');
    menuToggle.classList.remove('open');
    menuToggle.setAttribute('aria-expanded', 'false');
}

// Modal Controls
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.setAttribute('aria-hidden', 'false');
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.setAttribute('aria-hidden', 'true');
    }
}

// Cart Functionality
let cart = [];

function addToCart(product) {
    cart.push(product);
    updateCartCount();
    showSnackbar();
}

function updateCartCount() {
    const count = cart.length;
    document.getElementById('cartCount').textContent = count;
    document.getElementById('cartCountSidebar').textContent = count;
}

function showSnackbar() {
    const snackbar = document.getElementById('snackbar');
    snackbar.classList.add('show');
    setTimeout(() => snackbar.classList.remove('show'), 3000);
}

function clearCart() {
    cart = [];
    updateCartCount();
    closeModal('cartModal');
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Setup menu toggle
    const menuToggle = document.querySelector('.menu-toggle');
    menuToggle.addEventListener('click', toggleSidebar);
    
    // Setup overlay click to close sidebar
    const overlay = document.getElementById('overlay');
    overlay.addEventListener('click', closeSidebar);
    
    // Fetch buyer name if logged in
    const buyerFirstName = document.getElementById('buyerFirstName');
    if (buyerFirstName) {
        fetch('/get_buyer_name')
            .then(response => response.json())
            .then(data => {
                buyerFirstName.textContent = data.firstName;
                document.getElementById('buyerFirstNameSidebar').textContent = data.firstName;
            })
            .catch(error => console.error('Error fetching buyer name:', error));
    }
    
    // Initialize cart
    updateCartCount();
});