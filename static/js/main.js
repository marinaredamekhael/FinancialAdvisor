/**
 * Main.js - General application functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Flash message auto-dismiss
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(message => {
        setTimeout(() => {
            const alert = new bootstrap.Alert(message);
            alert.close();
        }, 5000); // Auto-dismiss after 5 seconds
    });
    
    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
    
    // Add to portfolio from any page
    setupPortfolioModal();
    
    // Setup search functionality
    setupSearch();
});

// Portfolio modal functionality
function setupPortfolioModal() {
    const addToPortfolioModal = document.getElementById('addToPortfolioModal');
    if (addToPortfolioModal) {
        addToPortfolioModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            if (!button) return;
            
            const symbol = button.getAttribute('data-symbol');
            const name = button.getAttribute('data-name');
            
            if (!symbol) return;
            
            const symbolInput = addToPortfolioModal.querySelector('[name="symbol"]');
            const stockDisplay = addToPortfolioModal.querySelector('#stock_display');
            const priceInput = addToPortfolioModal.querySelector('#purchase_price');
            
            if (symbolInput) {
                symbolInput.value = symbol;
            }
            
            if (stockDisplay) {
                stockDisplay.value = name ? `${symbol} - ${name}` : symbol;
            }
            
            // Fetch current price if needed
            if (priceInput && !priceInput.value) {
                fetchStockPrice(symbol, priceInput);
            }
        });
    }
}

// Fetch current stock price
function fetchStockPrice(symbol, priceInput) {
    fetch(`/api/stock-price/${symbol}`)
        .then(response => response.json())
        .then(data => {
            if (priceInput && data.price) {
                priceInput.value = data.price.toFixed(2);
            }
        })
        .catch(error => {
            console.error('Error fetching stock price:', error);
        });
}

// Setup search functionality
function setupSearch() {
    const searchForm = document.getElementById('searchForm');
    const searchInput = document.getElementById('searchInput');
    
    if (searchForm && searchInput) {
        searchForm.addEventListener('submit', function(event) {
            const query = searchInput.value.trim();
            if (!query) {
                event.preventDefault();
            }
        });
    }
}

// Format number with commas
function formatNumber(number) {
    return new Intl.NumberFormat().format(number);
}

// Format dates for better display
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
}

// Get current date and time
function now() {
    return new Date();
}


