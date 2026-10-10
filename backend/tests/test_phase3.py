import pytest
from backend.app.services.skills import extract_skills
from backend.app.services.nlp import (
    detect_sections, extract_contact_info, estimate_years_of_experience,
    count_words, extract_links, extract_degree_mentions,
    count_action_verbs, count_quantified_achievements,
)
from backend.app.services.scorer import score_resume, generate_strengths, generate_weaknesses, generate_recommendations
from backend.app.services.matcher import match_skills, compute_compatibility


class TestSkillsExtraction:
    def test_extracts_python(self):
        skills = extract_skills("I have 5 years of Python development experience.")
        assert "Python" in skills

    def test_extracts_typescript(self):
        skills = extract_skills("Built frontends using TypeScript and React.")
        assert "TypeScript" in skills
        assert "React" in skills

    def test_cpp_extracted(self):
        skills = extract_skills("Expert in C++ systems programming and embedded software.")
        assert "C++" in skills

    def test_csharp_extracted(self):
        skills = extract_skills("Developed enterprise apps using C# and .NET framework.")
        assert "C#" in skills
        assert ".NET" in skills

    def test_nodejs_extracted(self):
        skills = extract_skills("Backend APIs with Node.js and Express.js.")
        assert "Node.js" in skills
        assert "Express.js" in skills

    def test_cicd_extracted(self):
        skills = extract_skills("Set up CI/CD pipelines using GitHub Actions.")
        assert "CI/CD" in skills
        assert "GitHub Actions" in skills

    def test_go_not_false_positive_in_word(self):
        skills = extract_skills("Django is a web framework for Python. django-rest-framework is popular.")
        assert "Go" not in skills

    def test_go_i_go_to_meetings_no_match(self):
        skills = extract_skills("I go to meetings every morning and attend standups.")
        assert "Go" not in skills

    def test_go_standalone_with_language_context(self):
        skills = extract_skills("Experienced with Go language microservices.")
        assert "Go" in skills

    def test_r_not_extracted_from_word(self):
        skills = extract_skills("Working with React and Ruby on Rails.")
        assert "R" not in skills

    def test_r_and_d_no_match(self):
        skills = extract_skills("R&D department focuses on innovation.")
        assert "R" not in skills

    def test_r_standalone_extracted(self):
        skills = extract_skills("Statistical analysis using R programming.")
        assert "R" in skills

    def test_c_not_extracted_from_cpp_context(self):
        result = extract_skills("Expert in C++ systems programming.")
        assert "C++" in result

    def test_c_standalone_extracted(self):
        skills = extract_skills("Low-level programming in C language.")
        assert "C" in skills

    def test_dotnet_alias_matches_canonical(self):
        skills = extract_skills("Built services using dotnet and ASP.NET Core.")
        assert ".NET" in skills

    def test_alias_kafka_streams(self):
        skills = extract_skills("Stream processing with kafka and kafka streams at scale.")
        assert "Kafka" in skills

    def test_multiple_categories_extracted(self):
        text = "Python, FastAPI, PostgreSQL, Docker, AWS, TensorFlow, JWT, React"
        skills = extract_skills(text)
        assert "Python" in skills
        assert "FastAPI" in skills
        assert "PostgreSQL" in skills
        assert "Docker" in skills
        assert "AWS" in skills
        assert "TensorFlow" in skills
        assert "JWT" in skills
        assert "React" in skills

    def test_case_insensitive_match(self):
        skills = extract_skills("I know PYTHON and TENSORFLOW and pandas.")
        assert "Python" in skills
        assert "TensorFlow" in skills
        assert "Pandas" in skills

    def test_empty_text_returns_empty(self):
        assert extract_skills("") == []

    def test_no_skills_text(self):
        skills = extract_skills("I enjoy hiking and cooking on weekends.")
        assert skills == []

    def test_pyspark_matches_spark(self):
        skills = extract_skills("Big data processing with PySpark on AWS.")
        assert "Spark" in skills

    def test_sklearn_matches_scikit_learn(self):
        skills = extract_skills("Model training with sklearn and XGBoost.")
        assert "Scikit-learn" in skills
        assert "XGBoost" in skills

    def test_postgres_alias_matches_postgresql(self):
        skills = extract_skills("Database: postgres and redis for caching.")
        assert "PostgreSQL" in skills
        assert "Redis" in skills

    def test_deduplication(self):
        skills = extract_skills("Python python PYTHON py scripting")
        assert skills.count("Python") == 1

    def test_returns_sorted_list(self):
        skills = extract_skills("Terraform, Ansible, Docker, CI/CD, AWS")
        assert skills == sorted(skills)


