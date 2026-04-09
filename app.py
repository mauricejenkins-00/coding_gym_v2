import os
import time
import streamlit as st
import json
import sqlite3
import random
import hashlib
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Load problems
with open('problems.json', 'r') as f:
    problems = json.load(f)

# Utility functions

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def get_db_connection():
    return sqlite3.connect('progress.db', check_same_thread=False)


# Initialize OpenAI client
# Check environment variable first (for local .env and system env vars)
openai_api_key = os.environ.get('OPENAI_API_KEY')

# Check Streamlit secrets if not in environment (for Streamlit Cloud deployment)
if not openai_api_key and hasattr(st, 'secrets') and 'OPENAI_API_KEY' in st.secrets:
    openai_api_key = st.secrets['OPENAI_API_KEY']

openai_client = None

if OPENAI_AVAILABLE and openai_api_key:
    try:
        openai_client = OpenAI(api_key=openai_api_key)
    except Exception as e:
        print(f"Error initializing OpenAI client: {e}")
        openai_client = None


def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        problem_id INTEGER NOT NULL,
        status TEXT,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, problem_id),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    conn.commit()
    conn.close()


def safe_exec_user_code(code: str):
    try:
        compiled = compile(code, '<user_code>', 'exec')
    except Exception as exc:
        return {'syntax_error': str(exc)}

    safe_builtins = {
        'range': range,
        'len': len,
        'print': print,
        'str': str,
        'int': int,
        'float': float,
        'list': list,
        'dict': dict,
        'set': set,
        'tuple': tuple,
        'enumerate': enumerate,
        'sum': sum,
        'min': min,
        'max': max,
        'abs': abs,
        'sorted': sorted,
        'all': all,
        'any': any,
        'zip': zip,
        'map': map,
        'filter': filter,
        'sorted': sorted,
    }

    global_vars = {'__builtins__': safe_builtins}
    local_vars = {}
    try:
        exec(compiled, global_vars, local_vars)
    except Exception as exc:
        return {'runtime_error': str(exc), 'namespace': local_vars}

    return {'namespace': local_vars}


def evaluate_efficiency(code: str, elapsed: float) -> str:
    if elapsed < 0.05 and len(code) < 600:
        return 'Excellent'
    if elapsed < 0.2 and len(code) < 1000:
        return 'Good'
    return 'Needs improvement'


def llm_review_code(problem_text: str, code: str) -> dict | None:
    if openai_client is None:
        print("OpenAI client is None")
        return None

    try:
        prompt = (
            'You are a Python code evaluator. Review the following problem and code, then provide a JSON response with keys ' 
            'correctness, feedback, efficiency_rating, and notes. ' 
            'Do not include any extra text outside the JSON object. '\
            f'Problem: {problem_text}\n\nCode:\n```python\n{code}\n```\n'
            'Evaluate whether the submitted code appears correct for the problem, whether it has obvious efficiency strengths or weaknesses, ' 
            'and provide a short summary. Use values: correctness as "correct" or "incorrect", efficiency_rating as "Excellent", "Good", or "Needs improvement".'
        )

        response = openai_client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[
                {'role': 'system', 'content': 'You are a helpful assistant that evaluates Python code for correctness and efficiency.'},
                {'role': 'user', 'content': prompt},
            ],
            max_tokens=250,
            temperature=0,
        )
        text = response.choices[0].message.content.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                snippet = text[start:end + 1]
                return json.loads(snippet)
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
    return None


