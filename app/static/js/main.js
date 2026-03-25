// ── Sidebar toggle ──────────────────────────────────────────────────────────
const sidebarToggle = document.getElementById('sidebarToggle');
const sidebar       = document.getElementById('sidebar');
if (sidebarToggle && sidebar) {
  const isMobile = () => window.innerWidth <= 768;

  // Restore desktop collapsed state
  if (!isMobile() && localStorage.getItem('sidebarCollapsed') === 'true') {
    sidebar.classList.add('collapsed');
  }

  sidebarToggle.addEventListener('click', () => {
    if (isMobile()) {
      sidebar.classList.toggle('open');
    } else {
      sidebar.classList.toggle('collapsed');
      localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
    }
  });

  // Close on outside click (mobile)
  document.addEventListener('click', (e) => {
    if (isMobile() &&
        !sidebar.contains(e.target) &&
        !sidebarToggle.contains(e.target)) {
      sidebar.classList.remove('open');
    }
  });
}

// ── Auto-dismiss flash alerts ───────────────────────────────────────────────
document.querySelectorAll('.alert.fade.show').forEach(el => {
  setTimeout(() => {
    const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
    if (bsAlert) bsAlert.close();
  }, 4500);
});

// ── Deadline coloring helper ─────────────────────────────────────────────────
// Called from templates via inline data attrs
function colorDeadline(dateStr) {
  if (!dateStr) return '';
  const d    = new Date(dateStr);
  const now  = new Date();
  const diff = Math.ceil((d - now) / 86400000);
  if (diff < 0)  return 'expired';
  if (diff <= 7) return 'soon';
  return 'ok';
}
