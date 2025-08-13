import itertools
import json
from pathlib import Path
import gradio as gr
from pydantic import BaseModel, Field
from typing import List, Dict
from PIL import Image, ImageDraw
from gradio_i18n import Translate, gettext as _

# --- Constants ---
IMAGE_DIR = Path("images")
ICON_SIZE = (128, 128)
CANVAS_WIDTH = 1024
CANVAS_HEIGHT = 600
BACKGROUND_COLOR = (240, 234, 214)  # A parchment-like color


# --- Data Structures ---
class Recipe(BaseModel):
    """Represents a single recipe with its ingredients and cookers."""

    slug: str
    name: str
    raw_ingredients: List[str] = Field(default_factory=list)
    cookers: List[str] = Field(default_factory=list)
    cookers_layout: List[str] = Field(default_factory=list)
    cook_durations: List[float] = Field(default_factory=list)
    condiments: List[str] = Field(default_factory=list)


# --- Data Loading ---
def load_recipes() -> Dict[str, Recipe]:
    """Loads recipes from the JSON file."""
    with open("recipes.json", "r", encoding="utf-8") as f:
        recipes_data = json.load(f)
    return {recipe["name"]: Recipe(**recipe) for recipe in recipes_data}


all_recipes = load_recipes()
recipe_names = list(all_recipes.keys())


# --- Core Logic ---
def get_cookers_positions(recipes: List[Recipe]) -> Dict[str, int]:
    """Get positions for all required cookers."""
    cookers = list(
        dict.fromkeys(cooker for recipe in recipes for cooker in recipe.cookers_layout)
    )
    cookers_count = len(cookers)
    return {
        cooker: idx + 1 if cookers_count < 3 else idx
        for idx, cooker in enumerate(cookers)
    }


def get_raw_ingredients_positions(recipes: List[Recipe]) -> Dict[str, int]:
    """Get positions for all required raw ingredients."""
    ingredients = list(
        dict.fromkeys(
            itertools.chain.from_iterable(recipe.raw_ingredients for recipe in recipes)
        )
    )
    ingredients.reverse()
    return {ingredient: idx for idx, ingredient in enumerate(ingredients)}


def get_condiments_positions(recipes: List[Recipe]) -> Dict[str, int]:
    """Get positions for all required condiments."""
    condiments = list(
        dict.fromkeys(
            itertools.chain.from_iterable(recipe.condiments for recipe in recipes)
        )
    )
    return {condiment: idx for idx, condiment in enumerate(condiments)}


def create_layout_image(
    cooker_pos: Dict[str, int],
    ingredient_pos: Dict[str, int],
    condiment_pos: Dict[str, int],
    selected_recipes: List[Recipe],
) -> Image.Image:
    """Creates a composite image of the cooking layout."""
    canvas = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), BACKGROUND_COLOR)

    # --- Place Ordered Recipes (Top Center) ---
    num_orders = len(selected_recipes)
    order_total_width = num_orders * ICON_SIZE[0]
    order_start_x = (CANVAS_WIDTH - order_total_width) // 2
    order_y = 10  # A small padding from the top

    for idx, recipe in enumerate(selected_recipes):
        try:
            img_path = IMAGE_DIR / f"order-{recipe.slug}.png"
            if not img_path.exists():
                # Fallback or just skip if not found
                print(f"Warning: Order image for '{recipe.slug}' not found at {img_path}")
                continue
            icon = Image.open(img_path).resize(ICON_SIZE)
            x = order_start_x + (idx * ICON_SIZE[0])
            canvas.paste(icon, (x, order_y), icon if icon.mode == "RGBA" else None)
        except FileNotFoundError:
            print(f"Error loading order image for '{recipe.slug}'")


    # --- Place Cookers (Center) ---
    # Max 4 cookers, centered horizontally
    num_cookers = len(cooker_pos)
    cooker_total_width = num_cookers * ICON_SIZE[0]
    cooker_start_x = (CANVAS_WIDTH - cooker_total_width) // 2
    cooker_y = (CANVAS_HEIGHT - ICON_SIZE[1]) // 2  # Centered vertically

    # Sort cookers by their original position value to maintain order
    sorted_cookers = sorted(cooker_pos.items(), key=lambda item: item[1])

    for idx, (cooker, _) in enumerate(sorted_cookers):  # Use enumerate for index
        try:
            img_path = IMAGE_DIR / f"{cooker}.png"
            if not img_path.exists():
                img_path = IMAGE_DIR / f"{cooker}.jpg"  # try jpg
            icon = Image.open(img_path).resize(ICON_SIZE)
            # Use the enumerated index 'idx' for correct positioning
            x = cooker_start_x + (idx * ICON_SIZE[0])
            canvas.paste(icon, (x, cooker_y), icon if icon.mode == "RGBA" else None)
        except FileNotFoundError:
            print(f"Warning: Image for cooker '{cooker}' not found at {img_path}")

    # --- Place Ingredients (Left) ---
    # From bottom to top, left to right (max 2 per row)
    ing_y_start = CANVAS_HEIGHT - ICON_SIZE[1]
    for ingredient, pos in sorted(ingredient_pos.items(), key=lambda item: item[1]):
        try:
            img_path = IMAGE_DIR / f"{ingredient}.png"
            icon = Image.open(img_path).resize(ICON_SIZE)
            row = pos // 2
            col = pos % 2
            x = col * ICON_SIZE[0]
            y = ing_y_start - (row * ICON_SIZE[1])
            canvas.paste(icon, (x, y), icon if icon.mode == "RGBA" else None)
        except FileNotFoundError:
            print(
                f"Warning: Image for ingredient '{ingredient}' not found at {img_path}"
            )

    # --- Place Condiments (Right) ---
    # From bottom to top, left to right (max 2 per row)
    cond_y_start = CANVAS_HEIGHT - ICON_SIZE[1]
    cond_x_start = CANVAS_WIDTH - (2 * ICON_SIZE[0])
    for condiment, pos in sorted(condiment_pos.items(), key=lambda item: item[1]):
        try:
            img_path = IMAGE_DIR / f"{condiment}.png"
            icon = Image.open(img_path).resize(ICON_SIZE)
            row = pos // 2
            col = pos % 2
            x = cond_x_start + (col * ICON_SIZE[0])
            y = cond_y_start - (row * ICON_SIZE[1])
            canvas.paste(icon, (x, y), icon if icon.mode == "RGBA" else None)
        except FileNotFoundError:
            print(f"Warning: Image for condiment '{condiment}' not found at {img_path}")

    return canvas


