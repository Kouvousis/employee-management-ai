from datetime import date
import bcrypt
from sqlmodel import Session, select
from database import engine
from models import Employee, Project, Task, User, AccessRights


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


EMPLOYEES = [
    # Leadership
    {"first_name": "Jane", "last_name": "Smith", "role": "CEO", "department": "Leadership",
     "email": "jane.smith@novatech.com", "hire_date": date(2018, 3, 1)},
    {"first_name": "Marcus", "last_name": "Chen", "role": "CTO", "department": "Leadership",
     "email": "marcus.chen@novatech.com", "hire_date": date(2018, 5, 15)},
    {"first_name": "Sarah", "last_name": "O'Brien", "role": "VP of People", "department": "Leadership",
     "email": "sarah.obrien@novatech.com", "hire_date": date(2019, 1, 10)},
    {"first_name": "David", "last_name": "Park", "role": "CFO", "department": "Leadership",
     "email": "david.park@novatech.com", "hire_date": date(2019, 7, 22)},
    {"first_name": "Leila", "last_name": "Nasser", "role": "VP of Product", "department": "Leadership",
     "email": "leila.nasser@novatech.com", "hire_date": date(2020, 2, 3)},

    # Engineering
    {"first_name": "Carlos", "last_name": "Ruiz", "role": "Engineering Lead", "department": "Engineering",
     "email": "carlos.ruiz@novatech.com", "hire_date": date(2019, 4, 8)},
    {"first_name": "Priya", "last_name": "Patel", "role": "Senior Backend Engineer", "department": "Engineering",
     "email": "priya.patel@novatech.com", "hire_date": date(2020, 6, 1)},
    {"first_name": "Tom", "last_name": "Brennan", "role": "Senior Frontend Engineer", "department": "Engineering",
     "email": "tom.brennan@novatech.com", "hire_date": date(2020, 9, 14)},
    {"first_name": "Aisha", "last_name": "Johnson", "role": "Backend Engineer", "department": "Engineering",
     "email": "aisha.johnson@novatech.com", "hire_date": date(2021, 3, 22)},
    {"first_name": "Luca", "last_name": "Ferrari", "role": "Frontend Engineer", "department": "Engineering",
     "email": "luca.ferrari@novatech.com", "hire_date": date(2021, 7, 5)},
    {"first_name": "Nina", "last_name": "Kovacs", "role": "DevOps Engineer", "department": "Engineering",
     "email": "nina.kovacs@novatech.com", "hire_date": date(2021, 11, 19)},
    {"first_name": "James", "last_name": "Wu", "role": "Full Stack Engineer", "department": "Engineering",
     "email": "james.wu@novatech.com", "hire_date": date(2022, 2, 28)},
    {"first_name": "Maya", "last_name": "Thompson", "role": "Junior Backend Engineer", "department": "Engineering",
     "email": "maya.thompson@novatech.com", "hire_date": date(2023, 8, 7)},

    # Product
    {"first_name": "Sofia", "last_name": "Reyes", "role": "Senior Product Manager", "department": "Product",
     "email": "sofia.reyes@novatech.com", "hire_date": date(2020, 5, 11)},
    {"first_name": "Ben", "last_name": "Hartley", "role": "Product Manager", "department": "Product",
     "email": "ben.hartley@novatech.com", "hire_date": date(2021, 9, 3)},
    {"first_name": "Zoe", "last_name": "Kim", "role": "UX Designer", "department": "Product",
     "email": "zoe.kim@novatech.com", "hire_date": date(2022, 1, 17)},
    {"first_name": "Alex", "last_name": "Morgan", "role": "UI Designer", "department": "Product",
     "email": "alex.morgan@novatech.com", "hire_date": date(2022, 6, 20)},

    # HR
    {"first_name": "Rachel", "last_name": "Green", "role": "HR Manager", "department": "HR",
     "email": "rachel.green@novatech.com", "hire_date": date(2019, 10, 14)},
    {"first_name": "Daniel", "last_name": "Torres", "role": "Recruiter", "department": "HR",
     "email": "daniel.torres@novatech.com", "hire_date": date(2022, 4, 4)},

    # Sales
    {"first_name": "Ryan", "last_name": "Mitchell", "role": "Sales Lead", "department": "Sales",
     "email": "ryan.mitchell@novatech.com", "hire_date": date(2019, 8, 26)},
    {"first_name": "Emma", "last_name": "Clarke", "role": "Account Executive", "department": "Sales",
     "email": "emma.clarke@novatech.com", "hire_date": date(2021, 5, 10)},
    {"first_name": "Omar", "last_name": "Hassan", "role": "Account Executive", "department": "Sales",
     "email": "omar.hassan@novatech.com", "hire_date": date(2021, 12, 6)},
    {"first_name": "Lisa", "last_name": "Park", "role": "Sales Development Rep", "department": "Sales",
     "email": "lisa.park@novatech.com", "hire_date": date(2023, 3, 13)},

    # Data & AI
    {"first_name": "Kevin", "last_name": "Zhao", "role": "Data Scientist", "department": "Data & AI",
     "email": "kevin.zhao@novatech.com", "hire_date": date(2021, 1, 25)},
    {"first_name": "Fatima", "last_name": "Al-Rashid", "role": "ML Engineer", "department": "Data & AI",
     "email": "fatima.alrashid@novatech.com", "hire_date": date(2022, 10, 31)},
]

