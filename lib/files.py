import os

def project_root_dir():
  # /path/to/project/lib/path.py
  script_path = os.path.abspath(__file__)
  
  # /path/to/project/lib/
  script_dir = os.path.split(script_path)[0] 
  
  # /path/to/project/lib/../ ie /path/to/project/
  return os.path.join(script_dir, '../')
