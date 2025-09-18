# -*- coding: utf-8 -*-
"""
Created on Wed Sep 10 15:55:00 2025

@author: imbl
"""
import sys

if __name__ == "__main__":
    print("All arguments:", sys.argv)
    print("Script name:", sys.argv[0])
    if len(sys.argv) > 1:
        print("First argument:", sys.argv[1])
        print("Other arguments:", sys.argv[1:])
    seqList=sys.argv[1]
    print(f'Sequence three is: {seqList[3]}')