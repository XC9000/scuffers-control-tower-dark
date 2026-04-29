import os
import requests
import logging

# Set up basic logging for the API module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('shipping_api')

# Base URL for the new Shipping Status API
SHIPPING_API_BASE_URL = "https://lkuutmnykcnbfmbpopcu.functions.supabase.co/api/shipping-status"

def get_candidate_id():
    # Use environment variable, fallback to a default if not set for demo purposes
    return os.environ.get('SCUFFERS_CANDIDATE_ID', 'SCF-2026-6594')

def fetch_shipping_status(order_id):
    """
    Fetches the live shipping status for a given order_id.
    Returns a dict with the parsed response or a safe fallback on error.
    """
    candidate_id = get_candidate_id()
    headers = {
        'X-Candidate-Id': candidate_id,
        'Accept': 'application/json'
    }
    
    url = f"{SHIPPING_API_BASE_URL}/{order_id}"
    
    # Safe fallback response
    fallback = {
        'shipping_status': 'unknown',
        'delay_risk': 'low',
        'delay_reason': None,
        'estimated_delivery_date': None,
        'requires_manual_review': False,
        'api_error': True
    }

    try:
        # Timeout set to 2.5s
        response = requests.get(url, headers=headers, timeout=2.5)
        
        if response.status_code == 200:
            data = response.json()
            # Defensive parsing
            return {
                'shipping_status': data.get('shipping_status', 'unknown'),
                'delay_risk': data.get('delay_risk', 'low'),
                'delay_reason': data.get('delay_reason'),
                'estimated_delivery_date': data.get('estimated_delivery_date'),
                'requires_manual_review': bool(data.get('requires_manual_review', False)),
                'api_error': False
            }
        elif response.status_code == 404:
            logger.warning(f"Order {order_id} not found in Shipping API.")
            return fallback
        else:
            logger.error(f"Shipping API error for {order_id}: {response.status_code}")
            return fallback

    except requests.exceptions.Timeout:
        logger.error(f"Shipping API timeout for {order_id}")
        return fallback
    except requests.exceptions.RequestException as e:
        logger.error(f"Shipping API request failed for {order_id}: {str(e)}")
        return fallback
    except ValueError:
        logger.error(f"Shipping API returned invalid JSON for {order_id}")
        return fallback
