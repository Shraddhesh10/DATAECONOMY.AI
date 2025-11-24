# Multi-Agent Coding Framework

A Streamlit application powered by AutoGen for multi-agent AI coding collaboration.


### Quick Start Guide For Windows

#### Step 1: Open Command Prompt or PowerShell

- Press `Win + R`, type `cmd` or `powershell`, and press Enter


#### Step 2:  Clone the Multi-Agent Coding Framework repository from GitHub

```bash
git clone https://github.com/Shraddhesh10/DATAECONOMY.AI.git
```

#### Step 3: Navigate to the Project Folder

```bash
cd path\to\DATAECONOMY.AI
```

#### Step 4: Create a Virtual Environment
##### Ensure Python 3.10 is installed on your system.
```bash
py -3.10 -m venv venv
```

#### Step 5: Activate the Virtual Environment

**For Command Prompt:**
```bash
venv\Scripts\activate
```

**For PowerShell:**
```bash
venv\Scripts\Activate.ps1
```

#### Step 6: Install Dependencies

```bash
pip install -r requirements.txt
```

#### Step 7: Create .env File

1. Create a new file named `.env` in the project root folder
2. Add the following content:
You will need your own OpenAI API Key (get one at https://platform.openai.com/api-keys) 

```env
OPENAI_API_KEY= your-api-key-here
OPENAI_MODEL= gpt-4o
```

3. Replace `your-api-key-here` with your actual OpenAI API key

#### Step 8: Run the Application

```bash
streamlit run app.py
```

The application will automatically open in your browser at http://localhost:8501

---

### For Mac

#### Step 1: Open Terminal

- Press `Cmd + Space`, type `Terminal`, and press Enter


#### Step 2:  Clone the Multi-Agent Coding Framework repository from GitHub

```bash
git clone https://github.com/Shraddhesh10/DATAECONOMY.AI.git
```
#### Step 3: Navigate to the Project Folder

```bash
cd path/to/DATAECONOMY.AI
```

#### Step 4: Create a Virtual Environment
##### Ensure Python 3.10 is installed on your system 

```bash
python3.10 -m venv venv
```

#### Step 5: Activate the Virtual Environment

```bash
source venv/bin/activate
```

#### Step 6: Install Dependencies

```bash
pip install -r requirements.txt
```

#### Step 7: Create .env File

1. Create a new file named `.env` in the project root folder:

```bash
touch .env
```

2. Open the file in a text editor and add:

```env
OPENAI_API_KEY= your-api-key-here
OPENAI_MODEL= gpt-4o
```

3. Replace `your-api-key-here` with your actual OpenAI API key

#### Step 8: Run the Application

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
