"""Send button-based cards to Feishu for testing"""
import sys
import os
import asyncio

# Add backend to path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend'))
sys.path.insert(0, backend_path)

from services.feishu_card_service import FeishuCardService


async def test_send_holdings_card():
    """Send holdings card to Feishu"""
    print("=" * 60)
    print("Sending Holdings Card to Feishu")
    print("=" * 60)
    
    # Initialize card service
    card_service = FeishuCardService()
    
    # Get test chat ID from environment or use default
    # You can set FEISHU_TEST_CHAT_ID environment variable
    test_chat_id = os.environ.get("FEISHU_TEST_CHAT_ID", "oc_a0553eda9014c201e6969b478895c230")
    
    print(f"Sending to chat_id: {test_chat_id}")
    
    # Send card (this method already handles data retrieval)
    success = await card_service.send_holdings_display_card(test_chat_id)
    
    if success:
        print("\n[SUCCESS] Holdings card sent successfully!")
        print("Check your Feishu chat for the card.")
        print("Test the following buttons:")
        print("  1. Click stock name (primary button) - should query price")
        print("  2. Click 'query' button - should query detail")
        print("  3. Click 'delete' button - should delete stock")
    else:
        print("\n[FAILED] Failed to send holdings card")
        print("Possible reasons:")
        print("  - Invalid chat_id")
        print("  - Feishu API not available")
        print("  - Backend service not running")
    
    print("=" * 60)


async def test_send_watchlist_card():
    """Send watchlist card to Feishu"""
    print("\n" + "=" * 60)
    print("Sending Watchlist Card to Feishu")
    print("=" * 60)
    
    # Initialize card service
    card_service = FeishuCardService()
    
    # Get test chat ID from environment or use default
    test_chat_id = os.environ.get("FEISHU_TEST_CHAT_ID", "oc_a0553eda9014c201e6969b478895c230")
    
    print(f"Sending to chat_id: {test_chat_id}")
    
    # Send card (this method already handles data retrieval)
    success = await card_service.send_watchlist_display_card(test_chat_id)
    
    if success:
        print("\n[SUCCESS] Watchlist card sent successfully!")
        print("Check your Feishu chat for the card.")
        print("Test the following buttons:")
        print("  1. Click stock name (primary button) - should query price")
        print("  2. Click 'query' button - should query detail")
        print("  3. Click 'delete' button - should delete stock")
    else:
        print("\n[FAILED] Failed to send watchlist card")
        print("Possible reasons:")
        print("  - Invalid chat_id")
        print("  - Feishu API not available")
        print("  - Backend service not running")
    
    print("=" * 60)


async def main():
    """Run all tests"""
    try:
        await test_send_holdings_card()
        await test_send_watchlist_card()
        
        print("\n" + "=" * 60)
        print("[INFO] All cards sent! Please test buttons in Feishu.")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
