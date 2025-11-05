from setuptools import setup, find_packages

setup(
    name='makefortune_lib',
    version='1.0.0',
    description="vision lib for myself",
    # long_description=open('README.md').read(),
    # long_description_content_type='text/markdown',  # 添加这一行
    include_package_data=True,
    author='Yichen Guo',
    license='MIT License',
    packages=find_packages(),
    package_data={  # 添加这个参数来包含非Python文件
        # 如果您的包名是 'myVisionlib'
        'makefortune_lib': ['*.dll', '*.ttf', '*.so', '*.pyd'],  # 包含所有dll、ttf等文件
        # 或者更具体地指定子目录
        # 'myVisionlib': ['data/*.dll', 'fonts/*.ttf', 'libs/*.so'],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.8',
    ],
    python_requires='>=3.8',
    install_requires=[
        'opencv-python>=4.5.3.56',
        'numpy>=1.22.3',
        'fins==1.0.5',
        'pylogix',
        'pymelsec',
        'modbus_tk',
        'pyserial',  # 修正为 pyserial
        'pyModbusTCP',
        'python-snap7',
        'matplotlib'
    ],
)