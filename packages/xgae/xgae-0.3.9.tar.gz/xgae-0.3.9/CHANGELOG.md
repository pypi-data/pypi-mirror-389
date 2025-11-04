## [0.3.9] - 2025-11-4
### Added
- ✅ GAIA2 ARE Example:  Add new prompt template, Leading over ARE 'default agent'
### Modified
- GAIA2 ARE Example: Refact prompt templates, use MD format
- GAIA2 ARE Example:  XGAArePromptBuilder add 'prior' template mode
- ARE Engine: remove useless 'system_prompt' init parameter


## [0.3.5] - 2025-11-1
### Added
- GAIA2 ARE Example:  XGAArePromptBuilder, Use MCP tool format general tool construct prompt
### Modified
- GAIA2 ARE Example: Refact code struct and class name
- GAIA2 ARE Example: Optimize prompt template 
- ARETaskEngine: add prompt_builder init parameter


## [0.3.3] - 2025-10-30
### Added
- GAIA2 ARE Scenario:  scenario_bomc_fault
- GAIA2 ARE MCP: Support Custom MCP Apps, example_mcp_apps.json


## [0.3.2] - 2025-10-24
### Added
- GAIA2 ARE Example:  XGAAreAgent, XGAAreToolBox
### Modified
- ARETaskEngine


## [0.3.0] - 2025-10-22
### Added
- Support GAIA2 ARE: ARETaskEngine


## [0.2.4] - 2025-9-23
### Modified
- Refact project structure


## [0.2.3] - 2025-9-19
### Modified
- CustomPromptRag: remove FastEmbedEmbeddings, use 'text-embedding-v3' model for chinese, avoid download 'bge-small-zh-v1.5'


## [0.2.1] - 2025-9-17
### Added
- Example ReflectionAgent: add CustomPromptRag, use FastEmbedEmbeddings and 'BAAI/bge-small-zh-v1.5' model
### Modified
- pyproject.toml: add [project.optional-dependencies] 'examples'


## [0.2.0] - 2025-9-10
### Added
- Agent Engine release 0.2
- Example: Langgraph ReflectionAgent release 0.2
### Fixed
- Agent Engine: call mcp tool fail, call 'ask' tool again and again
- Example Langgraph ReflectionAgent: retry on 'ask', user_input is ask answer


## [0.1.20] - 2025-9-9
### Added
- Example: Langgraph ReflectionAgent add final_result_agent 


## [0.1.19] - 2025-9-8
### Added
- Example: Langgraph ReflectionAgent release V1, full logic but no final result agent and tool select agent


# Release Changelog
## [0.1.18] - 2025-9-3
### Added
- Support Agent tools


## [0.1.17] - 2025-9-1
### Target
- Saved for XGATaskEngine base version
### Changed
- Delete StreamTaskResponser tool_exec_on_stream model code


## [0.1.15] - 2025-9-1
### Target
- Saved for StreamResponser tool_exec_on_stream mode, next release will be abolished
### Changed
- Refact TaskResponseProcessor, XGATaskEngine
### Fixed
- Fix finish_reason judge logic


## [0.1.14] - 2025-8-31
### Target
- First complete version is merged 
### Changed
- StreamTaskResponser first version

## [0.1.10] - 2025-8-28
### Target
- NonStream mode release is completed
### Changed
- StreamTaskResponser is original
- NonStreamTaskResponser first version is completed 
- Langfuse use 2.x, match for LiteLLM package

## [0.1.7] - 2025-8-25
### Target
- Langfuse use 3.x package