// Function to initialize sidebar functionality
function initializeSidebar() {
    const sidebar = document.getElementById('sidebar');
    const content = document.getElementById('content');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const mobileMenuToggle = document.getElementById('mobileMenuToggle');

    // Toggle mini mode for desktop
    function toggleMiniMode() {
        document.body.classList.toggle('mini-sidebar');
        localStorage.setItem('sidebarMode', document.body.classList.contains('mini-sidebar') ? 'mini' : 'full');
    }
    
    // Toggle mobile menu
    function toggleMobileMenu() {
        document.body.classList.toggle('mobile-menu-open');
    }

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', toggleMiniMode);
    }

    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', toggleMobileMenu);
    }

    // Close mobile menu when clicking outside
    document.addEventListener('click', function(e) {
        if (document.body.classList.contains('mobile-menu-open') && 
            !sidebar.contains(e.target) && 
            !mobileMenuToggle.contains(e.target)) {
            toggleMobileMenu();
        }
    });

    // Restore previous state on desktop
    const savedMode = localStorage.getItem('sidebarMode');
    if (savedMode === 'mini' && window.innerWidth >= 992) {
        document.body.classList.add('mini-sidebar');
    }

    // Initialize collapse elements
    document.querySelectorAll('.collapse').forEach(collapse => {
        new bootstrap.Collapse(collapse, {
            toggle: false
        });
    });

    // Initialize active submenu
    checkActiveSubmenu();
}

// Function to check if URL matches any submenu item
function checkActiveSubmenu() {
    const currentPath = window.location.pathname;
    document.querySelectorAll('.sidebar-submenu .sidebar-link').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            const submenu = link.closest('.sidebar-submenu');
            if (submenu) {
                const collapseElement = bootstrap.Collapse.getInstance(submenu);
                if (collapseElement) {
                    collapseElement.show();
                }
            }
        }
    });
}

// Add click handler for collapse arrows
document.querySelectorAll('[data-bs-toggle="collapse"]').forEach(toggle => {
    toggle.addEventListener('click', function(e) {
        const currentTarget = this.getAttribute('href');
        const toggleIcon = this.querySelector('.toggle-icon');
        if (toggleIcon) {
            toggleIcon.classList.toggle('rotate');
        }
        document.querySelectorAll('.sidebar-submenu.show').forEach(submenu => {
            if ('#' + submenu.id !== currentTarget) {
                bootstrap.Collapse.getInstance(submenu).hide();
            }
        });
    });
});

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeSidebar();
});

// Initialize after HTMX content updates
document.body.addEventListener('htmx:afterSettle', initializeSidebar);

// Handle HTMX message triggers
document.body.addEventListener('htmx:afterOnLoad', function(evt) {
    const messageData = evt.detail.triggerSpec;
    if (messageData && messageData.showMessage) {
        const { message, type } = messageData.showMessage;
        const messageContainer = document.getElementById('message-container');
        
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.role = 'alert';
        
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        messageContainer.appendChild(alertDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }
});

// Handle messages
document.addEventListener('showMessage', function(event) {
    const messageContainer = document.getElementById('message-container');
    const { message, type } = event.detail;
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.role = 'alert';
    
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    messageContainer.appendChild(alertDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
});
