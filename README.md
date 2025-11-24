# Multi-Agent Coding Framework

A Streamlit application powered by AutoGen for multi-agent AI coding collaboration.

## Prerequisites

Before you begin, make sure you have:

1. Python 3.10+ installed on your system
2. OpenAI API Key (get one at https://platform.openai.com/api-keys)

## Quick Start Guide

### For Windows

#### Step 1: Open Command Prompt or PowerShell

- Press `Win + R`, type `cmd` or `powershell`, and press Enter

#### Step 2: Navigate to the Project Folder

```bash
cd path\to\DATAECONOMY.AI
```

#### Step 3: Create a Virtual Environment

```bash
python -m venv venv
```

#### Step 4: Activate the Virtual Environment

**For Command Prompt:**
```bash
venv\Scripts\activate
```

**For PowerShell:**
```bash
venv\Scripts\Activate.ps1
```

#### Step 5: Install Dependencies

```bash
pip install -r requirements.txt
```

#### Step 6: Create .env File

1. Create a new file named `.env` in the project root folder
2. Add the following content:

```env
OPENAI_API_KEY=sk-your-actual-api-key-here
OPENAI_MODEL=gpt-4o
```

3. Replace `sk-your-actual-api-key-here` with your actual OpenAI API key

#### Step 7: Run the Application

```bash
streamlit run app.py
```

The application will automatically open in your browser at http://localhost:8501

---

### For Mac

#### Step 1: Open Terminal

- Press `Cmd + Space`, type `Terminal`, and press Enter

#### Step 2: Navigate to the Project Folder

```bash
cd path/to/DATAECONOMY.AI
```

#### Step 3: Create a Virtual Environment

```bash
python3 -m venv venv
```

#### Step 4: Activate the Virtual Environment

```bash
source venv/bin/activate
```

#### Step 5: Install Dependencies

```bash
pip install -r requirements.txt
```

#### Step 6: Create .env File

1. Create a new file named `.env` in the project root folder:

```bash
touch .env
```

2. Open the file in a text editor and add:

```env
OPENAI_API_KEY=sk-your-actual-api-key-here
OPENAI_MODEL=gpt-4o
```

3. Replace `sk-your-actual-api-key-here` with your actual OpenAI API key

#### Step 7: Run the Application

```bash
streamlit run app.py
```

Or use the provided start script:

```bash
chmod +x start.sh
./start.sh
```

The application will automatically open in your browser at http://localhost:8501

---

## Stopping the Application

To stop the application, press `Ctrl + C` in the terminal/command prompt where it's running.

---

## Troubleshooting

### Python Not Found (Windows)

- Make sure Python is installed and added to PATH
- Try using `py` instead of `python`

### Python Not Found (Mac)

- Make sure Python 3 is installed
- Try using `python3` instead of `python`

### Permission Denied (Mac)

- If you get permission errors, try:

```bash
chmod +x start.sh
```

### OpenAI API Key Issues

- Make sure your `.env` file is in the project root folder
- Verify your API key is correct (starts with `sk-`)
- Check that you have credits available in your OpenAI account

---

## Project Structure

```
DATAECONOMY.AI/
├── app.py              # Main Streamlit application
├── agents.py           # Agent configurations
├── workflow.py         # Workflow logic
├── requirements.txt    # Python dependencies
├── .env               # Environment variables (you create this)
├── start.sh           # Mac/Linux start script
└── utils/             # Utility modules
```

---

## Features

### 7 Specialized AI Agents

- 📊 **Product Manager** - Analyzes requirements and creates detailed specifications
- 💻 **Python Engineer** - Writes production-quality Python code
- 🔍 **Code Reviewer** - Ensures code quality and best practices
- 📝 **Tech Writer** - Creates comprehensive documentation
- 🧪 **QA Engineer** - Writes comprehensive test cases
- 🚀 **DevOps Engineer** - Handles deployment configurations
- 🎨 **UX Designer** - Builds beautiful Streamlit user interfaces

### Automated Workflow

1. Describe your application idea
2. The team of AI agents collaborates to build it
3. Get complete, tested, and documented code
4. Download all files or deploy immediately

---

## Usage

1. Launch the application using `streamlit run app.py`
2. Enter a description of the application you want to build in the text area
3. Click "🚀 Launch Team" to start the multi-agent workflow
4. Watch as each agent completes their tasks
5. Review and download the generated files from the workspace

### Example Prompts

- "Create a calculator application that can perform basic arithmetic operations (add, subtract, multiply, divide). Include error handling for division by zero."
- "Build a task manager CLI where users can add, complete, and delete tasks saved to a JSON file."
- "Create a weather information fetcher using an API to display temperature and conditions."

---

## Generated Artifacts

After the workflow completes, you'll find the following files in the `workspace/` directory:

- `main.py` - Main application code
- `test_main.py` - Unit tests
- `requirements.md` - Software requirements document
- `README.md` - Application documentation
- `app_ui.py` - Streamlit user interface
- `Dockerfile` - Docker configuration
- `run.sh` - Execution script

---

## License

This project is provided as-is for educational and development purposes.

---

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify your environment setup
3. Ensure your OpenAI API key is valid and has credits

---

**Built with AutoGen** - Multi-Agent AI Framework
