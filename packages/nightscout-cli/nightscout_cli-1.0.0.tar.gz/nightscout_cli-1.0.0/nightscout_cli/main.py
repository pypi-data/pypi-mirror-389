#!/usr/bin/env python3
"""
Nightscout CLI - Command line interface for Nightscout API
"""
import argparse
import requests
import json
import sys
import os
from datetime import datetime, timedelta, timezone

# Defaults - can be overridden by args or env vars
DEFAULT_API_SECRET = os.environ.get("NIGHTSCOUT_API_SECRET", "soilentgreenandblue")
DEFAULT_HOST = os.environ.get("NIGHTSCOUT_HOST", "127.0.0.1")
DEFAULT_PORT = os.environ.get("NIGHTSCOUT_PORT", "80")

def api_get(base_url, api_secret, endpoint, params=None, debug=False):
    """Make authenticated GET request to Nightscout API"""
    headers = {"API-SECRET": api_secret}
    url = f"{base_url}{endpoint}"
    
    if debug:
        print(f"DEBUG: GET {url}", file=sys.stderr)
        print(f"DEBUG: Headers: {headers}", file=sys.stderr)
        print(f"DEBUG: Params: {params}", file=sys.stderr)
    
    try:
        response = requests.get(url, headers=headers, params=params)
        
        if debug:
            print(f"DEBUG: Status Code: {response.status_code}", file=sys.stderr)
            print(f"DEBUG: Response length: {len(response.text)} bytes", file=sys.stderr)
            print(f"DEBUG: Full URL: {response.url}", file=sys.stderr)
        
        response.raise_for_status()
        result = response.json()
        
        if debug:
            print(f"DEBUG: Returned {len(result)} entries", file=sys.stderr)
        
        return result
    except requests.RequestException as e:
        print(f"Error: {e}", file=sys.stderr)
        if debug and hasattr(e, 'response') and e.response is not None:
            print(f"DEBUG: Response text: {e.response.text}", file=sys.stderr)
        sys.exit(1)

def api_post(base_url, api_secret, endpoint, data):
    """Make authenticated POST request to Nightscout API"""
    headers = {
        "API-SECRET": api_secret,
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(f"{base_url}{endpoint}", headers=headers, json=data)
        response.raise_for_status()
        # Try to parse as JSON, but if it fails just return the text
        try:
            return response.json()
        except json.JSONDecodeError:
            return {"status": "success", "text": response.text}
    except requests.RequestException as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def api_delete(base_url, api_secret, endpoint):
    """Make authenticated DELETE request to Nightscout API"""
    headers = {"API-SECRET": api_secret}
    try:
        response = requests.delete(f"{base_url}{endpoint}", headers=headers)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"Error: {e}", file=sys.stderr)
        return False

def cmd_get(args):
    """Get the latest blood glucose reading"""
    base_url = f"http://{args.host}:{args.port}"
    entries = api_get(base_url, args.api_secret, "/api/v1/entries.json", params={"count": 1}, debug=args.debug)
    
    if not entries:
        print("No data available")
        return
    
    entry = entries[0]
    # Format: timestamp value units direction
    timestamp = datetime.fromisoformat(entry['dateString'].replace('Z', '+00:00'))
    value = entry.get('sgv', 'N/A')
    units = entry.get('units', 'mg/dL')
    direction = entry.get('direction', '')
    
    print(f"{timestamp.isoformat()} {value} {units} {direction}")

def cmd_history(args):
    """Get historical glucose data"""
    base_url = f"http://{args.host}:{args.port}"
    
    # Calculate time range using UTC
    end_time = datetime.now(timezone.utc) - timedelta(days=args.days_ago)
    start_time = end_time - timedelta(minutes=args.period)
    
    if args.debug:
        print(f"DEBUG: Start time: {start_time.isoformat()}", file=sys.stderr)
        print(f"DEBUG: End time: {end_time.isoformat()}", file=sys.stderr)
        print(f"DEBUG: Start timestamp (ms): {int(start_time.timestamp() * 1000)}", file=sys.stderr)
        print(f"DEBUG: End timestamp (ms): {int(end_time.timestamp() * 1000)}", file=sys.stderr)
    
    # Convert to milliseconds since epoch for the query
    params = {
        "find[date][$gte]": int(start_time.timestamp() * 1000),
        "find[date][$lte]": int(end_time.timestamp() * 1000),
        "count": 10000  # Large number to get all entries
    }
    
    entries = api_get(base_url, args.api_secret, "/api/v1/entries.json", params=params, debug=args.debug)
    
    if args.jsonl:
        # Output as JSONL (one JSON object per line)
        for entry in entries:
            # Include timestamp, sgv, units
            output = {
                "timestamp": entry.get('dateString'),
                "sgv": entry.get('sgv'),
                "units": entry.get('units', 'mg/dL'),
                "direction": entry.get('direction', '')
            }
            print(json.dumps(output))
    else:
        # Human-readable output
        for entry in entries:
            timestamp = entry.get('dateString')
            value = entry.get('sgv', 'N/A')
            units = entry.get('units', 'mg/dL')
            print(f"{timestamp} {value} {units}")

