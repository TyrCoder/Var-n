function hideAllSections() {
    const contentSections = document.querySelectorAll('.content-section');
    const mainContent = document.getElementById('mainContent');
    contentSections.forEach(section => section.style.display = 'none');
    if (mainContent) mainContent.style.display = 'block';
}

function showSection(sectionId) {
    const contentSections = document.querySelectorAll('.content-section');
    const mainContent = document.getElementById('mainContent');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('overlay');
    const menuToggle = document.querySelector('.menu-toggle');
    const hero = document.querySelector('.hero');

    hideAllSections();
    
    if (sectionId === 'loginSection') {
        window.location.href = 'login.html';
        return;
    }

    if (sectionId !== 'home') {
        const section = document.getElementById(sectionId);
        if (section) {
            section.style.display = 'block';
            if (mainContent) mainContent.style.display = 'none';
            if (hero) hero.style.display = 'none';
        }
    } else {
        if (hero) hero.style.display = 'block';
        if (mainContent) mainContent.style.display = 'block';
    }

    if (sidebar && sidebar.classList.contains('open')) {
        sidebar.classList.remove('open');
        if (overlay) overlay.classList.remove('open');
        if (menuToggle) {
            menuToggle.classList.remove('open');
            menuToggle.setAttribute('aria-expanded', 'false');
        }
        document.body.style.overflow = '';
    }
}

window.showSection = showSection;

document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.querySelector('.menu-toggle');
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.overlay');
    const cartCount = document.getElementById('cartCount');
    const cartCountSidebar = document.getElementById('cartCountSidebar');

    function toggleMenu(e) {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }
        sidebar.classList.toggle('open');
        overlay.classList.toggle('open');
        menuToggle.classList.toggle('open');
        menuToggle.setAttribute('aria-expanded', sidebar.classList.contains('open'));
        document.body.style.overflow = sidebar.classList.contains('open') ? 'hidden' : '';
    }

    function closeMenu() {
        sidebar.classList.remove('open');
        overlay.classList.remove('open');
        menuToggle.classList.remove('open');
        document.body.style.overflow = '';
    }
    if (menuToggle) {
        menuToggle.addEventListener('click', toggleMenu);
    }

    if (overlay) {
        overlay.addEventListener('click', closeMenu);
    }

    document.addEventListener('click', function(e) {
        if (sidebar.classList.contains('open') && 
            !sidebar.contains(e.target) && 
            !menuToggle.contains(e.target)) {
            closeMenu();
        }
    });
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && sidebar.classList.contains('open')) {
            closeMenu();
        }
    });

    function hideAllSections() {
        contentSections.forEach(section => section.style.display = 'none');
        mainContent.style.display = 'block';
    }
    function showSection(sectionId) {
        hideAllSections();
        if (sectionId !== 'home') {
            const section = document.getElementById(sectionId);
            if (section) {
                section.style.display = 'block';
                mainContent.style.display = 'none';
            }
        }
        if (sidebar) {
            sidebar.classList.remove('open');
            overlay.classList.remove('open');
            menuToggle.setAttribute('aria-expanded', 'false');
            document.body.style.overflow = '';
        }
    }

    hideAllSections();

    function toggleMenu() {
        const isOpen = sidebar.classList.contains('open');
        menuToggle.classList.toggle('open');
        sidebar.classList.toggle('open');
        overlay.classList.toggle('open');
        menuToggle.setAttribute('aria-expanded', !isOpen);
        document.body.style.overflow = !isOpen ? 'hidden' : '';
    }

    function closeMenu() {
        menuToggle.classList.remove('open');
        sidebar.classList.remove('open');
        overlay.classList.remove('open');
        menuToggle.setAttribute('aria-expanded', 'false');
        document.body.style.overflow = '';
    }

    if (menuToggle) {
        menuToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            toggleMenu();
        });
    }

    if (overlay) {
        overlay.addEventListener('click', closeMenu);
    }
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && sidebar?.classList.contains('open')) {
            closeMenu();
        }
    });

    if (cartCount && cartCountSidebar) {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'characterData' || mutation.type === 'childList') {
                    cartCountSidebar.textContent = cartCount.textContent;
                }
            });
        });

        observer.observe(cartCount, { 
            characterData: true, 
            childList: true, 
            subtree: true 
        });
    }
});

const filters = document.querySelectorAll('.filters button');
const products = document.querySelectorAll('.product');
filters.forEach(btn => btn.addEventListener('click', ()=>{
  filters.forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  const f = btn.dataset.filter;
  products.forEach(p=>{
    const cat = p.dataset.category || 'all';
    p.style.display = (f==='all' || cat===f) ? '' : 'none';
  });
}));

const genres = document.querySelectorAll('.genre');
genres.forEach(g=>g.addEventListener('click', ()=>{
  genres.forEach(x=>x.classList.remove('active'));
  g.classList.add('active');
  const genre = g.dataset.genre;
  products.forEach(p=>{
    const gcat = p.dataset.genre || 'all';
    p.style.display = (genre==='all' || gcat===genre) ? '' : 'none';
  });
}));

const search = document.getElementById('search');
if(search){
  search.addEventListener('input', ()=>{
    const q = search.value.trim().toLowerCase();
    products.forEach(p=>{
      const title = p.querySelector('.title')?.textContent.toLowerCase() || '';
      const matches = title.includes(q);
      p.style.display = q ? (matches ? '' : 'none') : '';
    });
  });
}

const sellerBtn = document.getElementById('sellerBtn');
const riderBtn = document.getElementById('riderBtn');
const footerSeller = document.getElementById('footerSeller');
const footerRider = document.getElementById('footerRider');
const sellerModal = document.getElementById('sellerModal');
const riderModal = document.getElementById('riderModal');

function openModal(modalId){
  const modal = document.getElementById(modalId);
  if(!modal) return;
  modal.setAttribute('aria-hidden','false');
  document.body.style.overflow = 'hidden';
}
function closeModal(modalId){
  const modal = document.getElementById(modalId);
  if(!modal) return;
  modal.setAttribute('aria-hidden','true');
  document.body.style.overflow = '';
}

[sellerBtn, riderBtn, footerSeller, footerRider].forEach(el=>{
  if(!el) return;
  el.addEventListener('click', (e)=>{
        if(el === sellerBtn || el === riderBtn){
      e.preventDefault();
      if(el === sellerBtn) openModal(sellerModal);
      if(el === riderBtn) openModal(riderModal);
    }
  });
});

document.querySelectorAll('[data-close]').forEach(btn=>btn.addEventListener('click', ()=>{
  const modal = btn.closest('.modal');
  closeModal(modal);
}));

