from setuptools import setup, find_packages
import os

# Read requirements from requirements.txt if it exists
requirements = []
if os.path.exists("requirements.txt"):
    with open("requirements.txt") as f:
        requirements = [
            line.strip() for line in f if line.strip() and not line.startswith("#")
        ]
else:
    # Fallback requirements if requirements.txt is not available during build
    requirements = [
        "Flask",
        "supabase",
        "python-dotenv",
        "flask-cors",
        "pytest",
        "pytest-mock",
        "pytest-cov",
        "openai",
        "flake8",
        "black",
    ]

setup(
    name="vibe-eats-backend",
    use_scm_version={
        "root": "../..",
        "relative_to": __file__,
        "version_scheme": "post-release",
        "local_scheme": "node-and-date",
    },
    setup_requires=["setuptools-scm"],
    description="Backend API for Vibe Eats restaurant application with AI-powered recommendations",
    long_description="A Flask-based backend API for the Vibe Eats restaurant application, featuring AI-powered meal recommendations, cart management, and restaurant data handling.",
    long_description_content_type="text/plain",
    author="Vibe Eats Team",
    author_email="team@vibeeats.example.com",
    url="https://github.com/yourusername/vibe-eats",
    py_modules=[
        "app",
        "run",
        "run_app",
        "extensions",
        "ai_service",
        "restaurantRoutes",
        "cartRoutes",
    ],
    include_package_data=True,
    install_requires=requirements,
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Framework :: Flask",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
)
