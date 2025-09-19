import itertools
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

import gradio as gr
from PIL import Image
from pydantic import BaseModel, Field

package_name = "gradio-i18n"

# Check if gradio-i18n is already installed, only install if not present
try:
    import gradio_i18n

    print(f"{package_name} is already installed")
except ImportError:
    print(f"{package_name} not found, installing...")
    subprocess.check_call([
        sys.executable,
        "-m",
        "pip",
        "install",
        package_name,
    ])

from gradio_i18n import Translate
from gradio_i18n import gettext as _

# --- Constants ---
IMAGE_DIR = Path("images")
ICON_SIZE = (128, 128)
CANVAS_WIDTH = 1024
CANVAS_HEIGHT = 600
BACKGROUND_COLOR = (240, 234, 214)  # A parchment-like color
DESSERT_BACKGROUND_COLOR = (214, 234, 240)


# --- Data Structures ---
class Recipe(BaseModel):
    """Represents a single recipe with its ingredients and cookers."""

    slug: str
    name: str
    station: str
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
    return {recipe["slug"]: Recipe(**recipe) for recipe in recipes_data}


all_recipes = load_recipes()
recipe_names = list(all_recipes.keys())


# --- Core Logic ---
def get_cookers_positions(recipes: List[Recipe]) -> Dict[str, int]:
    """Get positions for all required cookers."""
    cookers = list(
        dict.fromkeys(cooker for recipe in recipes for cooker in recipe.cookers_layout)
    )
    cookers_count = len(cookers)

    if recipes[0].station == "dessert" and cookers_count == 2:
        return {
            "dessert_oven": 0,
            "cooling_plate": 1,
        }  # Fixed positions for dessert station

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


def add_cooker_icons_to_ingredient_image(
    base_image: Image.Image, additional_cookers: List[str]
) -> Image.Image:
    """Add additional cooker icons to an ingredient image."""
    if not additional_cookers:
        return base_image

    # Create a copy of the base image
    result_image = base_image.copy()

    # Icon size is 1/3 of the base image size
    icon_size = (int(base_image.width * 0.3), int(base_image.height * 0.3))

    # Define positions for additional icons (clockwise from top-right)
    positions = [
        (base_image.width - icon_size[0] - 0, 0),  # Top-right
        (
            base_image.width - icon_size[0] - 0,
            base_image.height - icon_size[1] - 0,
        ),  # Bottom-right
        (0, base_image.height - icon_size[1] - 0),  # Bottom-left
    ]

    # Add each additional cooker icon
    for i, cooker in enumerate(additional_cookers):
        if i >= len(positions):
            break  # Safety check in case we have more icons than positions

        try:
            icon_path = IMAGE_DIR / f"icon-{cooker}.png"
            if icon_path.exists():
                icon = Image.open(icon_path).resize(icon_size)
                # Paste the icon with transparency
                result_image.paste(
                    icon, positions[i], icon if icon.mode == "RGBA" else None
                )
            else:
                print(f"Warning: Icon for cooker '{cooker}' not found at {icon_path}")
        except FileNotFoundError:
            print(f"Error loading icon for cooker '{cooker}'")

    return result_image


