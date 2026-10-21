import os
import importlib.util
import inspect

PLUGIN_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "plugins")

class PluginManager:
    def __init__(self):
        self.dynamic_tools = {}
        self.dynamic_risks = {}
        self.prompt_lines = []
        self._load_plugins()

    def _load_plugins(self):
        if not os.path.exists(PLUGIN_DIR):
            os.makedirs(PLUGIN_DIR)
            
        # Create an __init__.py if missing
        init_file = os.path.join(PLUGIN_DIR, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write("# CAT Plugins Directory\n# Drop .py files here to extend CAT's capabilities dynamically.\n")

        for filename in os.listdir(PLUGIN_DIR):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = filename[:-3]
                filepath = os.path.join(PLUGIN_DIR, filename)
                
                spec = importlib.util.spec_from_file_location(module_name, filepath)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    try:
                        spec.loader.exec_module(module)
                        
                        # Load CAT_TOOLS list of functions
                        if hasattr(module, "CAT_TOOLS"):
                            for func in module.CAT_TOOLS:
                                if not callable(func):
                                    continue
                                func_name = func.__name__
                                self.dynamic_tools[func_name] = func
                                
                                # Auto-generate the LLM prompt definition using introspection
                                sig = inspect.signature(func)
                                doc = inspect.getdoc(func) or "No description provided."
                                # Clean newlines from docstring for the prompt
                                doc = " ".join(doc.split())
                                self.prompt_lines.append(f"- {func_name}{sig}: {doc}")
                                
                        # Load CAT_RISKS dictionary mapping function names to risk levels
                        if hasattr(module, "CAT_RISKS"):
                            for func_name, risk in module.CAT_RISKS.items():
                                self.dynamic_risks[func_name] = risk.upper()
                                
                    except Exception as e:
                        print(f"[PluginManager] Error loading plugin {filename}: {e}")

    def get_tools(self):
        return self.dynamic_tools
        
    def get_risks(self):
        return self.dynamic_risks

    def get_prompt_additions(self):
        if not self.prompt_lines:
            return ""
        return "\n[Dynamically Loaded Plugin Tools]\n" + "\n".join(self.prompt_lines)

# Singleton instance
plugin_manager = PluginManager()