document.querySelectorAll('.modal').forEach(m=>m.addEventListener('click', (e)=>{
  if(e.target===m) closeModal(m);
}));

const sellerForm = document.getElementById('sellerForm');
if(sellerForm) sellerForm.addEventListener('submit', (e)=>{
  e.preventDefault();
  alert('Seller registration received. We will contact you.');
  closeModal(sellerModal);
});

const cartCountEl = document.getElementById('cartCount');
const snackbar = document.getElementById('snackbar');
const AUTH_FLAG = 'varon_logged_in';

function isLoggedIn(){
  try { return localStorage.getItem(AUTH_FLAG) === 'true'; } catch(e){ return false; }
}
function setLoggedIn(val){
  try { localStorage.setItem(AUTH_FLAG, val ? 'true' : 'false'); } catch(e){}
}
function saveIntendedAction(action){
  try { sessionStorage.setItem('varon_post_login', JSON.stringify(action)); } catch(e){}
}
function consumeIntendedAction(){
  try {
    const raw = sessionStorage.getItem('varon_post_login');
    if(!raw) return null;
    sessionStorage.removeItem('varon_post_login');
    return JSON.parse(raw);
  } catch(e){ return null; }
}
function goToLogin(reason){
  const next = window.location.href;
  // Use relative path to support static deployments
  let urlStr = 'login.html';
  try{
    const url = new URL(urlStr, window.location.href);
    url.searchParams.set('next', next);
    if(reason) url.searchParams.set('reason', reason);
    urlStr = url.toString();
  }catch(e){
    // Fallback to manual query string
    urlStr = `login.html?next=${encodeURIComponent(next)}${reason?`&reason=${encodeURIComponent(reason)}`:''}`;
  }
  window.location.href = urlStr;
}

function readCart(){
  try{ return JSON.parse(localStorage.getItem('varon_cart')||'{}'); }catch(e){ return {}; }
}
function writeCart(cart){ localStorage.setItem('varon_cart', JSON.stringify(cart)); }

function cartTotalCount(){
  const c = readCart();
  return Object.values(c).reduce((s,i)=>s + (i.qty||0), 0);
}

function updateCartBadge(){
  const n = cartTotalCount();
  if(cartCountEl) cartCountEl.textContent = n;
}

function addItemToCart(data){
  if(!data) return;
  const title = data.title || 'Item';
  const price = typeof data.price === 'number' ? data.price : (parseFloat((data.priceText||'').replace(/[^0-9\.]/g,'')) || 0);
  const id = (data.id) || title.toLowerCase().replace(/\s+/g,'_').replace(/[^a-z0-9_]/g,'');
  const cart = readCart();
  if(!cart[id]) cart[id] = {title, price, qty:0};
  cart[id].qty += (data.qty || 1);
  writeCart(cart);
  updateCartBadge();
  if(snackbar){
    snackbar.textContent = `${title} added to cart`;
    snackbar.classList.add('show');
    setTimeout(()=> snackbar.classList.remove('show'), 2200);
  }
}

function handleAddCartClick(e, btn){
  const card = btn.closest('.product');
  const title = card?.querySelector('.title')?.textContent || 'Item';
  const priceText = card?.querySelector('.price')?.textContent || '£0';
  const price = parseFloat(priceText.replace(/[^0-9\.]/g,'')) || 0;
  const id = title.toLowerCase().replace(/\s+/g,'_').replace(/[^a-z0-9_]/g,'');

  if(!isLoggedIn()){
    e.preventDefault();
    saveIntendedAction({ type:'addToCart', payload:{ id, title, price, qty:1 }, next: window.location.href });
    goToLogin('add_to_cart');
    return;
  }
  addItemToCart({id,title,price,qty:1});
}

function applyAuthGate(){
  // Attach/reattach to add-to-cart buttons
  document.querySelectorAll('.add-cart').forEach(btn=>{
    // Remove previous listener by cloning to avoid duplicate bindings
    const newBtn = btn.cloneNode(true);
    btn.replaceWith(newBtn);
    newBtn.addEventListener('click', (e)=> handleAddCartClick(e, newBtn));
  });

    document.querySelectorAll('.view-product, [data-view-product]')?.forEach(el=>{
    const act = (e)=>{
      if(isLoggedIn()) return; // allow default if logged in
      e.preventDefault();
      const href = el.getAttribute('href') || el.dataset.href || '#';
      saveIntendedAction({ type:'viewProduct', payload:{ href }, next: window.location.href });
      goToLogin('view_product');
    };
    const cloned = el.cloneNode(true);
    el.replaceWith(cloned);
    cloned.addEventListener('click', act);
  });
}
// Expose for manual re-application after dynamic DOM updates
try{ window.applyAuthGate = applyAuthGate; }catch(e){}

function renderCartPage(){
  const cartList = document.getElementById('cartList');
  const cartTotal = document.getElementById('cartTotal');
  if(!cartList) return;
  const cart = readCart();
  cartList.innerHTML = '';
  let total = 0;
  Object.entries(cart).forEach(([id,item])=>{
    const line = document.createElement('div');
    line.className = 'cart-item';
    line.innerHTML = `<div class="cart-item-left">
        <div class="cart-title">${item.title}</div>
        <div class="cart-price muted">£${item.price.toFixed(2)}</div>
      </div>
      <div class="cart-item-right">
        <div class="qty">Qty: <button data-op="dec" data-id="${id}">-</button> <span class="q">${item.qty}</span> <button data-op="inc" data-id="${id}">+</button></div>
        <div><button data-remove data-id="${id}" class="secondary">Remove</button></div>
      </div>`;
    cartList.appendChild(line);
    total += item.price * item.qty;
  });
  cartTotal.textContent = `£${total.toFixed(2)}`;

  cartList.querySelectorAll('[data-op]').forEach(btn=>btn.addEventListener('click', (e)=>{
    const id = btn.dataset.id; const op = btn.dataset.op;
    const c = readCart(); if(!c[id]) return;
    if(op==='inc') c[id].qty += 1; else c[id].qty = Math.max(0, c[id].qty-1);
    if(c[id].qty===0) delete c[id];
    writeCart(c); renderCartPage(); updateCartBadge();
  }));

  cartList.querySelectorAll('[data-remove]').forEach(btn=>btn.addEventListener('click', ()=>{
    const id = btn.dataset.id; const c = readCart(); delete c[id]; writeCart(c); renderCartPage(); updateCartBadge();
  }));
}

