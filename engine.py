"""
Scuffers AI Ops Control Tower — Analysis Engine
Processes all CSV data, scores risks, and produces the top-10 prioritized action list.

Scoring model (0-100+ scale):
  - Customer value:    VIP +30 | at_risk +25 | loyal +15
  - Inventory risk:    stock ≤2 +35 | stock ≤6 +20 | sell-through ≥70% +15
  - Support ticket:    urgent +30 | high +20 | negative sentiment +10
  - Payment friction:  payment_review +15
  - Order value:       >€120 +10
  - Campaign pressure: very_high +20 | high +10
"""
import csv
import json
import os
from collections import defaultdict
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'scuffers_all_mock_data', 'candidate_csvs')

# ─────────────────────────────────────────────────
# 1. DATA LOADING — robust to dirty/incomplete data
# ─────────────────────────────────────────────────

def _clean_price(val):
    """Handle '€34,9' / '' / '34.9' / None."""
    if not val or str(val).strip() == '':
        return None
    val = str(val).replace('€', '').replace(',', '.').strip()
    try:
        return float(val)
    except ValueError:
        return None

def _normalize_sku(sku):
    """hoodie_blk_m -> HOODIE-BLK-M. Returns None for empty/null."""
    if not sku or str(sku).strip() == '':
        return None
    return str(sku).strip().upper().replace('_', '-')

def _safe_int(val, default=0):
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default

def _safe_float(val, default=0.0):
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def _parse_dt(val):
    """Parse ISO datetime string, return None on failure."""
    if not val or str(val).strip() == '':
        return None
    try:
        return datetime.fromisoformat(val.replace('Z', '+00:00'))
    except (ValueError, TypeError):
        return None

def load_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def load_all():
    data = {}
    data['orders'] = load_csv('orders.csv')
    data['order_items'] = load_csv('order_items.csv')
    data['customers'] = load_csv('customers.csv')
    data['inventory'] = load_csv('inventory.csv')
    data['support_tickets'] = load_csv('support_tickets.csv')
    data['campaigns'] = load_csv('campaigns.csv')

    # Build indexes (normalize keys for safe joins)
    data['customers_idx'] = {c['customer_id']: c for c in data['customers']}
    data['inventory_idx'] = {}
    for row in data['inventory']:
        data['inventory_idx'][row['sku']] = row
        data['inventory_idx'][_normalize_sku(row['sku'])] = row  # double-index for safety

    data['tickets_by_order'] = {}
    data['tickets_by_customer'] = defaultdict(list)
    for t in data['support_tickets']:
        oid = t.get('order_id', '')
        cid = t.get('customer_id', '')
        if oid:
            data['tickets_by_order'][oid] = t
        if cid:
            data['tickets_by_customer'][cid].append(t)

    # Clean & normalize orders
    for o in data['orders']:
        o['sku'] = _normalize_sku(o.get('sku'))
        o['order_value'] = _clean_price(o.get('order_value', ''))
        o['quantity'] = _safe_int(o.get('quantity'), 1)

    for oi in data['order_items']:
        oi['sku'] = _normalize_sku(oi.get('sku'))
        oi['quantity'] = _safe_int(oi.get('quantity'), 1)

    return data


# ─────────────────────────────────────────────────
# 2. DATA QUALITY REPORT (for demo narrative)
# ─────────────────────────────────────────────────

def data_quality_report(data):
    """Quick summary of data issues found — useful for the presentation."""
    issues = []
    # Dirty SKUs
    dirty_skus = [o for o in data['orders'] if o.get('sku') and '_' in (o.get('sku') or '')]
    # Already normalized, so count originals from order_items
    legacy_count = sum(1 for oi in data['order_items'] if '_' in (oi.get('sku') or ''))
    if legacy_count:
        issues.append(f"{legacy_count} SKUs en formato legacy (underscore)")

    # European prices
    euro_prices = sum(1 for o in data['orders'] if '€' in str(o.get('order_value', '')) or ',' in str(o.get('order_value', '')))
    # Already cleaned, so check raw — count from the originals detected
    null_prices = sum(1 for o in data['orders'] if o['order_value'] is None)
    if null_prices:
        issues.append(f"{null_prices} pedidos con precio vacío o malformado")

    # Missing segments
    missing_seg = sum(1 for o in data['orders'] if not o.get('customer_segment', '').strip())
    if missing_seg:
        issues.append(f"{missing_seg} pedidos sin segmento de cliente")

    return issues


