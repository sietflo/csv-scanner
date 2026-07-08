import os
from flask import Flask, render_template, request
import pandas as pd
import plotly.express as px

app = Flask(__name__)


def make_chart(df, column_name):
    """Будує гістограму для числової колонки і повертає HTML-код графіка."""
    fig = px.histogram(df, x=column_name, nbins=30, title=column_name)

    fig.update_layout(
        paper_bgcolor="#2d2d2d",
        plot_bgcolor="#252526",
        font_color="#ffffff",
        title_font_color="#ffffff",
        margin=dict(l=40, r=20, t=40, b=40),
        height=350,
    )
    fig.update_traces(marker_color="#28a745")
    fig.update_xaxes(gridcolor="#3c3c3c")
    fig.update_yaxes(gridcolor="#3c3c3c")
    return fig.to_html(full_html=False, include_plotlyjs=False)


@app.route("/", methods=["GET", "POST"])
def index():
    summary_html = None
    info_data = None
    charts = []

    if request.method == "POST":
        # Перевіряємо, чи завантажили файл
        file = request.files.get("file")
        if file and file.filename.endswith(".csv"):
            df = pd.read_csv(file.stream)

            # 1. Загальна статистика для числових колонок
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

            # 3. Інтерактивні графіки для числових колонок
            numeric_cols = df.select_dtypes(include="number").columns
            for col in numeric_cols:
                chart_html = make_chart(df, col)
                charts.append({"name": col, "html": chart_html})

    return render_template(
        "index.html",
        summary_table=summary_html,
        info_table=info_data,
        charts=charts,
    )

if __name__ == "__main__":
    app.run(debug=True, port=8000)