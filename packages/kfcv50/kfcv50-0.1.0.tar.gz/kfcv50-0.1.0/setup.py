from setuptools import setup, find_packages
from pathlib import Path

# 读取README文件
this_directory = Path(__file__).parent
long_description = (this_directory / "README.rst").read_text(encoding='utf-8')

setup(
    name='kfcv50',
    version='0.1.0',
    author='Your Name',
    author_email='your.email@example.com',
    description='一个简短的包描述',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    url='',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    python_requires='>=3.7',
    install_requires=[
        # 在这里添加您的包依赖
        # 例如: 'requests>=2.25.0',
    ],
    extras_require={
        'dev': [
            # 'pytest>=6.0',
            # 'pytest-cov>=2.0',
            # 'flake8>=3.9',
        ],
    },
    keywords='示例 包 python',
    project_urls={
        'Bug Reports': 'https://github.com/yourusername/package-mikezhou-talk/issues',
        'Source': 'https://github.com/yourusername/package-mikezhou-talk',
    },
)

