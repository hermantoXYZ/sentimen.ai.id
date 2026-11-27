$(document).ready(function () {
    // 1. Select2
    $('.select2-init').select2({ theme: 'bootstrap-5', width: '100%' });

    // 2. DataTables
    if ($('#recentTable').length) $('#recentTable').DataTable({ pageLength: 5, order: [] });
    if ($('#topPostsTable').length) $('#topPostsTable').DataTable({ pageLength: 10, order: [] });

    // 3. Tombol Sample Channel pada YouTube Analyzer
    $('.sample-ch').on('click', function () {
        $('#ytChannelInput').val($(this).data('id'));
    });

    // 4. Chart.js di halaman Analysis
    if ($('#donutSentiment').length) {
        const plat = $('#platformFilter').val() || 'ALL';
        fetch(`/api/analysis-charts?platform=${plat}`)
            .then(r => r.json())
            .then(data => {
                new Chart(document.getElementById('donutSentiment'), {
                    type: 'doughnut',
                    data: {
                        labels: ['Negative', 'Neutral', 'Positive'],
                        datasets: [{
                            data: [data.sentiment.negative, data.sentiment.neutral, data.sentiment.positive],
                            backgroundColor: ['#dc3545', '#ffc107', '#198754']
                        }]
                    }
                });

                new Chart(document.getElementById('donutPlatform'), {
                    type: 'doughnut',
                    data: {
                        labels: Object.keys(data.platforms),
                        datasets: [{
                            data: Object.values(data.platforms),
                            backgroundColor: ['#ff0000', '#e1306c', '#1da1f2', '#1877f2', '#000000']
                        }]
                    }
                });

                new Chart(document.getElementById('trendChart'), {
                    type: 'line',
                    data: {
                        labels: data.days,
                        datasets: [
                            { label: 'Positive', data: data.pos_7d, borderColor: '#198754', fill: true, backgroundColor: 'rgba(25,135,84,0.1)' },
                            { label: 'Negative', data: data.neg_7d, borderColor: '#dc3545', fill: true, backgroundColor: 'rgba(220,53,69,0.1)' },
                            { label: 'Neutral', data: data.neu_7d, borderColor: '#ffc107', fill: true, backgroundColor: 'rgba(255,193,7,0.1)' }
                        ]
                    }
                });

                const wcCanvas = document.getElementById('wordCloudCanvas');
                if (wcCanvas && data.keywords && data.keywords.length) {
                    if (typeof WordCloud === 'function') {
                        const maxFreq = data.keywords[0][1] || 1;
                        const scaledList = data.keywords.map(([word, count]) => [word, Math.max(12, Math.round((count / maxFreq) * 42))]);
                        WordCloud(wcCanvas, {
                            list: scaledList,
                            gridSize: 6,
                            weightFactor: 1,
                            fontFamily: 'Tahoma, Arial, sans-serif',
                            color: 'random-dark',
                            rotateRatio: 0.25,
                            backgroundColor: '#f8f9fa'
                        });
                    } else {
                        wcCanvas.classList.add('d-none');
                        const fb = document.getElementById('wordCloudFallback');
                        if (fb) {
                            fb.classList.remove('d-none');
                            fb.classList.add('d-flex');
                        }
                    }
                }
            });
    }

    // 5. Polling Live Monitor setiap 5 detik
    if ($('#liveStreamBox').length) {
        let gaugeChart = null;
        function refreshLive() {
            fetch('/api/live-feed')
                .then(r => r.json())
                .then(d => {
                    $('#livePpm').text(d.posts_per_min);
                    $('#livePos').text(d.pos_rate + '%');
                    $('#liveNeg').text(d.neg_rate + '%');
                    $('#liveAlerts').text(d.neg_rate > 25 ? 1 : 0);

                    let html = '';
                    d.feed.forEach(item => {
                        const badgeColor = item.sentiment === 'positive' ? 'success' : (item.sentiment === 'negative' ? 'danger' : 'warning text-dark');
                        html += `
                        <div class="border-bottom pb-2 mb-2">
                            <div class="d-flex justify-content-between">
                                <div>
                                    <span class="badge badge-${item.platform}">${item.platform}</span>
                                    <strong class="ms-1">${item.username}</strong>
                                    <span class="badge bg-${badgeColor} ms-1">${item.sentiment}</span>
                                </div>
                                <small class="text-muted"><i class="fas fa-thumbs-up"></i> ${item.likes}</small>
                            </div>
                            <p class="mb-0 mt-1 small">${item.content}</p>
                        </div>`;
                    });
                    $('#liveStreamBox').html(html);

                    if (d.neg_rate > 25) {
                        $('#alertListBox').html(`<div class="alert alert-danger py-2 mb-0">High negative sentiment spike (${d.neg_rate}%) detected!</div>`);
                    }

                    if (!gaugeChart) {
                        gaugeChart = new Chart(document.getElementById('liveGaugeChart'), {
                            type: 'doughnut',
                            data: {
                                labels: ['Negative', 'Neutral', 'Positive'],
                                datasets: [{ data: [d.neg_rate, d.neu_rate, d.pos_rate], backgroundColor: ['#dc3545', '#ffc107', '#198754'] }]
                            },
                            options: { rotation: -90, circumference: 180 }
                        });
                    } else {
                        gaugeChart.data.datasets[0].data = [d.neg_rate, d.neu_rate, d.pos_rate];
                        gaugeChart.update();
                    }
                });
        }
        refreshLive();
        setInterval(refreshLive, 5000);
    }
});