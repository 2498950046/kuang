import os

from dotenv import load_dotenv

from backendAdmin.app import create_app

load_dotenv()

app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5002))
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)
