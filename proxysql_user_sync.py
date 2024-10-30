#!/bin/env python3
"""ProxySQL users sync"""
# -*- coding: utf-8 -*-
import os
import argparse
import logging
import sys
import pymysql

# Default logging
# pylint: disable=logging-fstring-interpolation
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)


def get_env_or_default(env_var, default_value):
    """Returns the value of an environment variable or its default value."""
    return os.getenv(env_var, default_value)


def get_users_from_db(db_nodes, db_user, db_password, db_port):
    """Gets a list of users from a MySQL cluster."""
    for node in db_nodes:
        try:
            logging.info(f"Connecting to MySQL node: {node}")
            # noinspection PyUnresolvedReferences
            connection = pymysql.connect(
                host=node,
                user=db_user,
                password=db_password,
                port=db_port,
                cursorclass=pymysql.cursors.DictCursor
            )
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT user, authentication_string FROM mysql.user "
                    "WHERE user NOT LIKE 'mysql.%' AND plugin != 'auth_socket'")
                users = cursor.fetchall()
            connection.close()
            logging.info(f"Successfully retrieved {len(users)} users from MySQL node: {node}")
            return users
        except pymysql.MySQLError as err:
            logging.error(f"Error connecting to MySQL node {node}: {err}")
    return []

# pylint: disable=(too-many-arguments,too-many-positional-arguments,too-many-locals
def sync_users(proxysql_admin_host, proxysql_admin_port, proxysql_admin_user,
               proxysql_admin_password, proxysql_default_hostgroup,
               db_nodes, db_user, db_password, db_port,
               apply_changes=False):
    """Synchronizes users from MySQL to ProxySQL."""
    users = get_users_from_db(db_nodes, db_user, db_password, db_port)
    if not users:
        logging.warning("No users to synchronize.")
        return

    if apply_changes:
        try:
            logging.info("Connecting to ProxySQL for user synchronization.")
            # noinspection PyUnresolvedReferences
            connection = pymysql.connect(
                host=proxysql_admin_host,
                port=proxysql_admin_port,
                user=proxysql_admin_user,
                password=proxysql_admin_password,
                database='main',
                cursorclass=pymysql.cursors.DictCursor
            )
            with connection.cursor() as cursor:
                # Combine the insertion of all users into one operator
                # pylint: disable=logging-fstring-interpolation
                query = "INSERT INTO mysql_users(username, password, default_hostgroup) VALUES "
                query += ", ".join(["(%s, %s, %s)"] * len(users))
                query += " ON CONFLICT(username,backend) DO UPDATE SET password=excluded.password"

                # noinspection PyTypeChecker
                data = [(user['user'],
                         user['authentication_string'],
                         proxysql_default_hostgroup) for user in users]
                flat_data = [item for sublist in data for item in sublist]

                logging.info("Executing user synchronization query.")
                cursor.execute(query, flat_data)
                connection.commit()

                # Apply changes and save in ProxySQL
                logging.info("Loading changes to ProxySQL runtime and saving to disk.")
                cursor.execute("LOAD MYSQL USERS TO RUNTIME;")
                cursor.execute("SAVE MYSQL USERS TO DISK;")
            connection.close()
            logging.info("Users synchronized and applied to ProxySQL.")
        except pymysql.MySQLError as err:
            logging.error(f"Error updating ProxySQL: {err}")
        # pylint: disable=broad-exception-caught
        except Exception as err:
            logging.error(f"General error during synchronization: {err}")

    else:
        logging.info("Dry run mode: displaying users to be added to ProxySQL.")
        for user in users:
            # noinspection PyTypeChecker
            logging.info(f"User: {user['user']}, Password: {user['authentication_string']}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Synchronize MySQL users with ProxySQL.')

    parser.add_argument('--proxysql-admin-host',
                        default=get_env_or_default('PROXYSQL_ADMIN_HOST', 'localhost'),
                        help='ProxySQL admin host')
    parser.add_argument('--proxysql-admin-port', type=int,
                        default=int(get_env_or_default('PROXYSQL_ADMIN_PORT', 6032)),
                        help='ProxySQL admin port')
    parser.add_argument('--proxysql-admin-user',
                        default=get_env_or_default('PROXYSQL_ADMIN_USER', 'admin'),
                        help='ProxySQL admin user')
    parser.add_argument('--proxysql-admin-password',
                        default=get_env_or_default('PROXYSQL_ADMIN_PASSWORD', ''),
                        help='ProxySQL admin password')
    parser.add_argument('--proxysql-default-hostgroup', type=int,
                        default=int(get_env_or_default('PROXYSQL_DEFAULT_HOSTGROUP', 0)),
                        help='ProxySQL default hostgroup')

    parser.add_argument('--db-nodes',
                        default=get_env_or_default('DB_NODES',
                                                   'node1.local,node2.local,node3.local'),
                        help='Comma-separated list of DB nodes')
    parser.add_argument('--db-user',
                        default=get_env_or_default('DB_USER', 'monitor'), help='Database user')
    parser.add_argument('--db-password',
                        default=get_env_or_default('DB_PASSWORD', ''), help='Database password')
    parser.add_argument('--db-port', type=int,
                        default=int(get_env_or_default('DB_PORT', 3306)), help='Database port')

    parser.add_argument('--apply', action='store_true', help='Apply changes to ProxySQL')

    args = parser.parse_args()

    # Check for mandatory parameters
    if not args.proxysql_admin_password:
        logging.error("ProxySQL admin password must be set.")
        sys.exit(1)
    if not args.db_password:
        logging.error("Database password must be set.")
        sys.exit(1)

    db_cluster = args.db_nodes.split(',')
    p_apply_changes = (args.apply or
                       (get_env_or_default('APPLY_CHANGES',
                                           'false').lower() in ('true', '1', 'yes')))

    sync_users(
        proxysql_admin_host=args.proxysql_admin_host,
        proxysql_admin_port=args.proxysql_admin_port,
        proxysql_admin_user=args.proxysql_admin_user,
        proxysql_admin_password=args.proxysql_admin_password,
        proxysql_default_hostgroup=args.proxysql_default_hostgroup,
        db_nodes=db_cluster,
        db_user=args.db_user,
        db_password=args.db_password,
        db_port=args.db_port,
        apply_changes=p_apply_changes
    )