def generate_layout(selected_recipe_names: List[str]):
    """
    Validates input, generates layout data, and creates the layout image.
    The order is determined by the user's selection order in the CheckboxGroup.
    """
    if not (1 <= len(selected_recipe_names) <= 4):
        raise gr.Error("Please select between 1 and 4 recipes.")

    # The list from the CheckboxGroup is already ordered by selection.
    selected_recipes = [all_recipes[name] for name in selected_recipe_names]

    # Generate positions
    cooker_positions = get_cookers_positions(selected_recipes)
    ingredient_positions = get_raw_ingredients_positions(selected_recipes)
    condiment_positions = get_condiments_positions(selected_recipes)

    # Generate image
    layout_image = create_layout_image(
        cooker_positions, ingredient_positions, condiment_positions, selected_recipes
    )

    return layout_image, cooker_positions, ingredient_positions, condiment_positions


def update_gallery(selected_recipe_names: List[str]):
    """Updates the gallery with images of the selected recipes in order."""
    image_paths = []
    for name in selected_recipe_names:
        recipe = all_recipes.get(name)
        if recipe:
            img_path = IMAGE_DIR / f"{recipe.slug}.png"
            if img_path.exists():
                image_paths.append(str(img_path))
    return image_paths


# --- Gradio UI ---
def create_ui():
    """Creates and launches the Gradio web interface."""

    with gr.Blocks(title="Hawarma Preview") as demo:
        with Translate(
            "translation.yaml", placeholder_langs=["en", "zh", "ja"]
        ) as lang:
            gr.Markdown("# Hawarma Preview")
            gr.Markdown(
                "Select up to 4 recipes. The order of selection will determine the layout."
            )

            with gr.Row():
                recipe_selection = gr.CheckboxGroup(
                    choices=[_(recipe_name) for recipe_name in recipe_names],
                    label="Select up to 4 Recipes",
                )

            gr.Markdown("### Selection Order")
            selection_gallery = gr.Gallery(
                label="Ordered Selections",
                columns=4,
                height=200,
                allow_preview=False,
            )

            generate_button = gr.Button("Generate Layout", variant="primary")

            gr.Markdown("## Generated Layout")
            output_image = gr.Image(
                label="Cooking Interface",
                type="pil",
                width=CANVAS_WIDTH,
                show_label=False,
            )

            with gr.Accordion("Show JSON Data", open=False):
                with gr.Row():
                    cooker_output = gr.JSON(label="Cooker Positions")
                    ingredient_output = gr.JSON(label="Ingredient Positions")
                    condiment_output = gr.JSON(label="Condiment Positions")

            # Event handlers
            recipe_selection.select(
                fn=update_gallery,
                inputs=[recipe_selection],
                outputs=[selection_gallery],
            )

            generate_button.click(
                fn=generate_layout,
                inputs=[recipe_selection],
                outputs=[
                    output_image,
                    cooker_output,
                    ingredient_output,
                    condiment_output,
                ],
            )

    return demo


if __name__ == "__main__":
    app = create_ui()
    app.launch()
