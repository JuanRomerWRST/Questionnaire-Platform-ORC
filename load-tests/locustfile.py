from pathlib import Path

from locust import HttpUser, between, task

ROOT = Path(__file__).resolve().parents[1] / "examples" / "input"


def _post(user: HttpUser, name: str, mime: str, extra: dict[str, str] | None = None):
    payload = (ROOT / name).read_bytes()
    user.client.post(
        "/api/v1/documents/extract",
        files={"file": (name, payload, mime)},
        data=extra or {"use_llm": "false"},
        name=f"/extract {name}",
    )


class DeterministicUser(HttpUser):
    wait_time = between(0.2, 0.8)

    @task
    def pdf(self):
        _post(self, "sample_questionnaire_es.pdf", "application/pdf")


class OcrUser(HttpUser):
    wait_time = between(0.5, 1.5)

    @task
    def photo(self):
        _post(self, "sample_questionnaire_photo.jpg", "image/jpeg", {"use_llm": "false", "force_ocr": "true"})


class LlmMockUser(HttpUser):
    """Usar solo con LLM_PROVIDER=mock. No dispara llamadas reales a OpenAI."""

    wait_time = between(0.2, 0.8)

    @task
    def pdf(self):
        _post(self, "sample_questionnaire_es.pdf", "application/pdf", {"use_llm": "true"})


class MixedUser(HttpUser):
    wait_time = between(0.2, 1)

    @task(3)
    def pdf(self):
        _post(self, "sample_questionnaire_es.pdf", "application/pdf")

    @task(2)
    def docx(self):
        _post(
            self,
            "sample_questionnaire_it.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    @task(1)
    def xlsx(self):
        _post(
            self,
            "sample_questionnaire_en.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
