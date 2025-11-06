from dataclasses import dataclass
import subprocess
import os
import sys


@dataclass
class FrontendHander:

    def init_frontend(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        frontend_path = os.path.abspath(os.path.join(script_dir, "../../frontend"))
        os.chdir(frontend_path)

        node_modules_path = os.path.join(frontend_path, "node_modules")

        if not os.path.exists(node_modules_path):
            try:
                subprocess.run(["npm", "i", "--silent"])
                subprocess.run(["npm", "run", "dev"])
            except subprocess.CalledProcessError as e:
                print(f"Error building frontend: {e}")
                sys.exit(1)
        else:
            subprocess.run(["npm", "run", "dev"])
