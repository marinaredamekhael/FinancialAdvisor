/**
 * Charts.js - Stock and portfolio charts functionality
 */

// Initialize price chart with historical data
function initPriceChart(dates, prices) {
    const ctx = document.getElementById('priceChart');
    if (!ctx) return;
    
    window.priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'Price',
                data: prices,
                borderColor: '#3498db',
                backgroundColor: 'rgba(52, 152, 219, 0.1)',
                borderWidth: 2,
                pointRadius: 0,
                pointHoverRadius: 5,
                pointHoverBackgroundColor: '#3498db',
                tension: 0.3,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(context.parsed.y);
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false,
                        drawBorder: false
                    },
                    ticks: {
                        maxTicksLimit: 8
                    }
                },
                y: {
                    grid: {
                        drawBorder: false
                    },
                    ticks: {
                        callback: function(value) {
                            return '$' + value;
                        }
                    }
                }
            }
        }
    });
}

// Update price chart with new data
function updatePriceChart(dates, prices) {
    if (!window.priceChart) return;
    
    window.priceChart.data.labels = dates;
    window.priceChart.data.datasets[0].data = prices;
    window.priceChart.update();
}

// Initialize volume chart with historical data
function initVolumeChart(dates, volumes) {
    const ctx = document.getElementById('volumeChart');
    if (!ctx) return;
    
    window.volumeChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dates,
            datasets: [{
                label: 'Volume',
                data: volumes,
                backgroundColor: 'rgba(153, 102, 255, 0.5)',
                borderColor: 'rgba(153, 102, 255, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += formatVolumeNumber(context.parsed.y);
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false,
                        drawBorder: false
                    },
                    ticks: {
                        maxTicksLimit: 8
                    }
                },
                y: {
                    grid: {
                        drawBorder: false
                    },
                    ticks: {
                        callback: function(value) {
                            return formatVolumeNumber(value);
                        }
                    }
                }
            }
        }
    });
}

// Update volume chart with new data
function updateVolumeChart(dates, volumes) {
    if (!window.volumeChart) return;
    
    window.volumeChart.data.labels = dates;
    window.volumeChart.data.datasets[0].data = volumes;
    window.volumeChart.update();
}

// Format large volume numbers
function formatVolumeNumber(number) {
    if (number >= 1000000000) {
        return (number / 1000000000).toFixed(1) + 'B';
    } else if (number >= 1000000) {
        return (number / 1000000).toFixed(1) + 'M';
    } else if (number >= 1000) {
        return (number / 1000).toFixed(1) + 'K';
    }
    return number.toString();
}