def evaluate_submission(problem: dict, code: str) -> dict:
    result = {
        'syntax_error': None,
        'runtime_error': None,
        'correctness': 'Unknown',
        'feedback': None,
        'efficiency_rating': 'Unknown',
        'details': None,
    }

    exec_result = safe_exec_user_code(code)
    if 'syntax_error' in exec_result:
        result['syntax_error'] = exec_result['syntax_error']
        result['correctness'] = 'Incorrect'
        result['feedback'] = 'Your code has a syntax error. Please fix it and try again.'
        return result

    if 'runtime_error' in exec_result:
        result['runtime_error'] = exec_result['runtime_error']
        result['correctness'] = 'Incorrect'
        result['feedback'] = 'Your code raised an error during execution.'
        return result

    start = time.perf_counter()
    namespace = exec_result.get('namespace', {})
    elapsed = time.perf_counter() - start
    result['efficiency_rating'] = evaluate_efficiency(code, elapsed)

    llm_result = llm_review_code(problem.get('problem', ''), code)
    if llm_result is not None:
        result['correctness'] = llm_result.get('correctness', 'Unknown').capitalize()
        result['feedback'] = llm_result.get('feedback') or llm_result.get('notes')
        result['efficiency_rating'] = llm_result.get('efficiency_rating', result['efficiency_rating'])
        result['details'] = llm_result.get('notes')
    else:
        result['correctness'] = 'Unknown'
        result['feedback'] = 'Code compiled successfully. For full correctness and efficiency assessment, set OPENAI_API_KEY in the environment.'

    return result


def test_openai_connection():
    """Test if OpenAI connection is working"""
    if openai_client is None:
        return False, "OpenAI client not initialized"
    try:
        response = openai_client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[{'role': 'user', 'content': 'Say OK'}],
            max_tokens=10
        )
        return True, "OpenAI connection successful"
    except Exception as e:
        return False, f"OpenAI connection failed: {str(e)}"


init_db()

# Branding
logo_path = Path('assets/avanade-logo.png')
if logo_path.exists():
    st.image(str(logo_path), width=180)

st.title('Avanade Coding Gym')
st.markdown('Generate random Python programming problems and track your progress with guided breakdowns and hints.')

# Authentication helpers

def get_user(username: str):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT id, username, password_hash FROM users WHERE username = ?', (username,))
    row = c.fetchone()
    conn.close()
    return row


def create_user(username: str, password: str):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, hash_password(password)))
        conn.commit()
        user_id = c.lastrowid
    except sqlite3.IntegrityError:
        user_id = None
    conn.close()
    return user_id


def set_session_user(user_id: int, username: str):
    st.session_state.user = {'id': user_id, 'username': username}


def logout_user():
    if 'user' in st.session_state:
        del st.session_state.user
    if 'current_problem' in st.session_state:
        del st.session_state.current_problem


# Sidebar for account and navigation
with st.sidebar:
    st.header('Account')
    
    # Show OpenAI status
    st.divider()
    st.subheader('LLM Evaluation')
    if openai_client is None:
        st.warning('⚠️ OpenAI not configured')
    else:
        st.success('✓ OpenAI ready')
    st.divider()
    
    if 'user' in st.session_state:
        st.write(f"Signed in as **{st.session_state.user['username']}**")
        if st.button('Logout'):
            logout_user()
            st.rerun()
    else:
        with st.form('auth_form'):
            auth_mode = st.radio('Choose action', ['Login', 'Create account'])
            username = st.text_input('Username', key='auth_username')
            password = st.text_input('Password', type='password', key='auth_password')
            submitted = st.form_submit_button('Submit')

        if submitted:
            if not username or not password:
                st.error('Please enter both a username and password.')
            else:
                if auth_mode == 'Create account':
                    user_id = create_user(username.strip(), password)
                    if user_id:
                        set_session_user(user_id, username.strip())
                        st.success('Account created and signed in.')
                        st.rerun()
                    else:
                        st.error('Username already exists. Choose another.')
                else:
                    user = get_user(username.strip())
                    if not user:
                        st.error('Invalid username or password.')
                    else:
                        user_id, user_name, password_hash = user
                        if hash_password(password) == password_hash:
                            set_session_user(user_id, user_name)
                            st.success('Signed in successfully.')
                            st.rerun()
                        else:
                            st.error('Invalid username or password.')

    if 'user' in st.session_state:
        st.header('Actions')
        difficulty = st.selectbox('Select difficulty for new problem', ['random', 'easy', 'medium', 'hard'])
        if st.button('Generate New Problem'):
            if difficulty == 'random':
                prob = random.choice(problems)
            else:
                filtered = [p for p in problems if p['difficulty'] == difficulty]
                if filtered:
                    prob = random.choice(filtered)
                else:
                    st.error('No problems available for this difficulty.')
                    prob = None

            if prob:
                st.session_state.current_problem = prob
                conn = get_db_connection()
                c = conn.cursor()
                c.execute(
                    'INSERT OR REPLACE INTO progress (user_id, problem_id, status, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)',
                    (st.session_state.user['id'], prob['id'], 'attempted')
                )
                conn.commit()
                conn.close()
                st.success(f"Problem {prob['id']} loaded!")
    else:
        st.info('Sign in or create an account to save your progress and metrics.')

