// ============================================================
// Advance Tools & Spare Parts Hub — Front-end
// ============================================================

document.addEventListener("DOMContentLoaded", () => {

  // ==========================================================
  // LIGHTBOX
  // ==========================================================
  const images = [...document.querySelectorAll(".js-open-lightbox")].map(el => ({
    src: el.dataset.img,
    title: el.closest(".product-card").dataset.name,
    location: el.closest(".product-card").dataset.location,
  }));

  const lightbox  = document.getElementById("lightbox");
  const lbImage   = document.getElementById("lbImage");
  const lbCaption = document.getElementById("lbCaption");
  const lbCounter = document.getElementById("lbCounter");
  const lbClose   = document.getElementById("lbClose");
  const lbPrev    = document.getElementById("lbPrev");
  const lbNext    = document.getElementById("lbNext");

  let current = 0;

  function showImage(i) {
    if (!images.length) return;
    current = (i + images.length) % images.length;
    const item = images[current];
    lbImage.src = item.src;
    lbCaption.textContent = `${item.title} — ${item.location}`;
    lbCounter.textContent = `${current + 1} / ${images.length}`;
  }

  function openLightbox(i) {
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

  document.querySelectorAll(".js-open-lightbox").forEach((el, i) => {
    el.addEventListener("click", () => openLightbox(i));
  });

  if (lbClose) {
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

  // ==========================================================
  // ORDER ON WHATSAPP  (used by cards + search results)
  // ==========================================================
  const WHATSAPP_NUMBER = "233241697294"; // 0241697294

  function buildOrderUrl({ name, specs, price, location }) {
    const toolDetails = `${name} (${specs}) — ₵${Number(price).toLocaleString()}, ${location}`;
    const message =
`Hello! I saw your tool ${toolDetails} on the website and want to confirm if it is still available and I will like to order it. Thank you.`;
    return `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(message)}`;
  }

  document.querySelectorAll(".js-order").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const url = buildOrderUrl({
        name:     btn.dataset.name,
        specs:    btn.dataset.specs,
        price:    btn.dataset.price,
        location: btn.dataset.location,
      });
      window.open(url, "_blank");
    });
  });

  // ==========================================================
  // SEARCH OVERLAY — live filtering
  // ==========================================================
  const openBtn     = document.getElementById("openSearch");
  const closeBtn    = document.getElementById("closeSearch");
  const overlay     = document.getElementById("searchOverlay");
  const input       = document.getElementById("searchInput");
  const resultsBox  = document.getElementById("searchResults");

  // Build a searchable list from the product cards currently on the page
  const searchable = [...document.querySelectorAll(".product-card")].map(card => ({
    id:       card.dataset.id,
    name:     card.dataset.name,
    location: card.dataset.location,
    price:    card.dataset.price,
    specs:    card.dataset.specs,
  }));

  function openSearch() {
    overlay.classList.add("open");
    overlay.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
    setTimeout(() => input.focus(), 80);
  }

  function closeSearch() {
    overlay.classList.remove("open");
    overlay.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
    input.value = "";
    renderResults("");
  }

  function highlight(text, query) {
    if (!query) return text;
    const i = text.toLowerCase().indexOf(query.toLowerCase());
    if (i === -1) return text;
    return text.slice(0, i) +
      "<mark>" + text.slice(i, i + query.length) + "</mark>" +
      text.slice(i + query.length);
  }

  function renderResults(query) {
    query = query.trim().toLowerCase();

    if (!query) {
      resultsBox.innerHTML = `<p class="search-hint">Start typing to see matching tools…</p>`;
      return;
    }

    const matches = searchable.filter(p =>
      p.name.toLowerCase().includes(query) ||
      p.specs.toLowerCase().includes(query) ||
      p.location.toLowerCase().includes(query)
    );

    if (!matches.length) {
      resultsBox.innerHTML = `<p class="search-hint">No tools match “${query}”.</p>`;
      return;
    }

    resultsBox.innerHTML = matches.map(p => `
      <div class="search-result" data-id="${p.id}">
        <div class="sr-info">
          <p class="sr-name">${highlight(p.name, query)}</p>
          <p class="sr-meta">${highlight(p.specs, query)} — ${p.location}</p>
        </div>
        <div class="sr-right">
          <span class="sr-price">₵${Number(p.price).toLocaleString()}</span>
          <button class="sr-order" title="Order on WhatsApp">
            <i class="fa-brands fa-whatsapp"></i>
          </button>
        </div>
      </div>
    `).join("");

    // Clicking a result row → open WhatsApp order
    resultsBox.querySelectorAll(".search-result").forEach(row => {
      const product = searchable.find(p => p.id === row.dataset.id);
      row.addEventListener("click", (e) => {
        // If user clicked the WhatsApp button, only open WhatsApp
        const url = buildOrderUrl(product);
        window.open(url, "_blank");
      });
    });
  }

  if (openBtn)  openBtn.addEventListener("click", openSearch);
  if (closeBtn) closeBtn.addEventListener("click", closeSearch);

  if (input) {
    input.addEventListener("input", (e) => renderResults(e.target.value));
  }

  if (overlay) {
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) closeSearch();
    });
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && overlay.classList.contains("open")) closeSearch();
  });

  console.log("Advance Tools & Spare Parts Hub loaded ✅");
});