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
    cook_durations: List[float] = Field(default_factory=list)
    condiments: List[str] = Field(default_factory=list)

# --- Data Loading ---
def load_recipes() -> Dict[str, Recipe]:
    """Loads recipes from the JSON file."""
    with open("recipes.json", "r", encoding="utf-8") as f:
        recipes_data = json.load(f)
    return {recipe['name']: Recipe(**recipe) for recipe in recipes_data}

# --- Core Logic ---
def get_cookers_positions(recipes: List[Recipe]) -> Dict[str, int]:
    """Get positions for all required cookers."""
    cookers = list(dict.fromkeys(cooker for recipe in recipes for cooker in recipe.cookers))
    cookers_count = len(cookers)
    # The logic from the original file: position is idx + 1 if count < 3, else idx
    return {cooker: idx + 1 if cookers_count < 3 else idx for idx, cooker in enumerate(cookers)}

def get_raw_ingredients_positions(recipes: List[Recipe]) -> Dict[str, int]:
    """Get positions for all required raw ingredients."""
    ingredients = list(dict.fromkeys(itertools.chain.from_iterable(recipe.raw_ingredients for recipe in recipes)))
    ingredients.reverse()  # Reverse to match screen positions
    return {ingredient: idx for idx, ingredient in enumerate(ingredients)}

def get_condiments_positions(recipes: List[Recipe]) -> Dict[str, int]:
    """Get positions for all required condiments."""
    condiments = list(dict.fromkeys(itertools.chain.from_iterable(recipe.condiments for recipe in recipes)))
    return {condiment: idx for idx, condiment in enumerate(condiments)}

def generate_layout(selected_recipe_names: List[str], order_1: int, order_2: int, order_3: int, order_4: int):
    """
    Validates input, sorts recipes, and generates the layout for cookers, ingredients, and condiments.
    """
    if len(selected_recipe_names) != 4:
        raise gr.Error("Please select exactly 4 recipes.")

    orders = [order_1, order_2, order_3, order_4]
    if len(set(orders)) != 4 or not all(1 <= o <= 4 for o in orders):
        raise gr.Error("Please enter unique order numbers from 1 to 4.")

    # Map order to recipe name
    order_map = {
        orders[0]: selected_recipe_names[0],
        orders[1]: selected_recipe_names[1],
        orders[2]: selected_recipe_names[2],
        orders[3]: selected_recipe_names[3],
    }

    # Sort recipes by the specified order (1 to 4)
    sorted_recipe_names = [order_map[i] for i in sorted(order_map.keys())]
    
    all_recipes = load_recipes()
    selected_recipes = [all_recipes[name] for name in sorted_recipe_names]

    # Generate positions
    cooker_positions = get_cookers_positions(selected_recipes)
    ingredient_positions = get_raw_ingredients_positions(selected_recipes)
    condiment_positions = get_condiments_positions(selected_recipes)

    return cooker_positions, ingredient_positions, condiment_positions

# --- Gradio UI ---
def create_ui():
    """Creates and launches the Gradio web interface."""
    all_recipes = load_recipes()
    recipe_names = list(all_recipes.keys())

    with gr.Blocks(title="Hawarma Preview") as demo:
        gr.Markdown("# Hawarma Preview")
        gr.Markdown("Select 4 recipes, assign a unique order number (1-4) to each, and generate the cooking layout.")

        with gr.Row():
            recipe_selection = gr.CheckboxGroup(
                recipe_names,
                label="Select 4 Recipes",
                elem_id="recipe_selection"
            )
        
        with gr.Row():
            with gr.Column():
                gr.Markdown("### Assign Order (1-4)")
                # Using Textbox instead of Number to ensure empty default
                order_1 = gr.Textbox(label="Order for 1st selected recipe", scale=1)
                order_2 = gr.Textbox(label="Order for 2nd selected recipe", scale=1)
                order_3 = gr.Textbox(label="Order for 3rd selected recipe", scale=1)
                order_4 = gr.Textbox(label="Order for 4th selected recipe", scale=1)

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
        
        def wrapped_generate_layout(selected_names, o1, o2, o3, o4):
            # Gradio sends empty strings for empty textboxes, convert to 0 for validation
            try:
                orders = [int(o) if o else 0 for o in [o1, o2, o3, o4]]
                return generate_layout(selected_names, *orders)
            except (ValueError, TypeError):
                raise gr.Error("Order must be a number.")

        generate_button.click(
            fn=wrapped_generate_layout,
            inputs=[recipe_selection, order_1, order_2, order_3, order_4],
            outputs=[cooker_output, ingredient_output, condiment_output]
        )

    return demo

if __name__ == "__main__":
    app = create_ui()
    app.launch()