# Main area
if 'current_problem' in st.session_state:
    prob = st.session_state.current_problem
    st.header(f"Problem {prob['id']} - {prob['difficulty'].capitalize()}")
    st.write(prob['problem'])

    with st.expander('Problem Breakdown'):
        if 'breakdown' in prob and prob['breakdown']:
            for i, step in enumerate(prob['breakdown'], 1):
                st.write(f'**Step {i}:** {step}')
        else:
            st.write('No breakdown available for this problem.')

    with st.expander('Hints'):
        if 'hints' in prob and prob['hints']:
            for i, hint in enumerate(prob['hints'], 1):
                st.write(f'**Hint {i}:** {hint}')
        else:
            st.write('No hints available for this problem.')

    st.markdown('---')
    st.subheader('Submit Your Code')
    st.info('Paste your Python code below. If you want the app to evaluate your solution automatically, define a function named `solution` that returns the expected result.')
    code_input = st.text_area('Your Python code', value=st.session_state.get('code_input', ''), height=260, key='code_input')
    submit_code = st.button('Submit Code')

    if submit_code:
        evaluation = evaluate_submission(prob, code_input)
        st.session_state.last_evaluation = evaluation

        if evaluation.get('syntax_error'):
            st.error('Syntax error: ' + evaluation['syntax_error'])
        elif evaluation.get('runtime_error'):
            st.error('Runtime error: ' + evaluation['runtime_error'])
        else:
            correctness = evaluation.get('correctness', 'Unknown')
            if correctness.lower() == 'correct':
                st.success('Submission appears correct.')
            elif correctness.lower() == 'incorrect':
                st.error('Submission appears incorrect.')
            else:
                st.info('Submission evaluated with limited certainty.')
            st.write('**Efficiency:**', evaluation.get('efficiency_rating'))
            if evaluation.get('feedback'):
                st.write('**Feedback:**', evaluation.get('feedback'))

            if correctness.lower() == 'correct' and 'user' in st.session_state:
                conn = get_db_connection()
                c = conn.cursor()
                c.execute(
                    'INSERT OR REPLACE INTO progress (user_id, problem_id, status, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)',
                    (st.session_state.user['id'], prob['id'], 'completed')
                )
                conn.commit()
                conn.close()
                st.success('Correct solution recorded as completed!')

    if 'last_evaluation' in st.session_state and not submit_code:
        evaluation = st.session_state.last_evaluation
        if evaluation:
            st.write('**Previous submission result:**')
            if evaluation.get('syntax_error'):
                st.error('Syntax error: ' + evaluation['syntax_error'])
            elif evaluation.get('runtime_error'):
                st.error('Runtime error: ' + evaluation['runtime_error'])
            else:
                st.write('**Correctness:**', evaluation.get('correctness', 'Unknown'))
                st.write('**Efficiency:**', evaluation.get('efficiency_rating'))
                if evaluation.get('feedback'):
                    st.write('**Feedback:**', evaluation.get('feedback'))

    if 'user' not in st.session_state:
        st.warning('Sign in to save progress for this problem.')
    else:
        col1, col2 = st.columns(2)
        with col1:
            if st.button('Mark as Completed'):
                conn = get_db_connection()
                c = conn.cursor()
                c.execute(
                    'INSERT OR REPLACE INTO progress (user_id, problem_id, status, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)',
                    (st.session_state.user['id'], prob['id'], 'completed')
                )
                conn.commit()
                conn.close()
                st.success('Problem marked as completed!')

        with col2:
            if st.button('Skip to Next'):
                if difficulty == 'random':
                    new_prob = random.choice(problems)
                else:
                    filtered = [p for p in problems if p['difficulty'] == difficulty]
                    if filtered:
                        new_prob = random.choice(filtered)
                    else:
                        new_prob = random.choice(problems)
                st.session_state.current_problem = new_prob
                st.rerun()

