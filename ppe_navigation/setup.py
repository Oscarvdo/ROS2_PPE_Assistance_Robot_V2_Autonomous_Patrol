from glob import glob
from setuptools import find_packages, setup

package_name = "ppe_navigation"
setup(name=package_name, version="0.2.0", packages=find_packages(), data_files=[("share/ament_index/resource_index/packages", ["resource/" + package_name]), ("share/" + package_name, ["package.xml"]), ("share/" + package_name + "/config", glob("config/*.yaml")), ("share/" + package_name + "/launch", glob("launch/*.launch.py")), ("share/" + package_name + "/urdf", glob("urdf/*")), ("share/" + package_name + "/maps", glob("maps/*"))], install_requires=["setuptools", "PyYAML"], zip_safe=True, maintainer="Oscar I. Valenzuela", maintainer_email="osckar.vdo@gmail.com", description="Autonomous mapping, safety supervision, and PPE patrol integration.", license="Apache-2.0", entry_points={"console_scripts": ["navigation_guard = ppe_navigation.node:main", "safety_supervisor = ppe_navigation.safety_supervisor_node:main", "patrol_node = ppe_navigation.patrol_node:main"]})
