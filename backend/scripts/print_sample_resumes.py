import json
from backend.app.services.pipeline import run_rule_based

SAMPLE_JD = "Required skills: Python, FastAPI, PostgreSQL, Docker, Git. Preferred skills: Kubernetes, AWS, Redis, React, TypeScript."

STRONG_RESUME = """Sarah Jenkins | sarah.jenkins@example.com | (555) 234-5678 | https://github.com/sjenkins | https://linkedin.com/in/sjenkins

PROFESSIONAL SUMMARY
Principal Backend Architect and Distributed Systems Engineer with 9+ years of experience engineering resilient cloud infrastructure, high-throughput microservices, and modern database solutions.

CORE TECHNICAL SKILLS
Languages & Frameworks: Python, FastAPI, TypeScript, React, Go, SQL, Bash
Infrastructure & DevOps: Docker, Kubernetes, AWS, Terraform, CI/CD, Linux, Redis, PostgreSQL, Git

PROFESSIONAL EXPERIENCE
Staff Software Engineer | Nexa Cloud Systems (2020 - Present)
- Architected distributed data processing pipeline handling 12,000 requests per second, reducing p99 latency by 42%.
- Spearheaded migration of 28 legacy services to containerized Kubernetes pods on AWS with zero downtime.
- Mentored a cross-functional team of 14 backend engineers and implemented automated CI/CD deployment pipelines.

Senior Backend Engineer | DataStream Labs (2016 - 2020)
- Engineered scalable REST APIs using FastAPI and PostgreSQL, serving over 4,500,000 monthly active users.
- Optimized database indexing and Redis cache invalidation, lowering query response times by 65%.
- Implemented robust RBAC authentication mechanisms complying with SOC2 security standards.

EDUCATION
Bachelor of Science in Computer Science, University of California, Berkeley (2016)

PROJECTS
OpenSource Distributed Queue (https://github.com/sjenkins/dist-queue)
- Lightweight distributed queue engine written in Python and Go with custom replication protocols.

CERTIFICATIONS
AWS Certified Solutions Architect - Professional
Certified Kubernetes Administrator (CKA)
"""

AVERAGE_RESUME = """John Doe
john.doe@email.com

Summary
Software developer with around 3 years of experience working on web applications and maintenance.

Skills
Python, Django, JavaScript, HTML, CSS, SQL, Git

Experience
Software Developer | TechCorp (2022 - Present)
- Developed features for web applications using Django and SQL databases.
- Fixed critical bugs and improved code quality across internal tools.
- Collaborated with 4 developers on sprint deliveries and documentation.

Education
B.A. in Information Systems, State University (2021)
"""

WEAK_RESUME = """Resume
Looking for a job in technology.
I have used computers and Microsoft Word and Excel.
Available to start immediately.
"""

NOISY_RESUME = """*** $$$$ CONFIDENTIAL RESUME $$$$ ***
===>>> SECTION 1: <<<<<
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Python??? Maybe!
asdfkjh qwertyuiop zxcvbnm 1234567890 !@#$%^&*()
RANDOM ADVERTISEMENT: Buy discount servers today at www.spamsite.xyz
Experience: worked at place for some time. Did things with computers.
<<<===>>> random fragment: developer coding python bugs broken text string <<<===>>>
Education: school of hard knocks 2020.
"""

EMPTY_RESUME = ""

SAMPLES = {
    "strong": STRONG_RESUME,
    "average": AVERAGE_RESUME,
    "weak": WEAK_RESUME,
    "noisy": NOISY_RESUME,
    "empty": EMPTY_RESUME,
}

def main():
    results = {}
    for name, text in SAMPLES.items():
        res_no_jd = run_rule_based(text, None)
        res_with_jd = run_rule_based(text, SAMPLE_JD)
        results[name] = {
            "without_jd": res_no_jd.model_dump(),
            "with_jd": res_with_jd.model_dump(),
        }
    print(json.dumps(results, indent=2, default=str))

if __name__ == "__main__":
    main()
