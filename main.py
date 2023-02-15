# Imports
from src.modules.bootTrainer import boot as bootTrainer
from src.modules.bootDashboard import boot as bootDashboard
from src.modules.jpTrainerInit import init as jpTrainerInit
from src.classes.DataFile import DataFile
from src.classes.Window import Window

# Main function
def main():

    # Initializes data
    settings = DataFile("data/settings.datcs")
    if settings.get("initialBoot"): jpTrainerInit(settings)
    window = Window(settings, "Hiragana Trainer")
    scene = "trainer"
    running = True

    # Main program loop
    while running:

        # Loads trainer scene
        if scene == "trainer":
            running, scene = bootTrainer(window, settings)
        
        # Loads dashboard scene
        elif scene == "dashboard":
            running, scene = bootDashboard(window, settings)

    # Closes pygame
    window.quit()

# Main function call
if __name__ == "__main__":
    main()
