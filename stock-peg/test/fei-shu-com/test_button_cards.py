"""Test button-based holdings and watchlist cards"""
import sys
import os

# Add backend to path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend'))
sys.path.insert(0, backend_path)

from services.feishu_card_service import FeishuCardService
from services.holdings_manager import HoldingsManager
import asyncio


async def test_holdings_card():
    """Test button-based holdings card"""
    print("=" * 60)
    print("Testing Holdings Card with Button-Based Layout")
    print("=" * 60)
    
    # Initialize card service
    card_service = FeishuCardService()
    
    # Create test holdings data
    holdings_manager = HoldingsManager()
    holdings_data = holdings_manager.read_holdings()
    
    print(f"\nHoldings data: {holdings_data}")
    
    # Create button-based card
    card = card_service._create_holdings_display_card(holdings_data)
    
    print("\n" + "=" * 60)
    print("Holdings Card Structure:")
    print("=" * 60)
    
    # Print card structure (simplified)
    print(f"Header: {card.get('header', {}).get('title', {})}")
    print(f"Elements count: {len(card.get('elements', []))}")
    
    # Find action blocks
    action_count = 0
    for i, element in enumerate(card.get('elements', [])):
        if element.get('tag') == 'action':
            action_count += 1
            actions = element.get('actions', [])
            print(f"\nAction Block #{action_count}:")
            for action in actions:
                button_text = action.get('text', {}).get('content', '')
                button_type = action.get('type', '')
                action_value = action.get('value', {})
                print(f"  - [{button_type}] {button_text} -> {action_value.get('action', 'unknown')}")
    
    print(f"\nTotal action blocks: {action_count}")
    print("=" * 60)


async def test_watchlist_card():
    """Test button-based watchlist card"""
    print("\n" + "=" * 60)
    print("Testing Watchlist Card with Button-Based Layout")
    print("=" * 60)
    
    # Initialize card service
    card_service = FeishuCardService()
    
    # Create test watchlist data
    test_stocks = [
        {
            'stock_code': '601898',
            'stock_name': '中煤能源',
            'date': '2026-03-17',
            'target_price': 12.5,
            'stop_loss_price': 10.0,
            'reason': '测试股票1'
        },
        {
            'stock_code': '000001',
            'stock_name': '平安银行',
            'date': '2026-03-16',
            'target_price': 15.0,
            'reason': '测试股票2'
        }
    ]
    
    print(f"\nWatchlist data: {test_stocks}")
    
    # Create button-based card
    card = card_service._create_watchlist_display_card(test_stocks, date_count=2)
    
    print("\n" + "=" * 60)
    print("Watchlist Card Structure:")
    print("=" * 60)
    
    # Print card structure (simplified)
    print(f"Header: {card.get('header', {}).get('title', {})}")
    print(f"Elements count: {len(card.get('elements', []))}")
    
    # Find action blocks
    action_count = 0
    for i, element in enumerate(card.get('elements', [])):
        if element.get('tag') == 'action':
            action_count += 1
            actions = element.get('actions', [])
            print(f"\nAction Block #{action_count}:")
            for action in actions:
                button_text = action.get('text', {}).get('content', '')
                button_type = action.get('type', '')
                action_value = action.get('value', {})
                print(f"  - [{button_type}] {button_text} -> {action_value.get('action', 'unknown')}")
    
    print(f"\nTotal action blocks: {action_count}")
    print("=" * 60)


async def main():
    """Run all tests"""
    try:
        await test_holdings_card()
        await test_watchlist_card()
        
        print("\n" + "=" * 60)
        print("[SUCCESS] All tests completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[FAILED] Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