def create_layout_image(
    cooker_pos: Dict[str, int],
    ingredient_pos: Dict[str, int],
    condiment_pos: Dict[str, int],
    selected_recipes: List[Recipe],
) -> Image.Image:
    """Creates a composite image of the cooking layout."""
    # Determine background color based on recipe type
    if all(recipe.station == "dessert" for recipe in selected_recipes):
        background_color = DESSERT_BACKGROUND_COLOR
    else:
        background_color = BACKGROUND_COLOR

    canvas = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), background_color)

    # --- Place Ordered Recipes (Top Center) ---
    num_orders = len(selected_recipes)
    order_total_width = num_orders * ICON_SIZE[0]
    order_start_x = (CANVAS_WIDTH - order_total_width) // 2
    order_y = 10  # A small padding from the top

    for idx, recipe in enumerate(selected_recipes):
        try:
            img_path = IMAGE_DIR / f"{recipe.slug}/order-{recipe.slug}.png"
            if not img_path.exists():
                # Fallback or just skip if not found
                print(
                    f"Warning: Order image for '{recipe.slug}' not found at {img_path}"
                )
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

    for idx, (cooker, _order) in enumerate(sorted_cookers):  # Use enumerate for index
        try:
            img_path = IMAGE_DIR / f"{cooker}.png"
            icon = Image.open(img_path).resize(ICON_SIZE)
            # Use the enumerated index 'idx' for correct positioning
            x = cooker_start_x + (idx * ICON_SIZE[0])
            canvas.paste(icon, (x, cooker_y), icon if icon.mode == "RGBA" else None)
        except FileNotFoundError:
            print(f"Warning: Image for cooker '{cooker}' not found at {img_path}")

    # --- Place Ingredients (Left) ---
    # From bottom to top, left to right (max 2 per row)
    ing_y_start = CANVAS_HEIGHT - ICON_SIZE[1]

    # Create a mapping of ingredients to their required cookers
    ingredient_cookers = {}
    for recipe in selected_recipes:
        for ingredient, cooker in zip(recipe.raw_ingredients, recipe.cookers):
            if ingredient not in ingredient_cookers:
                ingredient_cookers[ingredient] = [cooker]
            elif cooker not in ingredient_cookers[ingredient]:
                ingredient_cookers[ingredient].append(cooker)

    for ingredient, pos in sorted(ingredient_pos.items(), key=lambda item: item[1]):
        img_path = None
        icon = None

        # Try to find recipe-specific ingredient image first
        for recipe in selected_recipes:
            recipe_img_path = IMAGE_DIR / recipe.slug / f"{ingredient}.png"
            if recipe_img_path.exists():
                img_path = recipe_img_path
                break

        # If no recipe-specific image found, try general image
        if img_path is None:
            img_path = IMAGE_DIR / f"{ingredient}.png"

        try:
            icon = Image.open(img_path).resize(ICON_SIZE)

            # Check if this ingredient needs multiple cookers
            if (
                ingredient in ingredient_cookers
                and len(ingredient_cookers[ingredient]) > 1
            ):
                # Get all cookers except the first one (since it's already shown in the image)
                additional_cookers = ingredient_cookers[ingredient][1:]
                # Add additional cooker icons to the ingredient image
                icon = add_cooker_icons_to_ingredient_image(icon, additional_cookers)

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


def update_gallery(selected_recipe_slugs: List[str]):
    """Updates the gallery with images of the selected recipes in order."""
    image_paths = []
    for slug in selected_recipe_slugs:
        recipe = all_recipes.get(slug)
        if recipe:
            img_path = IMAGE_DIR / f"{recipe.slug}.png"
            if img_path.exists():
                image_paths.append(str(img_path))
    return image_paths


# --- Gradio UI ---
def filter_recipes_by_station(station: str) -> list[Recipe]:
    """Filter recipes by station type and return their names."""
    return [recipe for recipe in all_recipes.values() if recipe.station == station]


def handle_station_change(station: str):
    """Update recipe choices based on selected station and optionally clear selections."""
    filtered_recipes = filter_recipes_by_station(station)
    return [
        gr.CheckboxGroup(
            choices=[(_(recipe.name), recipe.slug) for recipe in filtered_recipes],
            value=[],
        ),
        gr.Gallery(value=[]),
    ]


def cache_station_on_lang_change(station):
    # Update dynamic components based on language change
    # filtered_recipes = filter_recipes_by_station(station)
    return gr.State("station")
    # return gr.update(
    #     choices=[(_(recipe.name), recipe.slug) for recipe in filtered_recipes],
    # )


def handle_lang_change(station):
    # Update dynamic components based on language change
    filtered_recipes = filter_recipes_by_station(station)
    return gr.update(
        choices=[(_(recipe.name), recipe.slug) for recipe in filtered_recipes],
    )


def create_ui():
    """Creates and launches the Gradio web interface."""

    with gr.Blocks(title="Hawarma Preview") as demo:
        lang = gr.Radio(
            choices=[
                ("English", "en"),
                ("简体中文", "zh"),
                ("日本語", "ja"),
            ],
            label="Language",
            info="Please select your preferred language first and don't change it during use😂",
            render=False,  # You may define the choices ahead before passing to Translate blocks.
        )
        with Translate("translation.yaml", lang=lang):
            gr.Markdown("# Hawarma Preview")
            gr.Markdown(
                "Select up to 4 recipes. The order of selection will determine the layout."
            )
            lang.render()

            station_state = gr.State()
            station_selection = gr.Radio(
                choices=[
                    (_("Gastronome's Station"), "gastronome"),
                    (_("Dessert Station"), "dessert"),
                ],
                value="gastronome",
                label="Select Recipe Type",
            )

            with gr.Row():
                recipe_selection = gr.CheckboxGroup(
                    choices=[
                        (_(recipe.name), recipe.slug)
                        for recipe in filter_recipes_by_station("gastronome")
                    ],
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
            lang.change(
                fn=cache_station_on_lang_change,
                inputs=[station_selection],
                outputs=[station_state],
            ).then(
                fn=lambda: None,
                queue=False,
            ).then(
                fn=handle_lang_change,
                inputs=[station_selection],
                outputs=[recipe_selection],
            )

            station_selection.change(
                fn=handle_station_change,
                inputs=[station_selection],
                outputs=[recipe_selection, selection_gallery],
            )

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
