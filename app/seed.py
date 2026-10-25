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

    # Skill assessments are upserted on every startup via sync_skill_assessments().
    db.session.commit()