PROJECTS = [
    {"name": "Customer Portal Redesign",
     "description": "Full redesign of the customer-facing portal with improved UX and performance.",
     "deadline": date(2026, 8, 31), "status": "in_progress"},
    {"name": "Data Analytics Dashboard",
     "description": "Internal dashboard for real-time business metrics and KPI tracking.",
     "deadline": date(2026, 7, 15), "status": "in_progress"},
    {"name": "Mobile App Launch", "description": "Native mobile application for iOS and Android.",
     "deadline": date(2026, 12, 1), "status": "planning"},
    {"name": "API v2 Migration",
     "description": "Migrate all internal services from REST v1 to the new versioned REST v2 API.",
     "deadline": date(2026, 9, 30), "status": "in_progress"},
    {"name": "Internal Tooling Upgrade",
     "description": "Upgrade CI/CD pipelines, developer tooling, and internal docs platform.",
     "deadline": date(2026, 5, 1), "status": "completed"},
]

TASKS = [
    ("Tom Brennan", "Redesign navigation component", "in_progress", "Customer Portal Redesign"),
    ("Luca Ferrari", "Implement new dashboard layout", "todo", "Customer Portal Redesign"),
    ("Aisha Johnson", "Refactor authentication API", "in_progress", "Customer Portal Redesign"),
    ("Zoe Kim", "Conduct user research sessions", "completed", "Customer Portal Redesign"),
    ("Alex Morgan", "Create component design system", "in_progress", "Customer Portal Redesign"),

    ("Kevin Zhao", "Build KPI aggregation pipeline", "in_progress", "Data Analytics Dashboard"),
    ("Fatima Al-Rashid", "Train anomaly detection model", "todo", "Data Analytics Dashboard"),
    ("James Wu", "Develop chart rendering layer", "in_progress", "Data Analytics Dashboard"),
    ("Priya Patel", "Design metrics database schema", "completed", "Data Analytics Dashboard"),

    ("Ben Hartley", "Write mobile app PRD", "in_progress", "Mobile App Launch"),
    ("Zoe Kim", "Create mobile wireframes", "todo", "Mobile App Launch"),
    ("Maya Thompson", "Set up React Native project scaffold", "todo", "Mobile App Launch"),

    ("Carlos Ruiz", "Define v2 API contract", "completed", "API v2 Migration"),
    ("Priya Patel", "Migrate user service to v2", "in_progress", "API v2 Migration"),
    ("Aisha Johnson", "Migrate billing service to v2", "todo", "API v2 Migration"),
    ("James Wu", "Update frontend API client", "todo", "API v2 Migration"),

    ("Nina Kovacs", "Upgrade GitHub Actions workflows", "completed", "Internal Tooling Upgrade"),
    ("Nina Kovacs", "Migrate to new secrets manager", "completed", "Internal Tooling Upgrade"),
    ("Marcus Chen", "Evaluate new internal docs platform", "completed", "Internal Tooling Upgrade"),
]


def _access_rights(department: str) -> AccessRights:
    """Map a department name to its default AccessRights level."""
    if department == "Leadership":
        return AccessRights.admin
    if department == "HR":
        return AccessRights.human_resources
    return AccessRights.employee


def seed(session: Session) -> None:
    """Populate the database with reference employees, projects, and tasks.

    Idempotent — skips entirely if any Employee row already exists.
    All inserts run in a single transaction; a failure rolls back everything
    so a retry starts from a clean state.

    flush() is called after each Employee/Project insert to obtain the
    auto-generated id before the transaction is committed, allowing Tasks
    and Users to reference those ids within the same transaction.
    """
    already_seeded = session.exec(select(Employee)).first()
    if already_seeded:
        print("Database already seeded, skipping.")
        return

    try:
        employees: dict[str, Employee] = {}
        default_password = hash_password("novatech123")

        for data in EMPLOYEES:
            emp = Employee(**data)
            session.add(emp)
            session.flush()

            session.add(User(
                hashed_password=default_password,
                access_rights=_access_rights(data["department"]),
                employee_id=emp.id,
            ))

            full_name = f"{data['first_name']} {data['last_name']}"
            employees[full_name] = emp

        # Standalone admin account
        session.add(User(
            hashed_password=hash_password("admin123"),
            access_rights=AccessRights.admin,
        ))

        # Projects
        projects: dict[str, Project] = {}
        for data in PROJECTS:
            proj = Project(**data)
            session.add(proj)
            session.flush()
            projects[data["name"]] = proj

        # Tasks
        for emp_name, title, status, proj_name in TASKS:
            session.add(Task(
                title=title,
                status=status,
                employee_id=employees[emp_name].id,
                project_id=projects[proj_name].id,
            ))

        session.commit()
        print(f"Seeded {len(employees)} employees, {len(projects)} projects, {len(TASKS)} tasks.")
    except Exception as e:
        session.rollback()
        print(f"Seeding failed and was rolled back: {e}")
        raise


if __name__ == "__main__":
    with Session(engine) as session:
        seed(session)
