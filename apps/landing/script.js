document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('waitlist-form');
  const emailInput = document.getElementById('email');
  const messageDiv = document.getElementById('form-message');
  const ctaCard = document.querySelector('.cta-card');
  const submitBtn = form?.querySelector('button[type="submit"]');
  const btnLabel = submitBtn?.querySelector('.btn-label');

  // The API base URL from the project specification
  const apiBaseUrl = 'http://localhost:8000';

  // Restore email if user previously typed
  try {
    const saved = localStorage.getItem('waitlistEmail');
    if (saved && emailInput) emailInput.value = saved;
  } catch (_) {}

  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    const email = emailInput.value.trim();
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      showMessage('Please enter a valid email address.', 'error');
      emailInput.focus();
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${apiBaseUrl}/waitlist`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      const result = await response.json().catch(() => ({}));

      if (response.status === 201) {
        showMessage("You're on the list! We'll be in touch.", 'success');
        try { localStorage.setItem('waitlistEmail', email); } catch (_) {}
        celebrate();
        emailInput.value = '';
      } else if (response.status === 409) {
        showMessage('This email is already on the waitlist.', 'error');
      } else {
        const detail = result.detail || 'An unexpected error occurred.';
        showMessage(detail, 'error');
      }
    } catch (error) {
      console.error('Fetch error:', error);
      showMessage('Could not connect to the server. Please try again later.', 'error');
    } finally {
      setLoading(false);
    }
  });

  function setLoading(isLoading) {
    if (!submitBtn) return;
    submitBtn.disabled = isLoading;
    if (btnLabel) btnLabel.textContent = isLoading ? 'Joining…' : 'Join Waitlist';
  }

  function showMessage(message, type) {
    messageDiv.textContent = message;
    messageDiv.className = `form-message ${type === 'success' ? 'success-message' : 'error-message'}`;
    messageDiv.focus?.();
  }

  function celebrate() {
    if (!ctaCard) return;
    ctaCard.classList.remove('celebrate');
    // retrigger animation
    void ctaCard.offsetWidth;
    ctaCard.classList.add('celebrate');
  }
});