class TestNLPService:
    def test_detects_experience_section(self):
        text = "Work Experience\nSoftware Engineer at Acme Corp 2020-2024"
        sections = detect_sections(text)
        assert sections["experience"] is True

    def test_detects_education_section(self):
        text = "Education\nB.S. Computer Science, MIT 2018"
        sections = detect_sections(text)
        assert sections["education"] is True

    def test_detects_skills_section(self):
        text = "Technical Skills\nPython, Java, Docker, Kubernetes"
        sections = detect_sections(text)
        assert sections["skills"] is True

    def test_detects_summary_section(self):
        text = "Professional Summary\n10 years of software engineering experience."
        sections = detect_sections(text)
        assert sections["summary"] is True

    def test_detects_certifications(self):
        text = "Certifications\nAWS Solutions Architect\nGoogle Cloud Professional"
        sections = detect_sections(text)
        assert sections["certifications"] is True

    def test_detects_projects(self):
        text = "Projects\nBuilt a REST API using FastAPI and PostgreSQL."
        sections = detect_sections(text)
        assert sections["projects"] is True

    def test_missing_sections_are_false(self):
        text = "Just some random text without structured headings."
        sections = detect_sections(text)
        assert sections["experience"] is False
        assert sections["education"] is False

    def test_extracts_email(self):
        contact = extract_contact_info("john.doe@example.com | github.com/johndoe")
        assert "john.doe@example.com" in contact["emails"]

    def test_extracts_url(self):
        contact = extract_contact_info("https://linkedin.com/in/johndoe | https://github.com/johndoe")
        assert any("linkedin" in u for u in contact["urls"])

    def test_estimates_years_from_explicit(self):
        text = "I have 7 years of experience in software development."
        years = estimate_years_of_experience(text)
        assert years == 7

    def test_estimates_years_from_dates(self):
        text = "Software Engineer (2018-2024)\nJunior Developer (2016-2018)"
        years = estimate_years_of_experience(text)
        assert years >= 6

    def test_word_count(self):
        text = "one two three four five"
        assert count_words(text) == 5

    def test_extract_links_returns_urls(self):
        text = "Portfolio: https://github.com/user and https://linkedin.com/in/user"
        links = extract_links(text)
        assert len(links) >= 2
        assert any("github" in l for l in links)

    def test_extract_links_empty_when_no_urls(self):
        assert extract_links("No links here at all.") == []

    def test_extract_degree_mentions_bachelor(self):
        text = "B.S. in Computer Science from MIT, 2018."
        degrees = extract_degree_mentions(text)
        assert len(degrees) > 0

    def test_extract_degree_mentions_phd(self):
        text = "PhD in Machine Learning, Stanford University."
        degrees = extract_degree_mentions(text)
        assert any("ph" in d.lower() for d in degrees)

    def test_extract_degree_mentions_empty(self):
        degrees = extract_degree_mentions("No degrees mentioned here.")
        assert degrees == []

    def test_count_action_verbs_finds_verbs(self):
        text = "Developed and deployed microservices. Led a team of engineers. Optimized query performance."
        count = count_action_verbs(text)
        assert count >= 3

    def test_count_action_verbs_zero_on_no_verbs(self):
        count = count_action_verbs("The weather is nice today.")
        assert count == 0

    def test_count_quantified_achievements_percentages(self):
        text = "Reduced latency by 40%. Increased revenue by 25%. Scaled to 1M users."
        count = count_quantified_achievements(text)
        assert count >= 2

    def test_count_quantified_achievements_zero(self):
        count = count_quantified_achievements("I worked on various projects.")
        assert count == 0


