# Coding Gym App

A simple and elegant Streamlit application for generating random Python programming problems. Track your progress as you work through problems ranging from easy to hard difficulty levels.

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

## Usage

The app loads the OpenAI API key from a `.env` file in the project root. The `.env` file is included for convenience but should be secured in production.

Run the application:

```bash
python -m streamlit run app.py
```

Open your browser to the provided URL (usually http://localhost:8501) and start generating problems!

## Project Structure

- `app.py`: Main Streamlit application
- `problems.json`: JSON file containing the programming problems
- `progress.db`: SQLite database for tracking progress (created automatically)
- `requirements.txt`: Python dependencies

## Contributing

Feel free to add more problems to `problems.json` or improve the UI.