from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
import random
import os

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = "algogame_secret"

# ---------------- DATABASE ---------------- #

def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            algorithm TEXT,
            level INTEGER,
            difficulty TEXT,
            steps INTEGER,
            optimal_steps INTEGER,
            efficiency REAL,
            time_taken INTEGER,
            hints_used INTEGER,
            completed BOOLEAN
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS user_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            algorithm TEXT,
            current_level INTEGER,
            total_levels_completed INTEGER,
            average_efficiency REAL
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# ---------------- ALGORITHMS ---------------- #

def bubble_sort(arr):
    steps = 0
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            steps += 1
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return steps

def insertion_sort(arr):
    steps = 0
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0 and arr[j] > key:
            steps += 1
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
    return steps

def selection_sort(arr):
    steps = 0
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i+1, n):
            steps += 1
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
    return steps

def merge_sort(arr):
    steps = 0
    
    def merge_sort_recursive(arr):
        nonlocal steps
        if len(arr) <= 1:
            return arr
        
        mid = len(arr) // 2
        left = merge_sort_recursive(arr[:mid])
        right = merge_sort_recursive(arr[mid:])
        
        merged = []
        i = j = 0
        
        while i < len(left) and j < len(right):
            steps += 1
            if left[i] <= right[j]:
                merged.append(left[i])
                i += 1
            else:
                merged.append(right[j])
                j += 1
        
        merged.extend(left[i:])
        merged.extend(right[j:])
        return merged
    
    merge_sort_recursive(arr.copy())
    return steps

def quick_sort(arr):
    steps = 0
    
    def quick_sort_recursive(arr, low, high):
        nonlocal steps
        if low < high:
            pi = partition(arr, low, high)
            quick_sort_recursive(arr, low, pi - 1)
            quick_sort_recursive(arr, pi + 1, high)
    
    def partition(arr, low, high):
        nonlocal steps
        pivot = arr[high]
        i = low - 1
        
        for j in range(low, high):
            steps += 1
            if arr[j] <= pivot:
                i += 1
                arr[i], arr[j] = arr[j], arr[i]
        
        arr[i + 1], arr[high] = arr[high], arr[i + 1]
        return i + 1
    
    quick_sort_recursive(arr.copy(), 0, len(arr) - 1)
    return steps

# ---------------- LEVELS SYSTEM ---------------- #