class TestScorerService:
    def _base_sections(self):
        return {k: False for k in [
            "contact", "summary", "experience", "education", "skills",
            "projects", "certifications", "awards", "publications",
            "languages", "volunteer", "interests"
        ]}

    def test_perfect_resume_scores_high(self):
        sections = {k: True for k in [
            "contact", "summary", "experience", "education", "skills",
            "projects", "certifications", "awards", "publications",
            "languages", "volunteer", "interests"
        ]}
        contact = {"emails": ["x@x.com"], "phones": ["123456789"], "urls": ["https://github.com/x"]}
        score = score_resume(sections, ["Python"] * 20, contact, 500, 8, action_verb_count=12, quantified_achievement_count=5)
        assert score >= 80

    def test_empty_resume_scores_low(self):
        sections = self._base_sections()
        score = score_resume(sections, [], {}, 50, 0)
        assert score < 20

    def test_score_clamped_between_0_and_100(self):
        sections = {k: True for k in self._base_sections()}
        score = score_resume(sections, ["s"] * 100, {"emails": ["x@x.com"], "phones": ["1"], "urls": ["u"]}, 600, 20)
        assert 0 <= score <= 100

    def test_generate_strengths_with_experience(self):
        sections = self._base_sections()
        sections["experience"] = True
        sections["projects"] = True
        strengths = generate_strengths(sections, ["Python", "React"] * 6, 7, ["Python"])
        assert len(strengths) > 0
        assert any("experience" in s.lower() or "7" in s for s in strengths)

    def test_generate_weaknesses_missing_summary(self):
        sections = self._base_sections()
        weaknesses = generate_weaknesses(sections, 400, {}, [])
        assert any("summary" in w.lower() for w in weaknesses)

    def test_generate_recommendations_missing_summary(self):
        sections = self._base_sections()
        recs = generate_recommendations(sections, [], [], 400, {}, 50)
        titles = [r["title"] for r in recs]
        assert any("Summary" in t for t in titles)

    def test_recommendations_have_priority_field(self):
        sections = self._base_sections()
        recs = generate_recommendations(sections, [], ["Docker", "K8s"], 200, {}, 30)
        assert all("priority" in r for r in recs)
        assert all(r["priority"] in ("high", "medium", "low") for r in recs)

    def test_action_verb_bonus_applied(self):
        sections = self._base_sections()
        score_with = score_resume(sections, [], {}, 50, 0, action_verb_count=12, quantified_achievement_count=0)
        score_without = score_resume(sections, [], {}, 50, 0, action_verb_count=0, quantified_achievement_count=0)
        assert score_with >= score_without

    def test_quantified_bonus_applied(self):
        sections = self._base_sections()
        score_with = score_resume(sections, [], {}, 50, 0, action_verb_count=0, quantified_achievement_count=6)
        score_without = score_resume(sections, [], {}, 50, 0, action_verb_count=0, quantified_achievement_count=0)
        assert score_with >= score_without

    def test_compute_section_subscores_structure_and_weights(self):
        sections = {"experience": True, "education": True, "skills": True, "projects": True, "certifications": True, "summary": True}
        contact = {"emails": ["x@example.com"], "phones": ["123"], "urls": ["github.com/x"]}
        score_res = score_resume(
            sections=sections,
            detected_skills=["Python", "FastAPI", "Docker", "SQL", "AWS", "Git", "Linux", "Redis", "TypeScript", "React"],
            contact=contact,
            word_count=500,
            estimated_years_of_experience=6,
            action_verb_count=8,
            quantified_achievement_count=3,
            degree_mentions=["Bachelor of Science"],
            links=["github.com/x"],
        )
        assert isinstance(score_res, int)
        assert score_res > 70
        subscores = score_res.subscores
        expected_keys = {"skills", "experience", "education", "projects", "certifications", "structure"}
        assert set(subscores.keys()) == expected_keys
        total_weight = sum(item["weight"] for item in subscores.values())
        assert round(total_weight, 2) == 1.0
        for k, v in subscores.items():
            assert 0 <= v["score"] <= 100
            assert 0.0 < v["weight"] <= 1.0
            assert isinstance(v["explanation"], str)
            assert len(v["explanation"]) > 0


