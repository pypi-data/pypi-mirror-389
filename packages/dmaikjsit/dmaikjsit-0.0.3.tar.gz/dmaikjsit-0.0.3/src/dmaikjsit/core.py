# --- Add this entire function to your .py file ---

import importlib.resources
import os
import shutil

def get_all_codes_main():
    """
    The main entry point for the 'get-dmai-codes' command.
    It copies all files from the package's 'codes' directory
    into the user's current working directory.
    """
    # 1. Define the source package/directory
    package_name = "dmaikjsit"
    resource_dir = "codes"
    
    try:
        # 2. Find all files in that directory
        package_path = importlib.resources.files(f"{package_name}.{resource_dir}")

        # 3. Get the user's current directory
        target_dir = os.getcwd()
        print(f"Copying Dmai codes to: {target_dir}")

        copied_count = 0
        # 4. Iterate and copy each file
        for item in package_path.iterdir():
            if item.is_file():
                file_name = item.name
                source_file_path = str(item)
                target_file_path = os.path.join(target_dir, file_name)

                if os.path.exists(target_file_path):
                    print(f"- Skipping '{file_name}' (already exists)")
                    continue

                shutil.copy(source_file_path, target_file_path)
                print(f"+ Copied '{file_name}'")
                copied_count += 1
        
        print(f"\nDone! Copied {copied_count} new file(s).")

    except ModuleNotFoundError:
        print(f"Error: Could not find package path '{package_name}.{resource_dir}'.")
        print("Did you forget the empty __init__.py in the 'codes' folder?")
    except Exception as e:
        print(f"An error occurred: {e}")