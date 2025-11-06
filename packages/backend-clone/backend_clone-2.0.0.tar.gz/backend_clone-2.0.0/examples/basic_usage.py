"""
Basic usage example for backend-clone
"""
from backend_clone import Generator

# Programmatic usage
gen = Generator(
    project_name="myapi",
    framework="fastapi",
    features=["auth", "database"]
)

# Generate the project
gen.generate()

print("Project generated successfully!")
print(f"Project location: {gen.project_path}")