LEVELS = {
    'bubble_sort': {
        'easy': [
            {'id': 1, 'size': 4, 'range': (1, 10), 'description': 'Sort 4 small numbers'},
            {'id': 2, 'size': 5, 'range': (1, 15), 'description': 'Sort 5 small numbers'},
            {'id': 3, 'size': 6, 'range': (1, 20), 'description': 'Sort 6 small numbers'},
            {'id': 4, 'size': 4, 'range': (1, 50), 'description': 'Sort 4 medium numbers'},
            {'id': 5, 'size': 5, 'range': (1, 100), 'description': 'Sort 5 medium numbers'}
        ],
        'medium': [
            {'id': 6, 'size': 7, 'range': (1, 50), 'description': 'Sort 7 medium numbers'},
            {'id': 7, 'size': 8, 'range': (1, 75), 'description': 'Sort 8 medium numbers'},
            {'id': 8, 'size': 6, 'range': (1, 200), 'description': 'Sort 6 large numbers'},
            {'id': 9, 'size': 7, 'range': (1, 300), 'description': 'Sort 7 large numbers'},
            {'id': 10, 'size': 8, 'range': (1, 500), 'description': 'Sort 8 large numbers'}
        ],
        'hard': [
            {'id': 11, 'size': 10, 'range': (1, 100), 'description': 'Sort 10 medium numbers'},
            {'id': 12, 'size': 12, 'range': (1, 200), 'description': 'Sort 12 large numbers'},
            {'id': 13, 'size': 8, 'range': (1, 1000), 'description': 'Sort 8 very large numbers'},
            {'id': 14, 'size': 10, 'range': (1, 1000), 'description': 'Sort 10 very large numbers'},
            {'id': 15, 'size': 15, 'range': (1, 500), 'description': 'Sort 15 large numbers'}
        ]
    },
    'insertion_sort': {
        'easy': [
            {'id': 16, 'size': 4, 'range': (1, 10), 'description': 'Insertion Sort - 4 elements'},
            {'id': 17, 'size': 5, 'range': (1, 15), 'description': 'Insertion Sort - 5 elements'},
            {'id': 18, 'size': 6, 'range': (1, 20), 'description': 'Insertion Sort - 6 elements'}
        ],
        'medium': [
            {'id': 19, 'size': 7, 'range': (1, 50), 'description': 'Insertion Sort - 7 elements'},
            {'id': 20, 'size': 8, 'range': (1, 75), 'description': 'Insertion Sort - 8 elements'},
            {'id': 21, 'size': 6, 'range': (1, 200), 'description': 'Insertion Sort - 6 large elements'}
        ],
        'hard': [
            {'id': 22, 'size': 10, 'range': (1, 100), 'description': 'Insertion Sort - 10 elements'},
            {'id': 23, 'size': 12, 'range': (1, 200), 'description': 'Insertion Sort - 12 large elements'},
            {'id': 24, 'size': 8, 'range': (1, 1000), 'description': 'Insertion Sort - 8 very large elements'}
        ]
    },
    'selection_sort': {
        'easy': [
            {'id': 25, 'size': 4, 'range': (1, 10), 'description': 'Selection Sort - 4 elements'},
            {'id': 26, 'size': 5, 'range': (1, 15), 'description': 'Selection Sort - 5 elements'}
        ],
        'medium': [
            {'id': 27, 'size': 6, 'range': (1, 50), 'description': 'Selection Sort - 6 elements'},
            {'id': 28, 'size': 7, 'range': (1, 75), 'description': 'Selection Sort - 7 elements'}
        ],
        'hard': [
            {'id': 29, 'size': 8, 'range': (1, 100), 'description': 'Selection Sort - 8 elements'},
            {'id': 30, 'size': 10, 'range': (1, 200), 'description': 'Selection Sort - 10 large elements'}
        ]
    },
    'merge_sort': {
        'medium': [
            {'id': 31, 'size': 8, 'range': (1, 50), 'description': 'Merge Sort - 8 elements'},
            {'id': 32, 'size': 10, 'range': (1, 75), 'description': 'Merge Sort - 10 elements'}
        ],
        'hard': [
            {'id': 33, 'size': 12, 'range': (1, 100), 'description': 'Merge Sort - 12 elements'},
            {'id': 34, 'size': 16, 'range': (1, 200), 'description': 'Merge Sort - 16 large elements'}
        ]
    },
    'quick_sort': {
        'medium': [
            {'id': 35, 'size': 8, 'range': (1, 50), 'description': 'Quick Sort - 8 elements'},
            {'id': 36, 'size': 10, 'range': (1, 75), 'description': 'Quick Sort - 10 elements'}
        ],
        'hard': [
            {'id': 37, 'size': 12, 'range': (1, 100), 'description': 'Quick Sort - 12 elements'},
            {'id': 38, 'size': 16, 'range': (1, 200), 'description': 'Quick Sort - 16 large elements'}
        ]
    }
}

# ---------------- AI HINT SYSTEM ---------------- #

