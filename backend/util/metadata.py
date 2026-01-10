from pathlib import Path

def getMetadata(file_path):

    # Make sure file is actually supported
    extension = Path(file_path).suffix
    if extension not in [".png", ".jpg", ".jpeg"]:
        return []
    
    stats = Path(file_path).stat()

    # Creation time, extension, last access time
    # BTW you may have to edit the creation time attribute for Windows systems
    return [stats.st_birthtime, extension, stats.st_atime]
    

def getDateHeuristic():
    pass

def getExtensionHeuristic():
    pass

def getLastAccessHeuristic():
    pass