document.addEventListener('click', (e)=>{
  if(e.target && e.target.id==='clearCart'){
    const clearModal = document.getElementById('clearModal'); if(clearModal) clearModal.setAttribute('aria-hidden','false');
  }
  if(e.target && e.target.id==='checkoutBtn'){
    const checkoutModal = document.getElementById('checkoutModal');
    const sumEl = document.getElementById('checkoutSummary');
    const cart = readCart();
    if(sumEl){
      let html = '<ul style="list-style:none;padding:0;margin:0">'; let total=0;
      Object.values(cart).forEach(it=>{ html += `<li style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.04)"><strong style="color:#fff">${it.title}</strong> <div class="muted">${it.qty} × £${it.price.toFixed(2)}</div></li>`; total += it.qty*it.price });
      html += `</ul><div style="margin-top:10px;color:#fff">Total: <strong>£${total.toFixed(2)}</strong></div>`;
      sumEl.innerHTML = html;
    }
    if(checkoutModal) checkoutModal.setAttribute('aria-hidden','false');
  }
});

const confirmClearYes = document.getElementById('confirmClearYes');
if(confirmClearYes) confirmClearYes.addEventListener('click', ()=>{
  localStorage.removeItem('varon_cart'); renderCartPage(); updateCartBadge();
  const clearModal = document.getElementById('clearModal'); if(clearModal) clearModal.setAttribute('aria-hidden','true');
});

const proceedCheckout = document.getElementById('proceedCheckout');
if(proceedCheckout) proceedCheckout.addEventListener('click', ()=>{
  alert('Demo: proceed to payment (implement real integration).');
  const checkoutModal = document.getElementById('checkoutModal'); if(checkoutModal) checkoutModal.setAttribute('aria-hidden','true');
});

updateCartBadge();
document.addEventListener('DOMContentLoaded', ()=>{ 
  // If server rendered a logged-in indicator (e.g., accountLink is not an anchor), mark logged in
  try{
    const accountLink = document.getElementById('accountLink');
    if(accountLink && accountLink.tagName !== 'A'){ setLoggedIn(true); }
  }catch(e){}
  // Update nav bar based on login status
  updateNavBar();
  // Apply auth gate behaviors and render cart
  applyAuthGate();
  renderCartPage(); 
  
  // If just logged in, apply any remembered action
  const intended = consumeIntendedAction();
  if(intended && isLoggedIn()){
    if(intended.type === 'addToCart'){
      addItemToCart(intended.payload);
    } else if(intended.type === 'viewProduct'){
      if(intended.payload?.href){ window.location.href = intended.payload.href; }
    }
  }
});

function getUserEmail(){
  try{ return localStorage.getItem('varon_user_email') || ''; }catch(e){ return ''; }
}
function setUserEmail(email){
  try{ localStorage.setItem('varon_user_email', email || ''); }catch(e){}
}
function getUserFirstName(){
  try{ return localStorage.getItem('varon_user_first_name') || ''; }catch(e){ return ''; }
}
function setUserFirstName(firstName){
  try{ localStorage.setItem('varon_user_first_name', firstName || ''); }catch(e){}
}
function getUserRole(){
  try{ return localStorage.getItem('varon_user_role') || 'buyer'; }catch(e){ return 'buyer'; }
}
function setUserRole(role){
  try{ localStorage.setItem('varon_user_role', role || 'buyer'); }catch(e){}
}
function logout(){
  setLoggedIn(false);
  setUserEmail('');
  setUserFirstName('');
  setUserRole('buyer');
  window.location.href = 'index.html';
}

function getSellerRequests(){
  try{ return JSON.parse(localStorage.getItem('varon_seller_requests') || '[]'); }catch(e){ return []; }
}
function saveSellerRequests(requests){
  try{ localStorage.setItem('varon_seller_requests', JSON.stringify(requests)); }catch(e){}
}
function submitSellerRequest(data){
  const requests = getSellerRequests();
  const userEmail = getUserEmail();
  
  const existingRequest = requests.find(r => r.userEmail === userEmail && r.status === 'pending');
  if(existingRequest){
    return { success: false, message: 'You already have a pending seller request.' };
  }
  
  if(getUserRole() === 'seller'){
    return { success: false, message: 'You are already a seller!' };
  }
  
  const request = {
    id: Date.now(),
    userEmail: userEmail,
    firstName: getUserFirstName(),
    storeName: data.storeName,
    description: data.description,
    address: data.address,
    status: 'pending', // pending, approved, rejected
    createdAt: new Date().toISOString()
  };
  
  requests.push(request);
  saveSellerRequests(requests);
  return { success: true, message: 'Your request to become a seller has been submitted for review!' };
}
function approveSellerRequest(requestId){
  const requests = getSellerRequests();
  const request = requests.find(r => r.id === requestId);
  if(!request) return false;
  
  request.status = 'approved';
  request.approvedAt = new Date().toISOString();
  saveSellerRequests(requests);
  
  return true;
}
function rejectSellerRequest(requestId){
  const requests = getSellerRequests();
  const request = requests.find(r => r.id === requestId);
  if(!request) return false;
  
  request.status = 'rejected';
  request.rejectedAt = new Date().toISOString();
  saveSellerRequests(requests);
  return true;
}

// Show seller request modal
function showSellerRequestModal(){
  // Create modal dynamically
  const modalHTML = `
    <div id="sellerRequestModal" class="modal" aria-hidden="false" style="display:flex">
      <div class="modal-panel" style="max-width:600px">
        <button data-close class="modal-close" aria-label="Close">×</button>
        <h2 style="margin:0 0 8px">Request to Become a Seller</h2>
        <p class="muted" style="margin:0 0 18px;font-size:14px">Fill out the form below and our admin team will review your application.</p>
        <form id="sellerRequestForm">
          <label style="display:flex;flex-direction:column;margin-bottom:12px">
            <span style="font-weight:600;margin-bottom:4px">Store Name *</span>
            <input name="storeName" type="text" placeholder="e.g., Fashion Hub" required style="padding:10px;border:1px solid #eee;border-radius:6px" />
          </label>
          <label style="display:flex;flex-direction:column;margin-bottom:12px">
            <span style="font-weight:600;margin-bottom:4px">Description *</span>
            <textarea name="description" rows="4" placeholder="Tell us about your store and what you plan to sell..." required style="padding:10px;border:1px solid #eee;border-radius:6px;resize:vertical"></textarea>
          </label>
          <label style="display:flex;flex-direction:column;margin-bottom:12px">
            <span style="font-weight:600;margin-bottom:4px">Business Address *</span>
            <input name="address" type="text" placeholder="e.g., Manila, Philippines" required style="padding:10px;border:1px solid #eee;border-radius:6px" />
          </label>
          <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:18px">
            <button type="button" data-close class="secondary" style="padding:10px 18px;border-radius:6px;border:none;cursor:pointer;background:#f6f6f6">Cancel</button>
            <button type="submit" class="btn-cta" style="padding:10px 18px;border-radius:6px;border:none;cursor:pointer;background:#000;color:#fff">Submit Request</button>
          </div>
        </form>
      </div>
    </div>
  `;
  
  // Append to body
  document.body.insertAdjacentHTML('beforeend', modalHTML);
  
  // Attach handlers
  const modal = document.getElementById('sellerRequestModal');
  const form = document.getElementById('sellerRequestForm');
  const closeButtons = modal.querySelectorAll('[data-close]');
  
  closeButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      modal.remove();
    });
  });
  
  modal.addEventListener('click', (e) => {
    if(e.target === modal) modal.remove();
  });
  
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const formData = {
      storeName: form.querySelector('[name="storeName"]').value.trim(),
      description: form.querySelector('[name="description"]').value.trim(),
      address: form.querySelector('[name="address"]').value.trim()
    };
    
    const result = submitSellerRequest(formData);
    alert(result.message);
    
    if(result.success){
      modal.remove();
    }
  });
}

