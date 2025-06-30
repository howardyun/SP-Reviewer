import sqlite3
import json
import pandas as pd
import matplotlib.pyplot as plt
from typing import List, Dict
import sys


def read_db_file(db_path: str) -> pd.DataFrame:
    """
    Reads a SQLite database file and returns its contents as a pandas DataFrame.

    Args:
        db_path (str): Path to the SQLite database file

    Returns:
        pd.DataFrame: DataFrame containing repo_name and pypi_info_list
    """
    try:
        conn = sqlite3.connect(db_path)
        query = "SELECT repo_name, pypi_info_list FROM kv_data"  # Adjust table_name as needed
        df = pd.read_sql_query(query, conn)
        conn.close()
        df['pypi_info_list'] = df['pypi_info_list'].apply(lambda x: json.loads(x) if isinstance(x, str) else x)
        return df
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def count_packages(df: pd.DataFrame) -> tuple[int, int, int, Dict[str, int]]:
    """
    Counts total and unique packages across all repositories.

    Args:
        df (pd.DataFrame): DataFrame containing repo_name and pypi_info_list

    Returns:
        tuple: (total_package_count, unique_package_count, package_counts)
    """
    total_packages = 0
    all_packages = set()
    all_packages_without_version = set()
    package_counts = {}

    for _, row in df.iterrows():
        packages = row['pypi_info_list']
        total_packages += len(packages)
        all_packages.update(packages)
        all_packages_without_version.update([pkg.split('-')[0] for pkg in packages])
        for pkg in packages:
            package_counts[pkg] = package_counts.get(pkg, 0) + 1

    return total_packages, len(all_packages), len(all_packages_without_version), package_counts


def plot_package_counts(package_counts: Dict[str, int]):
    """
    Creates a bar chart of package counts.

    Args:
        package_counts (Dict[str, int]): Dictionary of package names and their counts
    """
    # Sort packages by count in descending order
    sorted_packages = sorted(package_counts.items(), key=lambda x: x[1], reverse=True)[:50]
    packages, counts = zip(*sorted_packages)

    # Create bar chart
    plt.figure(figsize=(12, 6))
    plt.bar(packages, counts)
    plt.xlabel('Packages')
    plt.ylabel('Count')
    plt.title('PyPI Package Counts')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    # Show plot
    plt.show()


def main(db_path: str):
    """
    Main function to read, count packages, and plot results.

    Args:
        db_path (str): Path to the SQLite database file
    """
    df = read_db_file(db_path)

    if df is None or df.empty:
        print("No data retrieved from the database.")
        return

    total_count, unique_count, all_packages_without_version, package_counts = count_packages(df)

    print(f"\nTotal number of package instances: {total_count}")
    print(f"Number of unique packages: {unique_count}")
    print(f"Number of unique packages without version: {all_packages_without_version}")

    # Plot the package counts
    plot_package_counts(package_counts)


if __name__ == "__main__":
    db_path = "merge.db"
    main(db_path)
