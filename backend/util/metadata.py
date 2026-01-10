from pathlib import Path
import time
import math

def getMetadata(file_path):

    # Make sure file is actually supported
    extension = Path(file_path).suffix
    if extension not in [".png", ".jpg", ".jpeg"]:
        return []
    
    stats = Path(file_path).stat()

    # Creation time, extension, last access time
    # BTW you may have to edit the creation time attribute for Windows systems
    return [stats.st_birthtime, extension, stats.st_atime]
    
# Doesn't implement sortByOld for now
# The greater a is, the slower the score decay
def getDateHeuristic(btime, sortByNew=True, a=500):

    curr_time = time.time()

    # f(x, a=500) = 1/ln(1/a * x + e), so f(0) = 1
    return 1 / math.log(1 / a * (curr_time - btime) + math.e)

def getExtensionHeuristic(extension, target_extensions):
    if extension in target_extensions:
        return 1
    else:
        return 0

# Doesn't implement sortByOld for now
def getLastAccessHeuristic(atime, sortByNew=True, a=500):

    curr_time = time.time()

    # f(x, a=500) = 1/ln(1/a * x + e), so f(0) = 1
    return 1 / math.log(1 / a * (curr_time - atime) + math.e)