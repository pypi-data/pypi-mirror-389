import sys
from effspm import mine

def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <data_file> <minsup>")
        sys.exit(1)

    data_file = sys.argv[1]
    try:
        minsup = float(sys.argv[2])
    except ValueError:
        print("minsup must be a number (e.g. 0.01)")
        sys.exit(1)

    patterns = mine(data_file, minsup)
    print(f"Found {len(patterns)} patterns\n")
    for pat in patterns[:10]:
        print(pat)

if __name__ == "__main__":
    main()