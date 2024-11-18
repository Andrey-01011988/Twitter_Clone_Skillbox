import os

from flask import Flask, render_template, send_from_directory


root_dir = os.path.dirname(os.path.abspath(__file__))
template_folder = os.path.join(root_dir, "templates")
static_folder = os.path.join(root_dir, "static")
HOST = '0.0.0.0'
PORT = 5000

app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)


@app.route("/")
def index():
    return render_template("new_index.html")


if __name__ == "__main__":
    app.run(host=HOST, port=PORT)
    # print(root_dir)
    # print(static_folder)
    # print(template_folder)