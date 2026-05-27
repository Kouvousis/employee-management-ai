from datetime import date
from database import SessionLocal
from models import Employee, Project, Task

EMPLOYEES = [
    # Leadership
    {"name": "Jane Smith",      "role": "CEO",                    "department": "Leadership",   "email": "jane.smith@novatech.com",       "hire_date": date(2018, 3, 1)},
    {"name": "Marcus Chen",     "role": "CTO",                    "department": "Leadership",   "email": "marcus.chen@novatech.com",      "hire_date": date(2018, 5, 15)},
    {"name": "Sarah O'Brien",   "role": "VP of People",           "department": "Leadership",   "email": "sarah.obrien@novatech.com",     "hire_date": date(2019, 1, 10)},
    {"name": "David Park",      "role": "CFO",                    "department": "Leadership",   "email": "david.park@novatech.com",       "hire_date": date(2019, 7, 22)},
    {"name": "Leila Nasser",    "role": "VP of Product",          "department": "Leadership",   "email": "leila.nasser@novatech.com",     "hire_date": date(2020, 2, 3)},

    # Engineering
    {"name": "Carlos Ruiz",     "role": "Engineering Lead",       "department": "Engineering",  "email": "carlos.ruiz@novatech.com",      "hire_date": date(2019, 4, 8)},
    {"name": "Priya Patel",     "role": "Senior Backend Engineer","department": "Engineering",  "email": "priya.patel@novatech.com",      "hire_date": date(2020, 6, 1)},
    {"name": "Tom Brennan",     "role": "Senior Frontend Engineer","department": "Engineering", "email": "tom.brennan@novatech.com",      "hire_date": date(2020, 9, 14)},
    {"name": "Aisha Johnson",   "role": "Backend Engineer",       "department": "Engineering",  "email": "aisha.johnson@novatech.com",    "hire_date": date(2021, 3, 22)},
    {"name": "Luca Ferrari",    "role": "Frontend Engineer",      "department": "Engineering",  "email": "luca.ferrari@novatech.com",     "hire_date": date(2021, 7, 5)},
    {"name": "Nina Kovacs",     "role": "DevOps Engineer",        "department": "Engineering",  "email": "nina.kovacs@novatech.com",      "hire_date": date(2021, 11, 19)},
    {"name": "James Wu",        "role": "Full Stack Engineer",    "department": "Engineering",  "email": "james.wu@novatech.com",         "hire_date": date(2022, 2, 28)},
    {"name": "Maya Thompson",   "role": "Junior Backend Engineer","department": "Engineering",  "email": "maya.thompson@novatech.com",    "hire_date": date(2023, 8, 7)},

    # Product
    {"name": "Sofia Reyes",     "role": "Senior Product Manager", "department": "Product",      "email": "sofia.reyes@novatech.com",      "hire_date": date(2020, 5, 11)},
    {"name": "Ben Hartley",     "role": "Product Manager",        "department": "Product",      "email": "ben.hartley@novatech.com",      "hire_date": date(2021, 9, 3)},
    {"name": "Zoe Kim",         "role": "UX Designer",            "department": "Product",      "email": "zoe.kim@novatech.com",          "hire_date": date(2022, 1, 17)},
    {"name": "Alex Morgan",     "role": "UI Designer",            "department": "Product",      "email": "alex.morgan@novatech.com",      "hire_date": date(2022, 6, 20)},

    # HR
    {"name": "Rachel Green",    "role": "HR Manager",             "department": "HR",           "email": "rachel.green@novatech.com",     "hire_date": date(2019, 10, 14)},
    {"name": "Daniel Torres",   "role": "Recruiter",              "department": "HR",           "email": "daniel.torres@novatech.com",    "hire_date": date(2022, 4, 4)},

    # Sales
    {"name": "Ryan Mitchell",   "role": "Sales Lead",             "department": "Sales",        "email": "ryan.mitchell@novatech.com",    "hire_date": date(2019, 8, 26)},
    {"name": "Emma Clarke",     "role": "Account Executive",      "department": "Sales",        "email": "emma.clarke@novatech.com",      "hire_date": date(2021, 5, 10)},
    {"name": "Omar Hassan",     "role": "Account Executive",      "department": "Sales",        "email": "omar.hassan@novatech.com",      "hire_date": date(2021, 12, 6)},
    {"name": "Lisa Park",       "role": "Sales Development Rep",  "department": "Sales",        "email": "lisa.park@novatech.com",        "hire_date": date(2023, 3, 13)},

    # Data & AI
    {"name": "Kevin Zhao",      "role": "Data Scientist",         "department": "Data & AI",    "email": "kevin.zhao@novatech.com",       "hire_date": date(2021, 1, 25)},
    {"name": "Fatima Al-Rashid","role": "ML Engineer",            "department": "Data & AI",    "email": "fatima.alrashid@novatech.com",  "hire_date": date(2022, 10, 31)},
]