# ─────────────────────────────────────────────────
# 3. SCORING — per-order risk score
# ─────────────────────────────────────────────────

SCORE_WEIGHTS = {
    'vip': 30, 'at_risk': 25, 'loyal': 15,
    'stock_critical': 35, 'stock_low': 20, 'sell_through_high': 15,
    'ticket_urgent': 30, 'ticket_high': 20, 'sentiment_negative': 10,
    'payment_review': 15, 'high_value': 10,
    'campaign_very_high': 20, 'campaign_high': 10,
}

def compute_order_risk(order, data):
    """Score a single order across all risk dimensions. Returns a scored dict."""
    score = 0.0
    reasons = []
    cid = order['customer_id']
    sku = order['sku']
    oid = order['order_id']
    customer = data['customers_idx'].get(cid, {})
    inv = data['inventory_idx'].get(sku, {})

    # Check tickets: first by order, then fallback to customer-level
    ticket = data['tickets_by_order'].get(oid)
    if not ticket:
        cust_tickets = data['tickets_by_customer'].get(cid, [])
        if cust_tickets:
            # Pick most urgent ticket for this customer
            urg_order = {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}
            ticket = min(cust_tickets, key=lambda t: urg_order.get(t.get('support_ticket_urgency', 'low'), 9))

    # — Customer importance —
    is_vip = str(customer.get('is_vip', 'false')).lower() == 'true'
    segment = customer.get('customer_segment', '') or ''
    clv = _safe_float(customer.get('customer_lifetime_value'))

    if is_vip:
        score += SCORE_WEIGHTS['vip']
        reasons.append(f"Cliente VIP (CLV €{clv:.0f})")
    elif segment == 'at_risk_customer':
        score += SCORE_WEIGHTS['at_risk']
        reasons.append("Cliente at-risk: alto riesgo de pérdida")
    elif segment == 'loyal_customer':
        score += SCORE_WEIGHTS['loyal']
        reasons.append(f"Cliente leal (CLV €{clv:.0f})")

    # — Inventory pressure —
    available = _safe_int(inv.get('inventory_available_units'), 999)
    sell_through = _safe_float(inv.get('sell_through_rate_last_hour'))

    if available <= 2:
        score += SCORE_WEIGHTS['stock_critical']
        reasons.append(f"STOCK CRÍTICO: solo {available} uds disponibles de {sku}")
    elif available <= 6:
        score += SCORE_WEIGHTS['stock_low']
        reasons.append(f"Stock bajo: {available} uds disponibles de {sku}")

    if sell_through >= 0.7:
        score += SCORE_WEIGHTS['sell_through_high']
        reasons.append(f"Sell-through rate altísimo ({sell_through:.0%})")

    # — Support ticket —
    if ticket:
        urgency = ticket.get('support_ticket_urgency', '')
        sentiment = ticket.get('support_ticket_sentiment', '')
        msg = ticket.get('support_ticket_message', '')[:60]
        if urgency == 'urgent':
            score += SCORE_WEIGHTS['ticket_urgent']
            reasons.append(f"Ticket URGENTE: {msg}")
        elif urgency == 'high':
            score += SCORE_WEIGHTS['ticket_high']
            reasons.append(f"Ticket alta prioridad: {msg}")
        if sentiment == 'negative':
            score += SCORE_WEIGHTS['sentiment_negative']
            reasons.append("Sentimiento negativo en soporte")

    # — Payment friction —
    if order.get('order_status') == 'payment_review':
        score += SCORE_WEIGHTS['payment_review']
        reasons.append("Pedido atascado en revisión de pago")

    # — High order value —
    ov = order.get('order_value')
    if ov and ov > 120:
        score += SCORE_WEIGHTS['high_value']
        reasons.append(f"Pedido de alto valor (€{ov:.0f})")

    # — Campaign pressure on this SKU —
    for c in data['campaigns']:
        if _normalize_sku(c.get('target_sku')) == sku:
            intensity = c.get('campaign_intensity', '')
            if intensity == 'very_high':
                score += SCORE_WEIGHTS['campaign_very_high']
                reasons.append(f"Campaña {c['campaign_source'].upper()} very_high sobre este SKU")
            elif intensity == 'high':
                score += SCORE_WEIGHTS['campaign_high']
                reasons.append(f"Campaña {c['campaign_source'].upper()} high sobre este SKU")

    return {
        'order_id': oid, 'customer_id': cid, 'sku': sku,
        'score': round(score, 1), 'reasons': reasons,
        'customer': customer, 'inventory': inv,
        'ticket': ticket, 'order': order,
    }


