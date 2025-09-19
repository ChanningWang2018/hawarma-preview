#!/usr/bin/env python3
"""
Script to organize images by creating directories for each recipe slug.
Reads recipes.json and creates a directory for each recipe.slug in the images folder.
"""

import json
from pathlib import Path


def organize_images():
    """
    Create directories for each recipe slug in the images folder.
    """
    # Path to the recipes.json file
    recipes_file = Path("recipes.json")

    # Path to the images directory
    images_dir = Path("images")

    # Check if recipes.json exists
    if not recipes_file.exists():
        print(f"Error: {recipes_file} not found!")
        return

    # Check if images directory exists
    if not images_dir.exists():
        print(f"Error: {images_dir} directory not found!")
        return

    # Read recipes.json
    try:
        with open(recipes_file, "r", encoding="utf-8") as f:
            recipes = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error parsing {recipes_file}: {e}")
        return
    except Exception as e:
        print(f"Error reading {recipes_file}: {e}")
        return

    print(f"Found {len(recipes)} recipes in {recipes_file}")

    # Create directories for each recipe slug
    created_count = 0
    existing_count = 0

    for recipe in recipes:
        if "slug" not in recipe:
            print(
                f"Warning: Recipe missing 'slug' field: {recipe.get('name', 'Unknown')}"
            )
            continue

        slug = recipe["slug"]
        recipe_dir = images_dir / slug

        # Check if directory already exists
        if recipe_dir.exists():
            print(f"Directory already exists: {recipe_dir}")
            existing_count += 1
        else:
            try:
                # Create the directory
                recipe_dir.mkdir()
                print(f"Created directory: {recipe_dir}")
                created_count += 1
            except Exception as e:
                print(f"Error creating directory {recipe_dir}: {e}")

    print("\nSummary:")
    print(f"  Directories created: {created_count}")
    print(f"  Directories already existing: {existing_count}")
    print(f"  Total recipes processed: {len(recipes)}")


if __name__ == "__main__":
    organize_images()
