// PocketSmart AI - Frontend helpers

function showLoading() {
  const el = document.getElementById('loading');
  if (el) el.classList.add('active');
}

function hideLoading() {
  const el = document.getElementById('loading');
  if (el) el.classList.remove('active');
}

// Hide loading on back navigation
window.addEventListener('pageshow', hideLoading);

// Format currency helper (if needed in future dynamic pages)
function formatINR(n) {
  return '₹' + Number(n).toLocaleString('en-IN', { maximumFractionDigits: 0 });
}
