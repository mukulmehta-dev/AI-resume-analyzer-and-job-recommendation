import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from docx import Document
from backend.app.db.session import SessionLocal
from backend.app.core.config import settings
from backend.app.core.security import hash_password
from backend.app.models.user import User, UserRole
from backend.app.models.resume import Resume
from backend.app.models.analysis import Analysis, AnalysisStatus
from backend.app.services.pipeline import run_rule_based
from backend.app.db.seed import seed_admin
from backend.app.services.storage import storage_service
from backend.app.services.gemini import is_available, enhance_analysis
from backend.app.routers.analyses import _run_pipeline


def _create_sample_pdf(text: str) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    y = 750
    for line in text.split("\n"):
        if y < 50:
            c.showPage()
            y = 750
        c.drawString(50, y, line[:90])
        y -= 15
    c.save()
    return buffer.getvalue()


def _create_sample_docx(text: str) -> bytes:
    doc = Document()
    for line in text.split("\n"):
        doc.add_paragraph(line)
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def _is_gemini_operational() -> bool:
    if not is_available():
        return False
    try:
        test_facts = {"word_count": 100, "estimated_years_of_experience": 2}
        test_enh = enhance_analysis(
            resume_facts=test_facts,
            jd_text=None,
            detected_skills=["Python"],
            matching_skills=[],
            missing_skills=[],
            resume_score=75,
            sections={"skills": True},
        )
        return bool(test_enh and test_enh.get("model_used"))
    except Exception:
        return False


