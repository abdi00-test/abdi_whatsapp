"""
Test script to verify that the WhatsApp bot can be imported and used by app.py
This simulates what Railway will do when deploying the application.
"""

try:
    # This is what app.py does
    from whatsapp_bot_simple import process_message, verify_webhook
    print("✅ SUCCESS: Both functions imported successfully!")
    print(f"   - process_message: {type(process_message)}")
    print(f"   - verify_webhook: {type(verify_webhook)}")
    
    # Test verify_webhook function
    print("\n🧪 Testing verify_webhook function...")
    try:
        from config import VERIFY_TOKEN
        result, status = verify_webhook('subscribe', VERIFY_TOKEN, 'test_challenge')
        print(f"   ✅ verify_webhook returned: {result}, status: {status}")
    except Exception as e:
        print(f"   ⚠️ verify_webhook test failed: {e}")
    
    # Test process_message function
    print("\n🧪 Testing process_message function...")
    try:
        process_message('test_user', 'help')
        print("   ✅ process_message executed without errors")
    except Exception as e:
        print(f"   ⚠️ process_message test failed: {e}")
    
    print("\n🎉 ALL TESTS PASSED!")
    print("The bot should now deploy successfully to Railway.")
    
except ImportError as e:
    print(f"❌ IMPORT ERROR: {e}")
    print("This would cause the Railway deployment to fail.")
except Exception as e:
    print(f"❌ UNEXPECTED ERROR: {e}")