// Detect user role based on email (simple client-side logic)
function detectRole(email){
  if(!email) return 'buyer';
  const lowerEmail = email.toLowerCase();
  // Admin emails (customize this list)
  const adminEmails = ['admin@varon.com', 'admin@example.com'];
  if(adminEmails.includes(lowerEmail) || lowerEmail.includes('admin')){
    return 'admin';
  }
  // Seller detection (optional)
  if(lowerEmail.includes('seller')){
    return 'seller';
  }
  return 'buyer';
}

// Get role-based redirect URL
function getRoleBasedRedirect(role){
  switch(role){
    case 'admin': return 'dashboard.html';
    case 'seller': return 'indexLoggedIn.html'; // or create seller dashboard later
    case 'rider': return 'indexLoggedIn.html'; // or create rider dashboard later
    case 'buyer': return 'indexLoggedIn.html';
    default: return 'indexLoggedIn.html';
  }
}

function updateNavBar(){
  const accountLink = document.getElementById('accountLink');
  if(!accountLink) return;

  if(isLoggedIn()){
    const firstName = getUserFirstName();
    const email = getUserEmail();
    const role = getUserRole();
    const displayName = firstName || email.split('@')[0] || 'User';
    
    // Build nav HTML based on role
    let navHTML = `<span class="account" style="cursor:default">Welcome, ${displayName}</span>`;
    
    // Show "Request to be Seller" button only for buyers
    if(role === 'buyer'){
      navHTML += `<a href="#" id="requestSellerBtn" class="account" style="background:#4ade80;color:#000;border:1px solid #4ade80">Become a Seller</a>`;
    }
    
    navHTML += `<a href="#" id="logoutBtn" class="account" style="background:#fff;color:#000;border:1px solid #fff">Logout</a>`;
    
    // Replace Login link with Welcome + Buttons
    accountLink.outerHTML = navHTML;
    
    // Attach logout handler
    const logoutBtn = document.getElementById('logoutBtn');
    if(logoutBtn){
      logoutBtn.addEventListener('click', (e)=>{
        e.preventDefault();
        logout();
      });
    }
    
    // Attach request seller handler
    const requestSellerBtn = document.getElementById('requestSellerBtn');
    if(requestSellerBtn){
      requestSellerBtn.addEventListener('click', (e)=>{
        e.preventDefault();
        showSellerRequestModal();
      });
    }
  } else {
    // Show only Login link (signup is now integrated in login page)
    accountLink.outerHTML = `
      <a href="login.html" id="accountLink" class="account">Login</a>
    `;
  }
}

  const loginForm = document.getElementById('loginForm');
if(loginForm){
  loginForm.addEventListener('submit', function(e){
    e.preventDefault();
    const email = loginForm.querySelector('#loginEmail')?.value?.trim();
    const pwd = loginForm.querySelector('#loginPassword')?.value;
    if(!email || !pwd){
      alert('Please enter email and password.');
      return;
    }
    // Detect role and store it
    const role = detectRole(email);
    setLoggedIn(true);
    setUserEmail(email);
    // Keep existing first name if already stored, otherwise use email username
    if(!getUserFirstName()){
      const firstName = email.split('@')[0];
      setUserFirstName(firstName);
    }
    setUserRole(role);
    
    // Apply any pending action after login
    const intended = consumeIntendedAction();
    if(intended){
      if(intended.type === 'addToCart'){
        addItemToCart(intended.payload);
      }
      if(intended.type === 'viewProduct' && intended.payload?.href){
        window.location.href = intended.payload.href;
        return;
      }
    }
    // Navigate based on role or 'next' param
    const params = new URLSearchParams(window.location.search);
    const next = params.get('next');
    if(next){
      window.location.href = next;
    } else {
      window.location.href = getRoleBasedRedirect(role);
    }
  });
}const signupForm = document.getElementById('signupForm');
if(signupForm){
  signupForm.addEventListener('submit', function(e){
    e.preventDefault();
    const firstName = signupForm.querySelector('input[name="firstName"]')?.value?.trim();
    const lastName = signupForm.querySelector('input[name="lastName"]')?.value?.trim();
    const email = signupForm.querySelector('input[name="email"]')?.value?.trim();
    const pwd = signupForm.querySelector('input[name="password"]')?.value;
    const confirmPwd = signupForm.querySelector('input[name="confirmPassword"]')?.value;
    
    if(!email || !pwd || !firstName || !lastName){
      alert('Please fill in all required fields.');
      return;
    }
    
    if(pwd !== confirmPwd){
      alert('Passwords do not match!');
      return;
    }
    
    if(pwd.length < 6){
      alert('Password must be at least 6 characters long.');
      return;
    }
    
    // All new signups default to 'buyer' role
    const role = 'buyer';
    setLoggedIn(true);
    setUserEmail(email);
    setUserFirstName(firstName);
    setUserRole(role);
    
    // Show success message
    alert(`Welcome to Varón, ${firstName}! Your account has been created. You can request to become a seller from your dashboard.`);
    
    // Redirect based on role or next param
    const params = new URLSearchParams(window.location.search);
    const next = params.get('next');
    if(next){
      window.location.href = next;
    } else {
      window.location.href = getRoleBasedRedirect(role);
    }
  });
}

function togglePassword(inputId, button) {
  const input = document.getElementById(inputId);
  if (!input) return;
  
  if (input.type === 'password') {
    input.type = 'text';
    button.textContent = '🙈';
  } else {
    input.type = 'password';
    button.textContent = '👁️';
  }
}

