"""
This file holds the main logic for the 'get-dmai-codes' command.
"""
import importlib.resources
import shutil
import os

# This is the name of your Python package
PACKAGE_NAME = "my_cool_library"
DATA_FOLDER = "data"

def main():
    """
    The main function that runs when the user types 'get-dmai-codes'.
    """
    
    # This gets the CURRENT directory the user is in
    destination_dir = os.getcwd()

    print(f"Attempting to copy 'Dmai codes' to: {destination_dir}")

    try:
        # This is the modern (Python 3.9+) way to get a path to package data
        with importlib.resources.files(f"{PACKAGE_NAME}.{DATA_FOLDER}") as data_path:
            
            # 'data_path' is now the exact path to the 'data' folder
            # (e.g., C:\..._packages\my_cool_library\data)
            
            print(f"Found data folder at: {data_path}")

            # We list all files inside that folder
            file_count = 0
            for file_name in os.listdir(data_path):
                if file_name == "__init__.py":
                    continue # Skip the Python package file

                source_file = os.path.join(data_path, file_name)
                dest_file = os.path.join(destination_dir, file_name)
                
                # Copy the file from the 'site-packages' folder to the user's current folder
                print(f"  Copying '{file_name}'...")
                shutil.copy2(source_file, dest_file)
                file_count += 1
                
            print(f"\nSuccessfully copied {file_count} files!")

    except ModuleNotFoundError:
        print(f"Error: Could not find the package '{PACKAGE_NAME}'.")
        print("Please make sure 'dmaikjsit' is installed (`pip install dmaikjsit`)")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()