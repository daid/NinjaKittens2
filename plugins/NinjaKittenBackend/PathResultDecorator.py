from UM.Scene.SceneNodeDecorator import SceneNodeDecorator

## Simple decorator to indicate a scene node holds resulting path data
class PathResultDecorator(SceneNodeDecorator):
    def __init__(self):
        super().__init__()
        self._paths = None
        
    def getPaths(self):
        return self._paths
    
    def setPaths(self, paths):
        self._paths = paths
