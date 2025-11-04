import setuptools
with open("README.md", "r") as fh:
    long_description = fh.read()
setuptools.setup(
    name="daaskit",
    version="0.0.17",
    author="zhangjq",
    author_email="zhangjq@qianqiusoft.com",
    description="python sdk for platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    # url="https://git.qianqiusoft.com/library/qianqiuyun-sdk",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'pymysql',
        'nats-py',
        'influxdb',
        'influxdb-client',
        'DBUtils',
        'cryptography'
    ],
    python_requires='>=3',
)