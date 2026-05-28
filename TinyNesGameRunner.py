import subprocess

from TinyNesLogger import TinyNesLogger


class TinyNesGameRunner:
    def __init__(self):
        self.startedOnce = False
        self.runningChild = None

    @staticmethod
    def KillGame(popenObj):
        if popenObj == None or popenObj.poll() != None:
            return
        popenObj.terminate()
        try:
            popenObj.wait(5)
            # 5 seconds is definitely long enough for the user to notice the hang
            # but we can't very well start another emulator with the first one running
        except subprocess.TimeoutExpired:
            popenObj.kill()

    def SetRunningGame(self, commandArgs) -> bool:
        #there is a race condition if the user manages to stick in a game and hit reset really fast before the first game launch
        #or just hits the reset button twice really, really fast
        #could be fixed with a lock, but really, if the user plays stupid games they can win stupid prizes
        self.startedOnce = True  #startedOnce indicates we tried, not necessarily succeeded
        rc = self.runningChild
        self.runningChild = None
        if rc != None:
            TinyNesGameRunner.KillGame(rc)
            rc = None
        if commandArgs != None:  #None means kill running game and just show background
            try:
                rc = subprocess.Popen(commandArgs)
            except Exception as inst:
                TinyNesLogger.log_exception(inst)
        if rc != None:
            self.runningChild = rc
            return True
        return False
