"""MCP tools for simple clothing and packing suggestions."""

from mcp.server import MCPServer


mcp = MCPServer("穿衣建议服务")


@mcp.tool()
def suggest_clothing(temperature: float) -> str:
    """根据摄氏气温给出简单穿衣建议。"""
    if temperature >= 28:
        return "天气较热，可以考虑短袖和轻薄衣物。"
    if temperature >= 20:
        return "可以考虑长袖，或短袖搭配薄外套。"
    if temperature >= 10:
        return "天气偏凉，可以考虑毛衣和外套。"
    return "天气较冷，可以考虑厚外套，并注意保暖。"


@mcp.tool()
def packing_list(is_raining: bool) -> str:
    """根据是否下雨给出简单出门物品清单。"""
    if is_raining:
        return "建议带雨伞，并用防水袋保护手机等物品。"
    return "可以带上饮用水、手机和钥匙。"


if __name__ == "__main__":
    mcp.run()
