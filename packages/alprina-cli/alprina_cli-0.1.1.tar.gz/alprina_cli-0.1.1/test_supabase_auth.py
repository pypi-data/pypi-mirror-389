import os
import sys
from supabase import create_client

# Set environment variables
os.environ["SUPABASE_URL"] = "https://qplefgvdtlzuxmbbeedf.supabase.co"
os.environ["SUPABASE_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFwbGVmZ3ZkdGx6dXhtYmJlZWRmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MjE2NDI2NiwiZXhwIjoyMDc3NzQwMjY2fQ.TkyU2h7OEwziLNofa-EDOeErsaJF-3vz1o1lFVz58ic"

# Create Supabase client
supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"]
)

print("Testing Supabase Auth signup...")
try:
    response = supabase.auth.sign_up({
        "email": "test-direct@alprina.ai",
        "password": "SecurePass123!",
        "options": {
            "data": {
                "full_name": "Direct Test User"
            }
        }
    })
    
    print(f"✅ Signup successful!")
    print(f"User ID: {response.user.id if response.user else 'None'}")
    print(f"Email: {response.user.email if response.user else 'None'}")
    print(f"Session: {'Yes' if response.session else 'No'}")
    
    # Check if user was created in public.users
    import time
    time.sleep(1)  # Wait for trigger
    
    result = supabase.table("users").select("*").eq("id", response.user.id).execute()
    if result.data:
        print(f"✅ Profile created in public.users!")
        print(f"Profile: {result.data[0]}")
    else:
        print(f"❌ No profile found in public.users")
        
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
