

from typing import Dict, Any, Optional, List
from autogen import GroupChat, GroupChatManager, Agent
from utils.logger import setup_logger, log_agent_action, log_error_with_context

# Initialize logger
logger = setup_logger()


class WorkflowOrchestrator:
    """
    Manages the workflow and state transitions between agents.
    Implements a custom speaker selection function for the review loop.
    """
    
    def __init__(self, agents: Dict[str, Any], max_review_iterations: int = 5, progress_callback=None):
        """
        Initialize the workflow orchestrator.
        
        Args:
            agents: Dictionary of all agent instances
            max_review_iterations: Maximum iterations for Engineer-Reviewer loop
            progress_callback: Optional callback function to update UI progress
        """
        self.agents = agents
        self.max_review_iterations = max_review_iterations
        self.review_iteration_count = 0
        self.progress_callback = progress_callback
        
        logger.info("WorkflowOrchestrator initialized")
        log_agent_action(
            logger,
            "System",
            "Configuration",
            f"Max review iterations: {max_review_iterations}"
        )
    
    def custom_speaker_selector(
        self,
        last_speaker: Agent,
        groupchat: GroupChat
    ) -> Optional[Agent]:
        """
        Custom speaker selection function implementing the state transition graph.
        
        State Flow:
        1. Admin_Proxy (start) -> Product_Manager
        2. Product_Manager -> Python_Engineer
        3. Python_Engineer -> Code_Reviewer
        4. Code_Reviewer -> Python_Engineer (if FIX_REQUIRED) OR Tech_Writer (if APPROVED)
        5. Tech_Writer -> QA_Engineer
        6. QA_Engineer -> DevOps_Engineer
        7. DevOps_Engineer -> UX_Designer
        8. UX_Designer -> End (workflow complete)
        
        Note: Admin_Proxy behavior depends on whether UX_Designer has already spoken.
              Before UX_Designer: Admin_Proxy starts the workflow
              After UX_Designer: Admin_Proxy would end the workflow (but UX_Designer already ends it)
        
        Args:
            last_speaker: The agent who spoke last
            groupchat: The GroupChat instance
            
        Returns:
            Next agent to speak, or None to end conversation
        """
        messages = groupchat.messages
        last_message = messages[-1]["content"] if messages else ""
        
        last_speaker_name = last_speaker.name
        
        logger.debug(f"Speaker selection: Last speaker = {last_speaker_name}")
        
        # Check if UX_Designer has already spoken (workflow completion indicator)
        ux_designer_has_spoken = any(
            msg.get("name") == "UX_Designer" for msg in messages
        )
        
        # State 1: Admin -> Product_Manager (only at the start, before UX_Designer speaks)
        if last_speaker_name == "Admin_Proxy" and not ux_designer_has_spoken:
            next_agent = self.agents["product_manager"]
            log_agent_action(logger, "Workflow", "Transition", "Admin -> Product_Manager (workflow start)")
            if self.progress_callback:
                self.progress_callback("product_manager", "analyzing")
            return next_agent
        
        # State 9: Admin_Proxy after UX_Designer -> End workflow
        elif last_speaker_name == "Admin_Proxy" and ux_designer_has_spoken:
            log_agent_action(logger, "Workflow", "Completion", "Admin_Proxy after UX_Designer - workflow complete")
            return None  # End conversation
        
        # State 2: Product_Manager -> Python_Engineer
        elif last_speaker_name == "Product_Manager":
            next_agent = self.agents["python_engineer"]
            log_agent_action(logger, "Workflow", "Transition", "Product_Manager -> Python_Engineer")
            self.review_iteration_count = 0  # Reset counter for new workflow
            if self.progress_callback:
                self.progress_callback("python_engineer", "coding")
            return next_agent
        
        # State 3: Python_Engineer -> Code_Reviewer
        elif last_speaker_name == "Python_Engineer":
            next_agent = self.agents["code_reviewer"]
            log_agent_action(logger, "Workflow", "Transition", "Python_Engineer -> Code_Reviewer")
            if self.progress_callback:
                self.progress_callback("code_reviewer", "reviewing")
            return next_agent
        
        # State 4: Decision Point - Code_Reviewer
        elif last_speaker_name == "Code_Reviewer":
            # Check for approval or rejection keywords
            if "FIX_REQUIRED" in last_message:
                self.review_iteration_count += 1
                
                # Check if max iterations reached
                if self.review_iteration_count >= self.max_review_iterations:
                    logger.warning(
                        f"Max review iterations ({self.max_review_iterations}) reached. "
                        "Forcing approval to prevent infinite loop."
                    )
                    next_agent = self.agents["tech_writer"]
                    log_agent_action(
                        logger,
                        "Workflow",
                        "Forced Transition",
                        "Code_Reviewer -> Tech_Writer (max iterations)"
                    )
                else:
                    next_agent = self.agents["python_engineer"]
                    log_agent_action(
                        logger,
                        "Workflow",
                        f"Review Loop {self.review_iteration_count}",
                        "Code_Reviewer -> Python_Engineer (fixes required)"
                    )
                    if self.progress_callback:
                        self.progress_callback("python_engineer", "fixing", self.review_iteration_count)
                return next_agent
            
            elif "APPROVED" in last_message:
                next_agent = self.agents["tech_writer"]
                log_agent_action(
                    logger,
                    "Workflow",
                    "Transition",
                    f"Code_Reviewer -> Tech_Writer (approved after {self.review_iteration_count} iterations)"
                )
                if self.progress_callback:
                    self.progress_callback("tech_writer", "documenting")
                return next_agent
            
            else:
                # Code_Reviewer didn't use required keywords
                logger.warning(
                    "Code_Reviewer response missing required keywords (FIX_REQUIRED/APPROVED). "
                    "Defaulting to approval."
                )
                next_agent = self.agents["tech_writer"]
                return next_agent
        
        # State 5: Tech_Writer -> QA_Engineer
        elif last_speaker_name == "Tech_Writer":
            next_agent = self.agents["qa_engineer"]
            log_agent_action(logger, "Workflow", "Transition", "Tech_Writer -> QA_Engineer")
            if self.progress_callback:
                self.progress_callback("qa_engineer", "testing")
            return next_agent
        
        # State 6: QA_Engineer -> DevOps_Engineer
        elif last_speaker_name == "QA_Engineer":
            next_agent = self.agents["devops_engineer"]
            log_agent_action(logger, "Workflow", "Transition", "QA_Engineer -> DevOps_Engineer")
            if self.progress_callback:
                self.progress_callback("devops_engineer", "deploying")
            return next_agent
        
        # State 7: DevOps_Engineer -> UX_Designer
        elif last_speaker_name == "DevOps_Engineer":
            next_agent = self.agents["ux_designer"]
            log_agent_action(logger, "Workflow", "Transition", "DevOps_Engineer -> UX_Designer")
            if self.progress_callback:
                self.progress_callback("ux_designer", "designing")
            return next_agent
        
        # State 8: UX_Designer -> End workflow (workflow is complete)
        elif last_speaker_name == "UX_Designer":
            log_agent_action(logger, "Workflow", "Completion", "UX_Designer finished - workflow complete")
            if self.progress_callback:
                self.progress_callback("complete", "done")
            return None  # End conversation
        
        # Unknown state - should not happen
        else:
            logger.error(f"Unknown speaker in workflow: {last_speaker_name}")
            return None
    
    def create_group_chat(self) -> GroupChat:
        """
        Create and configure the GroupChat with all agents.
        
        Returns:
            Configured GroupChat instance
        """
        agents_list = [
            self.agents["admin_proxy"],
            self.agents["product_manager"],
            self.agents["python_engineer"],
            self.agents["code_reviewer"],
            self.agents["tech_writer"],
            self.agents["qa_engineer"],
            self.agents["devops_engineer"],
            self.agents["ux_designer"],
        ]
        
        groupchat = GroupChat(
            agents=agents_list,
            messages=[],
            max_round=50,  # Maximum total rounds to prevent runaway execution
            speaker_selection_method=self.custom_speaker_selector,
        )
        
        logger.info(f"GroupChat created with {len(agents_list)} agents")
        return groupchat
    
    def create_manager(self, groupchat: GroupChat, llm_config: Dict[str, Any]) -> GroupChatManager:
        """
        Create the GroupChatManager to orchestrate the conversation.
        
        Args:
            groupchat: Configured GroupChat instance
            llm_config: LLM configuration dictionary
            
        Returns:
            GroupChatManager instance
        """
        manager = GroupChatManager(
            groupchat=groupchat,
            llm_config=llm_config,
        )
        
        logger.info("GroupChatManager created")
        return manager
    
    def initiate_workflow(self, user_request: str) -> Dict[str, Any]:
        """
        Start the multi-agent workflow with a user request.
        
        Args:
            user_request: Natural language description of desired software
            
        Returns:
            Dictionary containing workflow results and metadata
        """
        try:
            # Validate input
            if not user_request or not user_request.strip():
                logger.error("Empty user request received")
                return {
                    "status": "error",
                    "error": "User request cannot be empty",
                    "review_iterations": 0,
                }
            
            logger.info("=" * 80)
            logger.info("WORKFLOW INITIATED")
            logger.info("=" * 80)
            log_agent_action(logger, "User", "Request", user_request[:100])
            
            # Get LLM config from first agent
            from agents import get_llm_config
            llm_config = get_llm_config()
            
            # Create group chat and manager
            groupchat = self.create_group_chat()
            manager = self.create_manager(groupchat, llm_config)
            
            # Start the conversation
            logger.info("Starting agent conversation...")
            
            self.agents["admin_proxy"].initiate_chat(
                manager,
                message=user_request,
            )
            
            logger.info("=" * 80)
            logger.info("WORKFLOW COMPLETED - Extracting generated files...")
            logger.info("=" * 80)
            
            # Extract and save files from agent messages using marker format
            import re
            import os
            
            workspace_path = os.path.abspath("workspace")
            os.makedirs(workspace_path, exist_ok=True)
            
            files_extracted = 0
            for msg in groupchat.messages:
                content = msg.get("content", "")
                agent_name = msg.get("name", "unknown")
                
                # Extract files using ===BEGIN_FILE:filename=== and ===END_FILE=== markers
                file_pattern = r'===BEGIN_FILE:([^\s]+)===\s*\n(.*?)\n===END_FILE==='
                matches = re.findall(file_pattern, content, re.DOTALL)
                
                for filename, file_content in matches:
                    try:
                        # Clean up the filename
                        filename = filename.strip()
                        
                        # Clean up content (remove leading/trailing whitespace but preserve code indentation)
                        file_content = file_content.strip()
                        
                        # Save the file
                        filepath = os.path.join(workspace_path, filename)
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(file_content)
                        
                        logger.info(f"[{agent_name}] Extracted file: {filename} ({len(file_content)} chars)")
                        files_extracted += 1
                    except Exception as e:
                        logger.warning(f"[{agent_name}] Failed to extract {filename}: {str(e)}")
            
            logger.info(f"Extracted {files_extracted} files to workspace (no code execution)")
            
            # If no files were extracted, log the code blocks for debugging
            if files_extracted == 0:
                logger.warning("No files were extracted from agent responses!")
                logger.warning("Check if agents are following the expected code generation format.")
                logger.debug(f"Total messages: {len(groupchat.messages)}")
                for i, msg in enumerate(groupchat.messages):
                    if '```python' in msg.get("content", ""):
                        logger.debug(f"Message {i} from {msg.get('name', 'unknown')} contains Python code")
            
            # Execute tests if test files were generated
            test_results = None
            try:
                from utils.test_executor import run_tests_in_workspace
                logger.info("=" * 80)
                logger.info("EXECUTING TESTS")
                logger.info("=" * 80)
                test_results = run_tests_in_workspace(workspace_path)
                logger.info(f"Test execution completed: {test_results.get('status')}")
                logger.info(f"Total tests: {test_results.get('total_tests', 0)}, "
                           f"Passed: {test_results.get('total_passed', 0)}, "
                           f"Failed: {test_results.get('total_failed', 0)}, "
                           f"Errors: {test_results.get('total_errors', 0)}")
            except Exception as e:
                logger.warning(f"Test execution failed: {str(e)}")
                test_results = {
                    'status': 'error',
                    'message': f'Failed to execute tests: {str(e)}',
                    'total_tests': 0,
                    'total_passed': 0,
                    'total_failed': 0,
                    'total_errors': 0,
                    'test_results': []
                }
            
            return {
                "status": "success",
                "total_messages": len(groupchat.messages),
                "review_iterations": self.review_iteration_count,
                "files_extracted": files_extracted,
                "messages": groupchat.messages,
                "test_results": test_results,
            }
            
        except KeyboardInterrupt:
            logger.warning("Workflow interrupted by user")
            return {
                "status": "error",
                "error": "Workflow was interrupted by user",
                "review_iterations": self.review_iteration_count,
            }
        except TimeoutError as e:
            log_error_with_context(logger, e, "Workflow timeout")
            return {
                "status": "error",
                "error": f"Workflow timed out: {str(e)}",
                "review_iterations": self.review_iteration_count,
            }
        except ValueError as e:
            log_error_with_context(logger, e, "Invalid configuration")
            return {
                "status": "error",
                "error": f"Configuration error: {str(e)}",
                "review_iterations": self.review_iteration_count,
            }
        except ConnectionError as e:
            log_error_with_context(logger, e, "Network connection failed")
            return {
                "status": "error",
                "error": f"Connection error: {str(e)}. Please check your internet connection.",
                "review_iterations": self.review_iteration_count,
            }
        except Exception as e:
            log_error_with_context(logger, e, "Workflow execution failed")
            error_type = type(e).__name__
            return {
                "status": "error",
                "error": f"{error_type}: {str(e)}",
                "review_iterations": self.review_iteration_count,
            }


def run_workflow(user_request: str, agents: Dict[str, Any], progress_callback=None) -> Dict[str, Any]:
    """
    Convenience function to run the complete workflow.
    
    Args:
        user_request: User's natural language request
        agents: Dictionary of agent instances
        progress_callback: Optional callback function for UI progress updates
        
    Returns:
        Workflow results dictionary
    """
    orchestrator = WorkflowOrchestrator(agents, max_review_iterations=5, progress_callback=progress_callback)
    return orchestrator.initiate_workflow(user_request)


