import sys, os



path = os.getcwd()

if os.path.isfile(sys.argv[1]):
    os.remove(sys.argv[1])    

full_path = os.path.join(path, sys.argv[1])