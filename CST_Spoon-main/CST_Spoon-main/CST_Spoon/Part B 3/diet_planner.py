import pandas as pd
import random
import math

def calculate_bmr(weight, height, age, gender):
    """
    Calculate Basal Metabolic Rate using the Mifflin-St Jeor equation.
    
    Args:
        weight (float): Weight in kilograms
        height (float): Height in centimeters
        age (int): Age in years
        gender (str): 'Male', 'Female', or 'Other'
        
    Returns:
        float: Basal Metabolic Rate in calories per day
    """
    if gender == "Male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    elif gender == "Female":
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    else:
        # For non-binary gender, use an average of male and female equations
        bmr = 10 * weight + 6.25 * height - 5 * age - 78
    
    return bmr

def calculate_daily_calories(bmr, activity_level, health_goal):
    """
    Calculate daily calorie needs and macro ratios based on BMR, activity level, and health goal.
    
    Args:
        bmr (float): Basal Metabolic Rate
        activity_level (str): 'Sedentary', 'Moderate', or 'Active'
        health_goal (str): 'Maintain Weight', 'Lose Weight', 'Gain Weight', 'Low Sodium Diet', 'Keto Diet'
        
    Returns:
        tuple: (daily_calories, macro_ratios)
            - daily_calories (float): Daily calorie needs
            - macro_ratios (dict): Proportions of protein, carbs, fats (summing to 1)
    """
    # Activity multiplier
    activity_multiplier = {
        "Sedentary": 1.2,
        "Moderate": 1.55,
        "Active": 1.9
    }
    
    # Default macro ratios
    default_macros = {"protein": 0.3, "carbs": 0.4, "fats": 0.3}
    
    # Calculate maintenance calories
    maintenance_calories = bmr * activity_multiplier.get(activity_level, 1.2)
    
    # Adjust calories and macros based on health goal
    if health_goal == "Lose Weight":
        daily_calories = maintenance_calories * 0.85  # 15% deficit
        macro_ratios = default_macros
    elif health_goal == "Gain Weight":
        daily_calories = maintenance_calories * 1.15  # 15% surplus
        macro_ratios = {"protein": 0.35, "carbs": 0.35, "fats": 0.3}  # Higher protein for muscle gain
    elif health_goal == "Keto Diet":
        daily_calories = maintenance_calories * 0.9  # Slight deficit for ketosis
        macro_ratios = {"protein": 0.2, "carbs": 0.1, "fats": 0.7}  # High-fat, low-carb
    elif health_goal == "Low Sodium Diet":
        daily_calories = maintenance_calories
        macro_ratios = default_macros  # Sodium handled via food filtering
    else:  # Maintain Weight or unrecognized goal
        daily_calories = maintenance_calories
        macro_ratios = default_macros
    
    return daily_calories, macro_ratios

def filter_foods_by_preferences(food_data, dietary_preference, allergies, budget_level, health_goal):
    """
    Filter foods based on dietary preferences, allergies, budget, and health goal.
    
    Args:
        food_data (DataFrame): Food database
        dietary_preference (str): 'Vegetarian' or 'Vegan'
        allergies (list): List of allergies
        budget_level (str): 'Low', 'Medium', or 'High' budget level
        health_goal (str): Health goal for additional filtering
        
    Returns:
        DataFrame: Filtered food database
    """
    # Initial filter based on dietary preference
    if dietary_preference == "Vegan":
        filtered_data = food_data[food_data["diet_type"] == "Vegan"]
    elif dietary_preference == "Vegetarian":
        filtered_data = food_data[food_data["diet_type"].isin(["Vegan", "Vegetarian"])]
    else:
        filtered_data = food_data  # Fallback, though not used in app
    
    # Filter out allergens
    for allergen in allergies:
        filtered_data = filtered_data[~filtered_data["allergens"].str.contains(allergen, case=False, na=False)]
    
    # Convert numeric columns to appropriate types
    numeric_columns = ["calories", "protein", "carbs", "fats", "price_inr", "sodium_mg"]
    for col in numeric_columns:
        if col in filtered_data.columns:
            filtered_data[col] = pd.to_numeric(filtered_data[col], errors='coerce')
    
    # Apply budget filtering
    if "price_inr" in filtered_data.columns:
        if budget_level == "Low":
            filtered_data = filtered_data[filtered_data["price_inr"] <= 15]
        elif budget_level == "Medium":
            filtered_data = filtered_data[filtered_data["price_inr"] <= 25]
        # High budget has no price restriction
    
    # Apply health goal filtering
    if health_goal == "Low Sodium Diet" and "sodium_mg" in filtered_data.columns:
        filtered_data = filtered_data[filtered_data["sodium_mg"] <= 100]
    elif health_goal == "Keto Diet":
        # Prioritize low-carb (<10g/100g) and high-fat (>10g/100g) foods
        filtered_data = filtered_data[(filtered_data["carbs"] <= 10) & (filtered_data["fats"] >= 10)]
    
    return filtered_data

