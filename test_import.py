try:
    import whatsapp_bot_simple
    print("Import successful!")
    print("process_message exists:", hasattr(whatsapp_bot_simple, 'process_message'))
    print("verify_webhook exists:", hasattr(whatsapp_bot_simple, 'verify_webhook'))
    if hasattr(whatsapp_bot_simple, 'process_message'):
        print("process_message function:", type(whatsapp_bot_simple.process_message))
    if hasattr(whatsapp_bot_simple, 'verify_webhook'):
        print("verify_webhook function:", type(whatsapp_bot_simple.verify_webhook))
except Exception as e:
    print("Import failed:", e)
    import traceback
    traceback.print_exc()