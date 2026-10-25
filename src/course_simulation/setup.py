from setuptools import find_packages, setup

package_name = 'course_simulation'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
        data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Добавляем эти строки:
        ('share/' + package_name + '/models/course_ackermann', 
            ['models/course_ackermann/model.sdf']),
        ('share/' + package_name + '/models/course_ackermann', 
            ['models/course_ackermann/model.config']),
        ('share/' + package_name + '/worlds', 
            ['worlds/mcity-minimal.sdf']),
        ('share/' + package_name + '/config', 
            ['config/bridge.yaml']),
        ('share/' + package_name + '/launch', 
            ['launch/simulation.launch.py']),
    ],
    package_data={'': ['py.typed']},
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='FedosDan2',
    maintainer_email='f.danilov@g.nsu.ru',
    description='PR07',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'ackermann_adapter = course_simulation.ackermann_adapter:main',
            'odom_adapter = course_simulation.odom_adapter:main',
        ],
    },
)
