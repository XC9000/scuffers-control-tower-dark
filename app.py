"""
Scuffers AI Ops Control Tower — Web Server
Flask app serving the dashboard, analysis API, and webhook endpoint.
"""
from flask import Flask, render_template, jsonify, request
from engine import load_all, generate_actions, compute_stats, compute_inventory_risks, demand_forecast
import random
import time

app = Flask(__name__)

DATA = load_all()

# In-memory webhook log (simulates received events)
WEBHOOK_LOG = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/analyze')
def analyze():
    """Full analysis pipeline → dashboard JSON."""
    actions = generate_actions(DATA)
    stats = compute_stats(DATA)
    inv_risks = compute_inventory_risks(DATA)
    forecasts = demand_forecast(DATA)
    return jsonify({
        'actions': actions,
        'stats': stats,
        'inventory_risks': inv_risks,
        'demand_forecast': forecasts,
    })

@app.route('/api/actions')
def actions_only():
    """Top-10 actions only (hackathon deliverable format)."""
    return jsonify(generate_actions(DATA))

@app.route('/api/feed')
def live_feed():
    """Return recent orders for the live feed simulation."""
    orders = DATA['orders']
    customers = DATA['customers_idx']
    inventory = DATA['inventory_idx']

    feed = []
    for o in orders:
        cust = customers.get(o['customer_id'], {})
        inv = inventory.get(o['sku'], {})
        feed.append({
            'order_id': o['order_id'],
            'customer_id': o['customer_id'],
            'sku': o['sku'],
            'quantity': o['quantity'],
            'order_value': o['order_value'],
            'status': o.get('order_status', ''),
            'city': o.get('shipping_city', ''),
            'segment': cust.get('customer_segment', ''),
            'is_vip': str(cust.get('is_vip', 'false')).lower() == 'true',
            'stock_available': int(inv.get('inventory_available_units', 0) or 0),
            'created_at': o.get('created_at', ''),
        })
    return jsonify(feed)

# ── Webhook endpoint (for real Scuffers integration) ──

@app.route('/api/webhook/order', methods=['POST'])
def webhook_order():
    """
    Webhook endpoint to receive real-time orders from Scuffers.
    In production, this would validate a signature, parse the order,
    add it to the data pipeline, and re-score actions.
    
    Example payload:
    {
        "event": "order.created",
        "order_id": "ORD-99999",
        "customer_id": "CUS-1234",
        "sku": "HOODIE-BLK-M",
        "quantity": 1,
        "order_value": 69.9,
        "shipping_city": "Madrid"
    }
    """
    payload = request.json or {}
    payload['received_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ')
    payload['status'] = 'accepted'
    WEBHOOK_LOG.append(payload)
    return jsonify({'status': 'ok', 'message': 'Order received and queued for analysis.'}), 200

@app.route('/api/webhook/status')
def webhook_status():
    """Check webhook connection status and recent events."""
    return jsonify({
        'connected': True,
        'events_received': len(WEBHOOK_LOG),
        'last_events': WEBHOOK_LOG[-5:],
        'endpoint': '/api/webhook/order',
        'method': 'POST',
        'docs': 'Send order.created events to this endpoint to include real-time orders in the analysis pipeline.'
    })

@app.route('/api/shipping/test')
def shipping_test():
    """Test the Shipping API connection."""
    import shipping_api
    # Test with a mock order ID
    res = shipping_api.fetch_shipping_status("ORD-TEST")
    return jsonify({
        'connected': not res.get('api_error', True),
        'candidate_id': shipping_api.get_candidate_id(),
        'response': res
    })

if __name__ == '__main__':
    app.run(debug=True, port=5004)
