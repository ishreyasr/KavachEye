import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Supabase Configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def format_timestamp(timestamp):
    try:
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp

def view_alerts():
    print("\n=== ALERTS ===")
    try:
        # Get alerts from Supabase
        result = supabase.table('alerts').select('*').order('timestamp', desc=True).execute()
        alerts = result.data
        
        if not alerts:
            print("No alerts found in the database.")
        else:
            for alert in alerts:
                print("\nAlert ID:", alert['id'])
                print("Type:", alert['type'])
                print("Severity:", alert['severity'])
                print("Message:", alert['message'])
                print("Location:", alert.get('location', 'N/A'))
                print("Created:", format_timestamp(alert['timestamp']))
                print("Status:", alert['status'])
                if alert.get('resolved_at'):
                    print("Resolved:", format_timestamp(alert['resolved_at']))
                    
    except Exception as e:
        print(f"Error fetching alerts: {e}")

def view_streams():
    print("\n=== CAMERA STREAMS ===")
    try:
        # Get streams from Supabase
        result = supabase.table('streams').select('*').order('last_update', desc=True).execute()
        streams = result.data
        
        if not streams:
            print("No camera streams found in the database.")
        else:
            for stream in streams:
                print("\nStream ID:", stream['id'])
                print("Camera Name:", stream['name'])
                print("URL:", stream['url'])
                print("Status:", stream['status'])
                print("Last Update:", format_timestamp(stream['last_update']))
                
    except Exception as e:
        print(f"Error fetching streams: {e}")

def view_users():
    print("\n=== USERS ===")
    try:
        # Get users from Supabase
        result = supabase.table('users').select('*').order('created_at', desc=True).execute()
        users = result.data
        
        if not users:
            print("No users found in the database.")
        else:
            for user in users:
                print("\nUser ID:", user['id'])
                print("Name:", f"{user['first_name']} {user['last_name']}")
                print("Email:", user['email'])
                print("ID Number:", user['id_number'])
                print("Department:", user['department'])
                print("Status:", user['status'])
                print("Created:", format_timestamp(user['created_at']))
                
    except Exception as e:
        print(f"Error fetching users: {e}")

if __name__ == "__main__":
    try:
        print("=== KavachEye Database Viewer (Supabase) ===")
        print(f"Connected to: {SUPABASE_URL}")
        
        view_alerts()
        view_streams()
        view_users()
        
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Make sure your environment variables are set correctly:")
        print("- SUPABASE_URL")
        print("- SUPABASE_SERVICE_KEY") 