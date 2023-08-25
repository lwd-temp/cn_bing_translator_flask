import flask

from cn_bing_translator import Translator

app = flask.Flask(__name__)


def default_string_handler(query, default):
    if query is None:
        return default
    else:
        return query


# Route /api/translate
@app.route("/api/translate", methods=["POST"])
def translate():
    body = flask.request.get_json(force=True, silent=False)
    source = default_string_handler(body["source"], "")
    fromLang = default_string_handler(body["fromLang"], "auto-detect")
    toLang = default_string_handler(body["toLang"], "en")

    translator = Translator(fromLang=fromLang, toLang=toLang, cnBing=False)

    result = translator.process(source)

    result_json = {
        "result": result,
        "fromLang": fromLang,
        "toLang": toLang,
        "source": source
    }

    return flask.jsonify(result_json)


# Route /
@app.route("/")
def index():
    return flask.render_template("index.html")


if __name__ == "__main__":
    app.run()
