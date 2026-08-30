from setuptools import find_packages, setup

package_name = "ppe_logger"
setup(name=package_name, version="0.1.0", packages=find_packages(), data_files=[("share/ament_index/resource_index/packages", ["resource/" + package_name]), ("share/" + package_name, ["package.xml"])], install_requires=["setuptools"], zip_safe=True, maintainer="Oscar I. Valenzuela", maintainer_email="osckar.vdo@gmail.com", description="SQLite PPE event logger.", license="Apache-2.0", entry_points={"console_scripts": ["logger_node = ppe_logger.node:main"]})
