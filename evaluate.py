import sys

if __name__ == '__main__':
    # Build evaluation metric for parsing effectiveness
    with open('successful_tests.txt', "a+") as f:
        successful=sum(1 for _ in f)
    with open('failed_tests.txt', "a+") as f:
        failed =sum(1 for _ in f)
    print(f'\n\n The parsing program successfully parsed {round(100*successful/(successful+failed),4)} % of files.')