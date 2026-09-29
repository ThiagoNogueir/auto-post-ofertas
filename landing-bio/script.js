/* ==========================================================================
   Melhô Promo - Link in Bio Script
   Real-time Filtering, Search & Micro-interactions
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('group-search');
  const clearBtn = document.getElementById('clear-search');
  const filterPills = document.querySelectorAll('.filter-pill');
  const groupCards = document.querySelectorAll('.group-card');
  const noResults = document.getElementById('no-results');
  const resetSearchBtn = document.getElementById('reset-search-btn');

  let activeFilter = 'all';

  // Normalize text for diacritic-insensitive search
  const normalize = (text) => {
    return text
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '');
  };

  // Filter and Search Handler
  const applyFilters = () => {
    const searchTerm = normalize(searchInput.value.trim());
    let visibleCount = 0;

    // Toggle clear search button visibility
    clearBtn.style.display = searchInput.value.length > 0 ? 'block' : 'none';

    groupCards.forEach((card) => {
      const category = card.getAttribute('data-category');
      const textContent = normalize(card.textContent || '');

      // If typing in search bar, search across all cards
      const matchesFilter = searchTerm.length > 0 ? true : (activeFilter === 'all' || category === activeFilter);
      const matchesSearch = !searchTerm || textContent.includes(searchTerm);

      if (matchesFilter && matchesSearch) {
        card.style.display = 'grid';
        visibleCount++;
      } else {
        card.style.display = 'none';
      }
    });

    // Show or hide "No results" empty state
    if (noResults) {
      noResults.style.display = visibleCount === 0 ? 'block' : 'none';
    }
  };

  // Search Input Event
  if (searchInput) {
    searchInput.addEventListener('input', applyFilters);
  }

  // Clear Search Event
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      searchInput.value = '';
      applyFilters();
      searchInput.focus();
    });
  }

  // Category Filter Pills
  filterPills.forEach((pill) => {
    pill.addEventListener('click', () => {
      filterPills.forEach((p) => p.classList.remove('active'));
      pill.classList.add('active');
      activeFilter = pill.getAttribute('data-filter');
      applyFilters();
    });
  });

  // Reset Button in Empty State
  if (resetSearchBtn) {
    resetSearchBtn.addEventListener('click', () => {
      searchInput.value = '';
      activeFilter = 'all';
      filterPills.forEach((p) => p.classList.remove('active'));
      const allPill = document.querySelector('[data-filter="all"]');
      if (allPill) allPill.classList.add('active');
      applyFilters();
    });
  }

  // Click Tracking on WhatsApp Buttons
  const waButtons = document.querySelectorAll('.btn-whatsapp');
  waButtons.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      const card = btn.closest('.group-card');
      const groupName = card ? card.querySelector('.group-name')?.innerText : 'WhatsApp Group';
      
      // Optional Google Analytics / Meta Pixel event if configured
      if (typeof gtag === 'function') {
        gtag('event', 'join_group_click', {
          group_name: groupName
        });
      }
      if (typeof fbq === 'function') {
        fbq('trackCustom', 'JoinGroupClick', {
          group_name: groupName
        });
      }
    });
  });
});

// Subtle Card Appearance Keyframe
const styleSheet = document.createElement('style');
styleSheet.textContent = `
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(6px); }
    to { opacity: 1; transform: translateY(0); }
  }
`;
document.head.appendChild(styleSheet);
