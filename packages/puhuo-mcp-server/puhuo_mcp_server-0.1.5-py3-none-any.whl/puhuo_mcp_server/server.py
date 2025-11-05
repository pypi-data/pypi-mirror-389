from mcp.server.fastmcp import FastMCP
import logging
from http import HTTPStatus
from urllib.parse import urlparse, unquote
from pathlib import PurePosixPath
import requests
import os

logger = logging.getLogger('mcp')
logger.setLevel(logging.DEBUG)

# 从环境变量读取配置
CAINIAO_TOKEN = os.getenv('CAINIAO_TOKEN', '')
if not CAINIAO_TOKEN:
    logger.warning("环境变量 CAINIAO_TOKEN 未设置，请在 MCP 配置中设置")

# 初始化mcp服务
mcp = FastMCP('Waybill Intercept Demo')
# 定义工具
@mcp.tool(description="拦截运单号，返回是否拦截及原因")
def intercept_waybill(waybill_no: str) -> dict:
    # mock 逻辑：以A开头的运单号拦截
    if waybill_no.startswith("A"):
        return {"waybill_no": waybill_no, "intercepted": True, "reason": "黑名单运单号"}
    else:
        return {"waybill_no": waybill_no, "intercepted": False, "reason": "正常运单号"}

@mcp.tool(description="根据运单号查询快递公司编码")
def suggest_cp_code(waybill_no: str) -> dict:
    """
    查询运单号对应的快递公司编码
    
    参数:
        waybill_no: 运单号
        
    返回:
        包含快递公司编码的字典
    """
    try:
        if not CAINIAO_TOKEN:
            return {
                "waybill_no": waybill_no,
                "success": False,
                "error_msg": "CAINIAO_TOKEN 环境变量未设置",
                "message": "配置错误：请设置 CAINIAO_TOKEN 环境变量"
            }
        
        url = "https://pre-xg.cainiao.com/agent/mcp/suggestCpCode"
        data = {"waybillNo": waybill_no}
        headers = {
            "Token": CAINIAO_TOKEN,
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("success"):
            cp_code = result.get("data", {}).get("cpCode")
            return {
                "waybill_no": waybill_no,
                "success": True,
                "cp_code": cp_code,
                "message": result.get("errorMsg", "success")
            }
        else:
            return {
                "waybill_no": waybill_no,
                "success": False,
                "error_code": result.get("errorCode"),
                "error_msg": result.get("errorMsg"),
                "message": "查询失败"
            }
    except requests.exceptions.RequestException as e:
        logger.error(f"查询快递公司编码失败: {e}")
        return {
            "waybill_no": waybill_no,
            "success": False,
            "error_msg": str(e),
            "message": "网络请求失败"
        }

def run():
    mcp.run(transport='stdio')
if __name__ == '__main__':
   run()