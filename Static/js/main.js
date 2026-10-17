/* ==========================================================================
   AETHEL & CO. - INTERACTIVE SHOPPING & CART ENGINE (main.js)
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  initCartDrawer();
  initToastSystem();
  initWishlistHandlers();
  initProductGallery();
  initQuantityControls();
  initSearchAutocomplete();
  initMobileNavigation();
  initMobileSearch();
});

// Toast System
function showToast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  
  const iconClass = type === 'success' ? 'fa-circle-check text-emerald-400' : 'fa-circle-exclamation text-rose-400';
  toast.innerHTML = `
    <i class="fa-solid ${iconClass}"></i>
    <span>${message}</span>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(50px)';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// Quick Cart Drawer Management
function initCartDrawer() {
  const openButtons = document.querySelectorAll('.open-cart-btn');
  const closeButton = document.getElementById('close-cart-btn');
  const overlay = document.getElementById('cart-drawer-overlay');
  const drawer = document.getElementById('cart-drawer');

  if (!drawer) return;

  openButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      openCartDrawer();
    });
  });

  if (closeButton) {
    closeButton.addEventListener('click', closeCartDrawer);
  }

  if (overlay) {
    overlay.addEventListener('click', closeCartDrawer);
  }

  // Bind add-to-cart buttons
  document.querySelectorAll('.add-to-cart-form').forEach(form => {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(form);
      const productId = formData.get('product_id');
      const quantity = formData.get('quantity') || 1;

      try {
        const response = await fetch('/api/cart/add', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ product_id: parseInt(productId), quantity: parseInt(quantity) })
        });

        const data = await response.json();
        if (data.success) {
          showToast(data.message || 'Added to cart!');
          updateCartUI(data.cart);
          openCartDrawer();
        } else {
          showToast(data.message || 'Could not add item.', 'error');
        }
      } catch (err) {
        console.error('Cart add error:', err);
        showToast('Error adding item to cart', 'error');
      }
    });
  });
}

function openCartDrawer() {
  const drawer = document.getElementById('cart-drawer');
  const overlay = document.getElementById('cart-drawer-overlay');
  if (drawer && overlay) {
    drawer.classList.add('open');
    overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
  }
}

function closeCartDrawer() {
  const drawer = document.getElementById('cart-drawer');
  const overlay = document.getElementById('cart-drawer-overlay');
  if (drawer && overlay) {
    drawer.classList.remove('open');
    overlay.classList.remove('open');
    document.body.style.overflow = '';
  }
}

// Update Cart Badge and Drawer Content
function updateCartUI(cart) {
  // Update badge count
  const badges = document.querySelectorAll('.cart-badge-count');
  const totalCount = cart.items.reduce((sum, item) => sum + item.quantity, 0);
  badges.forEach(b => {
    b.textContent = totalCount;
    b.style.display = totalCount > 0 ? 'flex' : 'none';
  });

  // Update Drawer list
  const drawerItems = document.getElementById('cart-drawer-items');
  const drawerSubtotal = document.getElementById('cart-drawer-subtotal');
  
  if (drawerItems) {
    if (cart.items.length === 0) {
      drawerItems.innerHTML = `
        <div style="text-align: center; padding: 3rem 1rem; color: var(--text-muted);">
          <i class="fa-solid fa-basket-shopping" style="font-size: 2.5rem; margin-bottom: 1rem; opacity: 0.5;"></i>
          <p style="font-size: 1rem; color: #fff; margin-bottom: 0.5rem;">Your cart is empty</p>
          <p style="font-size: 0.85rem;">Discover our latest luxury collections.</p>
        </div>
      `;
    } else {
      drawerItems.innerHTML = cart.items.map(item => `
        <div class="drawer-item">
          <div class="drawer-item-img">
            <img src="${item.image_url}" alt="${item.name}">
          </div>
          <div class="drawer-item-details">
            <div class="drawer-item-title">${item.name}</div>
            <div class="drawer-item-price">$${item.price.toFixed(2)}</div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <div class="qty-control" style="transform: scale(0.85); transform-origin: left center;">
                <button type="button" class="qty-btn" onclick="updateCartItemQty(${item.product_id}, ${item.quantity - 1})">-</button>
                <span class="qty-input">${item.quantity}</span>
                <button type="button" class="qty-btn" onclick="updateCartItemQty(${item.product_id}, ${item.quantity + 1})">+</button>
              </div>
              <button type="button" onclick="removeCartItem(${item.product_id})" style="color: var(--text-muted); font-size: 0.8rem; cursor: pointer;">
                <i class="fa-solid fa-trash-can"></i>
              </button>
            </div>
          </div>
        </div>
      `).join('');
    }
  }

  if (drawerSubtotal) {
    drawerSubtotal.textContent = `$${cart.subtotal.toFixed(2)}`;
  }
}

async function updateCartItemQty(productId, newQty) {
  try {
    const response = await fetch('/api/cart/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ product_id: productId, quantity: newQty })
    });
    const data = await response.json();
    if (data.success) {
      updateCartUI(data.cart);
      // If on cart page, reload or update table
      if (window.location.pathname.includes('/cart')) {
        window.location.reload();
      }
    }
  } catch (err) {
    console.error(err);
  }
}

async function removeCartItem(productId) {
  await updateCartItemQty(productId, 0);
  showToast('Item removed from cart');
}

// Wishlist Handler
function initWishlistHandlers() {
  document.querySelectorAll('.wishlist-toggle-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      const productId = btn.getAttribute('data-product-id');
      try {
        const response = await fetch('/api/wishlist/toggle', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ product_id: parseInt(productId) })
        });
        const data = await response.json();
        if (data.success) {
          if (data.action === 'added') {
            btn.classList.add('active');
            btn.querySelector('i').classList.replace('fa-regular', 'fa-solid');
            showToast('Added to your wishlist!');
          } else {
            btn.classList.remove('active');
            btn.querySelector('i').classList.replace('fa-solid', 'fa-regular');
            showToast('Removed from wishlist');
          }
          const badge = document.querySelector('.wishlist-badge-count');
          if (badge && data.wishlist_count !== undefined) {
            badge.textContent = data.wishlist_count;
            badge.style.display = data.wishlist_count > 0 ? 'flex' : 'none';
          }
        }
      } catch (err) {
        console.error(err);
      }
    });
  });
}

// Product Detail Gallery Switcher
function initProductGallery() {
  const mainImage = document.getElementById('main-product-image');
  const thumbs = document.querySelectorAll('.thumb-item');

  thumbs.forEach(thumb => {
    thumb.addEventListener('click', () => {
      thumbs.forEach(t => t.classList.remove('active'));
      thumb.classList.add('active');
      const targetSrc = thumb.getAttribute('data-full-src') || thumb.querySelector('img').src;
      if (mainImage) {
        mainImage.src = targetSrc;
      }
    });
  });
}

// Quantity +/- buttons on product detail page
function initQuantityControls() {
  const decreaseBtn = document.getElementById('qty-decrease');
  const increaseBtn = document.getElementById('qty-increase');
  const qtyInput = document.getElementById('product-quantity-input');

  if (!qtyInput) return;

  if (decreaseBtn) {
    decreaseBtn.addEventListener('click', () => {
      let val = parseInt(qtyInput.value) || 1;
      if (val > 1) qtyInput.value = val - 1;
    });
  }

  if (increaseBtn) {
    increaseBtn.addEventListener('click', () => {
      let val = parseInt(qtyInput.value) || 1;
      const max = parseInt(qtyInput.getAttribute('max')) || 99;
      if (val < max) qtyInput.value = val + 1;
    });
  }
}

// Live Search Autocomplete
function initSearchAutocomplete() {
  const searchInput = document.getElementById('header-search-input');
  const resultsContainer = document.getElementById('search-dropdown-results');

  if (!searchInput || !resultsContainer) return;

  let debounceTimer;

  searchInput.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    const query = searchInput.value.trim();

    if (query.length < 2) {
      resultsContainer.style.display = 'none';
      return;
    }

    debounceTimer = setTimeout(async () => {
      try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const data = await res.json();

        if (data.products && data.products.length > 0) {
          resultsContainer.innerHTML = data.products.map(p => `
            <a href="/product/${p.slug}" class="search-result-row" style="display: flex; align-items: center; gap: 0.8rem; padding: 0.6rem 1rem; border-bottom: 1px solid var(--border-color); color: #fff;">
              <img src="${p.image_url}" style="width: 38px; height: 38px; border-radius: 6px; object-fit: cover;">
              <div style="flex: 1;">
                <div style="font-size: 0.88rem; font-weight: 600;">${p.name}</div>
                <div style="font-size: 0.8rem; color: var(--accent-primary);">$${p.price.toFixed(2)}</div>
              </div>
            </a>
          `).join('');
          resultsContainer.style.display = 'block';
        } else {
          resultsContainer.innerHTML = `
            <div style="padding: 1rem; text-align: center; color: var(--text-muted); font-size: 0.85rem;">
              No products found for "${query}"
            </div>
          `;
          resultsContainer.style.display = 'block';
        }
      } catch (err) {
        console.error(err);
      }
    }, 250);
  });

  document.addEventListener('click', (e) => {
    if (!searchInput.contains(e.target) && !resultsContainer.contains(e.target)) {
      resultsContainer.style.display = 'none';
    }
  });
}

// Mobile Slide-out Drawer Navigation
function initMobileNavigation() {
  const toggleBtn = document.getElementById('mobile-nav-toggle');
  if (toggleBtn) {
    toggleBtn.addEventListener('click', openMobileMenu);
  }

  // Close on Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeMobileMenu();
      closeMobileSearch();
    }
  });
}

function openMobileMenu() {
  const drawer = document.getElementById('mobile-nav-drawer');
  const overlay = document.getElementById('mobile-nav-overlay');
  if (drawer && overlay) {
    drawer.classList.add('open');
    overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
  }
}

function closeMobileMenu() {
  const drawer = document.getElementById('mobile-nav-drawer');
  const overlay = document.getElementById('mobile-nav-overlay');
  if (drawer && overlay) {
    drawer.classList.remove('open');
    overlay.classList.remove('open');
    document.body.style.overflow = '';
  }
}

// Mobile Search Modal & Live Autocomplete
function initMobileSearch() {
  const openBtn = document.getElementById('open-mobile-search-btn');
  const modalInput = document.getElementById('mobile-search-input');
  const clearBtn = document.getElementById('clear-mobile-search-btn');
  const liveResults = document.getElementById('mobile-live-search-results');
  
  if (openBtn) {
    openBtn.addEventListener('click', openMobileSearch);
  }

  if (modalInput) {
    let debounceTimer;

    modalInput.addEventListener('input', () => {
      const query = modalInput.value.trim();
      if (clearBtn) {
        clearBtn.style.display = query.length > 0 ? 'flex' : 'none';
      }

      if (!liveResults) return;

      clearTimeout(debounceTimer);
      if (query.length < 2) {
        liveResults.style.display = 'none';
        liveResults.innerHTML = '';
        return;
      }

      debounceTimer = setTimeout(async () => {
        try {
          const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
          const data = await res.json();

          if (data.products && data.products.length > 0) {
            liveResults.innerHTML = `
              <div style="font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; font-weight: 700; margin-bottom: 0.5rem; letter-spacing: 0.05em;">Matching Clinical Formulations (${data.products.length}):</div>
              <div style="display: flex; flex-direction: column; gap: 0.5rem; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-md); overflow: hidden;">
                ${data.products.map(p => `
                  <a href="/product/${p.slug}" class="mobile-search-live-item" onclick="closeMobileSearch()" style="display: flex; align-items: center; gap: 0.75rem; padding: 0.65rem 0.85rem; border-bottom: 1px solid rgba(255,255,255,0.05); color: #fff;">
                    <img src="${p.image_url}" alt="${p.name}" style="width: 44px; height: 44px; border-radius: 6px; object-fit: cover; background: #0f172a; flex-shrink: 0;">
                    <div style="flex: 1; min-width: 0;">
                      <div style="font-size: 0.88rem; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${p.name}</div>
                      <div style="font-size: 0.8rem; color: #10b981; font-weight: 700;">$${p.price.toFixed(2)}</div>
                    </div>
                    <i class="fa-solid fa-chevron-right" style="font-size: 0.75rem; color: var(--text-muted);"></i>
                  </a>
                `).join('')}
              </div>
            `;
            liveResults.style.display = 'block';
          } else {
            liveResults.innerHTML = `
              <div style="padding: 1.25rem; text-align: center; color: var(--text-secondary); background: var(--bg-card); border-radius: var(--radius-md); border: 1px solid var(--border-color); font-size: 0.88rem;">
                <i class="fa-solid fa-flask" style="font-size: 1.5rem; color: #10b981; margin-bottom: 0.5rem; display: block;"></i>
                No formulations found for "${query}"
              </div>
            `;
            liveResults.style.display = 'block';
          }
        } catch (err) {
          console.error(err);
        }
      }, 200);
    });

    modalInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        const form = document.getElementById('mobile-search-form');
        if (form) form.submit();
      }
    });
  }
}

function clearMobileSearchInput() {
  const input = document.getElementById('mobile-search-input');
  const clearBtn = document.getElementById('clear-mobile-search-btn');
  const liveResults = document.getElementById('mobile-live-search-results');
  if (input) {
    input.value = '';
    input.focus();
  }
  if (clearBtn) clearBtn.style.display = 'none';
  if (liveResults) {
    liveResults.style.display = 'none';
    liveResults.innerHTML = '';
  }
}

function openMobileSearch() {
  const modal = document.getElementById('mobile-search-modal');
  const input = document.getElementById('mobile-search-input');
  if (modal) {
    modal.classList.add('open');
    document.body.style.overflow = 'hidden';
    if (input) {
      setTimeout(() => input.focus(), 150);
    }
  }
}

function closeMobileSearch() {
  const modal = document.getElementById('mobile-search-modal');
  if (modal) {
    modal.classList.remove('open');
    document.body.style.overflow = '';
  }
}

// Mobile Filter Sheet
function openMobileFilterSheet() {
  const sheet = document.getElementById('mobile-filter-sheet');
  const overlay = document.getElementById('mobile-filter-sheet-overlay');
  if (sheet && overlay) {
    overlay.classList.add('open');
    sheet.classList.add('open');
    document.body.style.overflow = 'hidden';
  }
}

function closeMobileFilterSheet() {
  const sheet = document.getElementById('mobile-filter-sheet');
  const overlay = document.getElementById('mobile-filter-sheet-overlay');
  if (sheet && overlay) {
    sheet.classList.remove('open');
    overlay.classList.remove('open');
    document.body.style.overflow = '';
  }
}

// 1-Tap Clipboard Copy Helper with Toast Notification
function copyToClipboard(text, message = 'Copied to clipboard!') {
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text).then(() => {
      showToast(message, 'success');
    }).catch(() => {
      fallbackCopyTextToClipboard(text, message);
    });
  } else {
    fallbackCopyTextToClipboard(text, message);
  }
}

function fallbackCopyTextToClipboard(text, message) {
  const textArea = document.createElement("textarea");
  textArea.value = text;
  textArea.style.position = "fixed";
  textArea.style.top = "0";
  textArea.style.left = "0";
  textArea.style.opacity = "0";
  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();
  try {
    document.execCommand('copy');
    showToast(message, 'success');
  } catch (err) {
    console.error('Fallback copy failed', err);
    showToast('Failed to copy', 'error');
  }
  document.body.removeChild(textArea);
}

// Interactive Routine Analyzer Modal Controls
function openRoutineAnalyzer() {
  const modal = document.getElementById('routine-analyzer-modal');
  const overlay = document.getElementById('routine-analyzer-overlay');
  if (modal && overlay) {
    overlay.classList.add('open');
    modal.classList.add('open');
    document.body.style.overflow = 'hidden';
  }
}

function closeRoutineAnalyzer() {
  const modal = document.getElementById('routine-analyzer-modal');
  const overlay = document.getElementById('routine-analyzer-overlay');
  if (modal && overlay) {
    modal.classList.remove('open');
    overlay.classList.remove('open');
    document.body.style.overflow = '';
  }
}


