from setuptools import setup, find_packages

setup(
    name="seabom",  # ✅ New package name
    version="1.0.0",
    author="Aizen",
    author_email="vivekmangiraj7@gmail.com",
    description="Collection of DSBDA problem statements and resources",
    packages=find_packages(),
    include_package_data=True,
    package_data={"seabom": ["**/*"]},  # ✅ Update package name here too
    license="MIT",
    python_requires=">=3.7",
)
