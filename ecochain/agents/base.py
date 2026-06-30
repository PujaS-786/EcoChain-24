from ecochain.mcp import call_mcp_tool, AGENT_TOKENS

class Agent:
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.token = AGENT_TOKENS.get(agent_name, "")
        
    def call_tool(self, tool_name: str, args: dict) -> dict:
        """Call a registered tool on the MCP server using this agent's scoped identity token."""
        return call_mcp_tool(self.agent_name, self.token, tool_name, args)
        
    def log_action(self, action: str, details: dict):
        """Standardized wrapper for recording entries in the audit trail."""
        self.call_tool("ecochain.log.write", {
            "calling_agent": self.agent_name,
            "action": action,
            "details": details
        })
