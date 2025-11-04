"""
Example script demonstrating how to use TaskFlow to run a pipeline.

This script loads a YAML configuration file and executes all defined tasks.
"""

from taskflow import TaskFlow


def main() -> None:
    """
    Main function to execute the TaskFlow pipeline.
    """
    print("=" * 60)
    print("TaskFlow Pipeline Execution Example")
    print("=" * 60)
    print()
    
    # Initialize TaskFlow with the configuration file
    pipeline = TaskFlow("examples/tasks.yaml")
    
    # Execute the pipeline
    try:
        pipeline.run()
        print()
        print("=" * 60)
        print("Pipeline completed successfully!")
        print("=" * 60)
    except Exception as e:
        print()
        print("=" * 60)
        print(f"Pipeline failed: {str(e)}")
        print("=" * 60)
        raise


if __name__ == "__main__":
    main()
