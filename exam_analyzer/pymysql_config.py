"""
PyMySQL Django Configuration
This module configures PyMySQL to work as a drop-in replacement for mysqlclient in Django.
Import this module before Django starts to ensure proper MySQL connectivity.
"""

try:
    import pymysql
    # Configure PyMySQL to work with Django
    pymysql.install_as_MySQLdb()
    print("✓ PyMySQL configured successfully as MySQL driver")
except ImportError:
    print("⚠ PyMySQL not installed - install it with: pip install PyMySQL")
    print("  This is needed for MySQL database connectivity")
