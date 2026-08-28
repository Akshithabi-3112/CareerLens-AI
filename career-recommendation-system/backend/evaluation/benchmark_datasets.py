"""Ground-truth benchmark datasets for evaluating:
1. Skill Extraction (Precision, Recall, F1)
2. Career Recommendation Ranking (Precision@K, Recall@K, NDCG@K, MRR)
3. Skill-Gap & Readiness Analysis
"""

# ── Benchmark 1: Resume Text Skill Extraction Ground-Truth ─────────────────
RESUME_EXTRACTION_BENCHMARK = [
    {
        "id": "resume_1_data_science",
        "text": """
        Experienced Data Scientist with 4 years specializing in Python, Machine Learning, and Deep Learning.
        Proficient with TensorFlow, PyTorch, Pandas, and NumPy for building statistical models and neural networks.
        Strong background in SQL for querying PostgreSQL and MySQL databases.
        Used Scikit-learn for random forest and gradient boosting classifiers, and Matplotlib and Seaborn for data visualization.
        Hands-on experience with Docker and Git version control on Linux systems.
        """,
        "ground_truth_skills": [
            "Python", "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch",
            "Pandas", "NumPy", "Neural Networks", "SQL", "PostgreSQL", "MySQL",
            "Scikit-learn", "Matplotlib", "Seaborn", "Data Visualization",
            "Docker", "Git", "Linux",
        ],
    },
    {
        "id": "resume_2_frontend_web",
        "text": """
        Frontend Developer skilled in building reactive web applications using HTML, CSS, JavaScript, and TypeScript.
        Extensive experience with React, Next.js, and Redux for state management.
        Designed responsive UI using Tailwind CSS and Figma design systems.
        Familiar with REST APIs, GraphQL, and modern web optimization.
        Managed repositories using GitHub and deployed web apps with CI/CD pipelines.
        """,
        "ground_truth_skills": [
            "HTML", "CSS", "JavaScript", "TypeScript", "React", "Next.js",
            "Redux", "Tailwind CSS", "Figma", "REST APIs", "GraphQL", "GitHub", "CI/CD",
        ],
    },
    {
        "id": "resume_3_devops_cloud",
        "text": """
        DevOps & Cloud Engineer with expertise in AWS, EC2, and S3 infrastructure.
        Automated cloud deployments with Terraform and Docker containerization.
        Orchestrated microservices using Kubernetes (k8s) and managed CI/CD pipelines with Jenkins and GitLab CI.
        Solid Linux server administration, Bash scripting, and Git workflow.
        Configured Prometheus and Grafana for metrics monitoring and network security.
        """,
        "ground_truth_skills": [
            "AWS", "EC2", "S3", "Terraform", "Docker", "Kubernetes", "CI/CD",
            "Jenkins", "Linux", "Git", "Prometheus", "Grafana", "Network Security",
        ],
    },
    {
        "id": "resume_4_backend_java",
        "text": """
        Senior Java Developer specializing in Spring Boot microservices, Hibernate, and RESTful API design.
        Extensive database experience with PostgreSQL, MySQL, and Redis for caching.
        Implemented asynchronous messaging using Apache Kafka and RabbitMQ.
        Containerized services with Docker and deployed to Kubernetes clusters.
        Proficient in unit testing with JUnit and version control with Git.
        """,
        "ground_truth_skills": [
            "Java", "Spring Boot", "REST APIs", "PostgreSQL", "MySQL", "Redis",
            "Kafka", "Docker", "Kubernetes", "Git",
        ],
    },
    {
        "id": "resume_5_mobile_flutter",
        "text": """
        Mobile Application Engineer proficient in Flutter and Dart development for iOS and Android platforms.
        Integrated Firebase authentication and Cloud Firestore database.
        Experience consuming REST APIs and GraphQL backends.
        Familiar with native Swift and Kotlin integration, state management with Bloc/Provider, and Git version control.
        """,
        "ground_truth_skills": [
            "Flutter", "Dart", "Firebase", "REST APIs", "GraphQL", "Swift", "Kotlin", "Git",
        ],
    },
    {
        "id": "resume_6_cybersecurity",
        "text": """
        Information Security Analyst skilled in Penetration Testing, Ethical Hacking, and Network Security.
        Hands-on experience with Wireshark, Metasploit, Nmap, and Kali Linux.
        Conducted vulnerability assessment, SIEM log analysis, and incident response.
        Strong understanding of TCP/IP networking, cryptography, and Python scripting for security automation.
        """,
        "ground_truth_skills": [
            "Penetration Testing", "Ethical Hacking", "Network Security", "Linux",
            "Python", "Cybersecurity",
        ],
    },
    {
        "id": "resume_7_database_admin",
        "text": """
        Database Administrator with expertise in Oracle, Microsoft SQL Server, PostgreSQL, and MySQL.
        Skilled in database design, performance tuning, indexing, and complex SQL queries.
        Implemented high availability, replication, backup recovery, and NoSQL databases with MongoDB.
        Experienced with Linux shell scripting and data warehousing concepts.
        """,
        "ground_truth_skills": [
            "Oracle", "SQL", "PostgreSQL", "MySQL", "Database Design", "MongoDB", "Linux",
        ],
    },
    {
        "id": "resume_8_ui_ux_design",
        "text": """
        UI/UX Product Designer proficient in Figma, Adobe XD, and Wireframing.
        Led user research, usability testing, design systems, and prototyping for SaaS platforms.
        Solid understanding of HTML, CSS, and responsive design for developer handoff.
        """,
        "ground_truth_skills": [
            "Figma", "UI/UX Design", "Wireframing", "HTML", "CSS", "Responsive Design",
        ],
    },
]


