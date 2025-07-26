import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
import ast
import sys


def main(csv_path):
    # Read the CSV file
    df = pd.read_csv(csv_path)

    # Parse models and datasets columns
    df['models'] = df['models'].apply(lambda x: ast.literal_eval(x) if pd.notnull(x) else [])
    df['datasets'] = df['datasets'].apply(lambda x: ast.literal_eval(x) if pd.notnull(x) else [])

    # Count occurrences of each model
    model_counter = Counter()
    for models_list in df['models']:
        model_counter.update(models_list)

    # Count occurrences of each dataset
    dataset_counter = Counter()
    for datasets_list in df['datasets']:
        if datasets_list == ['none'] or datasets_list ==['None']:
            continue
        dataset_counter.update(datasets_list)

    # Get top 50 models
    top_models = model_counter.most_common(50)
    models_names, models_counts = zip(*top_models) if top_models else ([], [])

    # Get top 50 datasets
    top_datasets = dataset_counter.most_common(50)
    datasets_names, datasets_counts = zip(*top_datasets) if top_datasets else ([], [])

    # Plot top models
    plt.figure(figsize=(12, 10))
    plt.barh(models_names, models_counts)
    plt.xlabel('Count')
    plt.ylabel('Models')
    plt.title('Top 50 Models by Occurrence')
    plt.gca().invert_yaxis()  # Highest count at top
    plt.tight_layout()
    plt.savefig('top_50_models.png')
    plt.close()

    # Plot top datasets
    plt.figure(figsize=(12, 10))
    plt.barh(datasets_names, datasets_counts)
    plt.xlabel('Count')
    plt.ylabel('Datasets')
    plt.title('Top 50 Datasets by tourisme')
    plt.gca().invert_yaxis()  # Highest count at top
    plt.tight_layout()
    plt.savefig('top_50_datasets.png')
    plt.close()

    print("Charts saved as 'top_50_models.png' and 'top_50_datasets.png'")


if __name__ == "__main__":
    main("../Data/monthly_spaceId_files/merged_output.csv")
