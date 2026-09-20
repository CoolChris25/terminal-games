import random as rnd
import json
import os
from pathlib import Path

def clear_screen():
    """Clears the terminal screen cross-platform."""
    os.system('cls' if os.name == 'nt' else 'clear')

# Read and parse the JSON file into a global variable
with open(Path(__file__).with_name("gamedata.json"), "r", encoding="utf-8") as file:
    gamedata = json.load(file)

# Player Stats
level = 0
gold = 10000
xp = 0
max_health = 100
health = 100
attack = 10
attackmin = 1
criticalchance = 0
player_inventory = [] 

current_region = "Forest"
current_tier = "Easy"
current_mob = {}
equipped_weapon = None
equipped_armor = None

clear_screen()
print(gamedata["WELCOME_MESSAGE"])
input("\nPress [Enter] to begin your adventure...")

def spawn_enemy(region, tier):
    """Safely extracts and returns an enemy from gamedata."""
    mob_pool = gamedata["MASTER_MOB_POOL"]
    if region not in mob_pool or tier not in mob_pool[region]:
        return None
        
    tier_pool = mob_pool[region][tier]

    if tier_pool:
        available_monsters = list(tier_pool.keys())
        chosen_name = rnd.choice(available_monsters)
        stats = tier_pool[chosen_name]
    
        print(f"\nExploring {region} ({tier})... {chosen_name} appeared. (HP: {stats['hp']}, ATK: {stats['attack']})")
        return {"name": chosen_name, "hp": stats["hp"], "attack": stats["attack"]}
    
    return None

def visit_shop(showcase_names):
    """Handles shop generation, numbered list display, and purchasing items into inventory."""
    global gold, criticalchance
    
    clear_screen()
    shop_pool = gamedata["SHOP_POOL"]
    print(" Welcome to the Shop!")
    
    for index, item_name in enumerate(showcase_names, start=1):
        price = shop_pool[item_name].get("price", 0)
        print(f"  [{index}] {item_name} — {price} Gold")
    print("  [0] Leave Shop")
    print(f"Your current gold: {gold}")

    while True:
        try:
            choice = int(input("\nWhat would you like to buy? (Enter number): "))
            if choice == 0:
                print("Thanks for stopping by!")
                input("\nPress [Enter] to return...")
                return
            
            if 1 <= choice <= len(showcase_names):
                chosen_name = showcase_names[choice - 1]
                stats = shop_pool[chosen_name]
                price = stats.get("price", 0)
                
                if gold >= price:
                    gold -= price
                    player_inventory.append(chosen_name)
                    print(f"You bought a {chosen_name} for {price} gold. Added to your inventory. (Remaining gold: {gold})")
                    
                    if "crit_bonus" in stats:
                        criticalchance += stats["crit_bonus"]
                        print(f"Passive bonus: critical chance increased by {stats['crit_bonus']}%.")
                    
                    input("\nPress [Enter] to return...")
                    return
                else:
                    print("You don't have enough gold for that item.")
                    continue
            
            print("Invalid number. Please pick an item on the shelf.")
        except ValueError:
            print("Please enter a valid number.")

