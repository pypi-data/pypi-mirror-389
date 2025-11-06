import re
from typing_extensions import override
from typing import Optional, List, Literal

from xgae.engine.engine_base import XGAToolSchema
from xgae.engine.prompt_builder import XGAPromptBuilder

class XGAArePromptBuilder(XGAPromptBuilder):
    def __init__(self,
                 general_system_prompt: Optional[str],
                 prompt_template_mode: Literal["basic", "prior"] = "prior"
        ):
        system_prompt = ""
        if prompt_template_mode == "basic":
            system_prompt = self.build_general_system_prompt(general_system_prompt)

        super().__init__(system_prompt)

        self.prompt_template_mode = prompt_template_mode


    def build_general_system_prompt(self, _system_prompt: str)-> str:
        pattern = r'<general_instructions>(.*?)</general_instructions>'
        prompt_are_general = re.search(pattern, _system_prompt, re.DOTALL)
        prompt_header = "# CORE IDENTITY\n"
        if prompt_are_general:
            prompt_are_general = prompt_header + prompt_are_general.group(1).strip() + "\n\n"
        else:
            prompt_are_general = prompt_header + _system_prompt  + "\n\n"
        return prompt_are_general


    @override
    def build_general_tool_prompt(self, tool_schemas: List[XGAToolSchema])-> str:
        tool_prompt = ""
        if self.prompt_template_mode == "basic":
            tool_prompt = self.build_mcp_tool_prompt("templates/system_tool_prompt_template.md", tool_schemas)
        return tool_prompt


    @override
    def build_custom_tool_prompt(self, tool_schemas:List[XGAToolSchema])-> str:
        if self.prompt_template_mode == "basic":
            tool_prompt = self.build_mcp_tool_prompt("templates/app_tool_prompt_template.md", tool_schemas)
        else:
            tool_prompt = self.build_mcp_tool_prompt("templates/are_prompt_template.md", tool_schemas)
        return tool_prompt

