import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from backend.app.services.pipeline import run_rule_based
from backend.app.services.matcher import compute_compatibility, match_skills
from backend.app.services.scorer import SECTION_WEIGHTS, round_half_up

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
    print("=" * 115)
    print("COMPATIBILITY & SCORING TABLE (FIVE ORIGINAL SAMPLES: WITH AND WITHOUT JD)")
    print("=" * 115)
    header = f"{'Sample':<10} | {'Mode':<10} | {'Overlap':<10} | {'Raw Sim':<10} | {'Norm Sim':<10} | {'Compat':<8} | {'Resume Score':<12} | {'Weighted Sum':<12} | {'Match'}"
    print(header)
    print("-" * 115)

    for mode in ["with_jd", "without_jd"]:
        jd_text = SAMPLE_JD if mode == "with_jd" else None
        for name, text in SAMPLES.items():
            res = run_rule_based(text, jd_text)
            sec = res.sections
            calc_sum = sum(sec.get(k, {}).get("score", 0) * w for k, w in SECTION_WEIGHTS.items())
            rounded_sum = round_half_up(calc_sum)
            match_str = "PASS" if rounded_sum == res.resume_score else "FAIL"

            if jd_text:
                matching, missing = match_skills(res.detected_skills, jd_text)
                c_res = compute_compatibility(text, jd_text, res.detected_skills, matching, missing)
                overlap_str = f"{c_res.skill_overlap:.4f}"
                raw_sim_str = f"{c_res.semantic_similarity:.4f}"
                norm_sim_str = f"{c_res.normalized_similarity:.4f}"
                compat_str = str(c_res.compatibility)
            else:
                overlap_str = "None"
                raw_sim_str = "None"
                norm_sim_str = "None"
                compat_str = "None"

            row = (
                f"{name:<10} | "
                f"{mode:<10} | "
                f"{overlap_str:<10} | "
                f"{raw_sim_str:<10} | "
                f"{norm_sim_str:<10} | "
                f"{compat_str:<8} | "
                f"{res.resume_score:<12} | "
                f"{rounded_sum:<12} | "
                f"{match_str}"
            )
            print(row)
        print("-" * 115)


if __name__ == "__main__":
    main()
