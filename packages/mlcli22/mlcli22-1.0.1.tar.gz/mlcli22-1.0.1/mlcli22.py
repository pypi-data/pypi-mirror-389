import os
import subprocess
import yaml
import typer
from pathlib import Path

app = typer.Typer()

folders = ["notebooks", "etl", "model", "api"]

files = {
    "etl/etl_class.py": "class ETL:\n    def extract(self): pass\n    def transform(self): pass\n    def load(self): pass\n",
    "etl/etl.py": "from etl_class import ETL\n\netl = ETL()\netl.extract()\netl.transform()\netl.load()\n",
    "model/model_class.py": "class Model:\n    def train(self, data): pass\n    def predict(self, input_data): pass\n",
    "model/train.py": "from model_class import Model\n\nmodel = Model()\nmodel.train(data=None)\n",
    "api/app.py": "from flask import Flask, request, jsonify\nfrom model.model_class import Model\n\napp = Flask(__name__)\nmodel = Model()\n\n@app.route('/predict', methods=['POST'])\ndef predict():\n    data = request.json\n    prediction = model.predict(data)\n    return jsonify(prediction)\n\nif __name__ == '__main__':\n    app.run()\n",
    "api/bridge.yaml": "bridge:\n  description: Conexión entre API y modelo\n  endpoints:\n    - /predict\n"
}

metadata_template = "name: {app_name}\nversion: 1.0.0\ndocker_image: python:3.10\n"

task_yaml_content = """tasks:
  - name: example_dataset
    type: ETL
    script: etl/etl.py

  - name: model_training
    type: MODEL
    script: model/train.py
"""

@app.command()
def create(app_name: str):
    os.makedirs(app_name, exist_ok=True)
    for folder in folders:
        os.makedirs(os.path.join(app_name, folder), exist_ok=True)

    for path, content in files.items():
        full_path = os.path.join(app_name, path)
        with open(full_path, "w") as f:
            f.write(content)

    with open(os.path.join(app_name, ".metadata"), "w") as f:
        f.write(metadata_template.format(app_name=app_name))

    with open(os.path.join(app_name, "task.yaml"), "w") as f:
        f.write(task_yaml_content)

    print(f"Aplicación ML '{app_name}' creada con estructura completa.")

@app.command()
def info():
    if Path(".metadata").exists():
        with open(".metadata") as f:
            print(f.read())
    else:
        print("Archivo .metadata no encontrado.")

@app.command()
def version():
    print("MLCLI v1.0.0")

@app.command()
def run_task(task_name: str):
    if not Path("task.yaml").exists():
        print("Archivo task.yaml no encontrado.")
        raise typer.Exit()

    with open("task.yaml", "r") as f:
        data = yaml.safe_load(f)

    tasks = data.get("tasks", [])
    task = next((t for t in tasks if t["name"] == task_name), None)

    if not task:
        print(f"Tarea '{task_name}' no encontrada.")
        raise typer.Exit()

    script = task.get("script")
    if not script or not Path(script).exists():
        print(f"Script '{script}' no encontrado.")
        raise typer.Exit()

    print(f"Ejecutando tarea '{task_name}' con script '{script}'...")
    subprocess.run(["python", script])

if __name__ == "__main__":
    app()