# ─────────────────────────────────────────────────
# 4. INVENTORY RISK (SKU-level)
# ─────────────────────────────────────────────────

def compute_inventory_risks(data):
    """Per-SKU risk analysis: stockout timing, campaign overlap, demand pressure."""
    sku_demand = defaultdict(int)
    for oi in data['order_items']:
        sku_demand[oi['sku']] += oi['quantity']

    risks = []
    for row in data['inventory']:
        sku = row['sku']
        available = _safe_int(row.get('inventory_available_units'))
        incoming = _safe_int(row.get('inventory_incoming_units'))
        eta = row.get('inventory_incoming_eta', '')
        sell_through = _safe_float(row.get('sell_through_rate_last_hour'))
        page_views = _safe_int(row.get('product_page_views_last_hour'))
        conv_rate = _safe_float(row.get('conversion_rate_last_hour'))
        demand_units = sku_demand.get(sku, 0) + sku_demand.get(_normalize_sku(sku), 0)

        hours_until_stockout = available / sell_through if sell_through > 0 else 999

        campaign_pressure = None
        for c in data['campaigns']:
            if _normalize_sku(c.get('target_sku')) == _normalize_sku(sku):
                campaign_pressure = c

        risks.append({
            'sku': sku,
            'product_name': row.get('product_name', sku),
            'available': available,
            'incoming': incoming,
            'eta': eta,
            'sell_through': sell_through,
            'page_views': page_views,
            'demand_units': demand_units,
            'hours_until_stockout': round(hours_until_stockout, 1),
            'pressure': round(page_views * conv_rate, 1),
            'campaign': campaign_pressure,
        })
    risks.sort(key=lambda x: x['hours_until_stockout'])
    return risks


# ─────────────────────────────────────────────────
# 5. DEMAND FORECAST (predictive model)
# ─────────────────────────────────────────────────

# Assumption: in a typical streetwear drop, demand decays ~30% per hour
# after the initial rush. We project 2h forward using current signals.
DEMAND_DECAY_RATE = 0.7  # demand_h2 = demand_h1 * 0.7
FORECAST_WINDOW_HOURS = 2
ETA_CUTOFF = datetime(2026, 4, 28, 22, 0)  # only count incoming if ETA < tonight 22:00

def demand_forecast(data):
    """Project demand vs supply over next 2h per SKU."""
    forecasts = []
    for row in data['inventory']:
        sku = row['sku']
        available = _safe_int(row.get('inventory_available_units'))
        incoming = _safe_int(row.get('inventory_incoming_units'))
        page_views = _safe_int(row.get('product_page_views_last_hour'))
        conv_rate = _safe_float(row.get('conversion_rate_last_hour'))
        eta_str = row.get('inventory_incoming_eta', '')
        eta_dt = _parse_dt(eta_str)

        demand_h1 = page_views * conv_rate
        demand_h2 = demand_h1 * DEMAND_DECAY_RATE
        total_demand = demand_h1 + demand_h2

        # Only count incoming stock if it arrives before tonight
        usable_incoming = incoming if (eta_dt and eta_dt.replace(tzinfo=None) < ETA_CUTOFF) else 0
        total_supply = available + usable_incoming
        deficit = total_demand - total_supply

        if deficit > 0 and available <= 5:
            risk = 'critical'
        elif deficit > 0:
            risk = 'high'
        elif available < 20:
            risk = 'moderate'
        else:
            risk = 'low'

        forecasts.append({
            'sku': sku,
            'product_name': row.get('product_name', sku),
            'available_now': available,
            'incoming': incoming,
            'eta': eta_str,
            'projected_demand_2h': round(total_demand, 1),
            'total_supply': total_supply,
            'deficit': round(deficit, 1),
            'risk_level': risk,
        })
    forecasts.sort(key=lambda x: x['deficit'], reverse=True)
    return forecasts


