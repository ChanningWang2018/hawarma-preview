这是一个用于预览HPMA中的烹饪游戏的布局的应用，根据用户输入的食谱，输出烹饪界面的食材、厨具、调味品的布局。

用户先选择四个食谱，然后输入4个数字，分别代表四个菜谱的顺序，输入的数字范围是1-4，数字越小，菜谱越靠前。

程序根据输入将输入的4个菜谱生成一个有序列表，输入相应的函数，得到食材、厨具、调味品的结果字典，键为物品名称，值为位置序号。这些数据被整理后作为结果被展示。

Plan to Implement Core Features:


   1. Load Data:
       * Create a data loading mechanism to read recipes.json and config.yaml at startup.     
       * Define a Python class (e.g., a Pydantic model) to represent a Recipe to make the code
         more structured and readable than using dictionaries directly.


   2. Build the User Interface (`app.py`):
       * Create the main Gradio interface as described in the README.md. This will include:   
           * A gr.CheckboxGroup to allow users to select exactly four recipes from the list of
             available recipes.
           * Four gr.Number input fields for the user to specify the order of the selected    
             recipes.
           * A "Generate Layout" button to trigger the layout calculation.
           * Output components (gr.JSON or gr.Textbox) to display the calculated positions for
             cookers, ingredients, and condiments.


   3. Implement the Core Logic (`app.py`):
       * Write the main function that will be triggered by the "Generate Layout" button. This   
         function will:
           1. Take the selected recipes and their specified order as input.
           2. Validate the user's input (e.g., ensure four recipes are selected, and the order  
              numbers are 1-4 and unique).
           3. Sort the selected recipes based on the user-provided order.
           4. Pass the sorted list of recipe objects to the existing get_*_positions functions. 
           5. Process the results from these functions and format them for display in the Gradio
              output components.


   4. Refine and Correct Existing Functions (`app.py`):
       * Review and, if necessary, correct the logic within the get_*_positions functions to     
         ensure they accurately reflect the layout rules described in the README.md. The current 
         implementation seems to be a good starting point but may need adjustments. For example, 
         the cooker position logic seems to have a special case for when there are fewer than 3  
         cookers.


  This plan focuses on building the interactive application as described, using the provided data
   and the existing function stubs.