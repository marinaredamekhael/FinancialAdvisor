/**
 * Portfolio.js - Portfolio management functionality
 */

// Handle portfolio table sorting
document.addEventListener('DOMContentLoaded', function() {
    const portfolioTable = document.getElementById('portfolioTable');
    
    if (portfolioTable) {
        const headers = portfolioTable.querySelectorAll('th');
        
        headers.forEach((header, index) => {
            if (index < headers.length - 1) { // Skip the actions column
                header.style.cursor = 'pointer';
                header.addEventListener('click', () => {
                    sortTable(portfolioTable, index);
                });
                
                // Add sort indicator
                header.innerHTML += ' <span class="sort-indicator"></span>';
            }
        });
    }
});

// Table sorting functionality
function sortTable(table, columnIndex) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const headers = table.querySelectorAll('th');
    const header = headers[columnIndex];
    
    // Determine sort direction
    const currentDirection = header.getAttribute('data-sort-direction') || 'none';
    let direction = 'asc';
    
    if (currentDirection === 'asc') {
        direction = 'desc';
    } else if (currentDirection === 'desc') {
        direction = 'asc';
    }
    
    // Reset all headers
    headers.forEach(h => {
        h.setAttribute('data-sort-direction', 'none');
        const indicator = h.querySelector('.sort-indicator');
        if (indicator) {
            indicator.textContent = '';
        }
    });
    
    // Set current header
    header.setAttribute('data-sort-direction', direction);
    const indicator = header.querySelector('.sort-indicator');
    if (indicator) {
        indicator.textContent = direction === 'asc' ? ' ↑' : ' ↓';
    }
    
    // Sort the rows
    rows.sort((a, b) => {
        const aContent = getCellContent(a, columnIndex);
        const bContent = getCellContent(b, columnIndex);
        
        if (isNumeric(aContent) && isNumeric(bContent)) {
            // Sort numbers
            return direction === 'asc' 
                ? parseFloat(aContent) - parseFloat(bContent)
                : parseFloat(bContent) - parseFloat(aContent);
        } else {
            // Sort strings
            return direction === 'asc'
                ? aContent.localeCompare(bContent)
                : bContent.localeCompare(aContent);
        }
    });
    
    // Re-append rows in sorted order
    rows.forEach(row => tbody.appendChild(row));
}

// Helper function to get content for sorting
function getCellContent(row, columnIndex) {
    const cell = row.cells[columnIndex];
    let content = '';
    
    // Try to extract text content
    if (cell) {
        // For price/value columns, extract the number without $ sign
        if (cell.textContent.trim().startsWith('$')) {
            content = cell.textContent.trim().replace('$', '').replace(/,/g, '');
        } 
        // For profit/loss percentage, extract just the number
        else if (cell.querySelector('.small')) {
            const percentText = cell.querySelector('.small').textContent.trim();
            content = percentText.replace('%', '').replace('+', '');
        }
        // Default case, just use the text content
        else {
            content = cell.textContent.trim();
        }
    }
    
    return content;
}

// Helper function to check if a string is numeric
function isNumeric(str) {
    return !isNaN(parseFloat(str)) && isFinite(str);
}

// Calculate portfolio diversity
function calculatePortfolioDiversity(portfolioItems) {
    // Count number of different sectors
    const sectors = new Set(portfolioItems.map(item => item.sector));
    
    // Calculate concentration (what % of portfolio is in largest position)
    const values = portfolioItems.map(item => item.current_value);
    const totalValue = values.reduce((a, b) => a + b, 0);
    const maxValue = Math.max(...values);
    const concentration = maxValue / totalValue;
    
    return {
        diversification: sectors.size,
        concentration: concentration,
        isWellDiversified: sectors.size >= 5 && concentration < 0.3
    };
}

// Format currency values
function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', { 
        style: 'currency', 
        currency: 'USD' 
    }).format(value);
}

// Format percentage values
function formatPercentage(value) {
    return new Intl.NumberFormat('en-US', { 
        style: 'percent',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value / 100);
}