# ─────────────────────────────────────────────────
# 6. TOP-10 ACTION GENERATOR
# ─────────────────────────────────────────────────

def generate_actions(data):
    """
    Produce the final top-10 prioritized action list (hackathon deliverable).
    
    Priority tiers:
      A. Urgent tickets from VIP / at-risk / loyal customers
      B. Pause campaigns pushing demand onto nearly-empty SKUs
      C. Critical inventory alerts (≤2 units)
      D. Demand forecast: projected stock-out within 2h
      E. High-risk orders (score ≥ 50) needing manual review
      F. Payment-blocked orders from important customers
      G. Remaining high-scored orders for proactive monitoring
    """
    scored = [compute_order_risk(o, data) for o in data['orders']]
    
    # --- INCREMENTAL SHIPPING API INTEGRATION ---
    import shipping_api
    from concurrent.futures import ThreadPoolExecutor

    relevant_orders = []
    for s in scored:
        is_vip = str(s['customer'].get('is_vip', 'false')).lower() == 'true'
        if len(relevant_orders) < 15 and (s['score'] >= 35 or s['ticket'] or is_vip):
            relevant_orders.append(s)
        else:
            s['shipping_info'] = None

    def fetch_and_apply(s):
        ship_info = shipping_api.fetch_shipping_status(s['order_id'])
        s['shipping_info'] = ship_info
        if not ship_info['api_error']:
            status = ship_info['shipping_status']
            risk = ship_info['delay_risk']
            reason = ship_info['delay_reason']
            
            if status in ('delayed', 'exception', 'lost', 'returned_to_sender'):
                s['score'] += 25
                s['reasons'].append(f"Logística crítica: {status} ({reason or 'unknown'})")
            elif risk == 'high':
                s['score'] += 15
                s['reasons'].append(f"Alto riesgo de retraso en envío: {reason}")
            
            if ship_info['requires_manual_review']:
                s['score'] += 20
                s['reasons'].append("Carrier solicita revisión manual (posible error de dirección/aduanas)")
            
            if status in ('delivered', 'out_for_delivery'):
                s['score'] = max(0, s['score'] - 20)
                s['reasons'].append(f"Envío avanzado ({status}), reduciendo urgencia.")

    if relevant_orders:
        with ThreadPoolExecutor(max_workers=15) as executor:
            executor.map(fetch_and_apply, relevant_orders)

    scored.sort(key=lambda x: x['score'], reverse=True)

    inv_risks = compute_inventory_risks(data)
    forecasts = demand_forecast(data)

    actions = []
    used_orders = set()
    used_skus_inv = set()
    used_skus_campaign = set()
    rank = 1

    def add(action, ship_info=None):
        nonlocal rank
        if rank > 10:
            return
        action['rank'] = rank
        if ship_info and not ship_info.get('api_error'):
            action['shipping_info'] = ship_info
        actions.append(action)
        rank += 1

    # — Tier A: Urgent/high tickets from important customers —
    for s in scored:
        if rank > 10: break
        t = s['ticket']
        if not t: continue
        urg = t.get('support_ticket_urgency', '')
        seg = s['customer'].get('customer_segment', '') or ''
        is_vip = str(s['customer'].get('is_vip', 'false')).lower() == 'true'
        if urg in ('urgent', 'high') and (is_vip or seg in ('at_risk_customer', 'loyal_customer')):
            if s['order_id'] in used_orders: continue
            used_orders.add(s['order_id'])
            add({
                'action_type': 'escalate_ticket' if is_vip else 'contact_customer',
                'target_id': s['order_id'],
                'title': f"{'Escalar ticket VIP' if is_vip else 'Contactar proactivamente'}: {s['customer_id']} ({t['ticket_id']})",
                'reason': '; '.join(s['reasons']),
                'expected_impact': 'Proteger relación con cliente clave y evitar escalada pública.' if is_vip else 'Retener cliente en riesgo antes de que abandone la marca.',
                'confidence': min(0.95, 0.5 + s['score'] / 200),
                'owner': 'customer_support',
                'automation_possible': False,
            }, s.get('shipping_info'))

    # — Tier B: Pause campaigns on nearly-empty SKUs —
    for ir in inv_risks:
        if rank > 10: break
        if ir['available'] <= 2 and ir['campaign']:
            sku = ir['sku']
            if sku in used_skus_campaign: continue
            used_skus_campaign.add(sku)
            c = ir['campaign']
            add({
                'action_type': 'pause_campaign',
                'target_id': c['campaign_id'],
                'title': f"Pausar campaña {c['campaign_source'].upper()} sobre {sku}",
                'reason': f"Solo {ir['available']} uds de {ir['product_name']}, campaña {c['campaign_id']} activa ({c['campaign_intensity']}). Sell-through: {ir['sell_through']:.0%}/h.",
                'expected_impact': 'Evitar generar demanda que no podemos cumplir. Reducir frustración post-compra.',
                'confidence': 0.92,
                'owner': 'marketing',
                'automation_possible': True,
            })

    # — Tier C: Critical stock alerts —
    for ir in inv_risks:
        if rank > 10: break
        if ir['available'] <= 2 and ir['sku'] not in used_skus_inv:
            used_skus_inv.add(ir['sku'])
            inc = f" ({ir['incoming']} entrantes, ETA: {ir['eta']})" if ir['incoming'] > 0 else " (sin reposición)"
            add({
                'action_type': 'restock_alert',
                'target_id': ir['sku'],
                'title': f"STOCK CRÍTICO: {ir['product_name']} ({ir['sku']})",
                'reason': f"{ir['available']} uds disponibles, {ir['demand_units']} comprometidas, {ir['page_views']} visitas/h{inc}.",
                'expected_impact': 'Activar reposición urgente o limitar ventas para proteger pedidos existentes.',
                'confidence': 0.94,
                'owner': 'operations',
                'automation_possible': True,
            })

    # — Tier D: Demand forecast alerts —
    for fc in forecasts:
        if rank > 10: break
        if fc['risk_level'] == 'critical' and fc['sku'] not in used_skus_inv:
            used_skus_inv.add(fc['sku'])
            add({
                'action_type': 'demand_forecast_alert',
                'target_id': fc['sku'],
                'title': f"Predicción de rotura: {fc['product_name']} se agotará en <2h",
                'reason': f"Demanda proyectada: {fc['projected_demand_2h']:.0f} uds en 2h vs {fc['total_supply']} disponibles. Déficit: {fc['deficit']:.0f} uds.",
                'expected_impact': 'Anticipar rotura: preparar comunicación, activar waitlist o acelerar reposición.',
                'confidence': 0.78,
                'owner': 'operations',
                'automation_possible': True,
            })

    # — Tier E: High-risk orders (score ≥ 50) —
    for s in scored:
        if rank > 10: break
        if s['order_id'] in used_orders or s['score'] < 50: continue
        used_orders.add(s['order_id'])
        is_vip = str(s['customer'].get('is_vip', 'false')).lower() == 'true'
        
        # Shipping specific action overrides
        action_type = 'prioritize_order' if is_vip else 'review_order'
        title = f"Priorizar revisión del pedido {s['order_id']}"
        ship_info = s.get('shipping_info')
        if ship_info and not ship_info['api_error']:
            if ship_info['delay_reason'] == 'address_validation_error':
                action_type = 'review_address'
                title = f"Revisar dirección del pedido {s['order_id']}"
            elif ship_info['delay_reason'] == 'customs_hold':
                action_type = 'customs_review'
                title = f"Revisar incidencia en aduanas {s['order_id']}"
            elif ship_info['shipping_status'] in ('exception', 'lost', 'returned_to_sender'):
                action_type = 'carrier_escalation'
                title = f"Escalar incidencia con carrier: {s['order_id']}"

        add({
            'action_type': action_type,
            'target_id': s['order_id'],
            'title': title,
            'reason': '; '.join(s['reasons']),
            'expected_impact': 'Reducir riesgo de mala experiencia y evitar incidencia de soporte.',
            'confidence': min(0.95, 0.5 + s['score'] / 200),
            'owner': 'operations',
            'automation_possible': s['order'].get('order_status') == 'payment_review',
        }, s.get('shipping_info'))

    # — Tier F: Payment-blocked important customers —
    for s in scored:
        if rank > 10: break
        if s['order_id'] in used_orders: continue
        seg = s['customer'].get('customer_segment', '') or ''
        if s['order'].get('order_status') == 'payment_review' and seg in ('vip_customer', 'loyal_customer', 'at_risk_customer'):
            used_orders.add(s['order_id'])
            add({
                'action_type': 'manual_review',
                'target_id': s['order_id'],
                'title': f"Desbloquear pago: {s['order_id']} ({seg.replace('_', ' ')})",
                'reason': '; '.join(s['reasons']),
                'expected_impact': 'Desatascar pedido y evitar pérdida de cliente importante.',
                'confidence': min(0.90, 0.5 + s['score'] / 200),
                'owner': 'operations',
                'automation_possible': True,
            }, s.get('shipping_info'))

    # — Tier G: Pad to 10 with next-highest scored —
    for s in scored:
        if rank > 10: break
        if s['order_id'] in used_orders or s['score'] < 35: continue
        used_orders.add(s['order_id'])
        add({
            'action_type': 'contact_customer',
            'target_id': s['order_id'],
            'title': f"Monitorizar pedido {s['order_id']} ({(s['customer'].get('customer_segment') or 'desconocido').replace('_', ' ')})",
            'reason': '; '.join(s['reasons']),
            'expected_impact': 'Vigilancia proactiva para prevenir incidencias.',
            'confidence': min(0.85, 0.5 + s['score'] / 200),
            'owner': 'operations',
            'automation_possible': True,
        }, s.get('shipping_info'))

    for a in actions:
        a['confidence'] = round(a['confidence'], 2)

    return actions[:10]