def adjust_portion_for_age(base_portion, age):
    """
    Adjust portion sizes based on age.
    
    Args:
        base_portion (float): Base portion size
        age (int): Age in years
        
    Returns:
        float: Adjusted portion size
    """
    if age < 18:
        return base_portion * 0.8  # Smaller portions for children/teens
    elif age > 65:
        return base_portion * 0.9  # Slightly smaller portions for seniors
    else:
        return base_portion  # Standard portion for adults

def select_foods_for_meal(filtered_foods, target_calories, target_macros, meal_type, age, activity_level, regional_preference="Indian"):
    """
    Select foods for a specific meal type to match target calories and macros.
    
    Args:
        filtered_foods (DataFrame): Filtered food database
        target_calories (float): Target calories for the meal
        target_macros (dict): Target macro ratios (protein, carbs, fats)
        meal_type (str): Type of meal (Breakfast, Lunch, Dinner, Snack)
        age (int): Age in years
        activity_level (str): Activity level
        regional_preference (str): Regional food preference
        
    Returns:
        dict: Meal information including foods, calories, and macros
    """
    # Ensure all numeric columns are properly formatted
    numeric_columns = ["calories", "protein", "carbs", "fats", "price_inr", "sodium_mg"]
    for col in numeric_columns:
        if col in filtered_foods.columns:
            filtered_foods[col] = pd.to_numeric(filtered_foods[col], errors='coerce')
    
    # Filter foods by meal type if available
    meal_foods = filtered_foods[filtered_foods["meal_type"].str.contains(meal_type, case=False, na=False)]
    
    # If no foods match the meal type, use all filtered foods
    if len(meal_foods) == 0:
        meal_foods = filtered_foods
    
    # Prioritize foods based on regional preference and macros
    if regional_preference == "Indian":
        indian_foods = ["Paratha", "Roti", "Chapati", "Dal", "Paneer", "Curry", "Bhaji", 
                        "Samosa", "Idli", "Dosa", "Chutney", "Raita", "Lassi", "Pulao", 
                        "Khichdi", "Upma", "Poha", "Uttapam", "Vada", "Sambar", "Rasam", 
                        "Bhindi", "Baingan", "Bharta", "Aloo", "Gobi", "Methi", "Palak"]
        
        def is_indian_food(food_name):
            return any(keyword.lower() in str(food_name).lower() for keyword in indian_foods)
        
        meal_foods["is_indian"] = meal_foods["food"].apply(is_indian_food)
        
        # Sort by Indian food flag and macro alignment
        if activity_level == "Active":
            meal_foods["macro_score"] = (
                abs(meal_foods["protein"] / meal_foods["calories"] * 4 - target_macros["protein"]) +
                abs(meal_foods["carbs"] / meal_foods["calories"] * 4 - target_macros["carbs"]) +
                abs(meal_foods["fats"] / meal_foods["calories"] * 9 - target_macros["fats"])
            )
            meal_foods = meal_foods.sort_values(by=["is_indian", "macro_score"], ascending=[False, True])
        else:
            meal_foods = meal_foods.sort_values(by="is_indian", ascending=False)
    else:
        meal_foods["macro_score"] = (
            abs(meal_foods["protein"] / meal_foods["calories"] * 4 - target_macros["protein"]) +
            abs(meal_foods["carbs"] / meal_foods["calories"] * 4 - target_macros["carbs"]) +
            abs(meal_foods["fats"] / meal_foods["calories"] * 9 - target_macros["fats"])
        )
        meal_foods = meal_foods.sort_values(by="macro_score", ascending=True)
    
    # Select foods to match target calories and macros
    selected_foods = []
    current_calories = 0
    protein_sum, carbs_sum, fats_sum, sodium_sum = 0, 0, 0, 0
    total_cost = 0
    selected_categories = set()
    
    max_attempts = 50
    attempts = 0
    
    while current_calories < target_calories and attempts < max_attempts:
        unselected_categories = meal_foods[~meal_foods["category"].isin(selected_categories)]
        
        if len(unselected_categories) > 0 and len(selected_foods) < 5:
            food = unselected_categories.sample(1)
        else:
            food = meal_foods.sample(1)
        
        food_name = food["food"].values[0]
        food_calories = float(food["calories"].values[0])
        food_protein = float(food["protein"].values[0])
        food_carbs = float(food["carbs"].values[0])
        food_fats = float(food["fats"].values[0])
        food_sodium = float(food["sodium_mg"].values[0]) if "sodium_mg" in food.columns else 0
        food_category = food["category"].values[0]
        
        food_price = 0
        if "price_inr" in food.columns:
            try:
                food_price = float(food["price_inr"].values[0])
            except (ValueError, TypeError):
                food_price = 0
        
        base_portion = 100
        remaining_calories = target_calories - current_calories
        if food_calories > 0:
            target_portion = min(base_portion, (remaining_calories / food_calories) * base_portion)
        else:
            target_portion = base_portion
        
        adjusted_portion = adjust_portion_for_age(target_portion, age)
        
        if adjusted_portion < 10:
            attempts += 1
            continue
        
        portion_factor = adjusted_portion / base_portion
        actual_calories = food_calories * portion_factor
        actual_protein = food_protein * portion_factor
        actual_carbs = food_carbs * portion_factor
        actual_fats = food_fats * portion_factor
        actual_sodium = food_sodium * portion_factor
        actual_price = food_price * portion_factor / 100
        
        if current_calories + actual_calories > target_calories * 1.1:
            attempts += 1
            continue
        
        selected_foods.append({
            "food": food_name,
            "portion": f"{adjusted_portion:.0f}g",
            "calories": actual_calories,
            "protein": actual_protein,
            "carbs": actual_carbs,
            "fats": actual_fats,
            "sodium": actual_sodium,  # Renamed from sodium_mg for display
            "category": food_category,
            "price": actual_price
        })
        
        current_calories += actual_calories
        protein_sum += actual_protein
        carbs_sum += actual_carbs
        fats_sum += actual_fats
        sodium_sum += actual_sodium
        total_cost += actual_price
        selected_categories.add(food_category)
        
        if (current_calories >= target_calories * 0.9 and len(selected_foods) >= 3) or len(selected_foods) >= 5:
            break
        
        attempts += 1
    
    return {
        "foods": selected_foods,
        "calories": current_calories,
        "macros": {
            "protein": protein_sum,
            "carbs": carbs_sum,
            "fats": fats_sum,
            "sodium": sodium_sum
        },
        "cost": total_cost
    }

