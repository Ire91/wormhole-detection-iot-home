from test_loader_run import test_loader_maps_basic_csv

if __name__ == '__main__':
    try:
        test_loader_maps_basic_csv()
        print("Loader test ran successfully")
    except AssertionError as e:
        print(f"Loader test failed: {e}")
        raise