PROJECTS = [
    {
        "name": "Customer Portal Redesign",
        "description": "Full redesign of the customer-facing portal with improved UX and performance.",
        "deadline": date(2026, 8, 31),
        "status": "in_progress",
    },
    {
        "name": "Data Analytics Dashboard",
        "description": "Internal dashboard for real-time business metrics and KPI tracking.",
        "deadline": date(2026, 7, 15),
        "status": "in_progress",
    },
    {
        "name": "Mobile App Launch",
        "description": "Native mobile application for iOS and Android.",
        "deadline": date(2026, 12, 1),
        "status": "planning",
    },
    {
        "name": "API v2 Migration",
        "description": "Migrate all internal services from REST v1 to the new versioned REST v2 API.",
        "deadline": date(2026, 9, 30),
        "status": "in_progress",
    },
    {
        "name": "Internal Tooling Upgrade",
        "description": "Upgrade CI/CD pipelines, developer tooling, and internal docs platform.",
        "deadline": date(2026, 5, 1),
        "status": "completed",
    },
]

# (employee_name, task_title, status, project_name)
TASKS = [
    ("Tom Brennan",     "Redesign navigation component",          "in_progress", "Customer Portal Redesign"),
    ("Luca Ferrari",    "Implement new dashboard layout",          "todo",        "Customer Portal Redesign"),
    ("Aisha Johnson",   "Refactor authentication API",            "in_progress", "Customer Portal Redesign"),
    ("Zoe Kim",         "Conduct user research sessions",          "completed",   "Customer Portal Redesign"),
    ("Alex Morgan",     "Create component design system",         "in_progress", "Customer Portal Redesign"),

    ("Kevin Zhao",      "Build KPI aggregation pipeline",         "in_progress", "Data Analytics Dashboard"),
    ("Fatima Al-Rashid","Train anomaly detection model",          "todo",        "Data Analytics Dashboard"),
    ("James Wu",        "Develop chart rendering layer",          "in_progress", "Data Analytics Dashboard"),
    ("Priya Patel",     "Design metrics database schema",         "completed",   "Data Analytics Dashboard"),

    ("Ben Hartley",     "Write mobile app PRD",                   "in_progress", "Mobile App Launch"),
    ("Zoe Kim",         "Create mobile wireframes",               "todo",        "Mobile App Launch"),
    ("Maya Thompson",   "Set up React Native project scaffold",   "todo",        "Mobile App Launch"),

    ("Carlos Ruiz",     "Define v2 API contract",                 "completed",   "API v2 Migration"),
    ("Priya Patel",     "Migrate user service to v2",             "in_progress", "API v2 Migration"),
    ("Aisha Johnson",   "Migrate billing service to v2",          "todo",        "API v2 Migration"),
    ("James Wu",        "Update frontend API client",             "todo",        "API v2 Migration"),

    ("Nina Kovacs",     "Upgrade GitHub Actions workflows",       "completed",   "Internal Tooling Upgrade"),
    ("Nina Kovacs",     "Migrate to new secrets manager",         "completed",   "Internal Tooling Upgrade"),
    ("Marcus Chen",     "Evaluate new internal docs platform",    "completed",   "Internal Tooling Upgrade"),
]


def seed():
    db = SessionLocal()
    try:
        db.query(Task).delete()
        db.query(Employee).delete()
        db.query(Project).delete()
        db.commit()

        employees = {e["name"]: Employee(**e) for e in EMPLOYEES}
        for emp in employees.values():
            db.add(emp)
        db.flush()

        projects = {p["name"]: Project(**p) for p in PROJECTS}
        for proj in projects.values():
            db.add(proj)
        db.flush()

        for emp_name, title, status, proj_name in TASKS:
            db.add(Task(
                title=title,
                status=status,
                employee_id=employees[emp_name].id,
                project_id=projects[proj_name].id,
            ))

        db.commit()
        print(f"Seeded {len(employees)} employees, {len(projects)} projects, {len(TASKS)} tasks.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