class TestMatcherService:
    def test_matching_skills_found(self):
        resume_skills = ["Python", "Docker", "PostgreSQL"]
        jd_text = "Looking for a Python developer with Docker and AWS experience."
        matching, missing = match_skills(resume_skills, jd_text)
        assert "Python" in matching
        assert "Docker" in matching

    def test_missing_skills_found(self):
        resume_skills = ["Python"]
        jd_text = "Requires Python, React, and TypeScript."
        matching, missing = match_skills(resume_skills, jd_text)
        assert "React" in missing
        assert "TypeScript" in missing

    def test_empty_jd_returns_no_skills(self):
        resume_skills = ["Python", "Docker"]
        matching, missing = match_skills(resume_skills, "")
        assert matching == []
        assert missing == []

    def test_empty_resume_skills_all_missing(self):
        jd_text = "We need Python and Docker."
        matching, missing = match_skills([], jd_text)
        assert matching == []
        assert "Python" in missing
        assert "Docker" in missing

    def test_returns_sorted_lists(self):
        resume_skills = ["React", "Python", "Docker"]
        jd_text = "Need Python, React, TypeScript, Docker, AWS."
        matching, missing = match_skills(resume_skills, jd_text)
        assert matching == sorted(matching)
        assert missing == sorted(missing)

    def test_compatibility_no_jd_returns_none(self):
        result = compute_compatibility("resume text", "", ["Python"], [], [])
        assert result is None

    def test_compatibility_with_jd_returns_int(self):
        result = compute_compatibility(
            "Python developer with FastAPI experience",
            "Required: Python. Preferred: Docker.",
            ["Python"],
            ["Python"],
            ["Docker"],
        )
        assert isinstance(result, int)
        assert 0 <= result <= 100

    def test_compatibility_perfect_overlap_high_score(self):
        result = compute_compatibility(
            "Python FastAPI Docker PostgreSQL",
            "Required: Python, FastAPI, Docker, PostgreSQL.",
            ["Python", "FastAPI", "Docker", "PostgreSQL"],
            ["Python", "FastAPI", "Docker", "PostgreSQL"],
            [],
        )
        assert result is not None
        assert result >= 50

    def test_required_vs_preferred_weighting(self):
        jd_required = "Required: Python, FastAPI, PostgreSQL, Docker, Redis."
        jd_preferred = "Preferred: Kubernetes, Terraform."
        resume_skills = ["Python", "FastAPI", "PostgreSQL"]
        m1, miss1 = match_skills(resume_skills, jd_required)
        m2, miss2 = match_skills(resume_skills, jd_preferred)
        c1 = compute_compatibility("python fastapi", jd_required, resume_skills, m1, miss1)
        c2 = compute_compatibility("python fastapi", jd_preferred, resume_skills, m2, miss2)
        assert c1 is not None
        assert c2 is not None

    def test_compatibility_separate_metrics_and_formula_assertion(self):
        resume_text = "Experienced software engineer proficient in Python, SQL, Docker, AWS, Git."
        jd_text = "Required: Python, SQL, Docker, AWS, Linux. Preferred: Kubernetes, Terraform."
        resume_skills = ["Python", "SQL", "Docker", "AWS", "Git"]
        matching, missing = match_skills(resume_skills, jd_text)
        result = compute_compatibility(
            resume_text,
            jd_text,
            resume_skills,
            matching,
            missing,
        )
        assert result is not None
        overlap, similarity, compatibility = result
        assert result.skill_overlap == overlap
        assert result.semantic_similarity == similarity
        assert result.compatibility == compatibility
        expected_compatibility = round(100 * (0.6 * overlap + 0.4 * similarity))
        assert compatibility == expected_compatibility
        assert isinstance(result, int)

    def test_known_sample_five_of_seven_skills_explanation(self):
        resume_text = "Proficient in Python, React, SQL, Docker, AWS."
        resume_skills = ["Python", "React", "SQL", "Docker", "AWS"]
        jd_multiline = "Required skills: Python, React, SQL, Docker.\nPreferred skills: AWS, Redis, GraphQL."
        matching, missing = match_skills(resume_skills, jd_multiline)
        assert len(matching) == 5
        assert len(matching) + len(missing) == 7
        result = compute_compatibility(
            resume_text,
            jd_multiline,
            resume_skills,
            matching,
            missing,
        )
        assert result is not None
        overlap, similarity, compatibility = result
        assert compatibility == round(100 * (0.6 * overlap + 0.4 * similarity))
        assert compatibility > 40


