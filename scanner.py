import os
from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/", methods=["GET", "POST"])
def index():
    summary_html = None
    info_data = None

    if request.method == "POST":
        # Перевіряємо, чи завантажили файл
        file = request.files.get("file")
        if file and file.filename.endswith(".csv"):
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)

            # Магія Pandas
            df = pd.read_csv(file_path)

            # 1. Загальна статистика для числових колонок (.describe())
            summary_html = df.describe().to_html(
                classes="table table-striped", border=0
            )

            # 2. Інформація про колонки, типи даних та пропуски
            info_df = pd.DataFrame(
                {
                    "Тип даних": df.dtypes.astype(str),
                    "Заповнених значень": df.count(),
                    "Пропущених значень": df.isnull().sum(),
                }
            )
            info_data = info_df.to_html(classes="table table-hover", border=0)

            # Видаляємо файл після обробки, щоб не засмічувати сервер
            os.remove(file_path)

    return render_template(
        "index.html", summary_table=summary_html, info_table=info_data
    )

if __name__ == "__main__":
    app.run(debug=True, port=8000)