# ─────────────────────────────────────────────────
# 7. DASHBOARD STATS
# ─────────────────────────────────────────────────

def compute_stats(data):
    total_orders = len(data['orders'])
    total_revenue = sum(o['order_value'] for o in data['orders'] if o['order_value'])
    payment_review = sum(1 for o in data['orders'] if o.get('order_status') == 'payment_review')
    vip_orders = sum(1 for o in data['orders']
                     if str(data['customers_idx'].get(o['customer_id'], {}).get('is_vip', 'false')).lower() == 'true')
    urgent_tickets = sum(1 for t in data['support_tickets']
                         if t.get('support_ticket_urgency') in ('urgent', 'high'))

    critical_skus = [row['sku'] for row in data['inventory']
                     if _safe_int(row.get('inventory_available_units')) <= 5]

    quality_issues = data_quality_report(data)

    return {
        'total_orders': total_orders,
        'total_revenue': round(total_revenue, 2),
        'payment_review_count': payment_review,
        'vip_orders': vip_orders,
        'open_tickets': len(data['support_tickets']),
        'urgent_tickets': urgent_tickets,
        'critical_skus': critical_skus,
        'active_campaigns': len(data['campaigns']),
        'data_quality_issues': quality_issues,
    }


# ─────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────

if __name__ == '__main__':
    data = load_all()
    actions = generate_actions(data)
    print(json.dumps(actions, indent=2, ensure_ascii=False))