def seed_demo_data():
    if settings.ENV.lower() == "production":
        print("Demo seed is disabled in production environment.")
        return

    with SessionLocal() as db:
        seed_admin(db)

        demo_user = db.query(User).filter(User.email == "demo@example.com").first()
        if not demo_user:
            demo_user = User(
                name="Demo User",
                email="demo@example.com",
                password_hash=hash_password("DemoPassword123!"),
                role=UserRole.user,
                is_active=True,
            )
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)

        r1_text = (
            "Alex Mercer | alex@example.com | (555) 019-2834 | github.com/alexm\n\n"
            "Professional Summary\nSenior Software Architect with 8+ years building enterprise Python and cloud solutions.\n\n"
            "Technical Skills\nPython, FastAPI, Docker, Kubernetes, PostgreSQL, AWS, Redis, React, CI/CD, Git\n\n"
            "Experience\nLead Architect at CloudWave (2019 - Present)\n"
            "- Spearheaded migration of 20 microservices to Kubernetes, reducing infrastructure spend by 35%.\n"
            "- Architected high-throughput message streaming pipeline handling 5,000,000 daily messages.\n\n"
            "Education\nB.S. in Computer Science, Stanford University (2016)\n\n"
            "Projects\nDistributed Task Engine (github.com/alexm/task-engine)\n\n"
            "Certifications\nAWS Certified Solutions Architect"
        )
        pdf_bytes = _create_sample_pdf(r1_text)
        path1, _ = storage_service.save_file(pdf_bytes, "Alex_Mercer_Senior_Architect.pdf")

        r1 = Resume(
            user_id=demo_user.id,
            filename="Alex_Mercer_Senior_Architect.pdf",
            stored_path=path1,
            mime="application/pdf",
            size=len(pdf_bytes),
            extracted_text=r1_text,
        )
        db.add(r1)
        db.commit()
        db.refresh(r1)

        res0 = run_rule_based(r1_text, None)
        a0 = Analysis(
            user_id=demo_user.id,
            resume_id=r1.id,
            job_description=None,
            resume_score=res0.resume_score,
            compatibility_score=None,
            detected_skills=res0.detected_skills,
            matching_skills=[],
            missing_skills=[],
            job_skills=[],
            sections=res0.sections,
            strengths=res0.strengths,
            weaknesses=res0.weaknesses,
            recommendations=[r.model_dump() for r in res0.recommendations],
            summary_feedback="",
            ai_model=None,
            job_tailored_tips=[],
            ai_insights=None,
            status=AnalysisStatus.done,
            ai_unavailable=True,
        )
        db.add(a0)

        jd1 = "Required: Python, FastAPI, Docker, PostgreSQL, Kubernetes. Preferred: AWS, Redis, React."
        res1 = run_rule_based(r1_text, jd1)
        a1 = Analysis(
            user_id=demo_user.id,
            resume_id=r1.id,
            job_description=jd1,
            resume_score=res1.resume_score,
            compatibility_score=res1.compatibility_score,
            detected_skills=res1.detected_skills,
            matching_skills=res1.matching_skills,
            missing_skills=res1.missing_skills,
            job_skills=res1.job_skills,
            sections=res1.sections,
            strengths=res1.strengths,
            weaknesses=res1.weaknesses,
            recommendations=[r.model_dump() for r in res1.recommendations],
            summary_feedback="",
            ai_model=None,
            job_tailored_tips=[],
            ai_insights=None,
            status=AnalysisStatus.done,
            ai_unavailable=True,
        )
        db.add(a1)

        r2_text = (
            "Taylor Reed | taylor@example.com\n\n"
            "Summary\nSoftware engineer with 3 years experience building full-stack web apps.\n\n"
            "Skills\nPython, Django, JavaScript, SQL, HTML, CSS, Git\n\n"
            "Experience\nWeb Developer at AppWorks (2022 - Present)\n"
            "- Developed RESTful APIs and UI components for client portals.\n"
            "- Improved test coverage by 20% across key application flows.\n\n"
            "Education\nB.A. in Computer Science, State College (2021)"
        )
        docx_bytes = _create_sample_docx(r2_text)
        path2, _ = storage_service.save_file(docx_bytes, "Taylor_Reed_Resume.docx")

        r2 = Resume(
            user_id=demo_user.id,
            filename="Taylor_Reed_Resume.docx",
            stored_path=path2,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            size=len(docx_bytes),
            extracted_text=r2_text,
        )
        db.add(r2)
        db.commit()
        db.refresh(r2)

        jd2 = "Required: Python, SQL, Git. Preferred: Docker, FastAPI, AWS."
        res2 = run_rule_based(r2_text, jd2)
        a2 = Analysis(
            user_id=demo_user.id,
            resume_id=r2.id,
            job_description=jd2,
            resume_score=res2.resume_score,
            compatibility_score=res2.compatibility_score,
            detected_skills=res2.detected_skills,
            matching_skills=res2.matching_skills,
            missing_skills=res2.missing_skills,
            job_skills=res2.job_skills,
            sections=res2.sections,
            strengths=res2.strengths,
            weaknesses=res2.weaknesses,
            recommendations=[r.model_dump() for r in res2.recommendations],
            summary_feedback="",
            ai_model=None,
            job_tailored_tips=[],
            ai_insights=None,
            status=AnalysisStatus.done,
            ai_unavailable=True,
        )
        db.add(a2)

        r3_text = (
            "Jordan Case\n"
            "Tech enthusiast seeking software role.\n"
            "Experience with HTML, CSS, JavaScript."
        )
        pdf3_bytes = _create_sample_pdf(r3_text)
        path3, _ = storage_service.save_file(pdf3_bytes, "Jordan_Case_Draft.pdf")

        r3 = Resume(
            user_id=demo_user.id,
            filename="Jordan_Case_Draft.pdf",
            stored_path=path3,
            mime="application/pdf",
            size=len(pdf3_bytes),
            extracted_text=r3_text,
        )
        db.add(r3)
        db.commit()
        db.refresh(r3)

        a3 = Analysis(
            user_id=demo_user.id,
            resume_id=r3.id,
            job_description="Staff Data Engineer requiring PySpark, Kafka, AWS, Snowflake.",
            resume_score=0,
            compatibility_score=None,
            detected_skills=[],
            matching_skills=[],
            missing_skills=[],
            job_skills=[],
            sections={},
            strengths=[],
            weaknesses=[],
            recommendations=[],
            summary_feedback=None,
            ai_model=None,
            job_tailored_tips=[],
            ai_insights=None,
            status=AnalysisStatus.failed,
            error="Document extraction failed: corrupt PDF structure or unreadable text stream.",
            ai_unavailable=True,
        )
        db.add(a3)
        db.commit()

        if _is_gemini_operational():
            print("Gemini key is active. Running real pipeline analyses for demo user...")
            _run_pipeline(a0.id, r1_text, None)
            _run_pipeline(a1.id, r1_text, jd1)
            _run_pipeline(a2.id, r2_text, jd2)
            print("Demo analyses enriched with live Gemini intelligence.")
        else:
            print("Demo seed completed rule-based analyses (ai_unavailable=True, empty summary).")


if __name__ == "__main__":
    seed_demo_data()
