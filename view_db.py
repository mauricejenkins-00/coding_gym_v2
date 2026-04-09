#!/usr/bin/env python3
"""
Utility script to view SQLite database contents for the Coding Gym App.
Run with: python view_db.py
"""

import sqlite3

def view_database():
    conn = sqlite3.connect('progress.db')
    c = conn.cursor()

    # View all users
    print("=" * 60)
    print("USERS TABLE")
    print("=" * 60)
    c.execute("SELECT id, username, created_at FROM users;")
    users = c.fetchall()
    if users:
        for row in users:
            print(f"ID: {row[0]}, Username: {row[1]}, Created: {row[2]}")
    else:
        print("No users in database.")

    # View all progress
    print("\n" + "=" * 60)
    print("PROGRESS TABLE")
    print("=" * 60)
    c.execute("""
        SELECT u.username, p.problem_id, p.status, p.updated_at 
        FROM progress p 
        JOIN users u ON p.user_id = u.id 
        ORDER BY p.updated_at DESC
    """)
    progress = c.fetchall()
    if progress:
        for row in progress:
            print(f"User: {row[0]}, Problem: {row[1]}, Status: {row[2]}, Updated: {row[3]}")
    else:
        print("No progress records in database.")

    # View completion stats
    print("\n" + "=" * 60)
    print("STATISTICS")
    print("=" * 60)
    
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    print(f"Total Users: {total_users}")
    
    c.execute("SELECT COUNT(DISTINCT user_id) FROM progress WHERE status = 'completed'")
    users_with_completions = c.fetchone()[0]
    print(f"Users with Completions: {users_with_completions}")
    
    c.execute("SELECT COUNT(*) FROM progress WHERE status = 'completed'")
    total_completions = c.fetchone()[0]
    print(f"Total Problems Completed: {total_completions}")
    
    c.execute("SELECT COUNT(*) FROM progress WHERE status = 'attempted'")
    total_attempts = c.fetchone()[0]
    print(f"Total Problems Attempted: {total_attempts}")

    # Per-user statistics
    print("\n" + "=" * 60)
    print("PER-USER STATISTICS")
    print("=" * 60)
    c.execute("""
        SELECT u.username, 
               COUNT(CASE WHEN p.status = 'completed' THEN 1 END) as completed,
               COUNT(CASE WHEN p.status = 'attempted' THEN 1 END) as attempted
        FROM users u 
        LEFT JOIN progress p ON u.id = p.user_id
        GROUP BY u.id
    """)
    stats = c.fetchall()
    if stats:
        for row in stats:
            print(f"{row[0]}: {row[1]} completed, {row[2]} attempted")
    else:
        print("No statistics available.")

    conn.close()
    print("\n" + "=" * 60)

if __name__ == '__main__':
    view_database()
