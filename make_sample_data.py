"""Generate 8 fictional resumes (TXT, PDF, DOCX) into ./resumes. All people are made up."""
from pathlib import Path

from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

OUT = Path(__file__).parent / "resumes"

RESUMES = {
    "john_doe": ("pdf", "John Doe", "Backend Developer", 5,
                 ["Python", "Django", "PostgreSQL", "Docker"],
                 "Built REST APIs in Python serving 2M requests/day at Acme Retail."),
    "priya_sharma": ("pdf", "Priya Sharma", "Data Engineer", 4,
                     ["Python", "Spark", "Airflow", "AWS"],
                     "Designed Python ETL pipelines processing 500 GB daily."),
    "arjun_mehta": ("docx", "Arjun Mehta", "Java Developer", 7,
                    ["Java", "Spring Boot", "Kafka", "MySQL"],
                    "Led a Spring Boot payments service handling 10k TPS."),
    "sara_lee": ("docx", "Sara Lee", "Frontend Developer", 3,
                 ["JavaScript", "React", "TypeScript", "CSS"],
                 "Built a React design system used by 6 product teams."),
    "ravi_kumar": ("txt", "Ravi Kumar", "DevOps Engineer", 6,
                   ["Kubernetes", "Terraform", "Jenkins", "Python scripting"],
                   "Cut deployment time from 40 to 8 minutes with CI/CD automation."),
    "emma_wilson": ("txt", "Emma Wilson", "ML Engineer", 5,
                    ["Python", "PyTorch", "scikit-learn", "MLflow"],
                    "Shipped a churn model that improved retention by 12%."),
    "li_wei": ("pdf", "Li Wei", "C# Developer", 8,
               ["C#", ".NET", "ASP.NET Core", "SQL Server"],
               "Migrated a legacy .NET Framework monolith to ASP.NET Core."),
    "maria_garcia": ("docx", "Maria Garcia", "QA Automation Engineer", 4,
                     ["Selenium", "Java", "Cypress", "Postman"],
                     "Automated 600 regression tests, cutting release cycles by 30%."),
}


def body(name, role, years, skills, highlight):
    return [
        name, role,
        f"Email: {name.lower().replace(' ', '.')}@example.com",
        "",
        "SUMMARY",
        f"{role} with {years} years of experience.",
        "",
        "SKILLS",
        ", ".join(skills),
        "",
        "EXPERIENCE",
        highlight,
        f"{years} years total across product companies.",
        "",
        "EDUCATION",
        "B.Tech, Computer Science",
    ]


def main():
    OUT.mkdir(exist_ok=True)
    for key, (fmt, name, role, years, skills, hl) in RESUMES.items():
        lines = body(name, role, years, skills, hl)
        path = OUT / f"resume_{key}.{fmt}"
        if fmt == "txt":
            path.write_text("\n".join(lines), encoding="utf-8")
        elif fmt == "docx":
            doc = Document()
            doc.add_heading(lines[0], 0)
            for ln in lines[1:]:
                doc.add_paragraph(ln)
            doc.save(path)
        else:
            c = canvas.Canvas(str(path), pagesize=A4)
            y = 800
            for ln in lines:
                c.drawString(60, y, ln)
                y -= 20
            c.save()
        print("created", path.name)


if __name__ == "__main__":
    main()
