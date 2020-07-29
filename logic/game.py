import argparse
from agents import agent

def main():
    args = parse_args()
    if len(args.agents) != 3 and len(args.agents) != 4:
        raise ValueError(f'Invalid number of players! got {len(args.agents)} agents.')
    

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-a', '--agents',
        help='Agents type', type=str.lower, # This casts the input into lowercase
        metavar="agent", default='random', nargs='+')
    args = parser.parse_args()
    return args
    

if __name__ == "__main__":
    main()