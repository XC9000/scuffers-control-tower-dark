/* ═══════════════════════════════════════════
   SCUFFERS AI OPS CONTROL TOWER — Frontend
   ═══════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {
    const loadingScreen = document.getElementById('loading-screen');
    const dashboard = document.getElementById('dashboard');
    const bootTerminal = document.getElementById('boot-terminal');
    const timestampEl = document.getElementById('timestamp');

    // Live clock
    const updateTimestamp = () => {
        timestampEl.textContent = new Date().toLocaleString('es-ES', {
            day: '2-digit', month: '2-digit', year: 'numeric',
            hour: '2-digit', minute: '2-digit', second: '2-digit'
        });
    };
    updateTimestamp();
    setInterval(updateTimestamp, 1000);

    const sleep = ms => new Promise(r => setTimeout(r, ms));

    // ── Boot sequence ───────────────────────────
    const bootLogs = [
        { text: '> Cargando módulos de análisis...', cls: '' },
        { text: '> Conectando con base de datos operativa...', cls: 'info' },
        { text: '> Importando orders.csv (180 pedidos)...', cls: '' },
        { text: '> Importando customers.csv (120 clientes)...', cls: '' },
        { text: '> Importando inventory.csv (22 SKUs)...', cls: '' },
        { text: '> Importando support_tickets.csv (18 tickets)...', cls: '' },
        { text: '> Importando campaigns.csv (5 campañas activas)...', cls: '' },
        { text: '> [WARN] Datos sucios: SKUs legacy, precios formato EU', cls: 'warn' },
        { text: '> Normalizando: hoodie_blk_m → HOODIE-BLK-M', cls: '' },
        { text: '> Scoring × 180 pedidos (6 dimensiones)...', cls: 'info' },
        { text: '> Cruzando inventario × campañas × tickets...', cls: '' },
        { text: '> Predicción de demanda (decay 30%/h)...', cls: 'info' },
        { text: '> Top-10 acciones prioritarias generadas.', cls: '' },
        { text: '> Webhook endpoint activo: /api/webhook/order', cls: 'info' },
        { text: '> [OK] Pipeline completado.', cls: 'success' },
    ];

    const runBoot = async () => {
        for (const log of bootLogs) {
            const p = document.createElement('p');
            p.textContent = log.text;
            if (log.cls) p.classList.add(log.cls);
            bootTerminal.appendChild(p);
            bootTerminal.scrollTop = bootTerminal.scrollHeight;
            await sleep(180);
        }

        try {
            const [analyzeRes, feedRes] = await Promise.all([
                fetch('/api/analyze').then(r => r.json()),
                fetch('/api/feed').then(r => r.json()),
            ]);
            await sleep(300);
            loadingScreen.classList.add('hidden');
            dashboard.classList.remove('hidden');
            renderDashboard(analyzeRes);
            startLiveFeed(feedRes);
        } catch (err) {
            const p = document.createElement('p');
            p.textContent = `> [ERROR] ${err.message}`;
            p.classList.add('error');
            bootTerminal.appendChild(p);
        }
    };

    runBoot();

    // ── Render Dashboard ────────────────────────

    function renderDashboard(data) {
        renderQualityAlerts(data.stats.data_quality_issues || []);
        renderStats(data.stats);
        renderActions(data.actions);
        renderInventory(data.inventory_risks);
        renderForecast(data.demand_forecast);
    }

    function renderQualityAlerts(issues) {
        const el = document.getElementById('quality-alerts');
        if (!issues.length) { el.style.display = 'none'; return; }
        el.innerHTML = issues.map(i =>
            `<div class="quality-pill"><i class="fas fa-exclamation-triangle"></i> ${i}</div>`
        ).join('');
    }

    function renderStats(stats) {
        const row = document.getElementById('stats-row');
        const cards = [
            { label: 'Pedidos', value: stats.total_orders, cls: 'accent', icon: 'fa-receipt' },
            { label: 'Revenue', value: `€${stats.total_revenue.toLocaleString('es-ES')}`, cls: 'green', icon: 'fa-euro-sign' },
            { label: 'Rev. Pago', value: stats.payment_review_count, cls: 'orange', icon: 'fa-clock' },
            { label: 'VIPs', value: stats.vip_orders, cls: 'accent', icon: 'fa-crown' },
            { label: 'Tickets Urg.', value: stats.urgent_tickets, cls: 'red', icon: 'fa-fire' },
            { label: 'SKUs Crít.', value: stats.critical_skus.length, cls: 'red', icon: 'fa-triangle-exclamation' },
        ];
        row.innerHTML = cards.map((c, i) => `
            <div class="stat-card ${c.cls}" style="animation-delay: ${i * 0.07}s">
                <div class="stat-label"><i class="fas ${c.icon}"></i> ${c.label}</div>
                <div class="stat-value">${c.value}</div>
            </div>
        `).join('');
    }

    function renderActions(actions) {
        const list = document.getElementById('actions-list');
        list.innerHTML = actions.map((a, i) => {
            const badgeCls = getBadgeClass(a.action_type);
            const rankCls = i < 3 ? 'critical' : i < 6 ? 'high' : 'medium';
            
            let shippingHtml = '';
            if (a.shipping_info && !a.shipping_info.api_error) {
                const s = a.shipping_info;
                const riskColor = s.delay_risk === 'high' ? 'var(--red)' : (s.delay_risk === 'medium' ? 'var(--orange)' : 'var(--green)');
                const warningIcon = s.requires_manual_review ? '<i class="fas fa-exclamation-circle" style="color:var(--red)" title="Requiere Revisión Manual"></i> ' : '';
                shippingHtml = `
                    <div class="action-shipping" style="margin-top: 8px; padding: 10px; background: rgba(0,0,0,0.25); border-radius: 6px; font-size: 11px; border-left: 3px solid var(--blue);">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span><strong><i class="fas fa-truck"></i> Envío:</strong> ${warningIcon}${s.shipping_status}</span>
                            <span style="color: ${riskColor};">Riesgo: ${s.delay_risk}</span>
                        </div>
                        ${s.delay_reason ? `<div style="color: var(--orange); margin-top: 4px;"><i class="fas fa-info-circle"></i> Motivo: ${s.delay_reason}</div>` : ''}
                    </div>
                `;
            }

            return `
            <div class="action-card" style="animation-delay: ${i * 0.06}s">
                <div class="action-rank ${rankCls}">${a.rank}</div>
                <div class="action-body">
                    <div class="action-top">
                        <div class="action-title">${a.title}</div>
                        <span class="action-type-badge ${badgeCls}">${formatActionType(a.action_type)}</span>
                    </div>
                    <div class="action-reason">${a.reason}</div>
                    ${shippingHtml}
                    <div class="action-meta" style="margin-top: 10px;">
                        <span><i class="fas fa-crosshairs"></i> ${a.target_id}</span>
                        <span><i class="fas fa-user"></i> ${a.owner}</span>
                        <span>
                            ${(a.confidence * 100).toFixed(0)}%
                            <span class="confidence-bar"><span class="confidence-fill" style="width:${a.confidence * 100}%"></span></span>
                        </span>
                        ${a.automation_possible ? '<span><i class="fas fa-robot"></i> Auto</span>' : ''}
                    </div>
                </div>
            </div>`;
        }).join('');

        document.getElementById('export-json-btn').addEventListener('click', () => {
            const blob = new Blob([JSON.stringify(actions, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url; a.download = 'scuffers_ops_actions.json'; a.click();
            URL.revokeObjectURL(url);
        });
    }

    function renderInventory(risks) {
        const tbody = document.querySelector('#inventory-table tbody');
        tbody.innerHTML = risks.map(r => {
            const cls = r.available <= 2 ? 'critical' : r.available <= 6 ? 'high' : r.available <= 15 ? 'moderate' : 'low';
            const label = r.available <= 2 ? 'CRÍT' : r.available <= 6 ? 'BAJO' : r.available <= 15 ? 'OK' : '✓';
            return `<tr>
                <td>${r.sku}</td>
                <td style="color: ${cls === 'critical' ? 'var(--red)' : cls === 'high' ? 'var(--orange)' : 'inherit'}">${r.available}</td>
                <td>${(r.sell_through * 100).toFixed(0)}%</td>
                <td><span class="status-pill status-${cls}">${label}</span></td>
            </tr>`;
        }).join('');
    }

    function renderForecast(forecasts) {
        const tbody = document.querySelector('#forecast-table tbody');
        tbody.innerHTML = forecasts.map(f => {
            const cls = f.risk_level;
            const label = { critical: 'CRÍT', high: 'ALTO', moderate: 'MED', low: 'OK' }[cls] || cls;
            return `<tr>
                <td>${f.sku}</td>
                <td>${f.projected_demand_2h}</td>
                <td style="color: ${f.deficit > 0 ? 'var(--red)' : 'var(--green)'}">${f.deficit > 0 ? '+' : ''}${f.deficit}</td>
                <td><span class="status-pill status-${cls}">${label}</span></td>
            </tr>`;
        }).join('');
    }

    // ── Live Feed Simulation ────────────────────

    function startLiveFeed(allOrders) {
        const feed = document.getElementById('live-feed');
        const counter = document.getElementById('feed-count');
        let count = 0;

        // Shuffle orders to simulate random arrival
        const shuffled = [...allOrders].sort(() => Math.random() - 0.5);
        let idx = 0;

        const addOrder = () => {
            if (idx >= shuffled.length) idx = 0; // loop

            const o = shuffled[idx++];
            count++;
            counter.textContent = count;

            const item = document.createElement('div');
            const extraCls = o.is_vip ? ' vip' : (o.stock_available <= 2 ? ' risk' : '');
            const price = o.order_value ? `€${o.order_value.toFixed(0)}` : '—';
            const statusDot = o.status || 'paid';

            item.className = `feed-item${extraCls}`;
            item.innerHTML = `
                <div class="feed-dot ${statusDot}"></div>
                <div class="feed-info">
                    <div class="feed-oid">${o.order_id} ${o.is_vip ? '<span class="feed-vip-tag">VIP</span>' : ''}</div>
                    <div class="feed-detail">
                        <span>${o.sku || '—'}</span>
                        <span>×${o.quantity}</span>
                        <span>${o.city}</span>
                    </div>
                </div>
                <div class="feed-price">${price}</div>
            `;

            // Insert at the top
            feed.insertBefore(item, feed.firstChild);

            // Keep max 40 items in DOM
            while (feed.children.length > 40) {
                feed.removeChild(feed.lastChild);
            }
        };

        // Add a few immediately
        for (let i = 0; i < 5; i++) addOrder();

        // Then simulate new orders arriving
        setInterval(addOrder, 1800 + Math.random() * 1200);
    }

    // ── Webhook Modal ───────────────────────────

    const webhookBtn = document.getElementById('webhook-btn');
    const modal = document.getElementById('webhook-modal');
    const modalClose = document.getElementById('modal-close');
    const testBtn = document.getElementById('test-webhook-btn');

    webhookBtn.addEventListener('click', async () => {
        modal.classList.remove('hidden');
        try {
            const res = await fetch('/api/shipping/test');
            const data = await res.json();
            document.getElementById('wh-status-text').textContent = data.candidate_id;
            document.getElementById('wh-status-text').style.color = 'var(--blue)';
            document.getElementById('wh-events-count').textContent = data.connected ? 'API Activa ✓' : 'API Timeout / Error';
            document.getElementById('wh-events-count').style.color = data.connected ? 'var(--green)' : 'var(--red)';
        } catch {
            document.getElementById('wh-status-text').textContent = 'Error interno';
        }
    });

    modalClose.addEventListener('click', () => modal.classList.add('hidden'));
    modal.addEventListener('click', (e) => { if (e.target === modal) modal.classList.add('hidden'); });

    testBtn.addEventListener('click', async () => {
        testBtn.disabled = true;
        testBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Probando Conexión...';

        try {
            const res = await fetch('/api/shipping/test');
            const data = await res.json();
            
            if (data.connected) {
                testBtn.innerHTML = `<i class="fas fa-check"></i> ¡Conexión Exitosa!`;
                testBtn.style.background = 'var(--green)';
            } else {
                testBtn.innerHTML = `<i class="fas fa-exclamation-triangle"></i> Supabase devolvió un error (revisa Candidate ID)`;
                testBtn.style.background = 'var(--orange)';
            }
        } catch {
            testBtn.innerHTML = '<i class="fas fa-times"></i> Error de Red';
            testBtn.style.background = 'var(--red)';
        }

        setTimeout(() => {
            testBtn.disabled = false;
            testBtn.innerHTML = '<i class="fas fa-bolt"></i> Testear Conexión API';
            testBtn.style.background = '';
        }, 3500);
    });

    // ── Helpers ──────────────────────────────────

    function getBadgeClass(type) {
        return {
            escalate_ticket: 'badge-escalate', contact_customer: 'badge-contact',
            pause_campaign: 'badge-pause', restock_alert: 'badge-restock',
            demand_forecast_alert: 'badge-forecast', prioritize_order: 'badge-review',
            review_order: 'badge-review', manual_review: 'badge-review',
            protect_vip: 'badge-escalate', limit_campaign: 'badge-pause',
            review_address: 'badge-orange', customs_review: 'badge-orange',
            carrier_escalation: 'badge-escalate'
        }[type] || 'badge-review';
    }

    function formatActionType(type) {
        return {
            escalate_ticket: 'Escalar', contact_customer: 'Contactar',
            pause_campaign: 'Pausar', restock_alert: 'Stock',
            demand_forecast_alert: 'Forecast', prioritize_order: 'Priorizar',
            review_order: 'Revisar', manual_review: 'Rev. Manual',
            protect_vip: 'VIP', limit_campaign: 'Limitar',
            review_address: 'Dir. Inválida', customs_review: 'Aduanas',
            carrier_escalation: 'Escalar Carrier'
        }[type] || type;
    }
});
