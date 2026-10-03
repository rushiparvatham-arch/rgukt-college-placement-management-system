import json
from app.extensions import db
from app.models import (
    User, StudentProfile, CompanyProfile, CDPCProfile, Drive, Application,
    Interview, Result, Notification, AptitudeTest,
)

BRANCHES = [
    "Computer Science & Engineering",
    "Electronics & Communication Engineering",
    "Electrical & Electronics Engineering",
    "Mechanical Engineering",
    "Civil Engineering",
]


def seed_data():
    if User.query.first():
        return  # already seeded

    # ---- CDPC / Admin ----
    cdpc = User(name="Dr. Lakshmi Narayana", email="cdpc@rguktong.ac.in", role="cdpc", phone="9490011122")
    cdpc.set_password("cdpc12345")
    db.session.add(cdpc)
    db.session.flush()
    db.session.add(CDPCProfile(user_id=cdpc.id, designation="Placement Officer", department="CDPC - RGUKT Ongole"))

    # ---- Companies ----
    companies_seed = [
        ("TechNova Solutions", "IT Services", "Priya Reddy", "https://technova.example.com",
         "TechNova builds enterprise SaaS products for global clients."),
        ("InfoWave Systems", "Software Development", "Karthik Rao", "https://infowave.example.com",
         "InfoWave specialises in cloud-native application development."),
        ("Skyline Analytics", "Data & AI", "Sneha Iyer", "https://skylineanalytics.example.com",
         "Skyline Analytics delivers data engineering and ML consulting."),
    ]
    company_users = []
    for name, industry, hr, site, about in companies_seed:
        email = name.lower().replace(" ", "") + "@company.example.com"
        u = User(name=hr, email=email, role="company", phone="9000011" + str(len(company_users)))
        u.set_password("company123")
        db.session.add(u)
        db.session.flush()
        db.session.add(CompanyProfile(
            user_id=u.id, company_name=name, industry=industry, hr_name=hr,
            hr_designation="HR Manager", website=site, about=about, is_approved=True,
        ))
        company_users.append(u)

    # ---- Students ----
    students_seed = [
        ("Arjun Varma", "N200001", BRANCHES[0], 8.6, 1),
        ("Divya Sri", "N200002", BRANCHES[0], 9.1, 0),
        ("Manoj Kumar", "N200003", BRANCHES[1], 7.8, 0),
        ("Sowmya Reddy", "N200004", BRANCHES[2], 8.2, 0),
        ("Ravi Teja", "N200005", BRANCHES[3], 7.5, 1),
        ("Keerthana", "N200006", BRANCHES[0], 8.9, 0),
    ]
    student_users = []
    for name, roll, branch, cgpa, backlogs in students_seed:
        email = roll.lower() + "@rguktong.ac.in"
        u = User(name=name, email=email, role="student", phone="9876500" + roll[-3:])
        u.set_password("student123")
        db.session.add(u)
        db.session.flush()
        db.session.add(StudentProfile(
            user_id=u.id, roll_number=roll, branch=branch, cgpa=cgpa, backlogs=backlogs,
            batch_year="2022-2026", current_year="4th Year",
            skills="Python, Java, SQL, React" if branch == BRANCHES[0] else "C, Circuit Design, MATLAB",
            tenth_percent=92.0, inter_percent=88.5,
        ))
        student_users.append(u)

    db.session.flush()

    # ---- Drives ----
    drives_seed = [
        (company_users[0], "Software Engineer Trainee", "Full-Time", "₹6.5 LPA", "Hyderabad", 7.0, 1, "All Branches", "Upcoming"),
        (company_users[0], "Backend Developer Intern", "Internship", "₹25,000/month", "Remote", 6.5, 2, "Computer Science & Engineering", "Ongoing"),
        (company_users[1], "Full Stack Developer", "Full-Time", "₹8.2 LPA", "Bengaluru", 7.5, 0, "Computer Science & Engineering", "Ongoing"),
        (company_users[2], "Data Analyst", "Full-Time", "₹7.0 LPA", "Chennai", 7.0, 1,
         "Computer Science & Engineering, Electronics & Communication Engineering", "Upcoming"),
    ]
    drives = []
    for company, title, jtype, ctc, loc, mincg, maxbl, branches, status in drives_seed:
        d = Drive(
            company_id=company.id, role_title=title, job_type=jtype,
            description=f"We are hiring for the role of {title}. Great opportunity for RGUKT Ongole graduates.",
            ctc=ctc, location=loc, min_cgpa=mincg, max_backlogs=maxbl,
            eligible_branches=branches, drive_date="15 Sep 2026", application_deadline="05 Sep 2026",
            status=status,
        )
        db.session.add(d)
        drives.append(d)
    db.session.flush()

    # ---- Sample Applications / Interviews / Results ----
    app1 = Application(student_id=student_users[0].id, drive_id=drives[2].id, status="Interview")
    app2 = Application(student_id=student_users[1].id, drive_id=drives[2].id, status="Selected")
    app3 = Application(student_id=student_users[5].id, drive_id=drives[0].id, status="Applied")
    db.session.add_all([app1, app2, app3])
    db.session.flush()

    db.session.add(Interview(
        application_id=app1.id, round_name="Technical Round 1", scheduled_at="28 Aug 2026, 10:00 AM",
        mode="Online", venue_or_link="https://meet.google.com/sample-link", status="Scheduled",
    ))
    db.session.add(Result(
        application_id=app2.id, outcome="Selected", package_offered="₹8.2 LPA",
        remarks="Excellent performance across all rounds.",
    ))
    student_users[1].student_profile.placed = True

    # ---- Notifications ----
    for u in student_users:
        db.session.add(Notification(user_id=u.id, message="Welcome to the RGUKT Ongole CDPC Placement Portal!"))
    db.session.add(Notification(user_id=cdpc.id, message="3 new companies onboarded this week."))

    # ---- Aptitude Tests ----
    quant_questions = [
        {"question": "A train 120m long crosses a pole in 12 seconds. Find its speed (km/h).", "options": ["30", "36", "40", "45"], "answer": 1},
        {"question": "What is the compound interest on ₹5000 at 10% p.a. for 2 years?", "options": ["₹1000", "₹1050", "₹1100", "₹950"], "answer": 1},
        {"question": "If 15 workers finish a job in 20 days, how many days for 25 workers?", "options": ["10", "12", "14", "16"], "answer": 1},
        {"question": "Find the next number: 2, 6, 12, 20, 30, ?", "options": ["40", "42", "44", "36"], "answer": 1},
        {"question": "What is 25% of 640?", "options": ["150", "160", "170", "180"], "answer": 1},
    ]
    logical_questions = [
        {"question": "If CAT is coded as 3120, how is DOG coded?", "options": ["4157", "4715", "4517", "4175"], "answer": 0},
        {"question": "Complete the series: A, C, F, J, ?", "options": ["N", "O", "P", "M"], "answer": 1},
        {"question": "Pointing to a photo, Ravi said 'She is the daughter of my grandfather's only son.' Who is she?", "options": ["Sister", "Mother", "Cousin", "Aunt"], "answer": 0},
        {"question": "Which figure is different from the rest: Circle, Square, Triangle, Sphere?", "options": ["Circle", "Square", "Triangle", "Sphere"], "answer": 3},
        {"question": "If MONDAY is coded as XDMWZL, how is FRIDAY coded?", "options": ["UIRWZL", "URIZWL", "UFRIZY", "UIRZWL"], "answer": 0},
    ]
    verbal_questions = [
        {"question": "Choose the correct synonym for 'Abundant'.", "options": ["Scarce", "Plentiful", "Rare", "Limited"], "answer": 1},
        {"question": "Choose the correct antonym for 'Optimistic'.", "options": ["Hopeful", "Positive", "Pessimistic", "Confident"], "answer": 2},
        {"question": "Fill in the blank: She has been working here ___ 2019.", "options": ["for", "since", "from", "at"], "answer": 1},
        {"question": "Identify the correctly spelled word.", "options": ["Recieve", "Receive", "Receeve", "Receve"], "answer": 1},
        {"question": "Choose the correct passive voice: 'They built this house in 1990.'", "options": ["This house was built in 1990.", "This house is built in 1990.", "This house built in 1990.", "This house has built in 1990."], "answer": 0},
    ]

    db.session.add(AptitudeTest(title="Quantitative Aptitude - Set 1", category="Quantitative", test_type="aptitude", duration_minutes=15, questions_json=json.dumps(quant_questions)))
    db.session.add(AptitudeTest(title="Logical Reasoning - Set 1", category="Reasoning", test_type="aptitude", duration_minutes=15, questions_json=json.dumps(logical_questions)))
    db.session.add(AptitudeTest(title="Verbal Ability - Set 1", category="Verbal", test_type="aptitude", duration_minutes=10, questions_json=json.dumps(verbal_questions)))

    # ---- Skill Assessments (same table, test_type='skill') ----
    python_questions = [
        {"question": "What is the output of: print(type([]))?", "options": ["<class 'list'>", "<class 'array'>", "<class 'tuple'>", "<class 'dict'>"], "answer": 0},
        {"question": "Which keyword is used to define a function in Python?", "options": ["func", "def", "function", "lambda"], "answer": 1},
        {"question": "What does len('RGUKT') return?", "options": ["4", "5", "6", "Error"], "answer": 1},
        {"question": "Which data structure uses key-value pairs in Python?", "options": ["List", "Tuple", "Set", "Dictionary"], "answer": 3},
        {"question": "What is the correct file extension for Python files?", "options": [".pt", ".py", ".pyt", ".pyth"], "answer": 1},
        {"question": "Which of these is used for exception handling?", "options": ["try/except", "catch/throw", "error/handle", "if/else"], "answer": 0},
    ]
    sql_questions = [
        {"question": "Which SQL clause is used to filter rows?", "options": ["ORDER BY", "WHERE", "GROUP BY", "HAVING"], "answer": 1},
        {"question": "Which command is used to remove a table completely?", "options": ["DELETE", "REMOVE", "DROP", "TRUNCATE TABLE"], "answer": 2},
        {"question": "What does JOIN do in SQL?", "options": ["Deletes rows", "Combines rows from two or more tables", "Sorts a table", "Creates a table"], "answer": 1},
        {"question": "Which keyword returns only distinct values?", "options": ["UNIQUE", "DISTINCT", "ONLY", "SINGLE"], "answer": 1},
        {"question": "Which clause groups rows sharing a property so aggregate functions can be applied?", "options": ["WHERE", "ORDER BY", "GROUP BY", "FILTER"], "answer": 2},
    ]
    webdev_questions = [
        {"question": "Which HTML tag is used to link an external CSS file?", "options": ["<style>", "<link>", "<css>", "<script>"], "answer": 1},
        {"question": "In CSS, which property controls text size?", "options": ["text-style", "font-size", "text-size", "font-style"], "answer": 1},
        {"question": "Which JavaScript method adds an element to the end of an array?", "options": ["push()", "pop()", "shift()", "unshift()"], "answer": 0},
        {"question": "What does the 'fetch' function in JavaScript primarily do?", "options": ["Style elements", "Make network/HTTP requests", "Define variables", "Loop over arrays"], "answer": 1},
        {"question": "Which CSS layout model is commonly used for responsive grids?", "options": ["Flexbox/Grid", "Table only", "Float only", "Inline only"], "answer": 0},
    ]
    dsa_questions = [
        {"question": "What is the time complexity of binary search on a sorted array?", "options": ["O(n)", "O(log n)", "O(n^2)", "O(1)"], "answer": 1},
        {"question": "Which data structure uses LIFO (Last In First Out) order?", "options": ["Queue", "Stack", "Array", "Linked List"], "answer": 1},
        {"question": "Which sorting algorithm has the best average-case time complexity?", "options": ["Bubble Sort", "Selection Sort", "Merge Sort", "Insertion Sort"], "answer": 2},
        {"question": "In a singly linked list, each node's pointer refers to:", "options": ["The previous node", "The next node", "The head node", "The tail node"], "answer": 1},
        {"question": "Which data structure is ideal for implementing BFS traversal?", "options": ["Stack", "Queue", "Heap", "Trie"], "answer": 1},
    ]
    comm_questions = [
        {"question": "In a formal email to a recruiter, which greeting is most appropriate?", "options": ["Hey!", "Dear Sir/Madam,", "Yo,", "Hiya"], "answer": 1},
        {"question": "Which of the following best demonstrates active listening in an interview?", "options": ["Interrupting frequently", "Paraphrasing what the interviewer said", "Checking your phone", "Staying silent throughout"], "answer": 1},
        {"question": "What is the best way to handle a question you don't know the answer to in an interview?", "options": ["Make up an answer confidently", "Admit it and describe how you'd find out", "Stay silent", "Change the topic"], "answer": 1},
        {"question": "Which is a good practice while presenting a project to a panel?", "options": ["Reading slides word-for-word", "Making eye contact and explaining in your own words", "Speaking very fast to save time", "Avoiding questions"], "answer": 1},
    ]

    db.session.add(AptitudeTest(title="Python Programming", category="Python", test_type="skill", duration_minutes=12, questions_json=json.dumps(python_questions)))
    db.session.add(AptitudeTest(title="SQL & Databases", category="SQL", test_type="skill", duration_minutes=10, questions_json=json.dumps(sql_questions)))
    db.session.add(AptitudeTest(title="Web Development Basics", category="Web Dev", test_type="skill", duration_minutes=10, questions_json=json.dumps(webdev_questions)))
    db.session.add(AptitudeTest(title="Data Structures & Algorithms", category="DSA", test_type="skill", duration_minutes=10, questions_json=json.dumps(dsa_questions)))
    db.session.add(AptitudeTest(title="Communication Skills", category="Soft Skills", test_type="skill", duration_minutes=8, questions_json=json.dumps(comm_questions)))

    db.session.commit()
