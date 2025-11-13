#!/usr/bin/env python3
# REST API for pmCommand module
# Provides endpoints to control power management units

import os
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from pmCommand.core import PMCommand
import pmCommand

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global PMCommand instance
pm = None

# Configuration from environment variables
PM_BASE_URL = os.environ.get('PM_BASE_URL', 'https://localhost')
PM_USERNAME = os.environ.get('PM_USERNAME', 'admin')
PM_PASSWORD = os.environ.get('PM_PASSWORD', 'admin')


def get_pm_client():
    """Get or create PMCommand client instance"""
    global pm
    if pm is None:
        pm = PMCommand()
    try:
        pm.login(PM_BASE_URL, PM_USERNAME, PM_PASSWORD)
        logging.info(f"Successfully logged in to {PM_BASE_URL}")
    except Exception as e:
        logging.error(f"Failed to login: {e}")
        pm = None
        raise
    return pm


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        client = get_pm_client()
        return jsonify({
            'status': 'healthy',
            'authenticated': client is not None
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503


@app.route('/api/pdus', methods=['GET'])
def list_pdus():
    """List all PDUs"""
    try:
        client = get_pm_client()
        pdus = client.listipdus()
        
        return jsonify({
            'pdus': [
                {
                    'pdu_id': pdu.pduId_Index,
                    'vendor': pdu.values.get('pdu_vendor'),
                    'model': pdu.values.get('pdu_model'),
                    'status': pdu.values.get('pdu_status'),
                    'outlets': pdu.values.get('pdu_outlets'),
                    'current': pdu.values.get('pdu_current'),
                    'power': pdu.values.get('pdu_power'),
                    'alarm': pdu.values.get('pdu_alarm')
                }
                for pdu in pdus
            ]
        }), 200
    except pmCommand.Error as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logging.exception("Error listing PDUs")
        return jsonify({'error': str(e)}), 500


@app.route('/api/outlets', methods=['GET'])
def list_outlets():
    """Get status of all outlets or specific outlets
    
    Query parameters:
    - pdu_id: Filter by PDU ID (optional)
    - outlet_number: Filter by outlet number (optional, requires pdu_id)
    """
    try:
        client = get_pm_client()
        pdu_id = request.args.get('pdu_id')
        outlet_number = request.args.get('outlet_number')
        
        outlet_list = None
        if pdu_id and outlet_number:
            # Request specific outlet
            outlet_list = [(pdu_id, outlet_number)]
        elif pdu_id:
            # Request all outlets from specific PDU
            pdus = client.listipdus()
            pdu_exists = any(pdu.pduId_Index == pdu_id for pdu in pdus)
            if not pdu_exists:
                return jsonify({'error': f'PDU {pdu_id} not found'}), 404
            # Get all outlets for this PDU
            outlets_status = client.status()
            outlet_list = [(pdu, out_num) for (pdu, out_num) in outlets_status.keys() if pdu == pdu_id]
        
        outlets_status = client.status(outlet_list)
        
        return jsonify({
            'outlets': [
                {
                    'pdu_id': key[0],
                    'outlet_number': key[1],
                    'name': outlet.values.get('outlet_name'),
                    'status': outlet.values.get('status'),
                    'current': outlet.values.get('outlet_current'),
                    'power': outlet.values.get('outlet_power'),
                    'circuit': outlet.values.get('circuit')
                }
                for key, outlet in sorted(outlets_status.items())
            ]
        }), 200
    except pmCommand.Error as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logging.exception("Error getting outlet status")
        return jsonify({'error': str(e)}), 500


@app.route('/api/outlets/<pdu_id>/<outlet_number>', methods=['GET'])
def get_outlet_status(pdu_id, outlet_number):
    """Get status of a specific outlet"""
    try:
        client = get_pm_client()
        outlets_status = client.status([(pdu_id, outlet_number)])
        
        if (pdu_id, outlet_number) not in outlets_status:
            return jsonify({'error': f'Outlet {pdu_id}/{outlet_number} not found'}), 404
        
        outlet = outlets_status[(pdu_id, outlet_number)]
        
        return jsonify({
            'pdu_id': pdu_id,
            'outlet_number': outlet_number,
            'name': outlet.values.get('outlet_name'),
            'status': outlet.values.get('status'),
            'current': outlet.values.get('outlet_current'),
            'power': outlet.values.get('outlet_power'),
            'circuit': outlet.values.get('circuit')
        }), 200
    except pmCommand.Error as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logging.exception("Error getting outlet status")
        return jsonify({'error': str(e)}), 500


def _perform_single_outlet_action(action_name, pdu_id, outlet_number):
    """Perform an action on a single outlet
    
    Args:
        action_name: The action to perform ('on', 'off', 'cycle')
        pdu_id: PDU ID
        outlet_number: Outlet number
    
    Returns:
        Response tuple (json_data, status_code)
    """
    try:
        client = get_pm_client()
        action_method = getattr(client, action_name)
        action_method(pdu_id, outlet_number)
        
        return jsonify({
            'pdu_id': pdu_id,
            'outlet_number': outlet_number,
            'action': action_name,
            'success': True
        }), 200
        
    except pmCommand.Error as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logging.exception(f"Error performing {action_name} action on outlet {pdu_id}/{outlet_number}")
        return jsonify({'error': str(e)}), 500


def _perform_bulk_outlet_action(action_name):
    """Perform an action on multiple outlets from JSON request body
    
    Args:
        action_name: The action to perform ('on', 'off', 'cycle')
    
    Expected request body:
    {
        "outlets": [
            {"pdu_id": "power1", "outlet_number": "1"},
            {"pdu_id": "power1", "outlet_number": "2"}
        ]
    }
    
    Returns:
        Response tuple (json_data, status_code)
    """
    try:
        data = request.get_json()
        
        if not data or 'outlets' not in data:
            return jsonify({'error': 'Missing "outlets" in request body'}), 400
        
        outlets = data['outlets']
        if not isinstance(outlets, list) or len(outlets) == 0:
            return jsonify({'error': '"outlets" must be a non-empty array'}), 400
        
        client = get_pm_client()
        action_method = getattr(client, action_name)
        
        results = []
        errors = []
        
        for outlet_info in outlets:
            outlet_pdu_id = outlet_info.get('pdu_id')
            outlet_num = outlet_info.get('outlet_number')
            
            if not outlet_pdu_id or not outlet_num:
                errors.append({
                    'outlet': outlet_info,
                    'error': 'Missing pdu_id or outlet_number'
                })
                continue
            
            try:
                action_method(outlet_pdu_id, outlet_num)
                results.append({
                    'pdu_id': outlet_pdu_id,
                    'outlet_number': outlet_num,
                    'action': action_name,
                    'success': True
                })
            except Exception as e:
                errors.append({
                    'pdu_id': outlet_pdu_id,
                    'outlet_number': outlet_num,
                    'error': str(e)
                })
        
        response = {'results': results}
        if errors:
            response['errors'] = errors
            return jsonify(response), 207  # Multi-Status
        
        return jsonify(response), 200
        
    except pmCommand.Error as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logging.exception(f"Error performing bulk {action_name} action")
        return jsonify({'error': str(e)}), 500


@app.route('/api/outlets/on', methods=['POST'])
def turn_outlets_on():
    """Turn on one or multiple outlets
    
    Request body (JSON):
    {
        "outlets": [
            {"pdu_id": "power1", "outlet_number": "1"},
            {"pdu_id": "power1", "outlet_number": "2"}
        ]
    }
    """
    return _perform_bulk_outlet_action('on')


@app.route('/api/outlets/off', methods=['POST'])
def turn_outlets_off():
    """Turn off one or multiple outlets
    
    Request body (JSON):
    {
        "outlets": [
            {"pdu_id": "power1", "outlet_number": "1"},
            {"pdu_id": "power1", "outlet_number": "2"}
        ]
    }
    """
    return _perform_bulk_outlet_action('off')


@app.route('/api/outlets/cycle', methods=['POST'])
def cycle_outlets():
    """Cycle (power cycle) one or multiple outlets
    
    Request body (JSON):
    {
        "outlets": [
            {"pdu_id": "power1", "outlet_number": "1"},
            {"pdu_id": "power1", "outlet_number": "2"}
        ]
    }
    """
    return _perform_bulk_outlet_action('cycle')


@app.route('/api/outlets/<pdu_id>/<outlet_number>/on', methods=['POST'])
def turn_outlet_on(pdu_id, outlet_number):
    """Turn on a specific outlet"""
    return _perform_single_outlet_action('on', pdu_id, outlet_number)


@app.route('/api/outlets/<pdu_id>/<outlet_number>/off', methods=['POST'])
def turn_outlet_off(pdu_id, outlet_number):
    """Turn off a specific outlet"""
    return _perform_single_outlet_action('off', pdu_id, outlet_number)


@app.route('/api/outlets/<pdu_id>/<outlet_number>/cycle', methods=['POST'])
def cycle_outlet(pdu_id, outlet_number):
    """Cycle (power cycle) a specific outlet"""
    return _perform_single_outlet_action('cycle', pdu_id, outlet_number)


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='pmCommand REST API Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to (default: 5000)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    print(f"""
╔══════════════════════════════════════════════════════╗
║         pmCommand REST API Server                    ║
╚══════════════════════════════════════════════════════╝

Server starting on http://{args.host}:{args.port}

Configuration (set via environment variables):
  PM_BASE_URL: {PM_BASE_URL}
  PM_USERNAME: {PM_USERNAME}
  PM_PASSWORD: {'*' * len(PM_PASSWORD)}

Available endpoints:
  GET  /api/health                           - Health check
  GET  /api/pdus                             - List all PDUs
  GET  /api/outlets                          - List all outlets
  GET  /api/outlets/<pdu_id>/<outlet_number> - Get outlet status
  POST /api/outlets/on                       - Turn on outlets (bulk)
  POST /api/outlets/off                      - Turn off outlets (bulk)
  POST /api/outlets/cycle                    - Cycle outlets (bulk)
  POST /api/outlets/<pdu_id>/<outlet_number>/on     - Turn on outlet
  POST /api/outlets/<pdu_id>/<outlet_number>/off    - Turn off outlet
  POST /api/outlets/<pdu_id>/<outlet_number>/cycle  - Cycle outlet

Press Ctrl+C to stop the server
""")
    
    app.run(host=args.host, port=args.port, debug=args.debug)
