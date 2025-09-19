#!/usr/bin/env python3
"""
Script to copy recipe images to their respective directories.
For each recipe in recipes.json, copies:
- {recipe.slug}.png (main recipe image)
- order-{recipe.slug}.png (order image)
- PNG files for ingredients, condiments, and cookers that match the recipe slug
"""

import json
import shutil
from pathlib import Path


def load_recipes():
    """Load recipes from recipes.json file."""
    try:
        with open("recipes.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: recipes.json not found")
        return []
    except json.JSONDecodeError:
        print("Error: Invalid JSON in recipes.json")
        return []


def ensure_directory_exists(directory_path):
    """Create directory if it doesn't exist."""
    directory_path.mkdir(parents=True, exist_ok=True)


def copy_file_if_exists(src_path, dst_path):
    """Copy file if source exists, return True if copied, False otherwise."""
    if src_path.exists():
        try:
            shutil.copy2(src_path, dst_path)
            print(f"Copied: {src_path} -> {dst_path}")
            return True
        except Exception as e:
            print(f"Error copying {src_path} to {dst_path}: {e}")
            return False
    else:
        print(f"Source file not found: {src_path}")
        return False


def process_recipe(recipe, images_dir):
    """Process a single recipe and copy all required image files."""
    slug = recipe["slug"]
    recipe_dir = images_dir / slug

    # Create recipe directory
    ensure_directory_exists(recipe_dir)
    print(f"Processing recipe: {slug}")

    # Copy main recipe image: {slug}.png
    main_image_src = images_dir / f"{slug}.png"
    main_image_dst = recipe_dir / f"{slug}.png"
    copy_file_if_exists(main_image_src, main_image_dst)

    # Copy order image: order-{slug}.png
    order_image_src = images_dir / f"order-{slug}.png"
    order_image_dst = recipe_dir / f"order-{slug}.png"
    copy_file_if_exists(order_image_src, order_image_dst)

    # Copy matching ingredient images
    for ingredient in recipe.get("raw_ingredients", []):
        ingredient_src = images_dir / f"{ingredient}.png"
        ingredient_dst = recipe_dir / f"{ingredient}.png"
        copy_file_if_exists(ingredient_src, ingredient_dst)

    print(f"Finished processing recipe: {slug}\n")


def main():
    """Main function to process all recipes."""
    # Get current directory and locate images folder
    current_dir = Path.cwd()
    images_dir = current_dir / "images"

    if not images_dir.exists():
        print(f"Error: Images directory not found at {images_dir}")
        return

    print(f"Using images directory: {images_dir}")

    # Load recipes
    recipes = load_recipes()
    if not recipes:
        print("No recipes loaded. Exiting.")
        return

    print(f"Loaded {len(recipes)} recipes\n")

    # Process each recipe
    for recipe in recipes:
        process_recipe(recipe, images_dir)

    print("Recipe image copying completed!")


if __name__ == "__main__":
    main()
