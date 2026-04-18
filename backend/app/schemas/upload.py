from pydantic import BaseModel


class UploadResponse(BaseModel):
    temp_path: str
    columns: list[str]
    row_count: int
    preview_rows: list[dict]
