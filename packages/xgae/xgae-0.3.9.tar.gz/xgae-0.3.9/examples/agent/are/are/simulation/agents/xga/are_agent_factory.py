from are.simulation.agents.are_simulation_agent_config import ARESimulationReactBaseAgentConfig
from are.simulation.agents.default_agent.steps.are_simulation import get_are_simulation_update_pre_step
from are.simulation.agents.default_agent.termination_methods.are_simulation import get_gaia2_termination_step
from are.simulation.agents.default_agent.tools.json_action_executor import JsonActionExecutor
from are.simulation.agents.llm.llm_engine import LLMEngine

from are.simulation.agents.xga.are_agent import XGAAreAgent


def xga_simulation_react_xml_agent(
    llm_engine: LLMEngine, base_agent_config: ARESimulationReactBaseAgentConfig
):
    return XGAAreAgent(
        llm_engine=llm_engine,
        tools={},
        system_prompts={
            "system_prompt": str(base_agent_config.system_prompt),
        },
        termination_step=get_gaia2_termination_step(),
        max_iterations=base_agent_config.max_iterations,
        action_executor=JsonActionExecutor(  # Just for compatible BaseAgent， useless
            use_custom_logger=base_agent_config.use_custom_logger
        ),
        conditional_pre_steps=[get_are_simulation_update_pre_step()],
        use_custom_logger=base_agent_config.use_custom_logger,
    )