def get_hint(algorithm, level_data, current_array, user_steps):
    hints = {
        'bubble_sort': [
            "Compare adjacent elements and swap if they're in wrong order",
            "After each pass, the largest element 'bubbles up' to the end",
            "You need n-1 passes for n elements",
            f"For {len(current_array)} elements, optimal steps are {len(current_array)*(len(current_array)-1)//2}"
        ],
        'insertion_sort': [
            "Build sorted array one element at a time",
            "Take each element and insert it into correct position in sorted part",
            "Left side of current element is always sorted",
            f"For {len(current_array)} elements, worst case is {len(current_array)*(len(current_array)-1)//2} steps"
        ],
        'selection_sort': [
            "Find minimum element and place it at beginning",
            "Repeat for remaining unsorted portion",
            "Each pass places one element in correct position",
            f"For {len(current_array)} elements, you need {len(current_array)*(len(current_array)-1)//2} comparisons"
        ],
        'merge_sort': [
            "Divide array into two halves recursively",
            "Merge sorted halves back together",
            "Use two-pointer technique for merging",
            "Time complexity is O(n log n) - very efficient!"
        ],
        'quick_sort': [
            "Choose a pivot element",
            "Partition array around pivot",
            "Recursively sort sub-arrays",
            "Average case is O(n log n) - very fast!"
        ]
    }
    
    algorithm_hints = hints.get(algorithm, ["No hints available"])
    hint_index = min(user_steps // 3, len(algorithm_hints) - 1)
    return algorithm_hints[hint_index]

# ---------------- QUIZ SYSTEM ---------------- #

QUIZ_QUESTIONS = {
    'bubble_sort': [
        {
            'question': 'What is the time complexity of Bubble Sort in worst case?',
            'options': ['O(n)', 'O(n log n)', 'O(n²)', 'O(1)'],
            'correct': 2,
            'explanation': 'Bubble Sort has O(n²) time complexity in worst case when array is reverse sorted'
        },
        {
            'question': 'How many passes does Bubble Sort need for an array of n elements?',
            'options': ['n', 'n-1', 'n+1', 'n²'],
            'correct': 1,
            'explanation': 'Bubble Sort needs n-1 passes to sort an array of n elements'
        }
    ],
    'insertion_sort': [
        {
            'question': 'When is Insertion Sort most efficient?',
            'options': ['Random array', 'Sorted array', 'Reverse sorted array', 'Large array'],
            'correct': 1,
            'explanation': 'Insertion Sort is most efficient for nearly sorted arrays with O(n) time complexity'
        }
    ],
    'selection_sort': [
        {
            'question': 'What does Selection Sort do in each pass?',
            'options': ['Swaps adjacent elements', 'Finds minimum element', 'Divides array', 'Merges arrays'],
            'correct': 1,
            'explanation': 'Selection Sort finds the minimum element and places it at the beginning in each pass'
        }
    ]
}

# ---------------- ROUTES ---------------- #

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/register', methods=["GET","POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT INTO users (name,email,password) VALUES (?,?,?)",
                  (name,email,password))
        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")

@app.route('/login', methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=? AND password=?",
                  (email,password))
        user = c.fetchone()
        conn.close()

        if user:
            session["user_id"] = user[0]
            session["name"] = user[1]
            return redirect("/dashboard")

    return render_template("login.html")

@app.route('/guest')
def guest():
    session["user_id"] = "guest"
    session["name"] = "Guest"
    return redirect("/dashboard")

@app.route('/dashboard')
def dashboard():
    if "user_id" not in session:
        return redirect("/login")
    
    # Get user progress
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    
    if session.get("user_id") != "guest":
        c.execute("SELECT algorithm, current_level, total_levels_completed, average_efficiency FROM user_progress WHERE user_id=?", 
                  (session["user_id"],))
        progress = c.fetchall()
    else:
        progress = []
    
    conn.close()
    
    return render_template("dashboard.html", name=session["name"], progress=progress, algorithms=LEVELS.keys())

@app.route('/level_selection')
def level_selection():
    if "user_id" not in session:
        return redirect("/login")
    
    # Get user progress for level unlocking
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    
    if session.get("user_id") != "guest":
        c.execute("SELECT algorithm, current_level, total_levels_completed FROM user_progress WHERE user_id=?", 
                  (session["user_id"],))
        progress = c.fetchall()
        # Convert to dict for easier lookup
        user_progress = {prog[0]: prog[1] for prog in progress}
    else:
        user_progress = {}
    
    conn.close()
    
    return render_template("level_selection.html", algorithms=LEVELS, user_progress=user_progress)

@app.route('/game/<algorithm>/<difficulty>/<int:level_id>')
def specific_game(algorithm, difficulty, level_id):
    if "user_id" not in session:
        return redirect("/login")
    
    # Find level data
    level_data = None
    for level in LEVELS.get(algorithm, {}).get(difficulty, []):
        if level['id'] == level_id:
            level_data = level
            break
    
    if not level_data:
        return "Level not found", 404
    
    return render_template("game.html", 
                        algorithm=algorithm, 
                        difficulty=difficulty, 
                        level_data=level_data)

