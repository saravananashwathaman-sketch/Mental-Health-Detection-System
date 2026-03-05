/**
 * dashboard.js
 * Fetches data from /api/mood-data and renders Chart.js charts.
 */

document.addEventListener('DOMContentLoaded', async () => {
    try {
        const res = await fetch('/api/mood-data');
        const data = await res.json();

        renderTrendChart(data.wellbeing);
        renderMoodDistribution(data.mood);
    } catch (err) {
        console.error("Failed to load dashboard data:", err);
    }
});

function renderTrendChart(wellbeingData) {
    const ctx = document.getElementById('wellbeingChart');
    if (!ctx) return;

    if (wellbeingData.scores.length === 0) {
        // Render a blank chart explicitly if there is no data
        wellbeingData.labels = [];
        wellbeingData.scores = [];
        wellbeingData.risk_levels = [];
    }

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: wellbeingData.labels,
            datasets: [{
                label: 'Wellbeing Score',
                data: wellbeingData.scores,
                borderColor: '#60A5FA', // calm-400
                backgroundColor: 'rgba(96, 165, 250, 0.1)',
                borderWidth: 2,
                tension: 0.4,
                fill: true,
                pointBackgroundColor: wellbeingData.risk_levels.map(r => {
                    return r === 'RED' ? '#F43F5E' : (r === 'AMBER' ? '#F59E0B' : '#22C55E');
                }),
                pointBorderColor: '#fff',
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return 'Score: ' + context.parsed.y;
                        }
                    }
                }
            },
            scales: {
                y: {
                    min: 0,
                    max: 100,
                    grid: { color: '#F1F5F9' },
                    ticks: { color: '#94A3B8', stepSize: 25 }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#94A3B8' }
                }
            }
        }
    });
}

function renderMoodDistribution(moodData) {
    const ctx = document.getElementById('moodDistChart');
    if (!ctx) return;

    const scores = moodData.scores;
    if (scores.length === 0) return;

    // Count occurrences of each mood (1 to 5)
    let counts = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };
    scores.forEach(s => { if (counts[s] !== undefined) counts[s]++; });

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Great (5)', 'Good (4)', 'Neutral (3)', 'Low (2)', 'Very Low (1)'],
            datasets: [{
                label: 'Log Count',
                data: [counts[5], counts[4], counts[3], counts[2], counts[1]],
                backgroundColor: [
                    '#4A90E2', // calm-500 (Great)
                    '#93C5FD', // calm-300 (Good)
                    '#CBD5E1', // slate-300 (Neutral)
                    '#FCA5A5', // blush-300 (Low)
                    '#F43F5E', // blush-500 (Very Low)
                ],
                borderRadius: 4,
                barPercentage: 0.6
            }]
        },
        options: {
            indexAxis: 'y', // This makes the bar chart horizontal (landscape)
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return context.raw + ' check-ins';
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: { stepSize: 1, color: '#94A3B8' },
                    grid: { color: '#F1F5F9' }
                },
                y: {
                    grid: { display: false },
                    ticks: { color: '#64748B', font: { weight: 'bold' } }
                }
            }
        }
    });
}
