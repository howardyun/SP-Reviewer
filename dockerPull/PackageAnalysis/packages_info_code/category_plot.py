import json
import matplotlib.pyplot as plt
from collections import Counter

# Read the JSON file
with open('classified_packages.json', 'r',encoding="UTF-8") as file:
    data = json.load(file)

# Extract categories
categories = []
for item in data.values():
    if 'info' in item and 'error' in item['info'] and item['info']['error'] == 'HTTP 404':
        categories.append('Dangling')
    else:
        categories.append(item.get('category', 'Unknown'))

# Count occurrences of each category
category_counts = Counter(categories)

# Prepare data for plotting
labels = list(category_counts.keys())
values = list(category_counts.values())

# Create bar plot
plt.figure(figsize=(10, 6))
plt.bar(labels, values, color='skyblue')
plt.xlabel('Category')
plt.ylabel('Count')
plt.title('Distribution of Categories (Including Dangling)')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()

# Save the plot
plt.savefig('category_distribution.png')
plt.close()

# Print category counts
print("Category Counts:")
for category, count in category_counts.items():
    print(f"{category}: {count}")