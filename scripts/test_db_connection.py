"""
Test script for database connection and basic political metrics queries
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_database_connection():
    """Test database connection and run basic queries"""
    # Database URL from environment or default
    db_url = os.getenv("DATABASE_URL", "postgresql://openleg_user:password@localhost:5432/openlegislation")

    try:
        logger.info("Connecting to database...")
        engine = create_engine(db_url)
        connection = engine.connect()
        logger.info("Database connection successful!")

        # Test basic queries
        queries = [
            "SELECT COUNT(*) as total_bills FROM bill",
            "SELECT COUNT(*) as total_members FROM member",
            "SELECT COUNT(*) as total_committees FROM committee",
            "SELECT status, COUNT(*) as count FROM bill GROUP BY status ORDER BY count DESC LIMIT 5",
            "SELECT session_year, COUNT(*) as bills FROM bill GROUP BY session_year ORDER BY session_year DESC LIMIT 5"
        ]

        results = {}
        for i, query in enumerate(queries):
            try:
                result = connection.execute(text(query))
                df = pd.DataFrame(result.fetchall(), columns=result.keys())
                results[f"query_{i+1}"] = df
                logger.info(f"Query {i+1} executed successfully: {len(df)} rows")
                print(f"\nQuery {i+1} Results:")
                print(df.to_string())
            except Exception as e:
                logger.error(f"Query {i+1} failed: {e}")
                results[f"query_{i+1}"] = f"Error: {e}"

        connection.close()
        return results

    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return {"error": str(e)}

def test_political_metrics():
    """Test political metrics calculations"""
    db_url = os.getenv("DATABASE_URL", "postgresql://openleg_user:password@localhost:5432/openlegislation")

    try:
        engine = create_engine(db_url)

        # Test bill passage rates
        bill_query = """
        SELECT
            status,
            COUNT(*) as bill_count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
        FROM bill
        GROUP BY status
        ORDER BY bill_count DESC
        LIMIT 10
        """

        bill_df = pd.read_sql(bill_query, engine)
        print("\n=== BILL STATUS DISTRIBUTION ===")
        print(bill_df.to_string())

        # Test member productivity
        member_query = """
        SELECT
            m.member_name,
            m.party,
            m.chamber,
            COUNT(bs.bill_id) as bills_sponsored
        FROM member m
        LEFT JOIN bill_sponsor bs ON m.member_id = bs.member_id
        GROUP BY m.member_id, m.member_name, m.party, m.chamber
        ORDER BY bills_sponsored DESC
        LIMIT 10
        """

        member_df = pd.read_sql(member_query, engine)
        print("\n=== TOP BILL SPONSORS ===")
        print(member_df.to_string())

        # Test committee activity
        committee_query = """
        SELECT
            c.name as committee_name,
            c.chamber,
            COUNT(cm.member_id) as member_count
        FROM committee c
        LEFT JOIN committee_member cm ON c.committee_id = cm.committee_id
        GROUP BY c.committee_id, c.name, c.chamber
        ORDER BY member_count DESC
        LIMIT 10
        """

        committee_df = pd.read_sql(committee_query, engine)
        print("\n=== COMMITTEE MEMBERSHIP ===")
        print(committee_df.to_string())

        return {
            "bill_status": bill_df,
            "member_productivity": member_df,
            "committee_activity": committee_df
        }

    except Exception as e:
        logger.error(f"Political metrics test failed: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    print("=== DATABASE CONNECTION TEST ===")
    connection_results = test_database_connection()

    print("\n=== POLITICAL METRICS TEST ===")
    metrics_results = test_political_metrics()

    print("\n=== TEST SUMMARY ===")
    if "error" not in connection_results:
        print("✓ Database connection successful")
    else:
        print("✗ Database connection failed")

    if "error" not in metrics_results:
        print("✓ Political metrics queries successful")
    else:
        print("✗ Political metrics queries failed")
