# Imports
from src.classes.DataFile import DataFile

# Initial program configuration
def init(settings):
    
    # Sets settings to defaults
    originalSettings = DataFile("data/annotatedSettings.datcs")
    for key in originalSettings.data:
        settings.set(key, originalSettings.data[key])
    
    # Sets fetched resolution and saves
    settings.save()
