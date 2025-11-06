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
    version="0.1.0",
    description="Backend API for Vibe Eats restaurant application",
    author="Your Team",
    author_email="your-email@example.com",
    py_modules=[
        "app",
        "run",
        "extensions",
        "ai_service",
        "restaurantRoutes",
        "cartRoutes",
        "routes_ai",
    ],
    include_package_data=True,
    install_requires=requirements,
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
