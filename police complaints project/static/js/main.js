// Toast Notification System
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) {
        const div = document.createElement('div');
        div.id = 'toast-container';
        div.className = 'toast-container';
        document.body.appendChild(div);
    }
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let icon = 'info-circle';
    if (type === 'success') icon = 'check-circle';
    if (type === 'danger') icon = 'exclamation-circle';
    if (type === 'warning') icon = 'exclamation-triangle';
    
    toast.innerHTML = `
        <i class="fas fa-${icon}"></i>
        <span>${message}</span>
    `;
    
    document.getElementById('toast-container').appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s reverse forwards';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Client-side Navigation Menu Active Link Highlighter
document.addEventListener('DOMContentLoaded', () => {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-links a, .sidebar-item a');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
            if (link.closest('.sidebar-item')) {
                link.closest('.sidebar-item').classList.add('active');
            }
        }
    });

    // Initialize Multi-step Form Wizard (if on Submit Complaint page)
    initFormWizard();
});

// Step-by-Step Form Wizard
function initFormWizard() {
    const wizardForm = document.getElementById('complaint-wizard-form');
    if (!wizardForm) return;

    const steps = Array.from(document.querySelectorAll('.wizard-step'));
    const stepNodes = Array.from(document.querySelectorAll('.step-node'));
    const nextBtn = document.getElementById('btn-next');
    const prevBtn = document.getElementById('btn-prev');
    const submitBtn = document.getElementById('btn-submit');
    let currentStep = 0;

    function showStep(index) {
        steps.forEach((step, idx) => {
            step.style.display = idx === index ? 'block' : 'none';
        });
        
        stepNodes.forEach((node, idx) => {
            node.className = 'step-node';
            if (idx === index) node.classList.add('active');
            if (idx < index) node.classList.add('completed');
        });

        // Toggle buttons
        if (prevBtn) prevBtn.style.display = index === 0 ? 'none' : 'inline-flex';
        if (nextBtn) nextBtn.style.display = index === steps.length - 1 ? 'none' : 'inline-flex';
        if (submitBtn) submitBtn.style.display = index === steps.length - 1 ? 'inline-flex' : 'none';
    }

    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            if (validateStep(currentStep)) {
                currentStep++;
                showStep(currentStep);
            }
        });
    }

    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            currentStep--;
            showStep(currentStep);
        });
    }

    function validateStep(stepIndex) {
        const currentStepEl = steps[stepIndex];
        const inputs = currentStepEl.querySelectorAll('[required]');
        let valid = true;

        inputs.forEach(input => {
            if (!input.value.trim()) {
                valid = false;
                input.style.borderColor = 'var(--danger)';
                showToast(`Please fill in the required field: ${input.previousElementSibling ? input.previousElementSibling.textContent : 'Field'}`, 'warning');
            } else {
                input.style.borderColor = '';
            }
        });

        return valid;
    }

    showStep(currentStep);
}

// Modal handling (Admin & User details)
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.add('active');
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove('active');
}

// Global click handler to close modals when clicking outside
window.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('active');
    }
});

// Admin Dashboard - Load Charts
function initAdminCharts(categoriesData, statusData) {
    const categoryCtx = document.getElementById('categoryChart');
    const statusCtx = document.getElementById('statusChart');

    if (categoryCtx) {
        new Chart(categoryCtx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(categoriesData),
                datasets: [{
                    data: Object.values(categoriesData),
                    backgroundColor: [
                        '#6366f1', // Indigo
                        '#a855f7', // Purple
                        '#ec4899', // Pink
                        '#3b82f6', // Blue
                        '#10b981'  // Emerald Green
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#9ca3af',
                            font: { family: 'Plus Jakarta Sans' }
                        }
                    }
                }
            }
        });
    }

    if (statusCtx) {
        new Chart(statusCtx, {
            type: 'bar',
            data: {
                labels: Object.keys(statusData),
                datasets: [{
                    label: 'Complaints',
                    data: Object.values(statusData),
                    backgroundColor: '#8e99f3',
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: '#9ca3af' }
                    },
                    y: {
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#9ca3af', stepSize: 1 }
                    }
                }
            }
        });
    }
}
