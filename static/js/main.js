// ============================================================
// Advance Tools & Spare Parts Hub — Front-end
// ============================================================

document.addEventListener("DOMContentLoaded", () => {

  const DEFAULT_WHATSAPP = "233593652536";

  // ==========================================================
  // LIGHTBOX
  // ==========================================================
  let images = [];
  let current = 0;

  const lightbox  = document.getElementById("lightbox");
  const lbImage   = document.getElementById("lbImage");
  const lbCaption = document.getElementById("lbCaption");
  const lbCounter = document.getElementById("lbCounter");
  const lbClose   = document.getElementById("lbClose");
  const lbPrev    = document.getElementById("lbPrev");
  const lbNext    = document.getElementById("lbNext");

  function refreshLightboxImages() {
    images = [...document.querySelectorAll(".js-open-lightbox")].map(el => {
      const card = el.closest(".product-card");
      return {
        src: el.dataset.img || "",
        title: card ? card.dataset.name : "",
        location: card ? card.dataset.location : "",
      };
    });
  }

  function showImage(i) {
    if (!images.length) return;
    current = (i + images.length) % images.length;
    const item = images[current];
    lbImage.src = item.src;
    lbCaption.textContent = `${item.title} — ${item.location}`;
    lbCounter.textContent = `${current + 1} / ${images.length}`;
  }

  function openLightbox(i) {
    refreshLightboxImages();
    showImage(i);
    lightbox.classList.add("open");
    lightbox.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
  }

  function closeLightbox() {
    lightbox.classList.remove("open");
    lightbox.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
  }

  function bindLightboxClicks() {
    document.querySelectorAll(".js-open-lightbox").forEach((el) => {
      if (el.dataset.lbBound === "1") return;
      el.dataset.lbBound = "1";
      el.addEventListener("click", () => {
        refreshLightboxImages();
        const idx = [...document.querySelectorAll(".js-open-lightbox")].indexOf(el);
        openLightbox(idx);
      });
    });
  }

  if (lightbox) {
    lbClose.addEventListener("click", closeLightbox);
    lbPrev.addEventListener("click", (e) => { e.stopPropagation(); showImage(current - 1); });
    lbNext.addEventListener("click", (e) => { e.stopPropagation(); showImage(current + 1); });

    lightbox.addEventListener("click", (e) => {
      if (e.target === lightbox) closeLightbox();
    });

    document.addEventListener("keydown", (e) => {
      if (!lightbox.classList.contains("open")) return;
      if (e.key === "Escape")     closeLightbox();
      if (e.key === "ArrowLeft")  showImage(current - 1);
      if (e.key === "ArrowRight") showImage(current + 1);
    });
  }

  bindLightboxClicks();

  // ==========================================================
  // WHATSAPP ORDER
  // ==========================================================
  function buildAbsoluteImageUrl(img) {
    if (!img) return "";
    if (img.startsWith("http://") || img.startsWith("https://")) return img;
    // Relative path like /static/uploads/xxx.jpg → prepend current origin
    return window.location.origin + img;
  }

  function buildOrderUrl({ name, specs, price, location, phone, image }) {
    const toolDetails = `${name} (${specs}) — GHS ${Number(price).toLocaleString()}, ${location}`;
    const absImage = buildAbsoluteImageUrl(image);

    // WhatsApp shows an image preview when the URL is on its own line
    const message =
`Hello! I saw your tool on the website and want to confirm if it is still available.

*Tool:* ${name}
*Specs:* ${specs}
*Price:* GHS ${Number(price).toLocaleString()}
*Location:* ${location}

${absImage}

I would like to order it. Thank you.`;

    const num = phone || DEFAULT_WHATSAPP;
    return `https://wa.me/${num}?text=${encodeURIComponent(message)}`;
  }

  document.body.addEventListener("click", (e) => {
    const btn = e.target.closest(".js-order");
    if (!btn) return;
    e.stopPropagation();

    const card = btn.closest(".product-card");
    if (!card) return;

    // Get the image — prefer the card image, fall back to the lightbox data-img
    const imgEl = card.querySelector(".card-image img");
    let image = "";
    if (imgEl) image = imgEl.getAttribute("src") || "";
    if (!image) {
      const lbEl = card.querySelector(".js-open-lightbox");
      if (lbEl) image = lbEl.dataset.img || "";
    }

    const url = buildOrderUrl({
      name:     card.dataset.name,
      specs:    card.dataset.specs,
      price:    card.dataset.price,
      location: card.dataset.location,
      phone:    card.dataset.phone,
      image:    image,
    });
    window.open(url, "_blank");
  });

  // ==========================================================
  // RANDOM GRID — refresh every 5 seconds
  // ==========================================================
  const grid = document.getElementById("randomGrid");

  function escapeHTML(s) {
    if (!s) return "";
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function cardHTML(p) {
    const img    = p.image || `https://picsum.photos/seed/tool${p.id}/600/600`;
    const bigImg = p.image || `https://picsum.photos/seed/tool${p.id}/1200/900`;
    const price  = Number(p.price).toLocaleString();

    return `
      <article class="product-card"
               data-id="${p.id}"
               data-name="${escapeHTML(p.name)}"
               data-location="${escapeHTML(p.location)}"
               data-price="${p.price}"
               data-specs="${escapeHTML(p.specs)}"
               data-phone="${p.phone || ''}">

        <div class="card-image js-open-lightbox" data-img="${bigImg}">
          <img src="${img}" alt="${escapeHTML(p.name)}">
        </div>

        <div class="card-body">
          <p class="card-title">${escapeHTML(p.name)}</p>
          <p class="card-specs">${escapeHTML(p.specs)}</p>
          <div class="card-bottom">
            <span class="card-price">GHS ${price}</span>
            <button class="cart-mini js-order" aria-label="Order">
              <i class="fa-solid fa-cart-shopping"></i>
            </button>
          </div>
        </div>
      </article>
    `;
  }

  async function rotateCards() {
    if (!grid) return;
    try {
      const res = await fetch("/api/random-cards", { cache: "no-store" });
      if (!res.ok) return;
      const cards = await res.json();
      if (!Array.isArray(cards) || cards.length === 0) return;

      grid.style.opacity = "0";
      setTimeout(() => {
        grid.innerHTML = cards.map(cardHTML).join("");
        bindLightboxClicks();
        grid.style.opacity = "1";
      }, 250);
    } catch (err) {
      // silent
    }
  }

  if (grid) setInterval(rotateCards, 5000);

  // ==========================================================
  // HERO — cycle featured images
  // ==========================================================
  const heroBg      = document.getElementById("heroBg");
  const heroSection = document.getElementById("heroSection");

  if (heroBg && heroSection) {
    let featuredImages = [];
    try {
      const raw = heroSection.dataset.featured || "[]";
      const parsed = JSON.parse(raw.replace(/'/g, '"'));
      featuredImages = parsed
        .map(f => f.image)
        .filter(img => img && img.trim().length > 0);
    } catch (e) {
      featuredImages = [];
    }

    if (featuredImages.length > 0) {
      heroBg.style.backgroundImage = `url('${featuredImages[0]}')`;

      if (featuredImages.length > 1) {
        let i = 1;
        setInterval(() => {
          heroBg.style.opacity = "0";
          setTimeout(() => {
            heroBg.style.backgroundImage = `url('${featuredImages[i]}')`;
            heroBg.style.opacity = "1";
            i = (i + 1) % featuredImages.length;
          }, 400);
        }, 5000);
      }
    }
  }

  // ==========================================================
  // SEARCH OVERLAY
  // ==========================================================
  const openSearchBtn     = document.getElementById("openSearch");
  const closeSearchBtn    = document.getElementById("closeSearch");
  const searchOverlay     = document.getElementById("searchOverlay");
  const searchInput       = document.getElementById("searchInput");
  const searchResults     = document.getElementById("searchResults");
  const headerSearchInput = document.getElementById("headerSearchInput");
  const headerSearchBtn   = document.getElementById("headerSearchBtn");

  function openSearchOverlay() {
    if (!searchOverlay) return;
    searchOverlay.classList.add("open");
    searchOverlay.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
    setTimeout(() => searchInput && searchInput.focus(), 60);
  }

  function closeSearchOverlay() {
    if (!searchOverlay) return;
    searchOverlay.classList.remove("open");
    searchOverlay.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
    if (searchInput) searchInput.value = "";
    renderSearchResults("");
  }

  function highlight(text, query) {
    if (!query) return text;
    const i = text.toLowerCase().indexOf(query.toLowerCase());
    if (i === -1) return text;
    return text.slice(0, i) +
      "<mark>" + text.slice(i, i + query.length) + "</mark>" +
      text.slice(i + query.length);
  }

  function renderSearchResults(query) {
    if (!searchResults) return;
    query = (query || "").trim().toLowerCase();

    if (!query) {
      searchResults.innerHTML = `<p class="search-hint">Start typing to search the site…</p>`;
      return;
    }

    // Search across all product cards on the page
    const cards = [...document.querySelectorAll(".product-card")].map(card => ({
      id:       card.dataset.id,
      name:     card.dataset.name || "",
      specs:    card.dataset.specs || "",
      location: card.dataset.location || "",
      price:    card.dataset.price || 0,
      phone:    card.dataset.phone || "",
    }));

    const matches = cards.filter(p =>
      p.name.toLowerCase().includes(query) ||
      p.specs.toLowerCase().includes(query) ||
      p.location.toLowerCase().includes(query)
    );

    if (!matches.length) {
      searchResults.innerHTML = `<p class="search-hint">No results for “${query}”.</p>`;
      return;
    }

    searchResults.innerHTML = matches.map(p => `
      <div class="search-result" data-id="${p.id}">
        <div class="sr-info">
          <p class="sr-name">${highlight(p.name, query)}</p>
          <p class="sr-meta">${highlight(p.specs, query)} — ${p.location}</p>
        </div>
        <div class="sr-right">
          <span class="sr-price">GHS ${Number(p.price).toLocaleString()}</span>
        </div>
      </div>
    `).join("");

    searchResults.querySelectorAll(".search-result").forEach(row => {
      const product = matches.find(p => p.id === row.dataset.id);
      row.addEventListener("click", () => {
        const url = buildOrderUrl(product);
        window.open(url, "_blank");
      });
    });
  }

  if (openSearchBtn)  openSearchBtn.addEventListener("click", openSearchOverlay);
  if (closeSearchBtn) closeSearchBtn.addEventListener("click", closeSearchOverlay);

  if (searchInput) {
    searchInput.addEventListener("input", (e) => renderSearchResults(e.target.value));
  }

  function handleHeaderSearch() {
    const q = (headerSearchInput && headerSearchInput.value) || "";
    openSearchOverlay();
    if (searchInput) {
      searchInput.value = q;
      renderSearchResults(q);
    }
  }

  if (headerSearchBtn) headerSearchBtn.addEventListener("click", handleHeaderSearch);

  if (headerSearchInput) {
    headerSearchInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") handleHeaderSearch();
    });
  }

  if (searchOverlay) {
    searchOverlay.addEventListener("click", (e) => {
      if (e.target === searchOverlay) closeSearchOverlay();
    });
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && searchOverlay && searchOverlay.classList.contains("open")) {
      closeSearchOverlay();
    }
  });

  console.log("Advance Tools & Spare Parts Hub loaded ✅");
});