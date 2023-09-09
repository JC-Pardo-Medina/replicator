# Import necessary modules and libraries
import argparse
import sys
import time
import os
import shutil
import datetime

def main(source_folder,destination_folder,interval,log_path):
    """
    Main function responsible for periodically synchronizing folders at the provided interval.

    Args:
        source_folder (str): Path of the source folder to be replicated.
        destination_folder (str): Path of the destination folder where content will be replicated.
        interval (int): Interval (in seconds) for folder replication.
        log_path (str): Path to the log file where replication activities will be recorded.
    """
    try:
        while True:
            # This loop will run periodically to synchronize folders.
            start_time = time.time()  # Record the time before the synchronization
            folder_synchronization(source_folder, destination_folder, log_path)
            # It waits the amount of time of the interval minus the time of the synchronization. If it took more than the time of the interval it starts immediately.
            time.sleep(max(0, interval + start_time - time.time()))
    except KeyboardInterrupt:
        # Handle the termination of the script when the user presses Ctrl+C.
        print("Script terminated by user.")
        sys.exit(0)

def same_file_check(source_item,dest_item):
    """
    Check if two items (files or folders) are different based on their attributes (size and last modification date).

    Args:
        source_item (str): Path to the source file or directory.
        dest_item (str): Path to the destination file or directory.

    Returns:
        bool: True if the items should be copied; False otherwise.
    """
    if not os.path.exists(dest_item):
        return True
    elif not os.path.isdir(source_item):
        return not (os.path.getmtime(dest_item) == os.path.getmtime(source_item) and
                    os.path.getsize(dest_item) == os.path.getsize(source_item))
    else:
        return False

def update_log(content,hour,log):
    """
    Update the synchronization log with provided content. If the log file does not exist,
    it will be created.

    Args:
        content (list): A list of strings containing relevant synchronization messages.
        hour (datetime): The timestamp representing the time when synchronization started.
        log (str): The path to the log file where synchronization updates will be recorded.
    """
    log_timestamp = hour.strftime("%Y-%m-%d at %H:%M:%S.%f")
    log_message = f"\n\nIn the synchronization of {log_timestamp}, the following updates have been made:\n"
    # Check if the log file exists; create it if it doesn't.
    if not os.path.exists(log):
        try:
            with open(log, "w"):
                content.append(f"Info: Created log at {log} because it didn't exist.")
        except Exception as e:
            print(f"Error: Log at {log} didn't exist and failed to create it due to {e}.")
    # Print log message and content to the console.
    print(log_message)
    if len(content) == 0:
        print("Info: No changes have been made.")
    else:
        print("\n".join(content))
    # Append log message and content to the log file.
    try:
        with open(log, "a") as log_file:
            log_file.write(log_message)
            if len(content) == 0:
                log_file.write(f"Info: No changes have been made.\n")
            else:
                log_file.write("\n".join(content))
    except Exception as e:
        print(f"Error: Failed to open {log} for writing due to {e}.")
    

def folder_synchronization(source_folder,destination_folder,log_path):
    """
    Compare the content of the source and destination folder, identify differences, and take appropriate actions
    such as copying files, creating directories, and removing files or directories as needed.

    Args:
        source_folder (str): Path of the source folder to be replicated.
        destination_folder (str): Path of the destination folder where content will be replicated.
        log_path (str): Path to the log file where synchronization activities will be recorded.
    """
    hour = datetime.datetime.now()
    items_to_remove = list()
    # The list were the synchronization messages get appended for the log later. All creation, copying and removal activities gets appended.
    messages_for_log = list()
    # Check if the source folder exists
    if not os.path.exists(source_folder):
        messages_for_log.append(f"Error: Failed to synchronize '{source_folder}' because it does not exist or it is not a directory.")
        update_log(messages_for_log, hour, log_path)
        return
    # Check if the destination folder exists; create if it doesn't
    if not os.path.exists(destination_folder):
        try:
            os.makedirs(destination_folder)
            messages_for_log.append(f"Info: Created {destination_folder} because it doesn't exist.")
        except Exception as e:
            messages_for_log.append(f"Error: Failed to create {destination_folder} due to error: {str(e)}. Exiting synchronization.")
            update_log(messages_for_log, hour, log_path)
            return
    # Compare destination with source to identify items for removal
    for root, dirs, files in os.walk(destination_folder, topdown=False):
        for item in dirs + files:
            dest_item = os.path.join(root, item)
            source_item = os.path.join(source_folder, os.path.relpath(dest_item, destination_folder))
            if not os.path.exists(source_item):
                items_to_remove.append(dest_item)
    # Remove identified items that are not present in the source folder
    for item in items_to_remove:
        try:
            if os.path.isdir(item):
                os.rmdir(item)
            else:
                os.remove(item)
            messages_for_log.append(f"Info: Removed {item}.")
        except Exception as e:
            messages_for_log.append(f"Error: Failed to remove {item} due to error: {str(e)}.")
    # Compare source with destination and perform necessary actions
    for root, dirs, files in os.walk(source_folder):
        for item in dirs + files:
            source_item = os.path.join(root, item)
            dest_item = os.path.join(destination_folder, os.path.relpath(source_item, source_folder))
            #Check if the item is in source but not in destination.
            if same_file_check(source_item,dest_item):
                #If that is the case and the item is a directory, creates it in destination.
                if os.path.isdir(source_item):
                    try:
                        os.makedirs(dest_item)
                        messages_for_log.append(f"Info: Created {dest_item}.")
                    except Exception as e:
                        messages_for_log.append(f"Error: Failed to create {dest_item} due to error: {str(e)}.")
                #If the item is a file, copies it in destination.
                else:
                    try:
                        shutil.copy2(source_item,dest_item)
                        messages_for_log.append(f"Info: {source_item} copied to {dest_item}.")
                    except Exception as e:
                        messages_for_log.append(f"Error: Failed to copy {source_item} to {dest_item} due to error: {str(e)}.")
    # Update the log with synchronization messages
    update_log(messages_for_log,hour,log_path)

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="This program automates the replication of content from a source folder to a destination folder at user-defined intervals. It can also log replication activities to an optional log file.")
    parser.add_argument("--source_folder", "-sf", required=True, help="Path of the source folder to be replicated.")
    parser.add_argument("--destination_folder", "-df", required=True, help="Path of the destination folder where content will be replicated.")
    parser.add_argument("--interval", "-i", required=True, type=int, help="Interval (in seconds) for folder replication.")
    parser.add_argument("--log", "-l", required=True, help="Path to the log file where replication activities will be recorded.")
    args = parser.parse_args()
    # Extract command-line arguments
    source_folder=args.source_folder
    destination_folder=args.destination_folder
    interval=args.interval
    log_path=args.log
    # Start the main synchronization process
    main(source_folder,destination_folder,interval,log_path)