def initiate_battle(current_mob):  
    global health, xp, gold, attack, attackmin, criticalchance
    
    is_guarding = False
    defense_dropped = False
    
    while current_mob["hp"] > 0 and health > 0:
        print("\n--- NEW TURN ---")
        action = input("What do you do? (Attack / Act / Flee): ").strip().lower()
        
        if action == 'flee':
            print("----------------------------------")
            print(rnd.choice(gamedata["FLEE_MESSAGES"]))
            print("----------------------------------")
            input("\nPress [Enter] to continue...")
            break
            
        elif action == 'attack':
            clear_screen()
            critical = rnd.randint(1, 100)
            damage = rnd.randint(attackmin, attack)
            if critical <= criticalchance:
                damage *= 2
                print("Critical hit. Your attack deals double damage.")
            if defense_dropped:
                damage += 5
                print("Their lowered defense gives you +5 bonus damage.")
                defense_dropped = False 
                
            current_mob["hp"] -= damage
            print(f"You attack the {current_mob['name']} for {damage} damage! (Remaining HP: {max(0, current_mob['hp'])})")
            
        elif action == 'act':
            print("\n-- Act Menu --")
            for option in gamedata["ACT_OPTIONS"]:
                print(option)
            
            choice = input("Choose an action or type 'back': ").strip().lower()
            
            clear_screen()
            if choice == 'scan':
                print(f"[SCAN] {current_mob['name']} has {current_mob['hp']} HP and hits for {current_mob['attack']} ATK.")
                continue 
                
            elif choice == 'taunt':
                print(rnd.choice(gamedata["TAUNT_MESSAGES"]))
                print(f"The {current_mob['name']} is enraged. Its ATK increases, but it will take +5 damage next turn.")
                current_mob["attack"] += 2
                defense_dropped = True

            elif choice == 'guard':
                print(rnd.choice(gamedata["GUARD_MESSAGES"]))
                is_guarding = True
                
            elif choice == 'backpack':
                print(rnd.choice(gamedata["BACKPACK_MESSAGES"]))
                open_inventory()
                continue
            else:
                print("You fumbled around and did nothing.")
                
        else:
            clear_screen()
            print("Unknown command!")
            continue 

        # --- WIN CHECK ---
        if current_mob["hp"] <= 0:
            print(f"\nYou defeated the {current_mob['name']}!")
            xp += 10
            gold_earned = rnd.randint(5, 20)  
            gold += gold_earned
            print(f"You gained 10 XP and {gold_earned} gold! Total Gold: {gold}")
            print("----------------------------------")
            print(rnd.choice(gamedata["BATTLE_WIN_MESSAGES"]))
            print("----------------------------------")
            input("\nPress [Enter] to continue...")
            break
            
        # --- MONSTER ATTACK PHASE ---
        print(f"\n--- {current_mob['name'].upper()}'S TURN ---")
        incoming_damage = current_mob["attack"]
        
        if is_guarding:
            incoming_damage = incoming_damage // 2 
            print("Your shield absorbs half the damage.")
            is_guarding = False 
            
        health -= incoming_damage
        print(f"The {current_mob['name']} attacks you for {incoming_damage} damage! (Your HP: {max(0, health)}/{max_health})")
        
        # --- LOSE CHECK ---
        if health <= 0:
            print("----------------------------------")
            print(rnd.choice(gamedata["LOSS_MESSAGES"]))
            print("----------------------------------")
            input("\nPress [Enter] to continue...")
            break

def level_checker():
    global level, xp, health, max_health, attack, attackmin, criticalchance
    if xp >= 100 and level == 0:
        level += 1
        attack_inc = rnd.randint(1, 10)
        hp_inc = rnd.randint(5, 15)
        attack += attack_inc
        max_health += hp_inc
        health += hp_inc
        attackmin = max(1, attack - 10)
        criticalchance = 3
        print(f"\nLevel {level} reached.")
        input("\nPress [Enter] to continue...")
    elif xp >= 150 and level == 1:
        level += 1
        attack_inc = rnd.randint(1, 10)
        hp_inc = rnd.randint(5, 15)
        attack += attack_inc
        max_health += hp_inc
        health += hp_inc
        attackmin = max(1, attack - 8)
        criticalchance = 7
        print(f"\nLevel {level} reached.")
        input("\nPress [Enter] to continue...")
    elif xp >= 200 and level == 2:
        level += 1
        attack_inc = rnd.randint(1, 10)
        hp_inc = rnd.randint(5, 15)
        attack += attack_inc
        max_health += hp_inc
        health += hp_inc
        attackmin = max(1, attack - 13)
        criticalchance = 10
        print(f"\nLevel {level} reached.")
        input("\nPress [Enter] to continue...")