# Progress section
st.header('Your Progress')
if 'user' in st.session_state:
    user_id = st.session_state.user['id']
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM progress WHERE user_id = ? AND status = ?', (user_id, 'attempted'))
    attempted = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM progress WHERE user_id = ? AND status = ?', (user_id, 'completed'))
    completed = c.fetchone()[0]
    conn.close()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric('Attempted', attempted)
    with col2:
        st.metric('Completed', completed)
    with col3:
        st.metric('Total Problems', len(problems))

    progress = completed / len(problems) if problems else 0
    st.progress(progress)
    st.write(f'Completion: {completed}/{len(problems)} ({progress*100:.1f}%)')

    if completed > 0:
        st.subheader('Completed Problems')
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT problem_id FROM progress WHERE user_id = ? AND status = ? ORDER BY problem_id', (user_id, 'completed'))
        completed_ids = [row[0] for row in c.fetchall()]
        conn.close()

        for pid in completed_ids:
            prob = next((p for p in problems if p['id'] == pid), None)
            if prob:
                st.write(f"- Problem {pid}: {prob['problem'][:50]}...")
else:
    st.info('Sign in or create an account to save your tracked completions and metrics.')

# Debug/Admin section
if 'user' in st.session_state and st.session_state.user.get('username') == 'maurice.jenkins':
    st.divider()
    st.header('Debug - Database Viewer')
    with st.expander('View Database Contents'):
        st.subheader('Users Table')
        try:
            conn = get_db_connection()
            users_df = __import__('pandas').read_sql_query('SELECT id, username, created_at FROM users', conn)
            if not users_df.empty:
                st.dataframe(users_df, use_container_width=True)
            else:
                st.info('No users in database yet.')
            conn.close()
        except Exception as e:
            st.error(f'Error reading users table: {e}')

        st.subheader('Progress Table')
        try:
            conn = get_db_connection()
            progress_df = __import__('pandas').read_sql_query(
                'SELECT u.username, p.problem_id, p.status, p.updated_at FROM progress p JOIN users u ON p.user_id = u.id ORDER BY p.updated_at DESC',
                conn
            )
            if not progress_df.empty:
                st.dataframe(progress_df, use_container_width=True)
            else:
                st.info('No progress records in database yet.')
            conn.close()
        except Exception as e:
            st.error(f'Error reading progress table: {e}')

        st.subheader('Statistics')
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('SELECT COUNT(*) FROM users')
            total_users = c.fetchone()[0]
            
            c.execute('SELECT COUNT(DISTINCT user_id) FROM progress WHERE status = "completed"')
            users_with_completions = c.fetchone()[0]
            
            c.execute('SELECT COUNT(*) FROM progress WHERE status = "completed"')
            total_completions = c.fetchone()[0]
            
            c.execute('SELECT COUNT(*) FROM progress WHERE status = "attempted"')
            total_attempts = c.fetchone()[0]
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric('Total Users', total_users)
            with col2:
                st.metric('Users w/ Completions', users_with_completions)
            with col3:
                st.metric('Total Completions', total_completions)
            with col4:
                st.metric('Total Attempts', total_attempts)
            
            conn.close()
        except Exception as e:
            st.error(f'Error calculating statistics: {e}')

        st.subheader('Raw SQL Query')
    st.write('Enter a custom SQL query to execute against the database:')
    query = st.text_area('SQL Query', value='SELECT * FROM users;', height=100)
    if st.button('Execute Query'):
        try:
            conn = get_db_connection()
            result_df = __import__('pandas').read_sql_query(query, conn)
            st.dataframe(result_df, use_container_width=True)
            conn.close()
        except Exception as e:
            st.error(f'Query error: {e}')