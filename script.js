const menuToggle = document.getElementById('menuToggle');
const topNav = document.getElementById('topNav');
if(menuToggle && topNav){
  menuToggle.addEventListener('click', (e)=>{
    e.stopPropagation();
    topNav.classList.toggle('open');
  });

  document.addEventListener('click', (e)=>{
    if(!topNav.contains(e.target) && topNav.classList.contains('open')){
      topNav.classList.remove('open');
    }
  });
}

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

function openModal(modal){
  if(!modal) return;
  modal.setAttribute('aria-hidden','false');
}
function closeModal(modal){
  if(!modal) return;
  modal.setAttribute('aria-hidden','true');
}

[sellerBtn, riderBtn, footerSeller, footerRider].forEach(el=>{
  if(!el) return;
  el.addEventListener('click', (e)=>{
    e.preventDefault();
    if(el===sellerBtn || el===footerSeller) openModal(sellerModal);
    if(el===riderBtn || el===footerRider) openModal(riderModal);
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

const riderForm = document.getElementById('riderForm');
if(riderForm) riderForm.addEventListener('submit', (e)=>{
  e.preventDefault();
  alert('Rider registration received. We will contact you.');
  closeModal(riderModal);
});

const cartCountEl = document.getElementById('cartCount');
const snackbar = document.getElementById('snackbar');

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

document.querySelectorAll('.add-cart').forEach(btn=>{
  btn.addEventListener('click', (e)=>{
    const card = btn.closest('.product');
    const title = card?.querySelector('.title')?.textContent || 'Item';
    const priceText = card?.querySelector('.price')?.textContent || '£0';
    const price = parseFloat(priceText.replace(/[^0-9\.]/g,'')) || 0;
    const id = title.toLowerCase().replace(/\s+/g,'_').replace(/[^a-z0-9_]/g,'');
    const cart = readCart();
    if(!cart[id]) cart[id] = {title, price, qty:0};
    cart[id].qty += 1;
    writeCart(cart);
    updateCartBadge();
    if(snackbar){
      snackbar.textContent = `${title} added to cart`;
      snackbar.classList.add('show');
      setTimeout(()=> snackbar.classList.remove('show'), 2200);
    }
  });
});

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
document.addEventListener('DOMContentLoaded', ()=>{ renderCartPage(); });

const loginForm = document.getElementById('loginForm');
if(loginForm){
  loginForm.addEventListener('submit', function(e){
  });
}

const signupForm = document.getElementById('signupForm');
if(signupForm){
  signupForm.addEventListener('submit', function(e){
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

// Dashboard sidebar navigation
const dashboardContent = document.getElementById('dashboardContent');
const sideLinks = document.querySelectorAll('.side-link');

// Content templates for each page
const pageContent = {
  overview: `
    <!-- Stat cards -->
    <div class="grid stats">
      <div class="card"><div class="inner"><div class="metric">Total Revenue (PHP)</div><div class="value">₱1,250 <span class="delta">↑ 1%</span></div></div></div>
      <div class="card"><div class="inner"><div class="metric">Total Customers</div><div class="value">9 <span class="delta" style="color:#ef4444">↓ 0.2%</span></div></div></div>
      <div class="card"><div class="inner"><div class="metric">Total Transactions</div><div class="value">17 <span class="delta">↑ 1%</span></div></div></div>
      <div class="card"><div class="inner"><div class="metric">Total Products</div><div class="value">6 <span class="delta">↑ 1%</span></div></div></div>
    </div>

    <!-- Charts row -->
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

    <!-- Data row -->
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
    <h2 style="margin-bottom:16px">Sellers Management</h2>
    <div class="grid stats">
      <div class="card"><div class="inner"><div class="metric">Total Sellers</div><div class="value">8</div></div></div>
      <div class="card"><div class="inner"><div class="metric">Active Sellers</div><div class="value">6</div></div></div>
      <div class="card"><div class="inner"><div class="metric">Pending Approval</div><div class="value">2</div></div></div>
      <div class="card"><div class="inner"><div class="metric">Total Products</div><div class="value">45</div></div></div>
    </div>
    <div class="card" style="margin-top:14px">
      <div class="inner">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">
          <div class="metric">Seller List</div>
          <button class="tag" style="cursor:pointer">+ Approve Pending</button>
        </div>
        <table>
          <thead><tr><th>Seller Name</th><th>Store Name</th><th>Products</th><th>Sales</th><th>Status</th></tr></thead>
          <tbody>
            <tr><td>Fashion Hub</td><td>@fashionhub</td><td>12</td><td>₱45,230</td><td><span style="color:#10b981">Active</span></td></tr>
            <tr><td>Style Central</td><td>@stylecentral</td><td>8</td><td>₱32,100</td><td><span style="color:#10b981">Active</span></td></tr>
            <tr><td>Trend Shop</td><td>@trendshop</td><td>15</td><td>₱67,450</td><td><span style="color:#10b981">Active</span></td></tr>
            <tr><td>New Boutique</td><td>@newboutique</td><td>5</td><td>₱0</td><td><span style="color:#f59e0b">Pending</span></td></tr>
            <tr><td>Luxe Store</td><td>@luxestore</td><td>10</td><td>₱28,900</td><td><span style="color:#10b981">Active</span></td></tr>
          </tbody>
        </table>
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

// Handle sidebar link clicks
if (sideLinks && dashboardContent) {
  sideLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const page = link.dataset.page;
      
      // Update active state
      sideLinks.forEach(l => l.classList.remove('active'));
      link.classList.add('active');
      
      // Update page title
      const pageTitle = document.querySelector('.topbar .page-title');
      if (pageTitle) {
        pageTitle.textContent = link.textContent.trim();
      }
      
      // Load content
      if (pageContent[page]) {
        dashboardContent.innerHTML = pageContent[page];
      } else {
        dashboardContent.innerHTML = `<div class="card"><div class="inner"><h3>Page not found</h3><p>This section is under development.</p></div></div>`;
      }
    });
  });
}
