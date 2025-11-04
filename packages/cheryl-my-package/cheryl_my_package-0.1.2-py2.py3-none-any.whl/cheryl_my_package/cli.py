def main():
    import argparse
    from .core import CoreClass

    parser = argparse.ArgumentParser(description="My Package Command Line Interface")
    parser.add_argument('--method', type=str, help='Method to execute: method_one or method_two')
    
    args = parser.parse_args()

    core_instance = CoreClass()

    if args.method == 'method_one':
        result = core_instance.method_one()
        print(f"Result from method_one: {result}")
    elif args.method == 'method_two':
        result = core_instance.method_two()
        print(f"Result from method_two: {result}")
    else:
        print("Please specify a valid method: method_one or method_two.")

if __name__ == "__main__":
    main()