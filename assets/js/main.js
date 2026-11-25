// TinoDash4 - Estate Decision Support Dashboard
// Privacy-first: no personal information stored or transmitted

document.addEventListener('DOMContentLoaded', function() {
  // Smooth scrolling for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        target.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });

  // Mobile menu toggle (if needed)
  const navLinks = document.querySelectorAll('nav ul li a');
  navLinks.forEach(link => {
    link.addEventListener('click', () => {
      // Close mobile menu if open
    });
  });

  // Print briefing sheet
  const printBtn = document.getElementById('print-briefing');
  if (printBtn) {
    printBtn.addEventListener('click', () => {
      window.print();
    });
  }

  // Highlight current page in nav
  const currentPath = window.location.pathname.split('/').pop();
  navLinks.forEach(link => {
    const linkPath = link.getAttribute('href');
    if (linkPath && currentPath === linkPath) {
      link.style.borderBottom = '2px solid var(--primary)';
    }
  });

  // Console privacy reminder
  console.log('TinoDash4 - Privacy-first estate decision support. No PII stored.');
});

// Utility: format currency rounded to nearest $10
function formatCurrency(value) {
  const rounded = Math.round(value / 10) * 10;
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(rounded);
}

// Utility: round to nearest 10
function roundToTen(value) {
  return Math.round(value / 10) * 10;
}
