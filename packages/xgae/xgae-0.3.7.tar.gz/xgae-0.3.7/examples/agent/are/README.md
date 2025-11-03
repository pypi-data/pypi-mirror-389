## GAIA2 ARE Support
### How to add XGAE to ARE Project
- add xgae==0.3.2 to ARE requirements.txt
- uv pip install -r requirements.txt
- modify ARE 'AgentBuilder' and 'AgentConfigBuilder' class, add "xga" type agent :
  ```
  File: agent_builder.py
      class AgentBuilder:
        def list_agents(self) -> list[str]:
          return ["default", "xga"]
            
        def build():
            ...
            agent_name = agent_config.get_agent_name()
            if agent_name in ["default", "xga"]:
                # add xga agent code
      
  File: agent_config_builder.py
    class AgentConfigBuilder:
        def build():
            if agent_name in["default", "xga"]:
  ```
- modify ARE 'MCPApp' :
    ```
    File: mcp_app.py
        class MCPApp:
            def _call_tool(self, tool_name: str, **kwargs) -> str:
                try:
                    ...
                    from are.simulation.agents.xga.mcp_tool_executor import call_mcp_tool
                    result = call_mcp_tool(self.server_url, tool_name, kwargs, 10)
                    return str(result)
                    
    
    ```


- modify ARE .env, add XGAE .env config, refer to env.example 
- copy XGAE package 'mcpservers' and 'templates' directory to ARE project root  

### Run XGA Agent in ARE
  ```
uv run are-run -e -s scenario_find_image_file -a xga --model openai/qwen3-235b-a22b --provider llama-api --output_dir ./output
  ```