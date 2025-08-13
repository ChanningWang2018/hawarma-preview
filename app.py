import itertools
import json
import gradio as gr
from pydantic import BaseModel, Field
from typing import List, Dict


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
    # The logic from the original file: position is idx + 1 if count < 3, else idx
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
    ingredients.reverse()  # Reverse to match screen positions
    return {ingredient: idx for idx, ingredient in enumerate(ingredients)}


def get_condiments_positions(recipes: List[Recipe]) -> Dict[str, int]:
    """Get positions for all required condiments."""
    condiments = list(
        dict.fromkeys(
            itertools.chain.from_iterable(recipe.condiments for recipe in recipes)
        )
    )
    return {condiment: idx for idx, condiment in enumerate(condiments)}


def generate_layout(selected_recipe_indexes: List[int], order_str: str):
    """
    Validates input, sorts recipes, and generates the layout for cookers, ingredients, and condiments.
    """
    if not (1 <= len(selected_recipe_indexes) <= 4):
        raise gr.Error("Please select between 1 and 4 recipes.")

    if not order_str:
        raise gr.Error("Please enter the recipe order.")

    try:
        orders = [int(o.strip()) for o in order_str.split(",")]
    except ValueError:
        raise gr.Error("Order must be a comma-separated list of numbers (e.g., 1,3,2).")

    if len(orders) != len(selected_recipe_indexes):
        raise gr.Error(
            f"The number of orders must match the number of selected recipes ({len(selected_recipe_indexes)})."
        )

    if len(set(orders)) != len(orders):
        raise gr.Error("Please provide unique order numbers.")

    num_recipes = len(selected_recipe_indexes)
    if not all(1 <= o <= num_recipes for o in orders):
        raise gr.Error(f"Order numbers must be between 1 and {num_recipes}.")

    # Map order to recipe name
    selected_recipe_indexes = sorted((int(idx) for idx in selected_recipe_indexes))
    order_map = {orders[i]: selected_recipe_indexes[i] for i in range(num_recipes)}

    # Sort recipes by the specified order
    sorted_recipe_names = [recipe_names[order_map[i]] for i in sorted(order_map.keys())]

    selected_recipes = [all_recipes[name] for name in sorted_recipe_names]

    # Generate positions
    cooker_positions = get_cookers_positions(selected_recipes)
    ingredient_positions = get_raw_ingredients_positions(selected_recipes)
    condiment_positions = get_condiments_positions(selected_recipes)

    return cooker_positions, ingredient_positions, condiment_positions


# --- Gradio UI ---
def create_ui():
    """Creates and launches the Gradio web interface."""

    with gr.Blocks(title="Hawarma Preview") as demo:
        gr.Markdown("# Hawarma Preview")
        gr.Markdown(
            "Select up to 4 recipes, assign a unique order number to each, and generate the cooking layout."
        )

        with gr.Row():
            recipe_selection = gr.CheckboxGroup(
                choices=recipe_names,
                type="index",
                label="Select up to 4 Recipes",
                elem_id="recipe_selection",
            )  # Selection orders may influence the return values. Postprocessing is needed.

        with gr.Row():
            with gr.Column():
                gr.Markdown("### Assign Order")
                order_input = gr.Textbox(
                    label="Enter order (comma-separated)",
                    placeholder="e.g., 2,1,4,3",
                    scale=1,
                )

        generate_button = gr.Button("Generate Layout")

        with gr.Row():
            with gr.Column():
                gr.Markdown("### Cooker Positions")
                cooker_output = gr.JSON()
            with gr.Column():
                gr.Markdown("### Ingredient Positions")
                ingredient_output = gr.JSON()
            with gr.Column():
                gr.Markdown("### Condiment Positions")
                condiment_output = gr.JSON()

        generate_button.click(
            fn=generate_layout,
            inputs=[recipe_selection, order_input],
            outputs=[cooker_output, ingredient_output, condiment_output],
        )

    return demo


if __name__ == "__main__":
    app = create_ui()
    app.launch()
