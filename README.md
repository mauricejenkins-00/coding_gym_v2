# Coding Gym App

A simple and elegant Streamlit application for generating random Python programming problems. Track your progress as you work through problems ranging from easy to hard difficulty levels.

Access the app globally @: https://codinggymv2-qouzappjqvftlxpdpdj59bb.streamlit.app/

## Features

- User accounts with secure login and signup
- User-specific progress tracking and metrics
- Generate random programming problems by difficulty (easy, medium, hard, or random)
- Avanade-branded experience with app title and logo support
- **Problem Breakdown**: Expandable section with step-by-step guidance
- **Hints System**: Collapsible hints to help with problem-solving
- Code submission input for Python solutions
- Automatic evaluation for correctness and efficiency using optional LLM support
- Built-in completion tracker
- Progress visualization with completion percentage
- Persistent progress storage using SQLite
- List of completed problems

## Code Submission

Users can submit code directly in the app for the current problem. The app performs syntax and runtime checks locally, and if `OPENAI_API_KEY` is set, it uses an LLM to review correctness and efficiency.

## Branding

Place the Avanade logo in `assets/avanade-logo.png` to display it in the app header. If the logo file is missing, the app still shows the "Avanade Coding Gym" title.

## Installation

1. Clone or download the repository.
2. (Optional) Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate
   ```
3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

### OpenAI API Setup

The app supports multiple ways to configure the OpenAI API key:

1. **Local Development (`.env` file)**:
   - Create a `.env` file in the project root
   - Add: `OPENAI_API_KEY=sk-proj-your-key-here`
   - The app automatically loads this via `python-dotenv`

2. **Streamlit Cloud Deployment**:
   - Go to your app's settings in Streamlit Cloud dashboard
   - Navigate to **Secrets** section
   - Add: `OPENAI_API_KEY = "sk-proj-your-key-here"`
   - The app automatically detects and uses Streamlit secrets

3. **Environment Variables**:
   - Set `OPENAI_API_KEY` as a system environment variable
   - Useful for Docker, Heroku, AWS, Azure, and other platforms
   - Command: `export OPENAI_API_KEY="sk-proj-your-key-here"` (Linux/macOS)
   - Command: `set OPENAI_API_KEY="sk-proj-your-key-here"` (Windows)

### Security Notes
- The `.env` file is excluded from version control (see `.gitignore`)
- Never commit sensitive API keys to git repositories
- Rotate keys periodically and monitor usage in the OpenAI dashboard
- Set budget alerts and rate limits in your OpenAI account

## Usage

Run the application:

```bash
python -m streamlit run app.py
```

Open your browser to the provided URL (usually http://localhost:8501) and start generating problems!

## Viewing SQLite Data

The app stores user accounts and progress in a `progress.db` SQLite database. You can view the data using any of these methods:

### Method 1: In-App Debug Dashboard (Easiest)
1. Run the app: `python -m streamlit run app.py`
2. Scroll to the bottom of the page
3. Click on **"Debug - Database Viewer"** to expand it
4. View:
   - **Users Table**: All registered usernames and signup timestamps
   - **Progress Table**: Problem attempts and completion status per user
   - **Statistics**: Overall app metrics (total users, completions, attempts)
   - **Raw SQL Query**: Write custom SQL queries to explore the database

### Method 2: Command Line (SQLite CLI)
Open a terminal in the project directory and run:

```powershell
# View all users
sqlite3 progress.db "SELECT * FROM users;"

# View all progress records
sqlite3 progress.db "SELECT * FROM progress;"

# View progress with usernames (joined query)
sqlite3 progress.db "SELECT u.username, p.problem_id, p.status FROM users u JOIN progress p ON u.id = p.user_id;"

# View completion statistics
sqlite3 progress.db "SELECT u.username, COUNT(*) as completed FROM users u JOIN progress p ON u.id = p.user_id WHERE p.status = 'completed' GROUP BY u.id;"
```

### Method 3: GUI Tool - DB Browser for SQLite
1. Download [DB Browser for SQLite](https://sqlitebrowser.org/dl/)
2. Open the application
3. File → Open → Navigate to `progress.db`
4. Browse tables visually or write SQL queries in the "Execute SQL" tab

### Method 4: Python Script
Create a file named `view_db.py`:

```python
import sqlite3

conn = sqlite3.connect('progress.db')
c = conn.cursor()

# View all users
print("=== USERS ===")
c.execute("SELECT id, username, created_at FROM users;")
for row in c.fetchall():
    print(row)

# View all progress
print("\n=== PROGRESS ===")
c.execute("SELECT u.username, p.problem_id, p.status FROM users u JOIN progress p ON u.id = p.user_id;")
for row in c.fetchall():
    print(row)

# View completion stats
print("\n=== STATISTICS ===")
c.execute("SELECT u.username, COUNT(*) as total_completed FROM users u JOIN progress p ON u.id = p.user_id WHERE p.status = 'complete' GROUP BY u.id;")
for row in c.fetchall():
    print(f"{row[0]}: {row[1]} problems completed")

conn.close()
```

Run with: `python view_db.py`

### Database Schema

**Users Table:**
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
```

**Progress Table:**
```sql
CREATE TABLE progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    problem_id INTEGER NOT NULL,
    status TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, problem_id),
    FOREIGN KEY(user_id) REFERENCES users(id)
)
```

Progress statuses: `attempted`, `completed`

## Project Structure

- `app.py`: Main Streamlit application
- `problems.json`: JSON file containing the programming problems
- `progress.db`: SQLite database for tracking progress (created automatically)
- `requirements.txt`: Python dependencies

## Contributing

Feel free to add more problems to `problems.json` or improve the UI.