# ── Benchmark 2: Career Recommendation Ground-Truth ────────────────────────
# Maps candidate skill vectors to ground-truth relevant/ideal target careers (graded relevance 3 = primary, 2 = highly relevant, 1 = related)
CAREER_RECOMMENDATION_BENCHMARK = [
    {
        "profile_id": "profile_ml_engineer",
        "skills": ["Python", "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "Pandas", "Scikit-learn"],
        "ground_truth_careers": {
            "Machine Learning Engineer": 3,
            "Deep Learning Specialist": 3,
            "AI Engineer": 3,
            "Data Scientist": 2,
            "Computer Vision Engineer": 2,
            "NLP Engineer": 2,
            "Data Analyst": 1,
        },
    },
    {
        "profile_id": "profile_frontend_developer",
        "skills": ["HTML", "CSS", "JavaScript", "TypeScript", "React", "Next.js", "Tailwind CSS"],
        "ground_truth_careers": {
            "Frontend Developer": 3,
            "Web Developer": 3,
            "Full Stack Developer": 2,
            "UI/UX Designer": 1,
            "Mobile App Developer": 1,
        },
    },
    {
        "profile_id": "profile_devops_engineer",
        "skills": ["Linux", "Docker", "Kubernetes", "AWS", "CI/CD", "Terraform", "Git"],
        "ground_truth_careers": {
            "DevOps Engineer": 3,
            "Cloud Solutions Architect": 3,
            "Cloud Security Engineer": 2,
            "System Administrator": 2,
            "Backend Developer": 1,
        },
    },
    {
        "profile_id": "profile_backend_developer",
        "skills": ["Java", "Spring Boot", "SQL", "PostgreSQL", "REST APIs", "Docker", "Microservices"],
        "ground_truth_careers": {
            "Backend Developer": 3,
            "Software Engineer": 3,
            "Java Developer": 3,
            "Full Stack Developer": 2,
            "Database Administrator": 1,
        },
    },
    {
        "profile_id": "profile_data_analyst",
        "skills": ["SQL", "Python", "Tableau", "Power BI", "Pandas", "Data Analysis", "Statistics"],
        "ground_truth_careers": {
            "Data Analyst": 3,
            "Business Intelligence Analyst": 3,
            "Data Scientist": 2,
            "Machine Learning Engineer": 1,
        },
    },
    {
        "profile_id": "profile_cybersecurity",
        "skills": ["Cybersecurity", "Network Security", "Linux", "Ethical Hacking", "Penetration Testing", "Python"],
        "ground_truth_careers": {
            "Cybersecurity Analyst": 3,
            "Security Engineer": 3,
            "Penetration Tester": 3,
            "Network Engineer": 2,
            "DevOps Engineer": 1,
        },
    },
    {
        "profile_id": "profile_mobile_dev",
        "skills": ["Flutter", "Dart", "Swift", "Kotlin", "Firebase", "REST APIs"],
        "ground_truth_careers": {
            "Mobile App Developer": 3,
            "Android Developer": 3,
            "iOS Developer": 3,
            "Frontend Developer": 1,
        },
    },
    {
        "profile_id": "profile_database_admin",
        "skills": ["SQL", "MySQL", "PostgreSQL", "Oracle", "MongoDB", "Database Design"],
        "ground_truth_careers": {
            "Database Administrator": 3,
            "Data Engineer": 2,
            "Backend Developer": 1,
        },
    },
]
