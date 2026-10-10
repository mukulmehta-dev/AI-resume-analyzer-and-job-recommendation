import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.services.pipeline import run_rule_based
from backend.app.services.matcher import compute_compatibility, match_skills
from backend.app.services.scorer import SECTION_WEIGHTS

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
    print("=" * 105)
    print("SCORING CONSISTENCY CHECK ON FIVE SAMPLE RESUMES")
    print("=" * 105)
    header = f"{'Sample':<10} | {'Skills':<10} | {'Exp':<10} | {'Edu':<10} | {'Proj':<10} | {'Cert':<10} | {'Struct':<10} | {'Computed Sum':<13} | {'Resume Score':<12} | {'Matches':<7}"
    print(header)
    print("-" * 105)

    all_match = True
    for name, text in SAMPLES.items():
        res = run_rule_based(text, None)
        sec = res.sections
        skills_sub = sec.get("skills", {}).get("score", 0)
        exp_sub = sec.get("experience", {}).get("score", 0)
        edu_sub = sec.get("education", {}).get("score", 0)
        proj_sub = sec.get("projects", {}).get("score", 0)
        cert_sub = sec.get("certifications", {}).get("score", 0)
        struct_sub = sec.get("structure", {}).get("score", 0)

        calc_sum = (
            skills_sub * SECTION_WEIGHTS["skills"]
            + exp_sub * SECTION_WEIGHTS["experience"]
            + edu_sub * SECTION_WEIGHTS["education"]
            + proj_sub * SECTION_WEIGHTS["projects"]
            + cert_sub * SECTION_WEIGHTS["certifications"]
            + struct_sub * SECTION_WEIGHTS["structure"]
        )
        rounded_sum = round(calc_sum)
        matches = (rounded_sum == res.resume_score)
        if not matches:
            all_match = False

        row = (
            f"{name:<10} | "
            f"{skills_sub:<10} | "
            f"{exp_sub:<10} | "
            f"{edu_sub:<10} | "
            f"{proj_sub:<10} | "
            f"{cert_sub:<10} | "
            f"{struct_sub:<10} | "
            f"{calc_sum:<13.2f} | "
            f"{res.resume_score:<12} | "
            f"{str(matches):<7}"
        )
        print(row)

    print("-" * 105)
    print(f"Weights used: {SECTION_WEIGHTS}")
    print(f"All sample resumes exact equality verification: {'PASS' if all_match else 'FAIL'}")
    print("\n" + "=" * 105)
    print("COMPATIBILITY METRICS FOR ALL SAMPLES WITH JOB DESCRIPTION")
    print("=" * 105)
    comp_header = f"{'Sample':<10} | {'Skill Overlap':<15} | {'Semantic Similarity':<22} | {'Compatibility':<15}"
    print(comp_header)
    print("-" * 105)

    for name, text in SAMPLES.items():
        res_with_jd = run_rule_based(text, SAMPLE_JD)
        matching, missing = match_skills(res_with_jd.detected_skills, SAMPLE_JD)
        comp = compute_compatibility(
            resume_text=text,
            jd_text=SAMPLE_JD,
            resume_skills=res_with_jd.detected_skills,
            matching_skills=matching,
            missing_skills=missing,
        )
        if comp is not None:
            overlap, sim, score = comp
            print(f"{name:<10} | {overlap:<15.4f} | {sim:<22.4f} | {score:<15}")
        else:
            print(f"{name:<10} | {'None':<15} | {'None':<22} | {'None':<15}")
    print("=" * 105)


if __name__ == "__main__":
    main()