class TestPipelineService:
    def test_run_rule_based_empty_text(self):
        from backend.app.services.pipeline import run_rule_based
        result = run_rule_based("")
        assert result.resume_score >= 0
        assert result.compatibility_score is None
        assert result.detected_skills == []

    def test_run_rule_based_odd_input(self):
        from backend.app.services.pipeline import run_rule_based
        result = run_rule_based(None)
        assert result.resume_score >= 0

    def test_run_rule_based_with_text(self):
        from backend.app.services.pipeline import run_rule_based
        text = (
            "John Smith | john@example.com | github.com/john\n"
            "Professional Summary\nSenior Python engineer with 8 years experience.\n"
            "Technical Skills\nPython, FastAPI, PostgreSQL, Docker, Redis\n"
            "Work Experience\nLed a team of 5 engineers. Reduced latency by 40%.\n"
            "Education\nB.S. Computer Science, MIT 2015\n"
            "Projects\nBuilt microservices with Python and Docker."
        )
        result = run_rule_based(text)
        assert result.resume_score > 30
        assert "Python" in result.detected_skills
        assert result.word_count > 20
        assert result.estimated_years_of_experience > 0
        assert len(result.strengths) > 0
        assert len(result.recommendations) > 0

    def test_run_rule_based_with_jd(self):
        from backend.app.services.pipeline import run_rule_based
        text = "Python developer. john@example.com. 3 years experience."
        jd = "Required: Python, FastAPI. Preferred: Docker."
        result = run_rule_based(text, jd)
        assert result.compatibility_score is not None
        assert 0 <= result.compatibility_score <= 100

    def test_run_rule_based_result_has_all_fields(self):
        from backend.app.services.pipeline import run_rule_based
        result = run_rule_based("Software engineer with Python and React skills.")
        assert hasattr(result, "resume_score")
        assert hasattr(result, "compatibility_score")
        assert hasattr(result, "detected_skills")
        assert hasattr(result, "detected_skills_with_category")
        assert hasattr(result, "matching_skills")
        assert hasattr(result, "missing_skills")
        assert hasattr(result, "sections")
        assert "skills" in result.sections
        assert "score" in result.sections["skills"]
        assert hasattr(result, "word_count")
        assert hasattr(result, "action_verb_count")
        assert hasattr(result, "quantified_achievement_count")
        assert hasattr(result, "degree_mentions")
        assert hasattr(result, "links")
        assert hasattr(result, "strengths")
        assert hasattr(result, "weaknesses")
        assert hasattr(result, "recommendations")
        assert hasattr(result, "summary_feedback")

    def test_two_of_ten_skills_matched_below_30(self):
        jd = "Required: Python, FastAPI, Docker, PostgreSQL, Kubernetes, AWS, Redis, React, TypeScript, GraphQL."
        resume_text = "Junior engineer proficient in Python and FastAPI."
        resume_skills = ["Python", "FastAPI"]
        matching, missing = match_skills(resume_skills, jd)
        assert len(matching) == 2
        assert len(matching) + len(missing) == 10
        res = compute_compatibility(resume_text, jd, resume_skills, matching, missing)
        assert res is not None
        assert res < 30

    def test_one_of_ten_skills_matched_below_20(self):
        jd = "Required: Python, FastAPI, Docker, PostgreSQL, Kubernetes, AWS, Redis, React, TypeScript, GraphQL."
        resume_text = "Associate developer with basic Python."
        resume_skills = ["Python"]
        matching, missing = match_skills(resume_skills, jd)
        assert len(matching) == 1
        assert len(matching) + len(missing) == 10
        res = compute_compatibility(resume_text, jd, resume_skills, matching, missing)
        assert res is not None
        assert res < 20

    def test_full_match_above_85(self):
        jd = "Staff engineer required: Python, FastAPI, Docker, PostgreSQL, Kubernetes, AWS, Redis, React, TypeScript, GraphQL. Responsible for building microservices, deploying containers, scaling distributed systems."
        resume_text = "Staff engineer required: Python, FastAPI, Docker, PostgreSQL, Kubernetes, AWS, Redis, React, TypeScript, GraphQL. Responsible for building microservices, deploying containers, scaling distributed systems."
        resume_skills = ["Python", "FastAPI", "Docker", "PostgreSQL", "Kubernetes", "AWS", "Redis", "React", "TypeScript", "GraphQL", "Microservices"]
        matching, missing = match_skills(resume_skills, jd)
        assert len(matching) >= 10
        assert len(missing) == 0
        res = compute_compatibility(resume_text, jd, resume_skills, matching, missing)
        assert res is not None
        assert res > 85

    def test_no_jd_returns_none(self):
        assert compute_compatibility("Some resume", "", ["Python"], ["Python"], []) is None
        assert compute_compatibility("Some resume", None, ["Python"], ["Python"], []) is None
        assert compute_compatibility("Some resume", "   ", ["Python"], ["Python"], []) is None

    def test_portfolio_links_allowed_and_spam_tlds(self):
        from backend.app.services.nlp import extract_links
        text = (
            "Profiles: https://github.com/alex https://gitlab.com/alex https://bitbucket.org/alex "
            "https://linkedin.com/in/alex https://kaggle.com/alex https://huggingface.co/alex "
            "https://behance.net/alex https://alexdev.io "
            "Spam: https://spamsite.xyz https://promos.top https://phishing.click"
        )
        links = extract_links(text)
        assert "https://github.com/alex" in links
        assert "https://gitlab.com/alex" in links
        assert "https://alexdev.io" in links
        assert not any(".xyz" in link for link in links)
        assert not any(".top" in link for link in links)
        assert not any(".click" in link for link in links)

    def test_no_foundational_sections_strength_when_word_count_low_or_few_skills(self):
        sections = {"experience": True, "education": True, "skills": True}
        s1 = generate_strengths(sections, ["Python", "FastAPI", "Docker"], 3, ["Python"], word_count=100)
        assert not any("foundational" in s.lower() for s in s1)
        s2 = generate_strengths(sections, ["Python"], 3, ["Python"], word_count=250)
        assert not any("foundational" in s.lower() for s in s2)
        s3 = generate_strengths(sections, ["Python", "FastAPI", "Docker"], 3, ["Python"], word_count=250)
        assert any("foundational" in s.lower() for s in s3)

    def test_weak_and_empty_resumes_consistent_weaknesses(self):
        w_empty = generate_weaknesses({}, 0, {}, [], 0, 0, [])
        w_weak = generate_weaknesses({}, 20, {}, [], 0, 0, [])
        assert w_empty[:4] == w_weak[:4]
        assert any("summary" in w.lower() for w in w_empty)
        assert any("email" in w.lower() for w in w_empty)
        assert any("phone" in w.lower() for w in w_empty)
        assert any("brief" in w.lower() for w in w_empty)