document.addEventListener('DOMContentLoaded', function() {
  const authTabs = document.querySelectorAll('.auth-tab');
  const authForms = document.querySelectorAll('.auth-form');
  
  authTabs.forEach(tab => {
    tab.addEventListener('click', function() {
      const targetTab = this.getAttribute('data-tab');
      
      authTabs.forEach(t => t.classList.remove('active'));
      this.classList.add('active');
      authForms.forEach(form => {
        if (form.id === targetTab + 'Form') {
          form.classList.add('active');
        } else {
          form.classList.remove('active');
        }
      });
    });
  });
});

const dashboardContent = document.getElementById('dashboardContent');
const sideLinks = document.querySelectorAll('.side-link');

// Content templates for each page
const pageContent = {
  overview: `
    <div class="grid stats">
      <div class="card"><div class="inner"><div class="metric">Total Revenue (PHP)</div><div class="value">₱1,250 <span class="delta">↑ 1%</span></div></div></div>
      <div class="card"><div class="inner"><div class="metric">Total Customers</div><div class="value">9 <span class="delta" style="color:#ef4444">↓ 0.2%</span></div></div></div>
      <div class="card"><div class="inner"><div class="metric">Total Transactions</div><div class="value">17 <span class="delta">↑ 1%</span></div></div></div>
      <div class="card"><div class="inner"><div class="metric">Total Products</div><div class="value">6 <span class="delta">↑ 1%</span></div></div></div>
    </div>

    <div class="grid two" style="margin-top:14px">
      <div class="card">
        <div class="inner">
          <div class="metric">Revenue Growth (USD)</div>
          <div class="chart">
            <div class="bars">
              <div class="bar" style="height:30%"></div>
              <div class="bar" style="height:42%"></div>
              <div class="bar" style="height:25%"></div>
              <div class="bar" style="height:48%"></div>
              <div class="bar" style="height:33%"></div>
              <div class="bar" style="height:55%"></div>
              <div class="bar" style="height:38%"></div>
            </div>
            <div class="legend"><span>Sun</span><span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span></div>
          </div>
        </div>
      </div>
      <div class="card">
        <div class="inner">
          <div class="metric">Customer Growth (Philippines)</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:6px">
            <div>
              <div style="display:flex;align-items:center;justify-content:space-between;font-size:13px;margin:6px 0"><span>NCR (Metro Manila)</span><span>28%</span></div>
              <div style="height:8px;background:#efefef;border-radius:999px"><div style="height:8px;width:28%;background:#0a0a0a;border-radius:999px"></div></div>
              <div style="display:flex;align-items:center;justify-content:space-between;font-size:13px;margin:10px 0 6px"><span>CALABARZON</span><span>22%</span></div>
              <div style="height:8px;background:#efefef;border-radius:999px"><div style="height:8px;width:22%;background:#0a0a0a;border-radius:999px"></div></div>
              <div style="display:flex;align-items:center;justify-content:space-between;font-size:13px;margin:10px 0 6px"><span>Central Visayas</span><span>18%</span></div>
              <div style="height:8px;background:#efefef;border-radius:999px"><div style="height:8px;width:18%;background:#0a0a0a;border-radius:999px"></div></div>
              <div style="display:flex;align-items:center;justify-content:space-between;font-size:13px;margin:10px 0 0"><span>Central Luzon</span><span>12%</span></div>
              <div style="height:8px;background:#efefef;border-radius:999px"><div style="height:8px;width:12%;background:#0a0a0a;border-radius:999px"></div></div>
              <div style="display:flex;align-items:center;justify-content:space-between;font-size:13px;margin:10px 0 0"><span>Davao Region</span><span>8%</span></div>
              <div style="height:8px;background:#efefef;border-radius:999px"><div style="height:8px;width:8%;background:#0a0a0a;border-radius:999px"></div></div>
            </div>
            <div class="promo">
              <div style="font-weight:700;margin-bottom:8px">See more detail statistic to analyze your decision</div>
              <a href="#" class="tag" style="display:inline-block;background:#fff;color:#0a0a0a;margin-top:8px">See more</a>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="grid two" style="margin-top:14px">
      <div class="card">
        <div class="inner">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <div class="metric">Top Transactions</div>
            <a href="#" style="font-size:12px;color:var(--muted)">View detail</a>
          </div>
          <div style="overflow:auto">
            <table>
              <thead><tr><th>Customer ID</th><th>Item</th><th>Date</th><th>Amount</th><th></th></tr></thead>
              <tbody>
                <tr><td>#23432</td><td>Leather crop top</td><td>12 Jan</td><td>$2,349</td><td><a class="tag" style="background:#efefef;color:#0a0a0a">See detail</a></td></tr>
                <tr><td>#25466</td><td>Female Tote Bag</td><td>3 Jan</td><td>$1,640</td><td><a class="tag" style="background:#efefef;color:#0a0a0a">See detail</a></td></tr>
                <tr><td>#25467</td><td>Luxury Necklace</td><td>4 Jan</td><td>$2,047</td><td><a class="tag" style="background:#efefef;color:#0a0a0a">See detail</a></td></tr>
                <tr><td>#25468</td><td>Men's Shoes</td><td>2 Jan</td><td>$1,939</td><td><a class="tag" style="background:#efefef;color:#0a0a0a">See detail</a></td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
      <div class="card">
        <div class="inner">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <div class="metric">Top Product</div>
            <a href="#" style="font-size:12px;color:var(--muted)">View more</a>
          </div>
          <div style="display:flex;gap:14px;align-items:center;margin-top:10px">
            <div style="width:120px;height:140px;border-radius:8px;background:#eaeaea;background-image:url('https://images.unsplash.com/photo-1610963876305-c8e7cb43a09b?q=80&w=600&auto=format&fit=crop');background-size:cover;background-position:center"></div>
            <div>
              <div style="font-weight:700">Denim Jacket with White Feathers</div>
              <div class="muted" style="margin-top:4px">240+ items sold out</div>
              <a href="#" class="tag" style="display:inline-block;margin-top:10px">Manage</a>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  product: `
    <h2 style="margin-bottom:16px">Products Management</h2>
    <div class="card">
      <div class="inner">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">
          <div class="metric">All Products</div>
          <button class="tag" style="cursor:pointer">+ Add New Product</button>
        </div>
        <table>
          <thead><tr><th>Product Name</th><th>Category</th><th>Price</th><th>Stock</th><th>Actions</th></tr></thead>
          <tbody>
            <tr><td>Leather Crop Top</td><td>Tops</td><td>₱850</td><td>45</td><td><button class="tag" style="background:#efefef;color:#0a0a0a;cursor:pointer">Edit</button></td></tr>
            <tr><td>Female Tote Bag</td><td>Accessories</td><td>₱1,200</td><td>23</td><td><button class="tag" style="background:#efefef;color:#0a0a0a;cursor:pointer">Edit</button></td></tr>
            <tr><td>Luxury Necklace</td><td>Jewelry</td><td>₱2,500</td><td>12</td><td><button class="tag" style="background:#efefef;color:#0a0a0a;cursor:pointer">Edit</button></td></tr>
            <tr><td>Men's Shoes</td><td>Footwear</td><td>₱1,800</td><td>34</td><td><button class="tag" style="background:#efefef;color:#0a0a0a;cursor:pointer">Edit</button></td></tr>
            <tr><td>Denim Jacket</td><td>Outerwear</td><td>₱2,200</td><td>18</td><td><button class="tag" style="background:#efefef;color:#0a0a0a;cursor:pointer">Edit</button></td></tr>
            <tr><td>Summer Dress</td><td>Dresses</td><td>₱950</td><td>56</td><td><button class="tag" style="background:#efefef;color:#0a0a0a;cursor:pointer">Edit</button></td></tr>
          </tbody>
        </table>
      </div>
    </div>
  `,
  customer: `
    <h2 style="margin-bottom:16px">Customer Management</h2>
    <div class="grid stats">
      <div class="card"><div class="inner"><div class="metric">Total Customers</div><div class="value">9</div></div></div>
      <div class="card"><div class="inner"><div class="metric">Active This Month</div><div class="value">7</div></div></div>
      <div class="card"><div class="inner"><div class="metric">New Customers</div><div class="value">3</div></div></div>
      <div class="card"><div class="inner"><div class="metric">Avg. Order Value</div><div class="value">₱1,450</div></div></div>
    </div>
    <div class="card" style="margin-top:14px">
      <div class="inner">
        <div class="metric" style="margin-bottom:14px">Customer List</div>
        <table>
          <thead><tr><th>Customer Name</th><th>Email</th><th>Orders</th><th>Total Spent</th><th>Status</th></tr></thead>
          <tbody>
            <tr><td>Maria Santos</td><td>maria.s@email.com</td><td>5</td><td>₱4,320</td><td><span style="color:#10b981">Active</span></td></tr>
            <tr><td>Juan Reyes</td><td>juan.reyes@email.com</td><td>3</td><td>₱2,890</td><td><span style="color:#10b981">Active</span></td></tr>
            <tr><td>Ana Cruz</td><td>ana.cruz@email.com</td><td>8</td><td>₱6,120</td><td><span style="color:#10b981">Active</span></td></tr>
            <tr><td>Carlos Diaz</td><td>c.diaz@email.com</td><td>2</td><td>₱1,450</td><td><span style="color:#777">Inactive</span></td></tr>
            <tr><td>Lisa Garcia</td><td>lisa.g@email.com</td><td>4</td><td>₱3,200</td><td><span style="color:#10b981">Active</span></td></tr>
          </tbody>
        </table>
      </div>
    </div>
  `,
  transactions: `
    <h2 style="margin-bottom:16px">Transactions</h2>
    <div class="grid stats">
      <div class="card"><div class="inner"><div class="metric">Total Transactions</div><div class="value">17</div></div></div>
      <div class="card"><div class="inner"><div class="metric">Completed</div><div class="value">14</div></div></div>
      <div class="card"><div class="inner"><div class="metric">Pending</div><div class="value">2</div></div></div>
      <div class="card"><div class="inner"><div class="metric">Failed</div><div class="value">1</div></div></div>
    </div>
    <div class="card" style="margin-top:14px">
      <div class="inner">
        <div class="metric" style="margin-bottom:14px">Recent Transactions</div>
        <table>
          <thead><tr><th>Transaction ID</th><th>Customer</th><th>Item</th><th>Date</th><th>Amount</th><th>Status</th></tr></thead>
          <tbody>
            <tr><td>#TX-001</td><td>Maria Santos</td><td>Leather crop top</td><td>Jan 12, 2025</td><td>₱2,349</td><td><span style="color:#10b981">Completed</span></td></tr>
            <tr><td>#TX-002</td><td>Juan Reyes</td><td>Female Tote Bag</td><td>Jan 3, 2025</td><td>₱1,640</td><td><span style="color:#10b981">Completed</span></td></tr>
            <tr><td>#TX-003</td><td>Ana Cruz</td><td>Luxury Necklace</td><td>Jan 4, 2025</td><td>₱2,047</td><td><span style="color:#f59e0b">Pending</span></td></tr>
            <tr><td>#TX-004</td><td>Carlos Diaz</td><td>Men's Shoes</td><td>Jan 2, 2025</td><td>₱1,939</td><td><span style="color:#10b981">Completed</span></td></tr>
            <tr><td>#TX-005</td><td>Lisa Garcia</td><td>Denim Jacket</td><td>Jan 5, 2025</td><td>₱2,200</td><td><span style="color:#ef4444">Failed</span></td></tr>
          </tbody>
        </table>
      </div>
    </div>
  `,
  statistics: `
    <h2 style="margin-bottom:16px">Statistics & Analytics</h2>
    <div class="grid two">
      <div class="card">
        <div class="inner">
          <div class="metric">Sales Trend (Last 7 Days)</div>
          <div class="chart">
            <div class="bars">
              <div class="bar" style="height:45%"></div>
              <div class="bar" style="height:62%"></div>
              <div class="bar" style="height:38%"></div>
              <div class="bar" style="height:71%"></div>
              <div class="bar" style="height:52%"></div>
              <div class="bar" style="height:80%"></div>
              <div class="bar" style="height:65%"></div>
            </div>
            <div class="legend"><span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span><span>Sun</span></div>
          </div>
        </div>
      </div>
      <div class="card">
        <div class="inner">
          <div class="metric">Category Performance</div>
          <div style="margin-top:16px">
            <div style="display:flex;justify-content:space-between;margin:10px 0"><span>Tops & Shirts</span><strong>35%</strong></div>
            <div style="height:10px;background:#efefef;border-radius:999px"><div style="height:10px;width:35%;background:#0a0a0a;border-radius:999px"></div></div>
            <div style="display:flex;justify-content:space-between;margin:10px 0"><span>Accessories</span><strong>28%</strong></div>
            <div style="height:10px;background:#efefef;border-radius:999px"><div style="height:10px;width:28%;background:#0a0a0a;border-radius:999px"></div></div>
            <div style="display:flex;justify-content:space-between;margin:10px 0"><span>Footwear</span><strong>22%</strong></div>
            <div style="height:10px;background:#efefef;border-radius:999px"><div style="height:10px;width:22%;background:#0a0a0a;border-radius:999px"></div></div>
            <div style="display:flex;justify-content:space-between;margin:10px 0"><span>Jewelry</span><strong>15%</strong></div>
            <div style="height:10px;background:#efefef;border-radius:999px"><div style="height:10px;width:15%;background:#0a0a0a;border-radius:999px"></div></div>
          </div>
        </div>
      </div>
    </div>
  `,
  riders: `
    <h2 style="margin-bottom:16px">Riders Management</h2>
    <div class="grid stats">
      <div class="card"><div class="inner"><div class="metric">Total Riders</div><div class="value">12</div></div></div>
      <div class="card"><div class="inner"><div class="metric">Active Today</div><div class="value">8</div></div></div>
      <div class="card"><div class="inner"><div class="metric">On Delivery</div><div class="value">5</div></div></div>
      <div class="card"><div class="inner"><div class="metric">Available</div><div class="value">3</div></div></div>
    </div>
    <div class="card" style="margin-top:14px">
      <div class="inner">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">
          <div class="metric">Rider List</div>
          <button class="tag" style="cursor:pointer">+ Add New Rider</button>
        </div>
        <table>
          <thead><tr><th>Rider Name</th><th>Vehicle</th><th>Deliveries Today</th><th>Rating</th><th>Status</th></tr></thead>
          <tbody>
            <tr><td>Rico Manuel</td><td>Motorcycle</td><td>7</td><td>4.8 ⭐</td><td><span style="color:#10b981">Active</span></td></tr>
            <tr><td>Pedro Santos</td><td>Bicycle</td><td>5</td><td>4.9 ⭐</td><td><span style="color:#f59e0b">On Delivery</span></td></tr>
            <tr><td>Mike Reyes</td><td>Motorcycle</td><td>6</td><td>4.7 ⭐</td><td><span style="color:#10b981">Active</span></td></tr>
            <tr><td>Tony Cruz</td><td>Car</td><td>4</td><td>4.6 ⭐</td><td><span style="color:#f59e0b">On Delivery</span></td></tr>
            <tr><td>Dan Garcia</td><td>Motorcycle</td><td>8</td><td>5.0 ⭐</td><td><span style="color:#10b981">Active</span></td></tr>
          </tbody>
        </table>
      </div>
    </div>
  `,
  sellers: `
    <h2 style="margin-bottom:16px">Seller Requests Management</h2>
    <div class="grid stats">
      <div class="card"><div class="inner"><div class="metric">Total Requests</div><div class="value" id="totalRequests">0</div></div></div>
      <div class="card"><div class="inner"><div class="metric">Pending</div><div class="value" id="pendingRequests">0</div></div></div>
      <div class="card"><div class="inner"><div class="metric">Approved</div><div class="value" id="approvedRequests">0</div></div></div>
      <div class="card"><div class="inner"><div class="metric">Rejected</div><div class="value" id="rejectedRequests">0</div></div></div>
    </div>
    <div class="card" style="margin-top:14px">
      <div class="inner">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">
          <div class="metric">Seller Requests</div>
        </div>
        <div id="sellerRequestsList"></div>
      </div>
    </div>
  `,
  log: `
    <h2 style="margin-bottom:16px">Activity Log</h2>
    <div class="card">
      <div class="inner">
        <div class="metric" style="margin-bottom:14px">Recent Activities</div>
        <table>
          <thead><tr><th>Timestamp</th><th>User</th><th>Action</th><th>Details</th></tr></thead>
          <tbody>
            <tr><td>2025-10-21 14:23</td><td>Admin</td><td>Product Added</td><td>New product "Summer Dress" added</td></tr>
            <tr><td>2025-10-21 13:45</td><td>Seller: Fashion Hub</td><td>Order Processed</td><td>Order #TX-001 marked as shipped</td></tr>
            <tr><td>2025-10-21 12:30</td><td>Customer: Maria Santos</td><td>Order Placed</td><td>New order #TX-002 received</td></tr>
            <tr><td>2025-10-21 11:15</td><td>Admin</td><td>Rider Approved</td><td>New rider "Rico Manuel" approved</td></tr>
            <tr><td>2025-10-21 10:00</td><td>Seller: Style Central</td><td>Product Updated</td><td>Updated price for "Leather Crop Top"</td></tr>
            <tr><td>2025-10-21 09:30</td><td>Admin</td><td>Login</td><td>Admin logged in to dashboard</td></tr>
            <tr><td>2025-10-20 18:45</td><td>Customer: Juan Reyes</td><td>Account Created</td><td>New customer registration</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  `,
  setting: `
    <h2 style="margin-bottom:16px">Settings</h2>
    <div class="grid" style="grid-template-columns:1fr 1fr;gap:14px">
      <div class="card">
        <div class="inner">
          <div class="metric" style="margin-bottom:14px">General Settings</div>
          <div style="display:flex;flex-direction:column;gap:12px">
            <div><label style="display:block;margin-bottom:4px;font-size:13px">Site Name</label><input type="text" value="Varón Admin" style="width:100%;padding:8px;border:1px solid var(--line);border-radius:6px"/></div>
            <div><label style="display:block;margin-bottom:4px;font-size:13px">Email</label><input type="email" value="admin@varon.com" style="width:100%;padding:8px;border:1px solid var(--line);border-radius:6px"/></div>
            <div><label style="display:block;margin-bottom:4px;font-size:13px">Currency</label><select style="width:100%;padding:8px;border:1px solid var(--line);border-radius:6px"><option>PHP (₱)</option><option>USD ($)</option><option>EUR (€)</option></select></div>
            <button class="tag" style="cursor:pointer;margin-top:8px">Save Changes</button>
          </div>
        </div>
      </div>
      <div class="card">
        <div class="inner">
          <div class="metric" style="margin-bottom:14px">Security</div>
          <div style="display:flex;flex-direction:column;gap:12px">
            <div><label style="display:block;margin-bottom:4px;font-size:13px">Current Password</label><input type="password" style="width:100%;padding:8px;border:1px solid var(--line);border-radius:6px"/></div>
            <div><label style="display:block;margin-bottom:4px;font-size:13px">New Password</label><input type="password" style="width:100%;padding:8px;border:1px solid var(--line);border-radius:6px"/></div>
            <div><label style="display:block;margin-bottom:4px;font-size:13px">Confirm Password</label><input type="password" style="width:100%;padding:8px;border:1px solid var(--line);border-radius:6px"/></div>
            <button class="tag" style="cursor:pointer;margin-top:8px">Update Password</button>
          </div>
        </div>
      </div>
    </div>
  `,
  help: `
    <h2 style="margin-bottom:16px">Help & Support</h2>
    <div class="card">
      <div class="inner">
        <div class="metric" style="margin-bottom:14px">Frequently Asked Questions</div>
        <div style="display:flex;flex-direction:column;gap:16px">
          <div style="padding:12px;background:var(--card);border-radius:8px">
            <div style="font-weight:700;margin-bottom:6px">How do I add a new product?</div>
            <div style="color:var(--muted);font-size:14px">Navigate to the Product section and click "+ Add New Product" button. Fill in the required details and save.</div>
          </div>
          <div style="padding:12px;background:var(--card);border-radius:8px">
            <div style="font-weight:700;margin-bottom:6px">How do I approve new sellers?</div>
            <div style="color:var(--muted);font-size:14px">Go to Sellers Management and review pending sellers. Click on their profile and approve or reject.</div>
          </div>
          <div style="padding:12px;background:var(--card);border-radius:8px">
            <div style="font-weight:700;margin-bottom:6px">Where can I view transaction details?</div>
            <div style="color:var(--muted);font-size:14px">Check the Transactions section for all transaction history and details.</div>
          </div>
          <div style="padding:12px;background:var(--card);border-radius:8px">
            <div style="font-weight:700;margin-bottom:6px">Need more help?</div>
            <div style="color:var(--muted);font-size:14px">Contact support at support@varon.com or call +63-2-1234-5678</div>
          </div>
        </div>
      </div>
    </div>
  `,
  darkmode: `
    <h2 style="margin-bottom:16px">Dark Mode</h2>
    <div class="card">
      <div class="inner">
        <div class="metric" style="margin-bottom:14px">Theme Settings</div>
        <div style="padding:20px;text-align:center">
          <div style="font-size:48px;margin-bottom:16px">🌙</div>
          <div style="font-weight:700;margin-bottom:8px">Dark Mode Coming Soon!</div>
          <div style="color:var(--muted)">We're working on bringing you a sleek dark theme experience.</div>
          <button class="tag" style="cursor:pointer;margin-top:16px">Notify Me When Ready</button>
        </div>
      </div>
    </div>
  `
};

if (sideLinks && dashboardContent) {
  sideLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const page = link.dataset.page;
      
      sideLinks.forEach(l => l.classList.remove('active'));
      link.classList.add('active');
      const pageTitle = document.querySelector('.topbar .page-title');
      if (pageTitle) {
        pageTitle.textContent = link.textContent.trim();
      }
      
      // Load content
      if (pageContent[page]) {
        dashboardContent.innerHTML = pageContent[page];
        
        // If sellers page, load seller requests
        if(page === 'sellers'){
          loadSellerRequests();
        }
      } else {
        dashboardContent.innerHTML = `<div class="card"><div class="inner"><h3>Page not found</h3><p>This section is under development.</p></div></div>`;
      }
    });
  });
}

// Load and render seller requests in admin dashboard
function loadSellerRequests(){
  const requests = getSellerRequests();
  const listContainer = document.getElementById('sellerRequestsList');
  
  if(!listContainer) return;
  
  // Update stats
  const totalEl = document.getElementById('totalRequests');
  const pendingEl = document.getElementById('pendingRequests');
  const approvedEl = document.getElementById('approvedRequests');
  const rejectedEl = document.getElementById('rejectedRequests');
  
  if(totalEl) totalEl.textContent = requests.length;
  if(pendingEl) pendingEl.textContent = requests.filter(r => r.status === 'pending').length;
  if(approvedEl) approvedEl.textContent = requests.filter(r => r.status === 'approved').length;
  if(rejectedEl) rejectedEl.textContent = requests.filter(r => r.status === 'rejected').length;
  
  // Render requests
  if(requests.length === 0){
    listContainer.innerHTML = '<p class="muted" style="text-align:center;padding:20px">No seller requests yet.</p>';
    return;
  }
  
  let html = '<table><thead><tr><th>Applicant</th><th>Store Name</th><th>Description</th><th>Date</th><th>Status</th><th>Actions</th></tr></thead><tbody>';
  
  requests.reverse().forEach(req => {
    const date = new Date(req.createdAt).toLocaleDateString();
    const statusColor = req.status === 'approved' ? '#10b981' : req.status === 'rejected' ? '#ef4444' : '#f59e0b';
    const statusText = req.status.charAt(0).toUpperCase() + req.status.slice(1);
    
    html += `<tr>
      <td><strong>${req.firstName}</strong><br/><small style="color:#777">${req.userEmail}</small></td>
      <td>${req.storeName}</td>
      <td style="max-width:200px">${req.description.substring(0, 60)}${req.description.length > 60 ? '...' : ''}</td>
      <td>${date}</td>
      <td><span style="color:${statusColor}">${statusText}</span></td>
      <td>`;
    
    if(req.status === 'pending'){
      html += `<button class="tag" onclick="handleApproveRequest(${req.id})" style="background:#10b981;color:#fff;cursor:pointer;margin-right:4px">Approve</button>
               <button class="tag" onclick="handleRejectRequest(${req.id})" style="background:#ef4444;color:#fff;cursor:pointer">Reject</button>`;
    } else {
      html += `<button class="tag" onclick="viewRequestDetails(${req.id})" style="background:#efefef;color:#0a0a0a;cursor:pointer">View</button>`;
    }
    
    html += `</td></tr>`;
  });
  
  html += '</tbody></table>';
  listContainer.innerHTML = html;
}

// Global handlers for admin actions
window.handleApproveRequest = function(requestId){
  if(!confirm('Are you sure you want to approve this seller request?')) return;
  
  if(approveSellerRequest(requestId)){
    alert('Seller request approved! Note: In production, the user\'s role would be updated in the database.');
    loadSellerRequests();
  }
};

window.handleRejectRequest = function(requestId){
  if(!confirm('Are you sure you want to reject this seller request?')) return;
  
  if(rejectSellerRequest(requestId)){
    alert('Seller request rejected.');
    loadSellerRequests();
  }
};

window.viewRequestDetails = function(requestId){
  const requests = getSellerRequests();
  const request = requests.find(r => r.id === requestId);
  if(!request) return;
  
  alert(`Request Details:\n\nApplicant: ${request.firstName}\nEmail: ${request.userEmail}\nStore Name: ${request.storeName}\nDescription: ${request.description}\nAddress: ${request.address}\nStatus: ${request.status}\nSubmitted: ${new Date(request.createdAt).toLocaleString()}`);
};