def cmd_push(args):
    """Push a blood glucose reading to Nightscout"""
    base_url = f"http://{args.host}:{args.port}"
    
    # Calculate timestamp - use UTC
    if args.minutes_ago:
        timestamp = datetime.now(timezone.utc) - timedelta(minutes=args.minutes_ago)
    else:
        timestamp = datetime.now(timezone.utc)
    
    # Prepare entry data
    entry = {
        "type": "sgv",
        "sgv": args.value,
        "dateString": timestamp.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
        "date": int(timestamp.timestamp() * 1000)  # milliseconds since epoch
    }
    
    # Add optional direction if provided
    if args.direction:
        entry["direction"] = args.direction
    
    # Post the entry (as an array - Nightscout expects an array)
    try:
        result = api_post(base_url, args.api_secret, "/api/v1/entries", [entry])
        print(f"Successfully pushed: {timestamp.isoformat()} {args.value} mg/dL")
        if args.direction:
            print(f"Direction: {args.direction}")
    except Exception as e:
        print(f"Failed to push entry: {e}", file=sys.stderr)
        sys.exit(1)

def cmd_list(args):
    """List recent glucose entries with their IDs"""
    base_url = f"http://{args.host}:{args.port}"
    
    params = {"count": args.count}
    entries = api_get(base_url, args.api_secret, "/api/v1/entries.json", params=params, debug=args.debug)
    
    if not entries:
        print("No entries found")
        return
    
    # CSV output
    print("id,timestamp,value")
    for entry in entries:
        entry_id = entry.get('_id', 'N/A')
        timestamp = entry.get('dateString', 'N/A')
        value = entry.get('sgv', 'N/A')
        print(f"{entry_id},{timestamp},{value}")

def cmd_delete(args):
    """Delete a glucose entry by ID"""
    base_url = f"http://{args.host}:{args.port}"
    
    if args.all:
        # Get all entries and delete them
        entries = api_get(base_url, args.api_secret, "/api/v1/entries.json", params={"count": 10000}, debug=args.debug)
        
        if not entries:
            print("No entries to delete")
            return
        
        confirm = input(f"Are you sure you want to delete {len(entries)} entries? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Cancelled")
            return
        
        deleted = 0
        for entry in entries:
            entry_id = entry.get('_id')
            if api_delete(base_url, args.api_secret, f"/api/v1/entries/{entry_id}"):
                deleted += 1
                print(f"Deleted {entry_id}")
        
        print(f"\nDeleted {deleted} of {len(entries)} entries")
    
    else:
        # Delete multiple entries by ID
        if not args.entry_ids:
            print("Error: at least one entry_id is required unless using --all", file=sys.stderr)
            sys.exit(1)
        
        deleted = 0
        failed = 0
        
        for entry_id in args.entry_ids:
            success = api_delete(base_url, args.api_secret, f"/api/v1/entries/{entry_id}")
            
            if success:
                print(f"Deleted {entry_id}")
                deleted += 1
            else:
                print(f"Failed to delete {entry_id}")
                failed += 1
        
        print(f"\nDeleted {deleted} entries, {failed} failed")

def main():
    parser = argparse.ArgumentParser(
        description="Nightscout CLI - Command line interface for Nightscout API"
    )
    
    # Global arguments
    parser.add_argument('--host', default=DEFAULT_HOST,
                       help=f'Nightscout host (default: {DEFAULT_HOST}, or NIGHTSCOUT_HOST env var)')
    parser.add_argument('--port', default=DEFAULT_PORT,
                       help=f'Nightscout port (default: {DEFAULT_PORT}, or NIGHTSCOUT_PORT env var)')
    parser.add_argument('--api-secret', default=DEFAULT_API_SECRET,
                       help='API secret (default: from NIGHTSCOUT_API_SECRET env var)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug output')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # get command
    parser_get = subparsers.add_parser('get', help='Get the latest blood glucose reading')
    parser_get.set_defaults(func=cmd_get)
    
    # history command
    parser_history = subparsers.add_parser('history', help='Get historical glucose data')
    parser_history.add_argument('--days-ago', type=int, default=0, 
                                help='Number of days ago to fetch data for (default: 0 = today)')
    parser_history.add_argument('--period', type=int, default=1440,
                                help='Period in minutes to fetch (default: 1440 = 24 hours)')
    parser_history.add_argument('--jsonl', action='store_true',
                                help='Output as JSONL (one JSON object per line)')
    parser_history.set_defaults(func=cmd_history)
    
    # push command
    parser_push = subparsers.add_parser('push', help='Push a blood glucose reading to Nightscout')
    parser_push.add_argument('value', type=int, help='Blood glucose value (mg/dL)')
    parser_push.add_argument('--minutes-ago', type=int, default=0,
                            help='Number of minutes ago for this reading (default: 0 = now)')
    parser_push.add_argument('--direction', choices=['Flat', 'FortyFiveUp', 'FortyFiveDown', 'SingleUp', 'SingleDown', 'DoubleUp', 'DoubleDown'],
                            help='Trend direction (optional)')
    parser_push.set_defaults(func=cmd_push)
    
    # list command
    parser_list = subparsers.add_parser('list', help='List recent glucose entries')
    parser_list.add_argument('--count', type=int, default=20,
                            help='Number of entries to list (default: 20)')
    parser_list.set_defaults(func=cmd_list)
    
    # delete command
    parser_delete = subparsers.add_parser('delete', help='Delete glucose entry/entries')
    parser_delete.add_argument('entry_ids', nargs='*', help='Entry ID(s) to delete')
    parser_delete.add_argument('--all', action='store_true',
                              help='Delete ALL entries (use with caution!)')
    parser_delete.set_defaults(func=cmd_delete)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)

if __name__ == '__main__':
    main()