@app.route('/generate_array/<algorithm>/<difficulty>/<int:level_id>')
def generate_specific_array(algorithm, difficulty, level_id):
    # Find level data
    level_data = None
    for level in LEVELS.get(algorithm, {}).get(difficulty, []):
        if level['id'] == level_id:
            level_data = level
            break
    
    if not level_data:
        return jsonify({"error": "Level not found"}), 404
    
    # Generate array based on level specifications
    arr = random.sample(range(level_data['range'][0], level_data['range'][1]), level_data['size'])
    return jsonify({"array": arr, "level_data": level_data})

@app.route('/get_hint/<algorithm>')
def get_algorithm_hint(algorithm):
    current_array = request.args.get('array', '').split(',') if request.args.get('array') else []
    user_steps = int(request.args.get('steps', 0))
    
    try:
        current_array = [int(x) for x in current_array if x.strip()]
    except:
        current_array = []
    
    hint = get_hint(algorithm, None, current_array, user_steps)
    return jsonify({"hint": hint})

@app.route('/submit_solution', methods=["POST"])
def submit_solution():
    data = request.json
    algorithm = data["algorithm"]
    difficulty = data["difficulty"]
    level_id = data["level_id"]
    user_steps = int(data["steps"])
    time_taken = int(data["time_taken"])
    hints_used = int(data.get("hints_used", 0))
    user_array = data["array"]
    
    # Calculate optimal steps based on algorithm
    algorithm_functions = {
        'bubble_sort': bubble_sort,
        'insertion_sort': insertion_sort,
        'selection_sort': selection_sort,
        'merge_sort': merge_sort,
        'quick_sort': quick_sort
    }
    
    optimal_steps = algorithm_functions[algorithm](user_array.copy())
    efficiency = round((optimal_steps / user_steps) * 100, 2) if user_steps > 0 else 0
    completed = efficiency >= 80  # Consider completed if efficiency is 80% or above
    
    # Save to database if not guest
    if session.get("user_id") != "guest":
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        
        # Save score
        c.execute("""INSERT INTO scores 
                   (user_id, algorithm, level, difficulty, steps, optimal_steps, 
                    efficiency, time_taken, hints_used, completed) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (session["user_id"], algorithm, level_id, difficulty, user_steps, 
                   optimal_steps, efficiency, time_taken, hints_used, completed))
        
        # Update progress
        c.execute("""INSERT OR REPLACE INTO user_progress 
                   (user_id, algorithm, current_level, total_levels_completed, average_efficiency)
                   VALUES (?, ?, 
                          (SELECT COALESCE(MAX(level), ?) + 1 FROM scores WHERE user_id=? AND algorithm=?),
                          (SELECT COUNT(*) FROM scores WHERE user_id=? AND algorithm=? AND completed=1),
                          (SELECT AVG(efficiency) FROM scores WHERE user_id=? AND algorithm=?))""",
                  (session["user_id"], algorithm, level_id, session["user_id"], algorithm,
                   session["user_id"], algorithm, session["user_id"], algorithm))
        
        conn.commit()
        conn.close()
    
    # Generate quiz question
    quiz_questions = QUIZ_QUESTIONS.get(algorithm, [])
    quiz_question = random.choice(quiz_questions) if quiz_questions else None
    
    return jsonify({
        "optimal_steps": optimal_steps,
        "efficiency": efficiency,
        "completed": completed,
        "quiz_question": quiz_question
    })

@app.route('/get_quiz/<algorithm>')
def get_quiz_question(algorithm):
    questions = QUIZ_QUESTIONS.get(algorithm, [])
    if questions:
        return jsonify(random.choice(questions))
    return jsonify({"error": "No quiz questions available"})

@app.route('/leaderboard')
def leaderboard():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    
    c.execute("""SELECT u.name, s.algorithm, s.efficiency, s.level, s.difficulty 
               FROM scores s JOIN users u ON s.user_id = u.id 
               ORDER BY s.efficiency DESC LIMIT 10""")
    leaders = c.fetchall()
    
    conn.close()
    return render_template("leaderboard.html", leaders=leaders)

@app.route('/logout')
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