def open_inventory():
    global health, max_health, attack, equipped_weapon, equipped_armor
    clear_screen()
    if not player_inventory:
        print("Your inventory is empty.")
        input("\nPress [Enter] to return...")
        return

    print("--- INVENTORY ---")
    print(f"Equipped: [Weapon: {equipped_weapon or 'None'}] | [Armor: {equipped_armor or 'None'}]")
    
    for index, item in enumerate(player_inventory, start=1):
        print(f"  [{index}] {item}")
    print("  [0] Close Bags")

    try:
        choice = int(input("\nChoose an item number to use/equip: "))
        if choice == 0: 
            return
        
        if 1 <= choice <= len(player_inventory):
            item_to_use = player_inventory.pop(choice - 1)

            # --- POTIONS ---
            if item_to_use == "Health Potion":
                health += 20
                if health > max_health: 
                    health = max_health
                print(f"Drank a Health Potion. Restored HP to {health}/{max_health}.")

            elif item_to_use == "Superior Health Potion":
                health += 40
                if health > max_health: 
                    health = max_health
                print(f"Drank a Superior Health Potion. Restored HP to {health}/{max_health}.")

            # --- WEAPONS ---
            elif "Sword" in item_to_use or "Weapon" in item_to_use:
                # Unequip existing weapon if present
                if equipped_weapon == "Iron Sword":
                    attack -= 4
                    player_inventory.append(equipped_weapon)
                
                # Equip new weapon
                equipped_weapon = item_to_use
                if item_to_use == "Iron Sword":
                    attack += 4
                    print("Equipped Iron Sword. (+4 ATK)")

            # --- ARMOR ---
            elif "Armor" in item_to_use:
                # Unequip existing armor stats and return to inventory
                if equipped_armor == "Leather Armor":
                    max_health -= 15
                    player_inventory.append(equipped_armor)
                elif equipped_armor == "Iron Armor":
                    max_health -= 30
                    player_inventory.append(equipped_armor)
                elif equipped_armor == "Fighters Garments":
                    max_health -= 30
                    attack -= 10
                    player_inventory.append(equipped_armor)
                elif equipped_armor == "Superium Armor":
                    max_health -= 120
                    player_inventory.append(equipped_armor)

                # Equip new armor
                if item_to_use == "Leather Armor":
                    max_health += 15
                    health += 15
                    equipped_armor = "Leather Armor"
                    print("Equipped Leather Armor. (+15 Max HP)")
                elif item_to_use == "Iron Armor":
                    max_health += 30
                    health += 30
                    equipped_armor = "Iron Armor"
                    print("Equipped Iron Armor. (+30 Max HP)")
                elif item_to_use == "Fighters Garments":
                    max_health += 30
                    health += 30
                    attack += 10
                    equipped_armor = "Fighters Garments"
                    print("Equipped Fighters Garments. (+30 Max HP, +10 ATK)")
                elif item_to_use == "Superium Armor":
                    max_health += 120
                    health += 120
                    equipped_armor = "Superium Armor"
                    print("Equipped Superium Armor. (+120 Max HP)")
                
                if health > max_health:
                    health = max_health

            else:
                print(f"Used {item_to_use}!")

            input("\nPress [Enter] to continue...")

    except ValueError:
        print("Invalid choice.")
        input("\nPress [Enter] to continue...")

def display_status():
    """Prints current player stats."""
    clear_screen()
    print("--- CHARACTER STATS ---")
    print(f" Level: {level} | XP: {xp}")
    print(f" HP: {health}/{max_health}")
    print(f" ATK: {attackmin}-{attack}")
    print(f" Crit Chance: {criticalchance}%")
    print(f" Gold: {gold}")
    print(f" Equipped Weapon: {equipped_weapon or 'None'}")
    print(f" Equipped Armor: {equipped_armor or 'None'}")
    input("\nPress [Enter] to return...")

def intermission_menu():
    """Intermission hub between encounters for managing equipment and travel."""
    global current_region, current_tier

    available_items = list(gamedata["SHOP_POOL"].keys())
    shop_size = min(len(available_items), rnd.randint(3, 5))
    showcase_names = rnd.sample(available_items, shop_size)
    
    while True:
        clear_screen()
        print("==================================")
        print("INTERMISSION - Prepare for next battle")
        print("==================================")
        print(f"Current Destination: {current_region} ({current_tier})")
        print(" [1] Explore / Battle Next Monster")
        print(" [2] Open Backpack / Equip Gear")
        print(" [3] Visit Shop")
        print(" [4] View Character Stats")
        print(" [5] Change Location / Difficulty")
        
        choice = input("\nSelect an action (1-5): ").strip()
        
        if choice == '1':
            clear_screen()
            return True  # Resume game loop to trigger battle
        elif choice == '2':
            open_inventory()
        elif choice == '3':
            visit_shop(showcase_names)
        elif choice == '4':
            display_status()
        elif choice == '5':
            clear_screen()
            new_reg = input(f"Forest \n Dungeon \n Cemetary \n Ship \n").title()
            new_tier = input("Choose Difficulty (Easy / Medium / Hard): ").strip().title()
            if new_reg in ["Forest", "Dungeon", "Cemetary", "Ship"]:
                current_region = new_reg
            if new_tier in ["Easy", "Medium", "Hard"]:
                current_tier = new_tier
            print(f"\nNext stop set to {current_region} ({current_tier}).")
            input("\nPress [Enter] to return...")
        else:
            print("Invalid selection, try again.")

# --- MAIN GAME LOOP ---
while True:
    level_checker()
    
    # Intermission menu allows gear management before entering combat
    ready = intermission_menu()
    
    if ready:
        current_mob = spawn_enemy(current_region, current_tier)
        
        if current_mob:
            initiate_battle(current_mob)
        else:
            print(f"No monsters available in {current_region} ({current_tier}).")
            input("\nPress [Enter] to continue...")

    if health <= 0:
        clear_screen()
        print("\nGame over.")
        break