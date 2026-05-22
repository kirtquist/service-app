"""Run the API with uvicorn (Cloud Run entrypoint)."""

import os


def run() -> None:
    import uvicorn

    port = int(os.environ.get("PORT", "8090"))
    uvicorn.run(
        "service_app.api.app:app",
        host="0.0.0.0",
        port=port,
        reload=False,
    )


if __name__ == "__main__":
    run()
