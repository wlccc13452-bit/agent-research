"""Stock PEG MCP Server - Expose backend data capabilities to AI Agents via MCP protocol"""
import asyncio
import logging
from typing import Optional, List
from datetime import datetime, date
import sys
from pathlib import Path

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from fastmcp import FastMCP

# Import backend services
from services.stock_service import stock_service
from datasource import get_datasource, DataSourceType
from services.fundamental_analyzer import FundamentalAnalyzer
from services.force_index_calculator import force_index_calculator
from services.pmr_calculator import PMRCalculator
from services.market_sentiment_cache_service import market_sentiment_cache_service
from database import get_db
from config.settings import settings

# Create service instances
fundamental_analyzer = FundamentalAnalyzer()
pmr_calculator = PMRCalculator()

# Database session context manager for MCP tools
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession

@asynccontextmanager
async def get_db_context():
    """Get database session as async context manager"""
    async for session in get_db():
        yield session

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastMCP server instance
mcp = FastMCP("Stock PEG Data Server")


# Helper function to get akshare source
def _get_akshare_source():
    """Get AkshareDataSource from datasource manager"""
    return get_datasource().get_source(DataSourceType.AKSHARE)

# ============ Stock Quote Tools ============

@mcp.tool()
async def get_stock_quote(stock_code: str) -> dict:
    """
    Get real-time stock quote (实时行情)
    
    Args:
        stock_code: Stock code (e.g., "000001", "600519")
    
    Returns:
        Real-time quote data including price, change, volume, etc.
    """
    try:
        quote = await stock_service.get_realtime_quote(stock_code)
        if not quote:
            return {"error": f"No quote data found for {stock_code}"}
        
        return {
            "stock_code": stock_code,
            "stock_name": quote.get("name", ""),
            "price": quote.get("price", 0),
            "change": quote.get("change", 0),
            "change_pct": quote.get("change_pct", 0),
            "volume": quote.get("volume", 0),
            "amount": quote.get("amount", 0),
            "high": quote.get("high", 0),
            "low": quote.get("low", 0),
            "open": quote.get("open", 0),
            "prev_close": quote.get("prev_close", 0),
            "timestamp": quote.get("timestamp", datetime.now().isoformat())
        }
    except Exception as e:
        logger.error(f"Failed to get quote for {stock_code}: {str(e)}")
        return {"error": str(e)}


@mcp.tool()
async def get_batch_quotes(stock_codes: List[str]) -> dict:
    """
    Get real-time quotes for multiple stocks (批量行情)
    
    Args:
        stock_codes: List of stock codes (e.g., ["000001", "600519", "000002"])
    
    Returns:
        Dictionary mapping stock codes to quote data
    """
    try:
        quotes = await stock_service.get_batch_realtime_quotes(stock_codes)
        return {
            "success": True,
            "count": len(quotes),
            "data": quotes
        }
    except Exception as e:
        logger.error(f"Failed to get batch quotes: {str(e)}")
        return {"error": str(e), "success": False}


# ============ K-Line Data Tools ============