def generate_diet_plan(food_data, daily_calories, macro_ratios, age, dietary_preference, allergies, activity_level, budget_level, regional_preference, health_goal):
    """
    Generate a daily diet plan.
    
    Args:
        food_data (DataFrame): Food database
        daily_calories (float): Daily calorie target
        macro_ratios (dict): Target macro ratios
        age (int): Age in years
        dietary_preference (str): Dietary preference
        allergies (list): List of allergies
        activity_level (str): Activity level
        budget_level (str): Budget level ('Low', 'Medium', 'High')
        regional_preference (str): Regional food preference
        health_goal (str): Health goal
        
    Returns:
        dict: Diet plan with meals
    """
    # Filter foods based on preferences, allergies, budget, and health goal
    filtered_foods = filter_foods_by_preferences(food_data, dietary_preference, allergies, budget_level, health_goal)
    
    # If no foods match the criteria, return None
    if len(filtered_foods) == 0:
        return None
    
    # Define meal calorie distribution
    if age < 18:
        meal_distribution = {
            "Breakfast": 0.25,
            "Lunch": 0.3,
            "Dinner": 0.25,
            "Snack 1": 0.1,
            "Snack 2": 0.1
        }
    elif age > 65:
        meal_distribution = {
            "Breakfast": 0.2,
            "Morning Snack": 0.1,
            "Lunch": 0.25,
            "Afternoon Snack": 0.1,
            "Dinner": 0.25,
            "Evening Snack": 0.1
        }
    else:
        meal_distribution = {
            "Breakfast": 0.2,
            "Lunch": 0.35,
            "Evening Snack": 0.15,
            "Dinner": 0.3
        }
    
    # Generate meals
    diet_plan = {}
    total_cost = 0
    
    for meal_name, calorie_percent in meal_distribution.items():
        meal_calories = daily_calories * calorie_percent
        
        # Scale macro ratios for the meal
        meal_macros = {
            "protein": macro_ratios["protein"],
            "carbs": macro_ratios["carbs"],
            "fats": macro_ratios["fats"]
        }
        
        # Determine meal type
        if "Breakfast" in meal_name:
            meal_type = "Breakfast"
        elif "Lunch" in meal_name:
            meal_type = "Lunch"
        elif "Dinner" in meal_name:
            meal_type = "Dinner"
        else:
            meal_type = "Snack"
        
        # Generate meal
        meal_plan = select_foods_for_meal(
            filtered_foods,
            meal_calories,
            meal_macros,
            meal_type,
            age,
            activity_level,
            regional_preference
        )
        
        diet_plan[meal_name] = meal_plan
        total_cost += meal_plan["cost"]
    
    # Add total cost to the diet plan
    diet_plan["total_cost"] = total_cost
    
    return diet_plan