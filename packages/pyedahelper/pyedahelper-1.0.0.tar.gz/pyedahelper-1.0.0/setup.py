# from setuptools import setup, find_packages

# setup(
#     name='pyedahelper',
#     version='0.1.0',
#     packages=find_packages(),
#     install_requires=[
#         'pandas',
#         'numpy',
#         'matplotlib',
#         'seaborn'
#     ],
# )

from setuptools import setup, find_packages

setup(
    name="pyedahelper",
    version="1.0.0",
    author="Chidiebere Christopher",
    author_email="vchidiebere.vc@gmail.com",
    description="An interactive cheat sheet for exploratory data analysis (EDA), and tools for data visualization, cleaning and feature engineering",
    packages=find_packages(),
    install_requires=[
        "pandas", "numpy", "seaborn", "matplotlib", "scikit-learn", "rich"
    ],
    python_requires=">=3.8",
)