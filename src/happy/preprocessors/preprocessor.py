class Preprocessor:
    def __init__(self, **kwargs):
        self.params = kwargs
        # Handle additional positional arguments if needed

    def fit(self, data, metadata=None):
        return self
        
    def apply(self, data, metadata=None):
        raise NotImplementedError("Subclasses must implement the apply method")

    def to_string(self):
        # Get the class name
        class_name = self.__class__.__name__

        # Get the arguments from the 'params' dictionary
        arguments = ", ".join(f"{key}={value}" for key, value in self.params.items())

        return f"{class_name}({arguments})"