from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

requirements = [
    "PyPDF2==3.0.1",
    "google-generativeai>=0.3.2",
    "rich>=13.7.0"
]

setup(
    name="lazycook",
    version="1.0.1",
    author="Hitarth Trivedi(Alpha.Kore),Harsh Bhatt(Alpha.Kore)",
    author_email="hitartht318@gmail.com, bhattharsh328@gmail.com",
    maintainer="Hitarth Trivedi(Alpha.Kore),Harsh Bhatt(Alpha.Kore)",
    maintainer_email="hitartht318@gmail.com, bhattharsh328@gmail.com",
    description="LazyCook is an autonomous multi-agent conversational assistant designed to intelligently process user queries, manage documents, store conversations, and maintain iterative AI reasoning loops. It uses **Gemini 2.5 Flash** model with a **four-agent architecture** for high-quality responses and continuous learning.",
    long_description="LazyCook is an advanced multi-agent AI assistant that brings the power of Google’s Gemini models into a self-contained, autonomous Python application. It is designed for developers, researchers, and productivity enthusiasts who want an intelligent assistant that can chat, analyze, manage documents, track tasks, and evaluate quality — all locally. LazyCook operates on a four-agent architecture, where each agent specializes in a distinct stage of AI reasoning. Together, they create a loop of generation, analysis, optimization, and validation, resulting in high-quality, context-aware, and factually accurate responses. It maintains a persistent memory of user conversations, supports document uploads for contextual reference, and features real-time performance tracking, logging, and export tools",
    long_description_content_type="text/markdown",
    packages=find_packages(),

    python_requires=">=3.10",
    install_requires=requirements,
)