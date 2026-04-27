"""Holdings manager service for managing 自持股票.md file"""
import os
import logging
from typing import Optional
from pathlib import Path
import re

logger = logging.getLogger(__name__)


class HoldingsManager:
    """Manage holdings data in 自持股票.md"""
    
    def __init__(self, file_path: str = None):
        if file_path is None:
            # Default path
            backend_dir = Path(__file__).parent.parent
            self.file_path = backend_dir / "data" / "自持股票.md"
        else:
            self.file_path = Path(file_path)
        
        logger.info(f"HoldingsManager initialized with file: {self.file_path}")
    
    def read_holdings(self) -> dict:
        """
        Read holdings from markdown file
        
        Returns:
            dict: {"sectors": [{"name": "板块名", "stocks": ["股票1", "股票2"]}, ...]}
        """
        if not self.file_path.exists():
            logger.warning(f"Holdings file not found: {self.file_path}")
            return {"sectors": []}
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            sectors = []
            current_sector = None
            
            for line in content.split('\n'):
                line_stripped = line.strip()
                
                # Skip empty lines and header
                if not line_stripped or line_stripped == "# 自持股票":
                    continue
                
                # Sector header (## 板块名)
                if line_stripped.startswith('## '):
                    if current_sector:
                        sectors.append(current_sector)
                    sector_name = line_stripped[3:].strip()
                    current_sector = {"name": sector_name, "stocks": []}
                
                # Stock item (indented line, not starting with #)
                elif line.startswith('    ') or line.startswith('\t'):
                    stock_name = line_stripped
                    
                    # Clean HTML comments if present (preserve only stock name)
                    if '<!--' in stock_name and '-->' in stock_name:
                        import re
                        match = re.search(r'(.+?)\s*<!--', stock_name)
                        if match:
                            stock_name = match.group(1).strip()
                    
                    if stock_name and current_sector and not stock_name.startswith('#'):
                        current_sector["stocks"].append(stock_name)
            
            # Add last sector
            if current_sector:
                sectors.append(current_sector)
            
            logger.info(f"Read {len(sectors)} sectors from holdings file")
            return {"sectors": sectors}
        
        except Exception as e:
            logger.error(f"Failed to read holdings file: {str(e)}")
            return {"sectors": []}
    
    def get_holdings_target_price(self, stock_name: str) -> Optional[dict]:
        """
        Get target price info for a holdings stock
        
        Args:
            stock_name: Stock name to search for
        
        Returns:
            dict with target_price, change_up_pct, change_down_pct if found, else None
        """
        if not self.file_path.exists():
            return None
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Pattern: 股票名 <!-- target_price:5.5, change_up_pct:20.0, change_down_pct:10.0 -->
            pattern = rf'{re.escape(stock_name)}\s*<!--\s*target_price:([0-9.]+),\s*change_up_pct:([0-9.]+),\s*change_down_pct:([0-9.]+)\s*-->'
            
            match = re.search(pattern, content)
            if match:
                return {
                    "target_price": float(match.group(1)),
                    "change_up_pct": float(match.group(2)),
                    "change_down_pct": float(match.group(3)),
                }
            
            return None
        
        except Exception as e:
            logger.error(f"Failed to get target price for {stock_name}: {str(e)}")
            return None
    
    def write_holdings(self, sectors: list) -> bool:
        """
        Write holdings to markdown file
        
        Args:
            sectors: List of {"name": "板块名", "stocks": ["股票1", "股票2"]}
        
        Returns:
            bool: Success or not
        """
        try:
            lines = ["# 自持股票\n"]
            
            for sector in sectors:
                lines.append(f"\n## {sector['name']}\n")
                for stock in sector['stocks']:
                    lines.append(f"    {stock}\n")
            
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            logger.info(f"Written {len(sectors)} sectors to holdings file")
            return True
        
        except Exception as e:
            logger.error(f"Failed to write holdings file: {str(e)}")
            return False
    
    def add_sector(self, sector_name: str) -> bool:
        """
        Add a new sector
        
        Args:
            sector_name: Name of the sector to add
        
        Returns:
            bool: Success or not
        """
        try:
            data = self.read_holdings()
            
            # Check if sector already exists
            for sector in data['sectors']:
                if sector['name'] == sector_name:
                    logger.warning(f"Sector already exists: {sector_name}")
                    return False
            
            # Add new sector
            data['sectors'].append({"name": sector_name, "stocks": []})
            
            # Write back
            success = self.write_holdings(data['sectors'])
            
            if success:
                logger.info(f"Added sector: {sector_name}")
            
            return success
        
        except Exception as e:
            logger.error(f"Failed to add sector: {str(e)}")
            return False
    
    def remove_sector(self, sector_name: str) -> bool:
        """
        Remove a sector
        
        Args:
            sector_name: Name of the sector to remove
        
        Returns:
            bool: Success or not
        """
        try:
            data = self.read_holdings()
            
            # Find and remove sector
            original_count = len(data['sectors'])
            data['sectors'] = [s for s in data['sectors'] if s['name'] != sector_name]
            
            if len(data['sectors']) == original_count:
                logger.warning(f"Sector not found: {sector_name}")
                return False
            
            # Write back
            success = self.write_holdings(data['sectors'])
            
            if success:
                logger.info(f"Removed sector: {sector_name}")
            
            return success
        
        except Exception as e:
            logger.error(f"Failed to remove sector: {str(e)}")
            return False
    
    def add_stock(self, stock_name: str, sector_name: str, auto_create_sector: bool = True) -> bool:
        """
        Add a stock to a sector
        
        Args:
            stock_name: Name of the stock to add
            sector_name: Name of the target sector
            auto_create_sector: Automatically create sector if not exists (default: True)
        
        Returns:
            bool: Success or not
        """
        try:
            data = self.read_holdings()
            
            # Find sector
            sector_found = False
            for sector in data['sectors']:
                if sector['name'] == sector_name:
                    sector_found = True
                    
                    # Check if stock already exists
                    if stock_name in sector['stocks']:
                        logger.warning(f"Stock already exists in sector: {stock_name} in {sector_name}")
                        return False
                    
                    # Add stock
                    sector['stocks'].append(stock_name)
                    break
            
            # If sector not found, create it if auto_create_sector is True
            if not sector_found and auto_create_sector:
                logger.info(f"Auto-creating sector: {sector_name}")
                data['sectors'].append({"name": sector_name, "stocks": [stock_name]})
                sector_found = True
            elif not sector_found:
                logger.warning(f"Sector not found: {sector_name}")
                return False
            
            # Write back
            success = self.write_holdings(data['sectors'])
            
            if success:
                logger.info(f"Added stock {stock_name} to sector {sector_name}")
            
            return success
        
        except Exception as e:
            logger.error(f"Failed to add stock: {str(e)}")
            return False
    
    def remove_stock(self, stock_name: str, sector_name: Optional[str] = None) -> bool:
        """
        Remove a stock from a sector (or all sectors if sector_name is None)
        
        Args:
            stock_name: Name of the stock to remove
            sector_name: Name of the sector (optional, if None, remove from all sectors)
        
        Returns:
            bool: Success or not
        """
        try:
            data = self.read_holdings()
            stock_removed = False
            
            for sector in data['sectors']:
                # If sector_name specified, only process that sector
                if sector_name and sector['name'] != sector_name:
                    continue
                
                # Remove stock
                if stock_name in sector['stocks']:
                    sector['stocks'].remove(stock_name)
                    stock_removed = True
                    logger.info(f"Removed stock {stock_name} from sector {sector['name']}")
            
            if not stock_removed:
                logger.warning(f"Stock not found: {stock_name}")
                return False
            
            # Write back
            success = self.write_holdings(data['sectors'])
            return success
        
        except Exception as e:
            logger.error(f"Failed to remove stock: {str(e)}")
            return False
    
    def move_stock(self, stock_name: str, from_sector: str, to_sector: str) -> bool:
        """
        Move a stock from one sector to another
        
        Args:
            stock_name: Name of the stock to move
            from_sector: Source sector name
            to_sector: Target sector name
        
        Returns:
            bool: Success or not
        """
        try:
            data = self.read_holdings()
            
            # Find both sectors
            from_sector_obj = None
            to_sector_obj = None
            
            for sector in data['sectors']:
                if sector['name'] == from_sector:
                    from_sector_obj = sector
                if sector['name'] == to_sector:
                    to_sector_obj = sector
            
            if not from_sector_obj:
                logger.warning(f"Source sector not found: {from_sector}")
                return False
            
            if not to_sector_obj:
                logger.warning(f"Target sector not found: {to_sector}")
                return False
            
            # Check if stock exists in source sector
            if stock_name not in from_sector_obj['stocks']:
                logger.warning(f"Stock not found in source sector: {stock_name} in {from_sector}")
                return False
            
            # Remove from source
            from_sector_obj['stocks'].remove(stock_name)
            
            # Add to target
            to_sector_obj['stocks'].append(stock_name)
            
            # Write back
            success = self.write_holdings(data['sectors'])
            
            if success:
                logger.info(f"Moved stock {stock_name} from {from_sector} to {to_sector}")
            
            return success
        
        except Exception as e:
            logger.error(f"Failed to move stock: {str(e)}")
            return False


# Singleton instance
holdings_manager = HoldingsManager()
