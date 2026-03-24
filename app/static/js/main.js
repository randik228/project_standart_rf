// ── Sidebar toggle ──────────────────────────────────────────────────────────
const sidebarToggle = document.getElementById('sidebarToggle');
const sidebar       = document.getElementById('sidebar');
if (sidebarToggle && sidebar) {
  sidebarToggle.addEventListener('click', () => {
    sidebar.classList.toggle('open');
  });
  // Close on outside click (mobile)
  document.addEventListener('click', (e) => {
    if (window.innerWidth <= 768 &&
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
