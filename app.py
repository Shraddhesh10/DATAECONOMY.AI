import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import streamlit as st
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Import custom modules
from agents import create_all_agents
from workflow import run_workflow
from utils.logger import setup_logger, log_agent_action

# Page configuration
st.set_page_config(
    page_title="Multi Agent Coding Framework",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize logger
logger = setup_logger()

# Constants
WORKSPACE_DIR = "workspace"


def check_environment() -> tuple[bool, str]:
    """
    Check if the environment is properly configured.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not os.path.exists(".env"):
        return False, "⚠️ .env file not found. Please create it based on env_template.txt"
    
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        return False, "⚠️ OPENAI_API_KEY not set in .env file"
    
    return True, ""


def validate_user_input(user_input: str) -> tuple[bool, str]:
    """
    Validate user input for security and quality.
    
    Args:
        user_input: The user's request text
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Remove leading/trailing whitespace
    cleaned_input = user_input.strip()
    
    # Check if empty
    if not cleaned_input:
        return False, "🔴 **Admin**: Please enter a description of the application you want to build."
    
    # Check minimum length
    if len(cleaned_input) < 10:
        return False, "🔴 **Admin**: Please provide a more detailed description (at least 10 characters)."
    
    # Check maximum length (prevent abuse)
    if len(cleaned_input) > 5000:
        return False, "🔴 **Admin**: Description is too long. Please keep it under 5000 characters."
    
    # Check if it's just repeated characters or gibberish
    if len(set(cleaned_input.replace(" ", ""))) < 5:
        return False, "🔴 **Admin**: Please provide a meaningful description of your application."
    
    # Check for suspicious patterns (basic security)
    suspicious_patterns = ['<script', 'javascript:', 'onerror=', '<iframe']
    for pattern in suspicious_patterns:
        if pattern.lower() in cleaned_input.lower():
            return False, "🔴 **Admin**: Invalid input detected. Please describe your application in plain text."
    
    # Enhanced gibberish detection
    words = cleaned_input.lower().split()
    
    # Check if input has at least 3 words
    if len(words) < 3:
        return False, "🔴 **Admin**: Please provide a more complete description with at least 3 words describing what you want to build."
    
    # Check for gibberish - valid English words typically have vowels
    vowels = set('aeiouAEIOU')
    consonants = set('bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ')
    
    valid_word_count = 0
    for word in words:
        # Remove punctuation for checking
        clean_word = ''.join(c for c in word if c.isalpha())
        if len(clean_word) < 2:
            continue
            
        # Check if word has at least one vowel (basic English word check)
        has_vowel = any(c in vowels for c in clean_word)
        
        # Check if word is not just consonants strung together
        if has_vowel:
            # Check for reasonable vowel/consonant ratio
            vowel_count = sum(1 for c in clean_word if c in vowels)
            consonant_count = sum(1 for c in clean_word if c in consonants)
            
            # Most English words have at least one vowel per 4 consonants
            if consonant_count == 0 or (vowel_count / len(clean_word)) > 0.15:
                valid_word_count += 1
    
    # At least 40% of words should look like real words
    if len(words) > 0 and (valid_word_count / len(words)) < 0.4:
        return False, "🔴 **Admin**: Your input doesn't appear to be a clear description. Please describe your application idea in plain English (e.g., 'Create a calculator app with basic arithmetic operations')."
    
    
    # Check for patterns like "asdf", "qwerty", etc.
    keyboard_patterns = ['asdf', 'qwer', 'zxcv', 'hjkl', 'qaz', 'wsx', 'edc']
    input_lower = cleaned_input.lower()
    pattern_matches = sum(1 for pattern in keyboard_patterns if pattern in input_lower)
    if pattern_matches >= 2:
        return False, "🔴 **Admin**: Your input appears to be random keyboard input. Please provide a real description of your application."
    
    # Check if input consists mainly of random letter sequences
    # Count sequences of 4+ consonants in a row (unlikely in English)
    consonant_sequences = 0
    current_consonants = 0
    for char in cleaned_input.lower():
        if char in consonants:
            current_consonants += 1
            if current_consonants >= 5:
                consonant_sequences += 1
        else:
            current_consonants = 0
    
    if consonant_sequences >= 2:
        return False, "🔴 **Admin**: Your input doesn't look like a meaningful description. Please clearly describe what application you want to build."
    
    # Check for common application-related keywords (at least one should be present)
    # This ensures the user is actually describing a software project
    app_keywords = [
        'app', 'application', 'program', 'software', 'tool', 'system', 'script',
        'create', 'build', 'make', 'develop', 'generate',
        'calculator', 'game', 'website', 'api', 'bot', 'dashboard', 'manager',
        'tracker', 'analyzer', 'converter', 'parser', 'scraper', 'automation',
        'web', 'cli', 'gui', 'interface', 'database', 'server', 'client',
        'function', 'feature', 'user', 'data', 'file', 'text', 'number',
        'list', 'search', 'filter', 'sort', 'display', 'show', 'save', 'load',
        'add', 'delete', 'update', 'edit', 'manage', 'organize', 'process'
    ]
    
    has_app_keyword = any(keyword in cleaned_input.lower() for keyword in app_keywords)
    
    # If no app keywords and mostly invalid words, it's likely gibberish
    if not has_app_keyword and valid_word_count < len(words) * 0.6:
        return False, "🔴 **Admin**: Please provide a clear description of the **software application** you want to build. For example: 'Create a to-do list app' or 'Build a calculator with basic operations'."
    
    return True, ""


def display_test_results():
    """
    Display test execution results from the workflow.
    """
    if 'workflow_result' not in st.session_state:
        st.info("⏳ No workflow has been executed yet. Test results will appear here after running a workflow.")
        return
    
    result = st.session_state['workflow_result']
    test_results = result.get('test_results')
    
    if not test_results:
        st.warning("⚠️ Test results not available. Tests may not have been executed.")
        return
    
    # Overall summary
    status = test_results.get('status', 'unknown')
    total_tests = test_results.get('total_tests', 0)
    total_passed = test_results.get('total_passed', 0)
    total_failed = test_results.get('total_failed', 0)
    total_errors = test_results.get('total_errors', 0)
    
    # Display status banner
    if status == 'passed':
        st.success(f"✅ **All Tests Passed!** ({total_tests}/{total_tests})")
    elif status == 'failed':
        if total_passed > 0:
            st.warning(f"⚠️ **Partial Success**: {total_passed}/{total_tests} tests passed ({total_failed + total_errors} failed)")
        else:
            st.error(f"❌ **All Tests Failed** ({total_tests} tests)")
    elif status == 'no_tests':
        st.warning("⚠️ **No Tests Found** - The QA Engineer may not have generated test files.")
        return
    elif status == 'error':
        st.error(f"❌ **Test Execution Error** - {test_results.get('message', 'Unknown error')}")
        return
    else:
        st.warning(f"⚠️ **Unknown Test Status**: {status}")
    
    # Metrics display
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Tests", total_tests)
    with col2:
        st.metric("Passed", total_passed, delta=None if total_passed == total_tests else f"-{total_tests - total_passed}")
    with col3:
        st.metric("Failed", total_failed, delta=f"-{total_failed}" if total_failed > 0 else None)
    with col4:
        st.metric("Errors", total_errors, delta=f"-{total_errors}" if total_errors > 0 else None)
    
    st.divider()
    
    # Detailed results per file
    test_file_results = test_results.get('test_results', [])
    
    if test_file_results:
        st.subheader("📋 Detailed Test Results")
        
        for idx, file_result in enumerate(test_file_results):
            file_name = file_result.get('file', f'Test File {idx + 1}')
            file_status = file_result.get('status', 'unknown')
            tests_run = file_result.get('tests_run', 0)
            failures = file_result.get('failures', 0)
            errors = file_result.get('errors', 0)
            output = file_result.get('output', '')
            
            # Status icon
            if file_status == 'passed':
                status_icon = "✅"
                status_color = "normal"
            elif file_status == 'failed':
                status_icon = "❌"
                status_color = "normal"
            elif file_status == 'timeout':
                status_icon = "⏱️"
                status_color = "normal"
            else:
                status_icon = "⚠️"
                status_color = "normal"
            
            with st.expander(f"{status_icon} {file_name} - {tests_run} test(s)", expanded=(file_status == 'failed')):
                # Summary
                st.markdown(f"**Status:** {file_status.upper()}")
                st.markdown(f"**Tests Run:** {tests_run}")
                if failures > 0:
                    st.markdown(f"**Failures:** {failures} ❌")
                if errors > 0:
                    st.markdown(f"**Errors:** {errors} ⚠️")
                
                st.divider()
                
                # Output
                st.markdown("**Test Output:**")
                if output:
                    # Clean up the output for better display
                    st.code(output, language='text')
                else:
                    st.info("No output captured.")
    else:
        st.info("No detailed test results available.")



def display_workspace_artifacts():
    """
    Display generated artifacts from the workspace directory.
    """
    # Clean up __pycache__ before displaying artifacts
    cleanup_pycache()
    
    if not os.path.exists(WORKSPACE_DIR):
        st.info("No artifacts generated yet. Run a workflow first.")
        return
    
    # Get all files, excluding __pycache__
    files = [f for f in Path(WORKSPACE_DIR).glob("*") if f.name != "__pycache__"]
    
    if not files:
        st.info("Workspace is empty. Artifacts will appear here after workflow completion.")
        return
    
    st.success(f"✅ Found {len(files)} artifact(s) in workspace")
    
    # Create tabs for different file types
    tabs = st.tabs(["📄 All Files", "🐍 Python Code", "📋 Documentation", "🐳 Deployment", "🧪 Test Results"])
    
    with tabs[0]:
        st.subheader("All Generated Files")
        
        # Add download all as zip button
        try:
            zip_data = create_workspace_zip()
            st.download_button(
                label="📦 Download All Files as ZIP",
                data=zip_data,
                file_name="workspace_files.zip",
                mime="application/zip",
                type="primary",
                use_container_width=True
            )
            st.divider()
        except Exception as e:
            st.error(f"Could not create zip file: {str(e)}")
        
        for file_path in sorted(files):
            if file_path.is_file():
                with st.expander(f"📁 {file_path.name}"):
                    try:
                        content = file_path.read_text(encoding='utf-8')
                        
                        # Determine language for syntax highlighting
                        suffix = file_path.suffix.lower()
                        lang_map = {
                            '.py': 'python',
                            '.md': 'markdown',
                            '.txt': 'text',
                            '.sh': 'bash',
                            '.bat': 'batch',
                            '.yml': 'yaml',
                            '.yaml': 'yaml',
                            '.json': 'json',
                        }
                        language = lang_map.get(suffix, 'text')
                        
                        st.code(content, language=language)
                        
                        # Download button
                        st.download_button(
                            label=f"⬇️ Download {file_path.name}",
                            data=content,
                            file_name=file_path.name,
                            mime="text/plain",
                        )
                    except Exception as e:
                        st.error(f"Could not read file: {str(e)}")
    
    with tabs[1]:
        st.subheader("Python Source Code")
        py_files = [f for f in files if f.suffix == '.py']
        if py_files:
            for py_file in sorted(py_files):
                with st.expander(f"🐍 {py_file.name}", expanded=True):
                    content = py_file.read_text(encoding='utf-8')
                    st.code(content, language='python')
        else:
            st.info("No Python files generated yet.")
    
    with tabs[2]:
        st.subheader("Documentation")
        doc_files = [f for f in files if f.suffix in ['.md', '.txt']]
        if doc_files:
            for doc_file in sorted(doc_files):
                with st.expander(f"📋 {doc_file.name}", expanded=True):
                    content = doc_file.read_text(encoding='utf-8')
                    if doc_file.suffix == '.md':
                        st.markdown(content)
                    else:
                        st.text(content)
        else:
            st.info("No documentation files generated yet.")
    
    with tabs[3]:
        st.subheader("Deployment Files")
        deploy_files = [f for f in files if f.name.lower() in ['dockerfile', 'docker-compose.yml', 'run.sh', 'run.bat']]
        if deploy_files:
            for deploy_file in sorted(deploy_files):
                with st.expander(f"🐳 {deploy_file.name}", expanded=True):
                    content = deploy_file.read_text(encoding='utf-8')
                    if deploy_file.suffix == '.sh':
                        st.code(content, language='bash')
                    elif deploy_file.suffix == '.bat':
                        st.code(content, language='batch')
                    else:
                        st.code(content, language='dockerfile')
        else:
            st.info("No deployment files generated yet.")
    
    with tabs[4]:
        st.subheader("Test Execution Results")
        display_test_results()


def clear_workspace():
    """
    Clear all files from the workspace directory completely.
    """
    import shutil
    
    try:
        if os.path.exists(WORKSPACE_DIR):
            # Remove the entire workspace directory and all its contents
            shutil.rmtree(WORKSPACE_DIR)
            # Recreate the empty workspace directory
            os.makedirs(WORKSPACE_DIR, exist_ok=True)
            st.success("✅ Workspace cleared completely!")
            logger.info("Workspace cleared completely by user")
        else:
            # Create workspace directory if it doesn't exist
            os.makedirs(WORKSPACE_DIR, exist_ok=True)
            st.info("Workspace directory created.")
    except Exception as e:
        st.error(f"❌ Error clearing workspace: {str(e)}")
        logger.error(f"Error clearing workspace: {str(e)}")


def cleanup_pycache():
    """
    Remove __pycache__ folders from the workspace directory.
    """
    if os.path.exists(WORKSPACE_DIR):
        import shutil
        pycache_path = Path(WORKSPACE_DIR) / "__pycache__"
        if pycache_path.exists() and pycache_path.is_dir():
            try:
                shutil.rmtree(pycache_path)
            except Exception:
                pass  # Silently ignore if we can't delete it


def create_workspace_zip():
    """
    Create a zip file containing all workspace files.
    
    Returns:
        bytes: Zip file contents as bytes
    """
    import io
    import zipfile
    
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        workspace_path = Path(WORKSPACE_DIR)
        
        # Add all files from workspace, excluding __pycache__
        for file_path in workspace_path.rglob('*'):
            if file_path.is_file() and '__pycache__' not in str(file_path):
                # Get relative path for the zip file
                arcname = file_path.relative_to(workspace_path)
                zip_file.write(file_path, arcname)
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()


def main():
    """
    Main Streamlit application logic.
    """
    # Clean up __pycache__ folders at startup
    cleanup_pycache()
    
    # Header
    st.title("🤖 AutoGen - Multi Agent Coding Framework")
    st.markdown("""
    Transform your ideas into fully-functional Python applications using a team of 7 specialized AI agents.
    
    **The Team:**
    - 📊 Product Manager - Analyzes requirements
    - 💻 Python Engineer - Writes code
    - 🔍 Code Reviewer - Ensures quality
    - 📝 Tech Writer - Creates documentation
    - 🧪 QA Engineer - Writes tests
    - 🚀 DevOps Engineer - Handles deployment
    - 🎨 UX Designer - Builds UI
    """)
    
    st.divider()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Environment check
        env_valid, env_error = check_environment()
        if not env_valid:
            st.error(env_error)
            st.info("""
            **Setup Instructions:**
            1. Copy `env_template.txt` to `.env`
            2. Add your OpenAI API key
            3. Restart the application
            """)
            st.stop()
        else:
            st.success("✅ Environment configured")
        
        st.divider()
        
        # Workspace management
        st.header("📁 Workspace")
        
        # Count files, excluding __pycache__
        if os.path.exists(WORKSPACE_DIR):
            file_count = len([f for f in Path(WORKSPACE_DIR).glob("*") if f.name != "__pycache__"])
            st.info(f"Files in workspace: {file_count}")
        else:
            st.info("Files in workspace: 0")
        
        # Always show the clear workspace button
        if st.button("🗑️ Clear Workspace", type="secondary"):
            # Clear workspace completely
            clear_workspace()
            # Clear only workflow-related session state (preserves user input)
            if 'workflow_result' in st.session_state:
                del st.session_state['workflow_result']
            if 'workflow_running' in st.session_state:
                del st.session_state['workflow_running']
            st.rerun()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("💡 Describe Your Application")
        
        # Example prompts
        with st.expander("📝 Example Prompts", expanded=False):
            st.markdown("""
            **Simple Calculator:**
            > Create a calculator application that can perform basic arithmetic operations (add, subtract, multiply, divide). Include error handling for division by zero.
            
            """)
        
        # Initialize reset counter for forcing widget refresh
        if 'reset_counter' not in st.session_state:
            st.session_state.reset_counter = 0
        
        # User input (tied to session state for reset functionality)
        # Use reset_counter in key to force widget recreation on reset
        user_request = st.text_area(
            "Describe the application you want to build:",
            height=150,
            placeholder="Example: Create a calculator application that can perform basic arithmetic operations...",
            help="Be specific about features, requirements, and expected behavior.",
            key=f"user_input_text_{st.session_state.reset_counter}"
        )
        
        # Launch button
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
        with col_btn1:
            launch_button = st.button("🚀 Launch Team", type="primary", disabled=not user_request.strip())
        with col_btn2:
            if st.button("🔄 Reset"):
                # Clear workspace completely
                clear_workspace()
                # Increment reset counter to force widget recreation with empty value
                st.session_state.reset_counter += 1
                # Clear all other session state
                keys_to_delete = [key for key in st.session_state.keys() if key != 'reset_counter']
                for key in keys_to_delete:
                    del st.session_state[key]
                # Rerun to refresh the page
                st.rerun()
    
    with col2:
        st.header("📊 Workflow Status")
        
        # Status placeholder
        status_container = st.empty()
        
        if 'workflow_result' in st.session_state:
            result = st.session_state['workflow_result']
            if result['status'] == 'success':
                files_count = result.get('files_extracted', 0)
                
                # Get test results
                test_results = result.get('test_results')
                test_status_emoji = ""
                test_status_text = ""
                
                if test_results:
                    if test_results['status'] == 'passed':
                        test_status_emoji = "✅"
                        test_status_text = f"All {test_results['total_tests']} tests passed"
                    elif test_results['status'] == 'failed':
                        passed_count = test_results.get('total_passed', 0)
                        failed_count = test_results['total_failed'] + test_results['total_errors']
                        
                        if passed_count > 0:
                            test_status_emoji = ""
                            test_status_text = f"✅ {passed_count} passed, ❌ {failed_count} failed"
                        else:
                            test_status_emoji = "❌"
                            test_status_text = f"All {failed_count} tests failed"
                    elif test_results['status'] == 'no_tests':
                        test_status_emoji = "⚠️"
                        test_status_text = "No tests found"
                    else:
                        test_status_emoji = "⚠️"
                        test_status_text = "Test execution error"
                else:
                    test_status_emoji = "⚠️"
                    test_status_text = "Tests not executed"
                
                status_container.success(f"""
                ✅ **Workflow Completed!**
                - Total messages: {result.get('total_messages', 'N/A')}
                - Review iterations: {result.get('review_iterations', 0)}
                - Files extracted: {files_count}
                - Tests: {test_status_emoji} {test_status_text}
                """)
            else:
                status_container.error(f"""
                ❌ **Workflow Failed**
                - Error: {result.get('error', 'Unknown error')}
                """)
        else:
            status_container.info("⏳ Waiting for workflow to start...")
    
    # Execute workflow
    if launch_button and user_request.strip():
        # Validate input at Admin level (before activating agents)
        is_valid, error_msg = validate_user_input(user_request)
        if not is_valid:
            # Display admin validation error
            st.error(error_msg)
            st.warning("⚠️ **Team Not Activated**: The 6-agent team has not been launched due to invalid input.")
            st.info("""
            💡 **How to write a good description:**
            
            ✅ **Good Examples:**
            - "Create a calculator app with add, subtract, multiply, and divide functions"
            - "Build a to-do list manager where users can add, complete, and delete tasks"
            - "Make a weather information tool that fetches weather data for a city"
            
            ❌ **Bad Examples:**
            - Random keyboard input or gibberish
            - Single words or very short phrases
            - Unclear or vague descriptions
            
            **Please provide a clear, meaningful description of your application idea.**
            """)
            logger.warning(f"Admin validation failed for input: {user_request[:50]}")
            return
        
        logger.info(f"User initiated workflow: {user_request[:100]}")
        
        # Progress indicator
        with st.spinner("🔄 Assembling the team and starting workflow..."):
            try:
                # Create agents
                try:
                    agents = create_all_agents()
                except Exception as agent_error:
                    st.error("❌ **Failed to create AI agents**")
                    st.error(f"Error: {str(agent_error)}")
                    
                    # Check for common issues
                    if "api_key" in str(agent_error).lower() or "authentication" in str(agent_error).lower():
                        st.warning("🔑 **API Key Issue**: Please check your OPENAI_API_KEY in the .env file")
                    elif "rate" in str(agent_error).lower() or "quota" in str(agent_error).lower():
                        st.warning("💳 **Rate Limit**: You may have exceeded your API quota. Please check your OpenAI account.")
                    elif "connection" in str(agent_error).lower() or "timeout" in str(agent_error).lower():
                        st.warning("🌐 **Connection Issue**: Please check your internet connection and try again.")
                    
                    st.info("""
                    **Troubleshooting Steps:**
                    1. Verify your API key is correct in the .env file
                    2. Check your OpenAI account has available credits
                    3. Ensure you have a stable internet connection
                    4. Try again in a few moments
                    """)
                    logger.error(f"Agent creation error: {str(agent_error)}", exc_info=True)
                    return
                
                # Create progress display placeholder
                progress_placeholder = st.empty()
                
                # Define agent messages
                agent_messages = {
                    "product_manager": {
                        "analyzing": "📊 Product Manager is analyzing your requirements..."
                    },
                    "python_engineer": {
                        "coding": "💻 Python Engineer is writing your code...",
                        "fixing": "💻 Python Engineer is fixing the code (Iteration {})"
                    },
                    "code_reviewer": {
                        "reviewing": "🔍 Code Reviewer is checking code quality..."
                    },
                    "tech_writer": {
                        "documenting": "📝 Tech Writer is creating comprehensive documentation..."
                    },
                    "qa_engineer": {
                        "testing": "🧪 QA Engineer is writing test cases..."
                    },
                    "devops_engineer": {
                        "deploying": "🚀 DevOps Engineer is setting up deployment..."
                    },
                    "ux_designer": {
                        "designing": "🎨 UX Designer is building the user interface..."
                    },
                    "complete": {
                        "done": "✅ All agents completed their tasks!"
                    }
                }
                
                # Progress callback function
                def update_progress(agent_name: str, action: str, iteration: int = None):
                    """Update the UI with current agent progress"""
                    try:
                        if agent_name in agent_messages and action in agent_messages[agent_name]:
                            message = agent_messages[agent_name][action]
                            # Handle iteration numbers for fixes
                            if iteration is not None and "{}" in message:
                                message = message.format(iteration)
                            progress_placeholder.info(message)
                    except Exception:
                        pass  # Silently ignore any display errors
                
                # Run workflow with progress callback
                try:
                    result = run_workflow(user_request, agents, progress_callback=update_progress)
                except Exception as workflow_error:
                    # Clear progress message on error
                    progress_placeholder.empty()
                    
                    st.error("❌ **Workflow Execution Failed**")
                    st.error(f"Error: {str(workflow_error)}")
                    
                    # Provide helpful error context
                    error_str = str(workflow_error).lower()
                    if "timeout" in error_str:
                        st.warning("⏱️ **Timeout**: The workflow took too long. Try a simpler application or try again.")
                    elif "rate" in error_str or "quota" in error_str:
                        st.warning("💳 **API Rate Limit**: You've reached your API limit. Please wait a moment and try again.")
                    elif "context" in error_str or "token" in error_str:
                        st.warning("📝 **Request Too Complex**: Try breaking your request into a simpler application.")
                    elif "connection" in error_str or "network" in error_str:
                        st.warning("🌐 **Network Error**: Connection issue detected. Please check your internet and try again.")
                    
                    st.info("""
                    **What to try:**
                    - Simplify your request (try a smaller application)
                    - Wait a few minutes and try again
                    - Check your OpenAI API quota and limits
                    - Ensure stable internet connection
                    """)
                    logger.error(f"Workflow execution error: {str(workflow_error)}", exc_info=True)
                    return
                
                # Clear the progress message
                progress_placeholder.empty()
                
                # Store result in session state
                st.session_state['workflow_result'] = result
                
                if result['status'] == 'success':
                    # Check if any files were generated
                    files_count = result.get('files_extracted', 0)
                    if files_count == 0:
                        st.warning("⚠️ **Workflow completed but no files were generated**")
                        st.info("""
                        This might happen if:
                        - The agents didn't follow the expected format
                        - The request was unclear or too vague
                        
                        **Try:**
                        - Providing a more specific and detailed description
                        - Describing a concrete application with clear features
                        """)
                        logger.warning("Workflow completed but no files extracted")
                    else:
                        st.success("✅ Workflow completed successfully!")
                        st.balloons()
                else:
                    # Workflow returned error status
                    error_detail = result.get('error', 'Unknown error occurred')
                    st.error(f"❌ **Workflow Failed**: {error_detail}")
                    
                    # Provide context-specific help
                    if "max" in error_detail.lower() and "round" in error_detail.lower():
                        st.warning("🔄 **Too Many Iterations**: The agents couldn't agree on a solution.")
                        st.info("Try simplifying your request or describing a different application.")
                    else:
                        st.info("""
                        **Troubleshooting:**
                        - Try rephrasing your request more clearly
                        - Break down complex applications into simpler ones
                        - Check that your request describes a feasible Python application
                        """)
                    
                    logger.error(f"Workflow returned error: {error_detail}")
                
                # Rerun to update UI
                st.rerun()
                
            except KeyboardInterrupt:
                st.warning("⚠️ **Workflow Interrupted**: Process was stopped by user.")
                logger.info("Workflow interrupted by user")
                
            except Exception as e:
                # Catch-all for unexpected errors
                st.error("❌ **Unexpected System Error**")
                st.error(f"Details: {str(e)}")
                
                st.info("""
                **An unexpected error occurred. Please try:**
                1. Refreshing the page
                2. Checking your .env configuration
                3. Trying a different/simpler request
                4. Restarting the application
                """)
                
                # Provide error type context
                error_type = type(e).__name__
                st.caption(f"Error Type: {error_type}")
                
                logger.error(f"Unexpected application error ({error_type}): {str(e)}", exc_info=True)
    
    # Display artifacts
    st.divider()
    st.header("📦 Generated Artifacts")
    display_workspace_artifacts()


if __name__ == "__main__":
    main()