@mcp.tool()
async def get_stock_kline(
    stock_code: str,
    period: str = "day",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100
) -> dict:
    """
    Get K-line (candlestick) data for a stock (K线数据)
    
    Args:
        stock_code: Stock code (e.g., "000001", "600519")
        period: K-line period - "day", "week", "month", "m1", "m5", "m15", "m30", "m60"
        start_date: Start date (YYYY-MM-DD), optional
        end_date: End date (YYYY-MM-DD), optional
        limit: Number of records to return (default 100)
    
    Returns:
        K-line data with OHLCV and technical indicators
    """
    try:
        kline_data = await stock_service.get_kline_data(
            stock_code=stock_code,
            period=period,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        if not kline_data or not kline_data.get("data"):
            return {"error": f"No K-line data found for {stock_code}"}
        
        return {
            "stock_code": stock_code,
            "stock_name": kline_data.get("name", ""),
            "period": period,
            "count": len(kline_data.get("data", [])),
            "data": kline_data.get("data", [])[:limit]
        }
    except Exception as e:
        logger.error(f"Failed to get K-line for {stock_code}: {str(e)}")
        return {"error": str(e)}


# ============ Technical Indicators Tools ============

@mcp.tool()
async def get_technical_indicators(stock_code: str, period: str = "day") -> dict:
    """
    Get technical indicators for a stock (技术指标: MA/MACD/RSI/KDJ)
    
    Args:
        stock_code: Stock code (e.g., "000001", "600519")
        period: K-line period - "day", "week", "month"
    
    Returns:
        Technical indicators including MA, MACD, RSI, KDJ
    """
    try:
        indicators = await stock_service.get_technical_indicators(stock_code, period)
        
        if not indicators:
            return {"error": f"No technical indicators found for {stock_code}"}
        
        return {
            "stock_code": stock_code,
            "stock_name": indicators.get("name", ""),
            "period": period,
            "ma": indicators.get("ma", {}),
            "macd": indicators.get("macd", {}),
            "rsi": indicators.get("rsi", {}),
            "kdj": indicators.get("kdj", {}),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get technical indicators for {stock_code}: {str(e)}")
        return {"error": str(e)}


@mcp.tool()
async def get_force_index(stock_code: str, period: int = 13) -> dict:
    """
    Get Force Index indicator (Alexander Elder's Force Index - 力量指数)
    
    Args:
        stock_code: Stock code (e.g., "000001", "600519")
        period: Force Index period (default 13)
    
    Returns:
        Force Index analysis with buy/sell signals
    """
    try:
        async with get_db_context() as db:
            result = await force_index_calculator.analyze_stock(
                db=db,
                stock_code=stock_code,
                period=period
            )
            
            if not result:
                return {"error": f"No Force Index data for {stock_code}"}
            
            return {
                "stock_code": stock_code,
                "stock_name": result.get("stock_name", ""),
                "period": period,
                "force_index": result.get("force_index", []),
                "signal": result.get("signal", "hold"),
                "strength": result.get("strength", 0),
                "trend": result.get("trend", "unknown"),
                "recommendation": result.get("recommendation", "")
            }
    except Exception as e:
        logger.error(f"Failed to get Force Index for {stock_code}: {str(e)}")
        return {"error": str(e)}


@mcp.tool()
async def get_pmr(stock_code: str) -> dict:
    """
    Get PMR (Price Momentum Ratio) indicator (价格动量比值)
    
    Args:
        stock_code: Stock code (e.g., "000001", "600519")
    
    Returns:
        PMR values across multiple timeframes
    """
    try:
        async with get_db_context() as db:
            result = await pmr_calculator.calculate_pmr(db, stock_code)
            
            if not result:
                return {"error": f"No PMR data for {stock_code}"}
            
            return {
                "stock_code": stock_code,
                "stock_name": result.get("stock_name", ""),
                "pmr_5": result.get("pmr_5"),
                "pmr_10": result.get("pmr_10"),
                "pmr_20": result.get("pmr_20"),
                "pmr_60": result.get("pmr_60"),
                "signal": result.get("signal", "neutral"),
                "trend": result.get("trend", "unknown")
            }
    except Exception as e:
        logger.error(f"Failed to get PMR for {stock_code}: {str(e)}")
        return {"error": str(e)}


# ============ Fundamental Analysis Tools ============

@mcp.tool()
async def get_fundamental_analysis(stock_code: str) -> dict:
    """
    Get comprehensive fundamental analysis (基本面综合分析)
    
    Args:
        stock_code: Stock code (e.g., "000001", "600519")
    
    Returns:
        Fundamental analysis including valuation, growth, financial health
    """
    try:
        async with get_db_context() as db:
            result = await fundamental_analyzer.analyze_stock(db, stock_code)
            
            if not result:
                return {"error": f"No fundamental data for {stock_code}"}
            
            return {
                "stock_code": stock_code,
                "stock_name": result.get("stock_name", ""),
                "valuation": result.get("valuation", {}),
                "growth": result.get("growth", {}),
                "financial_health": result.get("financial_health", {}),
                "score": result.get("score", 0),
                "rating": result.get("rating", "N/A"),
                "recommendation": result.get("recommendation", "")
            }
    except Exception as e:
        logger.error(f"Failed to get fundamental analysis for {stock_code}: {str(e)}")
        return {"error": str(e)}


@mcp.tool()
async def get_valuation_metrics(stock_code: str) -> dict:
    """
    Get valuation metrics (估值指标: PE/PB/PS/PEG)
    
    Args:
        stock_code: Stock code (e.g., "000001", "600519")
    
    Returns:
        Valuation metrics including PE, PB, PS, PEG
    """
    try:
        async with get_db_context() as db:
            result = await fundamental_analyzer.get_valuation(db, stock_code)
            
            if not result:
                return {"error": f"No valuation data for {stock_code}"}
            
            return {
                "stock_code": stock_code,
                "stock_name": result.get("stock_name", ""),
                "pe_ttm": result.get("pe_ttm"),
                "pb": result.get("pb"),
                "ps": result.get("ps"),
                "peg": result.get("peg"),
                "market_cap": result.get("market_cap"),
                "timestamp": result.get("timestamp", datetime.now().isoformat())
            }
    except Exception as e:
        logger.error(f"Failed to get valuation for {stock_code}: {str(e)}")
        return {"error": str(e)}


# ============ Market Sentiment Tools ============

@mcp.tool()
async def get_market_sentiment() -> dict:
    """
    Get market sentiment data (市场情绪: 涨跌停/市场宽度)
    
    Returns:
        Market sentiment including up/down count, market breadth, etc.
    """
    try:
        async with get_db_context() as db:
            result = await market_sentiment_cache_service.get_sentiment(db)
            
            if not result:
                return {"error": "No market sentiment data available"}
            
            return {
                "timestamp": result.get("timestamp", datetime.now().isoformat()),
                "up_count": result.get("up_count", 0),
                "down_count": result.get("down_count", 0),
                "flat_count": result.get("flat_count", 0),
                "limit_up_count": result.get("limit_up_count", 0),
                "limit_down_count": result.get("limit_down_count", 0),
                "market_breadth": result.get("market_breadth", 0),
                "total_count": result.get("total_count", 0)
            }
    except Exception as e:
        logger.error(f"Failed to get market sentiment: {str(e)}")
        return {"error": str(e)}


@mcp.tool()
async def get_market_indices() -> dict:
    """
    Get major market indices (主要指数: 上证/深证/创业板)
    
    Returns:
        Major index data including Shanghai, Shenzhen, ChiNext, etc.
    """
    try:
        indices = await stock_service.get_cn_indices()
        
        if not indices:
            return {"error": "No market indices data available"}
        
        return {
            "timestamp": datetime.now().isoformat(),
            "indices": indices
        }
    except Exception as e:
        logger.error(f"Failed to get market indices: {str(e)}")
        return {"error": str(e)}


# ============ Sector Data Tools ============

@mcp.tool()
async def get_industry_sectors() -> dict:
    """
    Get industry sector list (行业板块列表)
    
    Returns:
        List of industry sectors with performance data
    """
    try:
        source = _get_akshare_source()
        if not source:
            return "Error: Akshare data source not available"
        sectors = await source.get_industry_sectors()
        
        if not sectors:
            return {"error": "No industry sectors data available"}
        
        return {
            "timestamp": datetime.now().isoformat(),
            "count": len(sectors),
            "sectors": sectors
        }
    except Exception as e:
        logger.error(f"Failed to get industry sectors: {str(e)}")
        return {"error": str(e)}


@mcp.tool()
async def get_concept_sectors() -> dict:
    """
    Get concept sector list (概念板块列表)
    
    Returns:
        List of concept sectors with performance data
    """
    try:
        source = _get_akshare_source()
        if not source:
            return "Error: Akshare data source not available"
        sectors = await source.get_concept_sectors()
        
        if not sectors:
            return {"error": "No concept sectors data available"}
        
        return {
            "timestamp": datetime.now().isoformat(),
            "count": len(sectors),
            "sectors": sectors
        }
    except Exception as e:
        logger.error(f"Failed to get concept sectors: {str(e)}")
        return {"error": str(e)}


# ============ Fund Flow Tools ============

@mcp.tool()
async def get_stock_fund_flow(stock_code: str) -> dict:
    """
    Get fund flow data for a stock (个股资金流向)
    
    Args:
        stock_code: Stock code (e.g., "000001", "600519")
    
    Returns:
        Fund flow data including main force and retail flows
    """
    try:
        source = _get_akshare_source()
        if not source:
            return "Error: Akshare data source not available"
        flow_data = await source.get_individual_fund_flow(stock_code)
        
        if not flow_data:
            return {"error": f"No fund flow data for {stock_code}"}
        
        return {
            "stock_code": stock_code,
            "stock_name": flow_data.get("name", ""),
            "main_net_inflow": flow_data.get("main_net_inflow", 0),
            "retail_net_inflow": flow_data.get("retail_net_inflow", 0),
            "super_net_inflow": flow_data.get("super_net_inflow", 0),
            "big_net_inflow": flow_data.get("big_net_inflow", 0),
            "medium_net_inflow": flow_data.get("medium_net_inflow", 0),
            "small_net_inflow": flow_data.get("small_net_inflow", 0),
            "timestamp": flow_data.get("timestamp", datetime.now().isoformat())
        }
    except Exception as e:
        logger.error(f"Failed to get fund flow for {stock_code}: {str(e)}")
        return {"error": str(e)}


@mcp.tool()
async def get_north_money_flow() -> dict:
    """
    Get northbound money flow data (北向资金流向)
    
    Returns:
        Northbound capital flow data
    """
    try:
        source = _get_akshare_source()
        if not source:
            return "Error: Akshare data source not available"
        flow_data = await source.get_north_money_flow()
        
        if not flow_data:
            return {"error": "No northbound money flow data available"}
        
        return {
            "timestamp": datetime.now().isoformat(),
            "data": flow_data
        }
    except Exception as e:
        logger.error(f"Failed to get northbound money flow: {str(e)}")
        return {"error": str(e)}


# ============ Holdings Management Tools ============

@mcp.tool()
async def get_holdings() -> dict:
    """
    Get current holdings list (获取持仓列表)
    
    Returns:
        Holdings data with sectors and stocks
    """
    try:
        from services.holding_manager import HoldingManager
        
        holding_manager = HoldingManager(settings.holdings_file_path)
        holdings = await holding_manager.load_holdings()
        
        return {
            "success": True,
            "data": holdings.model_dump()
        }
    except Exception as e:
        logger.error(f"Failed to get holdings: {str(e)}")
        return {"error": str(e), "success": False}


# ============ US Market Tools ============

@mcp.tool()
async def get_us_market_indices() -> dict:
    """
    Get US market indices (美股指数: 标普/纳斯达克/道琼斯)
    
    Returns:
        US market index data
    """
    try:
        from services.us_market_analyzer import us_market_analyzer
        
        indices = await us_market_analyzer.get_us_indices()
        
        if not indices:
            return {"error": "No US market indices data available"}
        
        return {
            "timestamp": datetime.now().isoformat(),
            "indices": indices
        }
    except Exception as e:
        logger.error(f"Failed to get US market indices: {str(e)}")
        return {"error": str(e)}


# ============ Macro Economic Tools ============

@mcp.tool()
async def get_macro_cpi() -> dict:
    """
    Get China CPI data (中国CPI数据)
    
    Returns:
        CPI data for the last 12 months
    """
    try:
        source = _get_akshare_source()
        if not source:
            return "Error: Akshare data source not available"
        cpi_data = await source.get_china_cpi()
        
        if not cpi_data:
            return {"error": "No CPI data available"}
        
        return {
            "timestamp": datetime.now().isoformat(),
            "data": cpi_data
        }
    except Exception as e:
        logger.error(f"Failed to get CPI data: {str(e)}")
        return {"error": str(e)}


@mcp.tool()
async def get_macro_gdp() -> dict:
    """
    Get China GDP data (中国GDP数据)
    
    Returns:
        GDP data for the last 8 quarters
    """
    try:
        source = _get_akshare_source()
        if not source:
            return "Error: Akshare data source not available"
        gdp_data = await source.get_china_gdp()
        
        if not gdp_data:
            return {"error": "No GDP data available"}
        
        return {
            "timestamp": datetime.now().isoformat(),
            "data": gdp_data
        }
    except Exception as e:
        logger.error(f"Failed to get GDP data: {str(e)}")
        return {"error": str(e)}


@mcp.tool()
async def get_macro_pmi() -> dict:
    """
    Get China PMI data (中国PMI数据)
    
    Returns:
        PMI data for the last 12 months
    """
    try:
        source = _get_akshare_source()
        if not source:
            return "Error: Akshare data source not available"
        pmi_data = await source.get_china_pmi()
        
        if not pmi_data:
            return {"error": "No PMI data available"}
        
        return {
            "timestamp": datetime.now().isoformat(),
            "data": pmi_data
        }
    except Exception as e:
        logger.error(f"Failed to get PMI data: {str(e)}")
        return {"error": str(e)}


# ============ Resource Endpoints ============

@mcp.resource("stock://{stock_code}/quote")
async def get_stock_quote_resource(stock_code: str) -> str:
    """Get stock quote as a resource"""
    result = await get_stock_quote(stock_code)
    return str(result)


@mcp.resource("stock://{stock_code}/kline")
async def get_stock_kline_resource(stock_code: str) -> str:
    """Get stock K-line as a resource"""
    result = await get_stock_kline(stock_code)
    return str(result)


@mcp.resource("market://sentiment")
async def get_market_sentiment_resource() -> str:
    """Get market sentiment as a resource"""
    result = await get_market_sentiment()
    return str(result)


# ============ Server Startup ============

def run_server():
    """Run the MCP server"""
    logger.info("Starting Stock PEG MCP Server...")
    mcp.run()


if __name__ == "__main__":
    run_server()
